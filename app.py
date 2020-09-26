from flask import Flask, request, jsonify, g, redirect, url_for, make_response
import pymongo
import secrets
#from flask.ext.hashing import Hashing
from passlib.hash import sha256_crypt
import time
from functools import wraps

app = Flask(__name__)
#hashing = Hashing(app)
client = pymongo.MongoClient(
   "mongodb+srv://Avatars:QrQnDDetR8cceWAS@cluster0.g15s2.mongodb.net/<dbname>?retryWrites=true&w=majority")
db = client.WaveDirectBackend
users = db.Users
auth = db.Auth
print(users.find_one())

def check_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("in decorator")
        if "x-wave-auth" not in request.cookies:
            print("not logged in")
            return {"error": "00", "message": "not logged in"}, 403
        else:
            print("hello")
            get_hash = auth.find_one({"token": request.cookies['x-wave-auth']})
            print(get_hash)
            if get_hash is None:
                print("no entry")
                return {"error":"00", "message":"not logged in"}, 403
            elif get_hash['time'] < time.time():
                print("expired")
                auth.delete_one({"token": request.cookies['x-wave-auth']})
                res = make_response({"error": "00", "message": "timed out"}, 403)
                res.set_cookie('x-wave-auth', expires=0)
                return res
            else:
                print("authed")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def hello_world():
    return 'Rans is a good person'

@app.route('/json', methods=['GET'])
@check_auth
def send_json():
    return jsonify({'texts': "hello"})

@app.route('/register', methods=['POST'])
def register():
    content = request.json

    if users.find_one({"Email": content['email']}):
        return {"error": "01", "message": "already a user associated with account"}, 401
    password = sha256_crypt.encrypt(content['password'])
    users.insert_one({
        "Account #": str(users.count() + 10001),
        "First Name": content['first'],
        "Last Name": content['last'],
        "Address": content['address'],
        "Town": content['town'],
        "Provice": content['province'],
        "Country": content['country'],
        "Email": content['email'],
        'Phone': content['phone'],
        'Package_id': content['package'],
        "AP_id": content["ap"],
        "Password": password
    })
    auth_token = str(int(time.time()) + 3600) + secrets.token_urlsafe()
    auth_token = "wave_" + auth_token
    auth.insert_one({"token": auth_token, "email": content['email'], "time": int(time.time() + 3600)
    })
    return {'auth': auth_token}, 200, {'Set-Cookie': 'x-wave-auth={}'.format(auth_token)}

@app.route('/login', methods=['POST'])
def login():
 content = request.json
 user_object = users.find_one({"Email": content['email']})
 print(user_object)
 if sha256_crypt.verify(content['password'], user_object['Password']):
     auth_token = str(int(time.time()) + 3600) + secrets.token_urlsafe()
     auth_token = "wave_" + auth_token
     if auth.find_one({'email': content['email']}):
         auth.delete_one({'email': content['email']})

     auth.insert_one({"token": auth_token, "email": content['email'], "time": int(time.time() + 3600)
                      })
     res = make_response({'auth': auth_token}, 200)
     res.set_cookie('x-wave-auth', auth_token, max_age=3600)
     return res

@app.route('/logout', methods=['POST'])
def logout():
    content = request.json

    if auth.find_one({'email': content['email']}):
        auth.delete_one({'email': content['email']})
        res = make_response({"message": "ok"}, 200)
        res.set_cookie('x-wave-auth', expires=0)
    return res

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
    print(list(users.find({})))
    return jsonify(list(users.find({}, {'_id': False})))