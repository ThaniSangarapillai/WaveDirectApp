from flask import Flask, jsonify
import pymongo

app = Flask(__name__)

@app.route("/")
def hello_world():
    return 'Rans is a bad person'

@app.route('/json', methods=['GET'])
def send_json():
    return jsonify({'texts': "hello"})

client = pymongo.MongoClient(
   "mongodb+srv://Avatars:QrQnDDetR8cceWAS@cluster0.g15s2.mongodb.net/<dbname>?retryWrites=true&w=majority")
db = client.test

