from flask import Flask, jsonify
import pymongo

app = Flask(__name__)

client = pymongo.MongoClient(
   "mongodb+srv://Avatars:QrQnDDetR8cceWAS@cluster0.g15s2.mongodb.net/<dbname>?retryWrites=true&w=majority")
db = client.WaveDirectBackend
users = db.Users
print(users.find_one())

@app.route('/test', methods=['GET'])
def test():
    users = db.Users
    print(users.find_one())
    return jsonify(users.find_one())

@app.route('/packages', methods=['GET'])
def packages():
    packages = db.Packages
    print(list(packages.find({})))
    return jsonify(list(packages.find({}, {'_id': False})))

@app.route('/outages', methods=['GET'])
def outages():
    outages = db.Outages
    print(list(outages.find({})))
    return jsonify(list(outages.find({}, {'_id': False})))

@app.route('/users', methods=['GET'])
def users():
    users = db.Users
    print(list(users.find({})))
    return jsonify(list(users.find({}, {'_id': False})))