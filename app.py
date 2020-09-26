from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def hello_world():
    return 'Hello, World!'

@app.route('/json/', methods=['GET'])
def send_json():
    return jsonify({'texts': "hello"})

