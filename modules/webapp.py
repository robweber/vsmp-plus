import modules.utils as utils
import os
import redis
import json
from flask import Flask, render_template, flash, url_for, jsonify, request
from modules.analyze import Analyzer

# encapsulates the functions for the web service so they can be run in a new thread
def webapp_thread(port_number, debugMode=False):
    app = Flask(import_name="vsmp-plus", static_folder=os.path.join(utils.DIR_PATH, 'web', 'static'), template_folder=os.path.join(utils.DIR_PATH, 'web', 'templates'))
    db = redis.Redis('localhost', decode_responses=True)

    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html', status=json.loads(db.get(utils.DB_PLAYER_STATUS)))


    @app.route('/setup', methods=['GET'])
    def setup_view():
        return render_template('setup.html', config=utils.get_configuration())

    @app.route('/analyze', methods=['GET'])
    def setup_analyze():
        return render_template('analyze.html', config=utils.get_configuration())

    @app.route('/api/configuration', methods=['GET'])
    def get_configuration():
        return jsonify(utils.get_configuration())


    @app.route('/api/configuration', methods=['POST'])
    def save_configuration():
        result = {'success': True, 'message': 'Settings Updated'}

        # get the request data and do some verification
        data = request.get_json(force=True)

        # if passed get current config
        currentConfig = utils.get_configuration()

        # merge changed values into current and save
        currentConfig.update(data)

        checkConfig = utils.validate_configuration(currentConfig)

        if(checkConfig[0]):
            utils.write_json(utils.CONFIG_FILE, currentConfig)
        else:
            result['success'] = False
            result['message'] = checkConfig[1]

        return jsonify(result)


    @app.route('/api/control/<action>', methods=['POST'])
    def execute_action(action):
        result = {'success': True, 'message': ''}

        # get the action
        if(action in ['pause', 'resume']):
            # store the new value
            db.set(utils.DB_PLAYER_STATUS, json.dumps({'running':  action == 'resume'}))  # eval to True/False

            result['message'] = 'Action %s executed' % action
        else:
            result['success'] = False
            result['message'] = 'Not a valid control action'

        return jsonify(result)


    @app.route('/api/status', methods=['GET'])
    def status():
        return jsonify(utils.read_json(utils.LAST_PLAYED_FILE))

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

            result['data'] = analyze.run()
        else:
            result['success'] = False
            result['message'] = checkConfig[1]

        return jsonify(result)

    # run the web app
    app.run(debug=debugMode, host='0.0.0.0', port=port_number, use_reloader=False)
