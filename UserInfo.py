from flask import Flask, jsonify
import pymongo
from app import test

app = Flask(__name__)

client = pymongo.MongoClient(
   "mongodb+srv://Avatars:QrQnDDetR8cceWAS@cluster0.g15s2.mongodb.net/<dbname>?retryWrites=true&w=majority")
db = client.WaveDirectBackend
users = db.Users
input = "vmacleod@lostmytoothdentist.com"

print(users.find_one({"Email": input}))








