from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def hello_world():
    return 'Rans is a good person'

@app.route('/json', methods=['GET'])
def send_json():
    return jsonify({'texts': "hello"})

