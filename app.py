from flask import Flask, jsonify
import pymongo

app = Flask(__name__)

client = pymongo.MongoClient(
   "mongodb+srv://Avatars:QrQnDDetR8cceWAS@cluster0.g15s2.mongodb.net/<dbname>?retryWrites=true&w=majority")
db = client.WaveDirectBackend
users = db.Users
print(users.find_one())

@app.route('/offers', methods=['GET'])
def offers():
    packages = db.Packages
    return jsonify(list(packages.find({})))



