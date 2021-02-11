import utils
import os
from flask import Flask, render_template, flash, url_for, jsonify, request

def webapp_thread(port_number):
    app = Flask(import_name="vsmp-plus", static_folder=os.path.join(utils.DIR_PATH, 'web', 'static'), template_folder=os.path.join(utils.DIR_PATH, 'web', 'templates'))

    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html')

    @app.route('/status', methods=['GET'])
    def status():
        return jsonify(utils.read_json(utils.LAST_PLAYED_FILE))

    app.run(debug=True, host='0.0.0.0', port=port_number, use_reloader=False)
