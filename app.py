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

def check_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("in decorator")
        if "x-wave-auth" not in request.cookies and 'x-wave-auth' not in request.headers:
            print("not logged in")
            return {"error": "00", "message": "not logged in"}, 401
        else:
            print("hello")
            temp_token = request.cookies['x-wave-auth'] if 'x-wave-auth' not in request.headers else request.headers['x-wave-auth']
            get_hash = auth.find_one({"token": temp_token})
            print(get_hash)
            if get_hash is None:
                print("no entry")
                return {"error":"00", "message":"not logged in"}, 401
            elif get_hash['time'] < time.time():
                print("expired")
                auth.delete_one({"token": temp_token})
                res = make_response({"error": "00", "message": "timed out"}, 403)
                res.set_cookie('x-wave-auth', expires=0)
                return res
            else:
                print("authed")
                if get_hash['time'] - 86400 < time.time():
                    print("updating time")
                    auth.update_one({
                        '_id': get_hash['_id']
                    },
                        {'$set': {'time': int(time.time() + 172800)}})
                    res = make_response({'auth': get_hash['token']}, 200)
                    res.set_cookie('x-wave-auth', get_hash['token'], max_age=172800)
                    kwargs['update_cookie'] = (True, get_hash['token'])
                else:
                    kwargs['update_cookie'] = (False, None)
        return f(*args, **kwargs)
    return decorated_function

def check_super(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("in decorator")
        temp_token = request.cookies['x-wave-auth'] if 'x-wave-auth' not in request.headers else request.headers['x-wave-auth']
        get_hash = auth.find_one({"token": temp_token})
        if get_hash['super'] == False:
            return {"message": "Not a superadmin"}, 403
        return f(*args, **kwargs)
    return decorated_function



@app.route("/")
def hello_world():
    return 'Rans is a good person'

@app.route('/json', methods=['GET'])
@check_auth
def send_json(*args, **kwargs):
    res = make_response({'texts':"hello"})
    if kwargs["update_cookie"][0] == True:
        res.set_cookie('x-wave-auth', kwargs['update_cookie'][1], max_age=172800)
    return res

@app.route('/register', methods=['POST'])
def register():
    content = request.json

    temp_user = users.find_one({"Email": content['email']})
    if temp_user != None:
        if temp_user['created'] == True:
            return {"error": "01", "message": "Already a account created for this email"}, 401


    password = sha256_crypt.encrypt(content['password'])
    users.insert_one({
        "Account #": users.count() + 10001,
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
        "Password": password,
        "super": False,
        "created": True
    })
    user_object = users.find_one({"Email": content['email']})
    auth_token = str(int(time.time()) + 172800) + secrets.token_urlsafe()
    auth_token = "wave_" + auth_token
    auth.insert_one({"token": auth_token, "user_id": user_object['_id'], "time": int(time.time() + 172800), "super": user_object['super']
    })
    return {'auth': auth_token}, 200, {'Set-Cookie': 'x-wave-auth={}'.format(auth_token)}


@app.route('/login', methods=['POST'])
def login():
 content = request.json
 user_object = users.find_one({"Email": content['email']})
 print(user_object)
 if sha256_crypt.verify(content['password'], user_object['Password']):
     auth_token = str(int(time.time()) + 172800) + secrets.token_urlsafe()
     auth_token = "wave_" + auth_token
     if auth.find_one({"user_id": user_object['_id']}):
         auth.delete_one({"user_id": user_object['_id']})

     auth.insert_one({"token": auth_token, "user_id": user_object['_id'], "time": int(time.time() + 172800), "super": user_object['super']
                      })
     res = make_response({'auth': auth_token}, 200)
     res.set_cookie('x-wave-auth', auth_token, max_age=172800)
     return res


@app.route('/logout', methods=['POST'])
def logout():
    content = request.json
    temp_token = request.cookies['x-wave-auth'] if 'x-wave-auth' not in request.headers else request.headers[
        'x-wave-auth']
    if auth.find_one({'token': temp_token}):
        auth.delete_one({'token': temp_token})
        res = make_response({"message": "ok"}, 200)
        res.set_cookie('x-wave-auth', expires=0)
    return res


@app.route('/test', methods=['GET'])
def test(*args, **kwargs):
    users = db.Users
    print(users.find_one())
    return jsonify(users.find_one())


@app.route('/packages/get', methods=['GET'])
def packages_get(*args, **kwargs):
    packages = db.Packages
    print(list(packages.find({})))
    return jsonify(list(packages.find({}, {'_id': False})))

@app.route('/packages/set', methods=["POST"])
@check_auth
@check_super
def packages_set(*args, **kwargs):
    packages = db.Packages
    content = request.json
    packages.update_one(
        {'ID': content['ID']},
        {
            "$set": {
                'ID' : content['ID'],
                'Name' : content['Name'],
                'Data Limit' : content['Data Limit'],
                'Upload speed (Mbps)' : content['Upload speed (Mbps)'],
                'Download  speed (Mbps)' : content['Download speed (Mbps)'],
            }
        },
        upsert=True
    )

    res = make_response({"message": "ok"}, 200)
    if kwargs["update_cookie"][0] == True:
        res.set_cookie('x-wave-auth', kwargs['update_cookie'][1], max_age=172800)
    return res


@app.route('/outages/get', methods=['GET'])
def outages_get(*args, **kwargs):
    outages = db.Outages
    print(list(outages.find({})))
    return jsonify(list(outages.find({}, {'_id': False})))

@app.route('/outages/set', methods=['POST'])
@check_auth
@check_super
def outages_set(*args, **kwargs):
    outages = db.Outages
    content = request.json

    outages.update_one(
        {'ID': content['ID']},
        {
            "$set": {
                'ID' : content['ID'],
                'Name' : content['Name'],
                'Google Maps latitude/longtitude' : content['Google Maps latitude/longtitude'],
                'Radius (km)' : content['Radius (km)'],
                'Status' : content['Status'],
            }
        },
        upsert=True
    )
    res = make_response({"message": "ok"}, 200)
    if kwargs["update_cookie"][0] == True:
        res.set_cookie('x-wave-auth', kwargs['update_cookie'][1], max_age=172800)
    return res

@app.route('/users/get', methods=['GET'])
@check_auth
def users_get(*args, **kwargs):
    print("before user")
    temp_token = request.cookies['x-wave-auth'] if 'x-wave-auth' not in request.headers else request.headers[
        'x-wave-auth']
    user = users.find_one(
        {"_id": auth.find_one({"token": temp_token})['user_id']}
    , {"_id": False, "Password": False})

    res = make_response(user, 200)
    if kwargs["update_cookie"][0] == True:
        res.set_cookie('x-wave-auth', kwargs['update_cookie'][1], max_age=172800)
    return res

@app.route('/users/set', methods=['POST'])
@check_auth
def users_set(*args, **kwargs):
    content = request.json
    print("before user")
    temp_token = request.cookies['x-wave-auth'] if 'x-wave-auth' not in request.headers else request.headers[
        'x-wave-auth']
    users.update_one(
        {"_id": auth.find_one({"token": temp_token})['user_id']},
        {"$set": {
            "First Name": content['first'],
            "Last Name": content['last'],
            "Address": content['address'],
            "Town": content['town'],
            "Provice": content['province'],
            "Country": content['country'],
            "Email": content['email'],
            'Phone': content['phone'],
            'Package_id': content['package'],
        }}
    )
    res = make_response({"message": "ok"}, 200)
    if kwargs["update_cookie"][0] == True:
        res.set_cookie('x-wave-auth', kwargs['update_cookie'][1], max_age=172800)
    return res
