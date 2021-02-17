import utils
import os
from flask import Flask, render_template, flash, url_for, jsonify, request

def webapp_thread(port_number):
    app = Flask(import_name="vsmp-plus", static_folder=os.path.join(utils.DIR_PATH, 'web', 'static'), template_folder=os.path.join(utils.DIR_PATH, 'web', 'templates'))

    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html', config=utils.get_configuration())

    @app.route('/setup', methods=['GET'])
    def setup_view():
        return render_template('setup.html', config=utils.get_configuration())

    @app.route('/api/configuration', methods=['GET'])
    def get_configuration():
        return jsonify(utils.get_configuration())

    @app.route('/api/configuration', methods=['POST'])
    def save_configuration():
        result = {'success': False, 'message': ''}

        # get the request data and do some verification
        data = request.get_json(force=True)

        # check mode
        if(data['mode'] not in ['file', 'dir']):
            result['message'] = 'Incorrect mode, must be "file" or "dir"'
            return jsonify(result)

        # check if file or dir path is correct
        if(data['mode'] == 'file' and not utils.check_mp4(data['path'])):
            result['message'] = 'File path is not a valid file'
            return jsonify(result)
        elif(data['mode'] == 'dir' and not utils.check_dir(data['path'])):
            result['message'] = 'Directory path is not valid'
            return jsonify(result)

        # verify cron expression
        if(not utils.check_cron(data['update'])):
            result['message'] = 'Cron expression for update interval is invalid'
            return jsonify(result)

        # if passed get current config
        currentConfig = utils.get_configuration()

        # merge changed values into current and save
        currentConfig.update(data)
        utils.write_json(utils.CONFIG_FILE, currentConfig)

        result['success'] = True
        result['message'] = 'Settings updated'
        return jsonify(result)

    @app.route('/api/control/<action>', methods=['POST'])
    def execute_action(action):
        result = {'success': True, 'message': ''}

        # get the action
        if(action in ['pause', 'play']):
            config = utils.get_configuration()
            config['running'] = action == 'play'  # eval to True/False
            utils.write_json(utils.CONFIG_FILE, config)
            result['message'] = 'Action %s executed' % action
        else:
            result['success'] = False
            result['message'] = 'Not a valid control action'

        return jsonify(result)


    @app.route('/api/status', methods=['GET'])
    def status():
        return jsonify(utils.read_json(utils.LAST_PLAYED_FILE))

    app.run(debug=True, host='0.0.0.0', port=port_number, use_reloader=False)
