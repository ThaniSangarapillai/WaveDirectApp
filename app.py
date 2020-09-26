from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def hello_world():
    return 'Rans is a bad person'

@app.route('/json', methods=['GET'])
def send_json():
    return jsonify({'texts': "hello"})

