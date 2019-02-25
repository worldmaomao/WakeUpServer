from flask import Flask
from flask import request

try:
    import simplejson as json
except ImportError:
    import json
from flask import jsonify
import os
import time
import jwt
import socket
import binascii

app = Flask(__name__)
config = {}
# do change it
jwt_secret = b'\x7d\xef\x87\xd5\xf8\xbb\xff\xfc\x80\x91\x06\x91\xfd\xfc\xed\x69'


class ParentError(RuntimeError):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class LoginError(ParentError):
    def __init__(self, message):
        ParentError.__init__(self, 401, message)


class AuthError(ParentError):
    def __init__(self, message):
        ParentError.__init__(self, 401, message)


def load_config():
    file_path = os.path.abspath(os.path.dirname(__file__)) + os.path.sep + "config.json"
    if not os.path.isfile(file_path):
        print("Can not find file config.json ")
        return False
    with open(file_path) as text:
        loaded_json = json.load(text)
        for item in loaded_json:
            if config.has_key(item['username']):
                print("WARNING!!! the username is duplicate in config.json. please check!")
                return False
            device_list = item['devices']
            device_name_set = set()
            for device in device_list:
                if device['device_name'] in device_name_set:
                    print("WARNING!! the device[%s] is duplicate in config.json for user[%s]." % (
                    device['device_name'], item['username']))
                    return False
                device_name_set.add(device['device_name'])
            config[item['username']] = item
    return True


@app.errorhandler(LoginError)
def login_error_handler(error):
    response = jsonify(code=401, message=error.message, data=None)
    return response, 401


@app.errorhandler(AuthError)
def auth_error_handler(error):
    response = jsonify(code=401, message=error.message, data=None)
    return response, 401


@app.errorhandler(404)
def error404(error):
    response = jsonify(code=404, message='Not found', data=None)
    return response, 404


@app.errorhandler(400)
def error400(error):
    response = jsonify(code=400, message='Bad request', data=None)
    return response, 400


def get_jwt(username):
    expire_time = int(time.time() + 3600 * 24 * 7)
    encoded = jwt.encode({'username': username, "exp": expire_time}, jwt_secret, algorithm='HS256')
    return encoded


def decode_jwt(jwt_token):
    if jwt_token is None:
        return None
    info = None
    try:
        info = jwt.decode(jwt_token, jwt_secret, algorithms='HS256')
    except Exception:
        print('parse jwt token error.')
    return info


@app.route("/user/login", methods=['POST'])
def login():
    login_data = request.get_json(force=True)
    username = login_data['username']
    password = login_data['password']
    if username is None or password is None:
        raise LoginError('username or password is null')
    config_item_info = config[username]
    if config_item_info is None:
        raise LoginError('username is wrong')
    if config_item_info['password'] != password:
        raise LoginError('password is wrong')
    jwt_token = get_jwt(username)
    response = jsonify(code=10000, message="ok", data={"token": jwt_token})
    return response, 201


def check_token(request):
    jwt_token = request.headers['token']
    if jwt_token is None:
        raise AuthError('token is null')
    user_info = decode_jwt(jwt_token)
    if user_info is None:
        raise AuthError('token is error')
    username = user_info['username']
    exp = user_info['exp']
    now = int(time.time())
    if now >= exp:
        raise AuthError('token is expired')
    return username


@app.route("/devices/<device_name>/wakeup", methods=['POST'])
def wakeup(device_name):
    username = check_token(request)
    user_device_config = config[username]
    if user_device_config is None:
        response = jsonify(code=20001, message='config is missing for user[%s].' % username, data=None)
        return response, 200
    device_list = user_device_config['devices']
    if device_list is None or len(device_list) == 0:
        response = jsonify(code=20002, message='device[%s] config is missing for user[%s].' % (device_name, username),
                           data=None)
        return response, 200
    found_device = None
    for device in device_list:
        if device_name == device['device_name']:
            found_device = device
            break;
    if found_device is None:
        response = jsonify(code=20003, message='device[%s] config is missing for user[%s].' % (device_name, username),
                           data=None)
        return response, 200
    print("wake up %s" % device_name)
    send_wakeup_package(found_device['broadcast_ip'], found_device['mac'])
    response = jsonify(code=20000, message='success', data=None)
    return response, 201


@app.route("/devices", methods=['GET'])
def get_device_list():
    username = check_token(request)
    user_device_config = config[username]
    device_name_list = []
    for device in user_device_config['devices']:
        device_name_list.append(device['device_name'])
    response = jsonify(code=30000, message='ok', data=device_name_list)
    return response, 200


def send_wakeup_package(broadcast_ip, mac):
    f = lambda x: x.strip() if len(x.strip()) == 12 else x.strip().replace(x.strip()[2], "")
    mac = f(mac)
    package = binascii.unhexlify('FF' * 6 + mac * 16 + '00' * 6)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.sendto(package, (broadcast_ip, 9))
    s.close()


if __name__ == '__main__':
    if load_config():
        # app.debug = True
        app.run(host='0.0.0.0')
