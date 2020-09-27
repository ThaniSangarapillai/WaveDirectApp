from flask import Flask, request, jsonify, g, redirect, url_for, make_response
import pymongo
import secrets
#from flask.ext.hashing import Hashing
from passlib.hash import sha256_crypt
import time
from functools import wraps
from flask_mail import Mail
from flask_mail import Message

app = Flask(__name__)

app.config['DEBUG'] = False
app.config['SERVER'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
#app.config['MAIL_DEBUG'] = TRUE
app.config['MAIL_USERNAME'] = 'noreply.wavedirect@gmail.com'
app.config['MAIL_PASSWORD'] = 'borderhacks2020'
app.config['MAIL_DEFAULT_SENDER'] = 'noreply.wavedirect@gmail.com'
app.config['MAIL_MAX_EMAILS'] = 5
#app.config['MAIL_SUPPRESS_SEND'] =
app.config['MAIL_ASCII_ATTACHMENTS'] = False

mail = Mail(app)

base_url = "http://192.168.0.119:5000"

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

@app.route('/json', methods=['GET'])
@check_auth
def send_json(*args, **kwargs):
    res = make_response({'texts':"hello"})
    if kwargs["update_cookie"][0] == True:
        res.set_cookie('x-wave-auth', kwargs['update_cookie'][1], max_age=172800)
    return res

@app.route('/verify', methods=['GET'])
def verify():
    try:
        verification_token = request.args.get("token")
        temp_user = users.find_one({"verification": verification_token})
    except:
        return {"message": "invalid token, please try again"}, 404



    if temp_user == None:
        return {"message": "invalid token, please try again"}, 404
    else:
        users.update_one({"verification": verification_token}, {"$set":{"verification":"","verified": True}})

    return "Successfully verified! You may now login from the app.", 200


@app.route('/register', methods=['POST'])
def register():
    content = request.json

    temp_user = users.find_one({"Email": content['email']})
    users.update_many({}, {"$set": {"verified": False}})
    if temp_user == None:
        return {"type": "error", "message":"You currently do not have an account with us."}
    if temp_user['created'] == True:
        return {"type": "error", "message": "Already a e-account created for this email"}, 401


    password = sha256_crypt.encrypt(content['password'])
    verification_token = secrets.token_urlsafe()
    users.update_one(temp_user,{"$set":{
        "Account #": temp_user['Account #'],
        "First Name": content['first'],
        "Last Name": content['last'],
        "Address": content['address'],
        "Town": content['town'],
        "Provice": content['province'],
        "Country": content['country'],
        "Email": content['email'],
        'Phone': content['phone'],
        'Package_id': temp_user['Package_id'],
        "AP_id": temp_user["AP_id"],
        "Password": password,
        "super": False,
        "created": True,
        "verified": False,
        "verification": verification_token
    }})

    msg = Message("WaveDirect Account Verification", recipients=["thanigajan.sangarapillai@ontariotechu.net"])
    msg.html = '<p><img src="https://blackburnnews.com/wp-content/uploads/2019/04/Logo-2018.png" alt="" width="300" height="111" /></p><p>Dear {0} {1},</p><p>&nbsp;</p><p>Please click the following link to verify your account: {2}.</p><p>&nbsp;</p><p>Sincerely,&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p>WaveDirect Team.</p><p>&nbsp;</p>'.format(
        content['first'], content['last'], base_url + "/verify?token=" + verification_token)
    mail.send(msg)

    # user_object = users.find_one({"Email": content['email']})
    # auth_token = str(int(time.time()) + 172800) + secrets.token_urlsafe()
    # auth_token = "wave_" + auth_token
    # auth.insert_one({"token": auth_token, "user_id": user_object['_id'], "time": int(time.time() + 172800), "super": user_object['super']
    # })
    return {'type':"message", 'message': "The verification email has been sent. Please verify your email before logging in."}, 200


@app.route('/login', methods=['POST'])
def login():
    content = request.json
    print(content)
    user_object = users.find_one({"Email": content['email']})
    print(user_object)
    if user_object == None:
        res = make_response({"type": "error",'message': "You do not have an account with us!"}, 400)
        return res
    if user_object['created'] == False:
        res = make_response({"type": "error",'message': "You do not have an e-account created!"}, 400)
        return res
    if user_object['verified'] == False:
        res = make_response({"type": "error",'message': "You have not verified your account!"}, 400)
        return res
    if sha256_crypt.verify(content['password'], user_object['Password']):
        auth_token = str(int(time.time()) + 172800) + secrets.token_urlsafe()
        auth_token = "wave_" + auth_token
        if auth.find_one({"user_id": user_object['_id']}):
            auth.delete_one({"user_id": user_object['_id']})

        auth.insert_one({"token": auth_token, "user_id": user_object['_id'], "time": int(time.time() + 172800), "super": user_object['super']
                      })
        res = make_response({"type": "message",'auth': auth_token}, 200)
        res.set_cookie('x-wave-auth', auth_token, max_age=172800)
        return res
    else:
        res = make_response({"type": "error",'message': "incorrect"}, 500)
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

@app.route('/refer', methods={'POST'})
@check_auth
def refer(*args, **kwargs):
    references = db.References
    content = request.json

    temp_user = users.find_one({"Email": content['email']})
    if temp_user != None:
        return {"error": "01", "message": "Already an account created for this email"}, 401

    temp_reference = references.find_one({"Email Address": content['email']})
    if temp_reference != None:
        return {"error": "02", "message": "Reference email already used"}, 401

    temp_token = request.cookies['x-wave-auth'] if 'x-wave-auth' not in request.headers else request.headers[
        'x-wave-auth']
    user = users.find_one(
        {"_id": auth.find_one({"token": temp_token})['user_id']}
        , {"_id": False, "Password": False})

    auth_token = str(int(time.time()) + 172800) + secrets.token_urlsafe()

    references.insert_one({

        "First Name": content['first'],
        "Last Name": content['last'],
        'Phone Number': content['phone'],
        'Email Address': content['email'],
        'Referred By': user['Account #'],
        'Ref First Name': user['First Name'],
        'Ref Last Name': user['Last Name'],
        'Email Token': auth_token,

    })

    msg = Message("WaveDirect Referral Program", recipients=["katigi3851@qatw.net"])
    msg.html = '<p><img src="https://blackburnnews.com/wp-content/uploads/2019/04/Logo-2018.png" alt="" width="300" height="111" /></p><p>Dear {0} {1},</p><p>&nbsp;</p><p>You have been referred by {2} {3} to join our program. The referral process offers you a $10 coupon to our services. If you are interested in this deal or have any questions please email us back or call us at (519) 737-9283. Thank you for your time.</p><p>&nbsp;</p><p>Sincerely,&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p>WaveDirect Team.</p><p>&nbsp;</p>'.format(content['first'],content['last'],user['First Name'],user['Last Name'])
    mail.send(msg)


    if __name__ == '__main__':
        app.run()

    res = make_response({"message": "ok"}, 200)
    if kwargs["update_cookie"][0] == True:
        res.set_cookie('x-wave-auth', kwargs['update_cookie'][1], max_age=172800)
    return res






