from flask import Flask, jsonify
import pymongo


app = Flask(__name__)

client = pymongo.MongoClient(
   "mongodb+srv://Avatars:QrQnDDetR8cceWAS@cluster0.g15s2.mongodb.net/<dbname>?retryWrites=true&w=majority")
db = client.WaveDirectBackend
users = db.Users

#app.route('/createUser', methods=['GET'])
def create():
    email = input("Enter an email : ")
    password = input("Enter a password : ")
    re_password = input("Re-Enter a password : ")

    print(email)
    print(password)
    print(re_password)

    return 0

input = "johnston@goskydivingonmars.com"
output = users.find_one({"Email": input})

print("a", output)

if not output:
    create()










