import utils
import os
from flask import Flask, render_template, flash, url_for, jsonify, request

def webapp_thread(port_number, tmp_dir):
    TMP_DIR = tmp_dir
    app = Flask(__name__)

    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html')

    @app.route('/status', methods=['GET'])
    def status():
        return jsonify(utils.read_json(os.path.join(TMP_DIR, 'last_played.json')))

    app.run(debug=True, host='0.0.0.0', port=port_number, use_reloader=False)
