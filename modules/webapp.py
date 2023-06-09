import modules.utils as utils
import os
import redis
import logging
from modules.videoinfo import VideoInfo
from flask import Flask, render_template, jsonify, request, send_file
from modules.analyze import Analyzer


# encapsulates the functions for the web service so they can be run in a new thread
def webapp_thread(port_number, debugMode=False, logHandlers=[]):
    app = Flask(import_name="vsmp-plus", static_folder=os.path.join(utils.DIR_PATH, 'web', 'static'),
                template_folder=os.path.join(utils.DIR_PATH, 'web', 'templates'))

    # add handlers for this app
    for h in logHandlers:
        app.logger.addHandler(h)

    # set log level
    logLevel = 'INFO' if not debugMode else 'DEBUG'
    app.logger.setLevel(getattr(logging, logLevel))

    # turn of web server logging if not in debug mode
    if(not debugMode):
        werkzeug = logging.getLogger('werkzeug')
        werkzeug.disabled = True

    db = redis.Redis('localhost', decode_responses=True)

    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html', status=utils.read_db(db, utils.DB_PLAYER_STATUS),
                               config=utils.get_configuration(db))

    @app.route('/setup', methods=['GET'])
    def setup_view():
        return render_template('setup.html', config=utils.get_configuration(db))

    @app.route('/screenshot', methods=['GET'])
    def screenshot_view():
        return render_template('screenshot.html', file_info=utils.read_db(db, utils.DB_LAST_PLAYED_FILE))

    @app.route('/analyze', methods=['GET'])
    def setup_analyze():
        return render_template('analyze.html', config=utils.get_configuration(db))

    @app.route('/api/configuration', methods=['GET'])
    def get_configuration():
        return jsonify(utils.get_configuration(db))

    @app.route('/api/configuration', methods=['POST'])
    def save_configuration():
        result = {'success': True, 'message': 'Settings Updated'}

        # get the request data and do some verification
        data = request.get_json(force=True)

        # if passed get current config
        currentConfig = utils.get_configuration(db)

        # merge changed values into current and save
        currentConfig.update(data)

        checkConfig = utils.validate_configuration(currentConfig)

        if(checkConfig[0]):
            utils.write_db(db, utils.DB_CONFIGURATION, currentConfig)
        else:
            result['success'] = False
            result['message'] = checkConfig[1]

        return jsonify(result)

    @app.route('/api/control/<action>', methods=['POST'])
    def execute_action(action):
        result = {'success': True, 'message': '', 'action': action}

        # get the action
        if(action in ['pause', 'resume']):
            # store the new value
            utils.write_db(db, utils.DB_PLAYER_STATUS, {'running': action == 'resume'})  # eval to True/False
            result['message'] = f"Action {action} executed"
        elif(action in ['next', 'prev']):
            config = utils.get_configuration(db)

            if(config['mode'] == 'dir'):
                nextVideo = utils.read_db(db, utils.DB_LAST_PLAYED_FILE)

                # use the info parser to find the next or previous video
                info = VideoInfo(utils.get_configuration(db))
                if(action == 'next'):
                    nextVideo = info.find_next_video(nextVideo['file'])
                else:
                    nextVideo = info.find_prev_video(nextVideo['file'])

                # save the video file
                utils.write_db(db, utils.DB_LAST_PLAYED_FILE, nextVideo)
                result['message'] = f"Next video will be {nextVideo['name']}"
            else:
                result['success'] = False
                result['message'] = 'Cannot use next/prev actions when in file mode'
        elif(action == 'seek'):
            # get the seek amount as a percent
            data = request.get_json(force=True)

            if('amount' in data and data['amount'] > 0 and data['amount'] <= 100):
                nextVideo = utils.read_db(db, utils.DB_LAST_PLAYED_FILE)

                if('file' in nextVideo):
                    # see to this value
                    info = VideoInfo(utils.get_configuration(db))
                    nextVideo = info.seek_video(nextVideo, data['amount'])

                    result['message'] = f"Seeking to {data['amount']:.2f} percent on next update"
                    result['data'] = nextVideo

                    # save the new position
                    utils.write_db(db, utils.DB_LAST_PLAYED_FILE, nextVideo)
                else:
                    result['success'] = False
                    result['message'] = 'No video loaded to seek'
            else:
                result['success'] = False
                result['message'] = 'Value must be between 0 and 100'
        else:
            result['success'] = False
            result['message'] = 'Not a valid control action'

        return jsonify(result)

    @app.route('/api/screenshot', methods=['GET'])
    def screenshot():
        # load the image from tmp directory and output as response
        return send_file(os.path.join(utils.TMP_DIR, 'screenshot.png'), mimetype="image/png")

    @app.route('/api/status', methods=['GET'])
    def status():
        lastPlayed = utils.read_db(db, utils.DB_LAST_PLAYED_FILE)

        # set the player status
        pStatus = utils.read_db(db, utils.DB_PLAYER_STATUS)
        pStatus.update(utils.read_db(db, utils.DB_NEXT_RUN))
        pStatus.update(utils.read_db(db, utils.DB_LAST_RUN))

        lastPlayed['player'] = pStatus

        # set some dummy values if no file loaded
        if('file' not in lastPlayed):
            lastPlayed['file'] = ''
            lastPlayed['name'] = 'No file loaded'
            lastPlayed['percent_complete'] = 0
            lastPlayed['pos'] = 0
            lastPlayed['info'] = {}

        return jsonify(lastPlayed)

    @app.route('/api/analyze', methods=['POST'])
    def run_analyzer():
        result = {'success': True, 'message': ''}

        # verify the given configuration settings
        data = request.get_json(force=True)
        checkConfig = utils.validate_configuration(data)

        if(checkConfig[0]):
            result['message'] = 'Done'

            # run the analyzer
            analyze = Analyzer(data, db)

            result['data'] = analyze.run(utils.read_db(db, utils.DB_LAST_PLAYED_FILE))
        else:
            result['success'] = False
            result['message'] = checkConfig[1]

        return jsonify(result)

    @app.route('/api/browse_files/', methods=['GET'], defaults={'browse_path': ''})
    @app.route('/api/browse_files/<path:browse_path>', methods=['GET'])
    def list_directory(browse_path):
        browse_path = f"/{browse_path}"  # add slash to start path from root

        while(not os.path.exists(browse_path)):
            browse_path = os.path.dirname(browse_path)

        # if path is a file, get directory
        if(os.path.isfile(browse_path)):
            browse_path = os.path.dirname(browse_path)

        # get a list of all the directories
        dirs = sorted([name for name in os.listdir(browse_path) if os.path.isdir(os.path.join(browse_path, name))])

        # get a list of all the files, filter on valid video files
        files = utils.list_video_files(browse_path)

        return jsonify({'success': True, 'dirs': dirs, 'files': files, 'path': browse_path})

    # run the web app
    app.run(debug=debugMode, host='0.0.0.0', port=port_number, use_reloader=False)
