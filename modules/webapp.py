import modules.utils as utils
import os
import redis
import json
from modules.videoinfo import VideoInfo
from flask import Flask, render_template, flash, url_for, jsonify, request
from modules.analyze import Analyzer

# encapsulates the functions for the web service so they can be run in a new thread
def webapp_thread(port_number, debugMode=False):
    app = Flask(import_name="vsmp-plus", static_folder=os.path.join(utils.DIR_PATH, 'web', 'static'), template_folder=os.path.join(utils.DIR_PATH, 'web', 'templates'))
    db = redis.Redis('localhost', decode_responses=True)

    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html', status=utils.read_db(db, utils.DB_PLAYER_STATUS), config=utils.get_configuration(db))


    @app.route('/setup', methods=['GET'])
    def setup_view():
        return render_template('setup.html', config=utils.get_configuration(db))

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
            utils.write_db(db, utils.DB_PLAYER_STATUS, {'running':  action == 'resume'})  # eval to True/False
            result['message'] = 'Action %s executed' % action
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
                result['message'] = 'Next video will be %s' % nextVideo['name']
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

                    result['message'] = 'Seeking to %6.2f percent on next update' % data['amount']
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


    @app.route('/api/status', methods=['GET'])
    def status():
        lastPlayed = utils.read_db(db, utils.DB_LAST_PLAYED_FILE)

        # set the player status
        lastPlayed['player'] = utils.read_db(db, utils.DB_PLAYER_STATUS)

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
            analyze = Analyzer(data)

            result['data'] = analyze.run(utils.read_db(db, utils.DB_LAST_PLAYED_FILE))
        else:
            result['success'] = False
            result['message'] = checkConfig[1]

        return jsonify(result)

    # run the web app
    app.run(debug=debugMode, host='0.0.0.0', port=port_number, use_reloader=False)
