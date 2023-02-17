#!/usr/bin/env python
# encoding: utf-8

import os
import json
import docker
import yaml
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required, JWTManager
import shutil
import psutil

app = Flask(__name__)
CORS(app)

app.config['JWT_SECRET_KEY'] = 'drokku'
jwt = JWTManager(app)

APP_DIR = os.path.expanduser('~')

client = docker.from_env()

def get_container(name):
    try:
        return client.containers.get(name)
    except Exception as e:
        print(e)
    return None

@app.route('/')
def index():
    return jsonify({})

@app.route('/login', methods=['POST'])
def login():
    print('json:', request.json)
    username = request.json.get('username')
    password = request.json.get('password')

    if username == 'test' and password == '00test':
        token = create_access_token(identity=username)
        return jsonify({'token':token})

    return jsonify({'msg': 'Invalid username or password'}), 401

@app.route('/apps')
@jwt_required()
def apps():
    apps = []
    names = [os.path.splitext(os.path.basename(x))[0] for x in os.listdir() if x.endswith('.git')]
    for name in names:
        info = get_appinfo(name)
        apps.append(info)
    return jsonify(apps)

def get_appinfo(name):
    file = os.path.join(APP_DIR, f'{name}.git', 'app.yml')
    if os.path.exists(file):
        with open(file, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {}
    attrs = get_container(name).attrs if get_container(name) is not None else {}
    return {'name': name, 'config': config, 'container': attrs}
    

@app.route('/apps/<string:name>', methods=['GET', 'POST'])
@jwt_required()
def appinfo(name):
    file = os.path.join(APP_DIR, f'{name}.git', 'app.yml')
    print(request.method)
    if request.method == 'GET':
        if os.path.exists(file):
            with open(file, 'r') as f:
                config = yaml.safe_load(f)
        else:
            config = {}
        attrs = get_container(name).attrs if get_container(name) is not None else {}
    
        return jsonify({'config': config, 'container': attrs})

    elif request.method == 'POST':
        data = request.json
        print(f'data: {data}')
        if 'cmd' in data:
            cmd = data['cmd']
            if cmd == 'restart':
                container = get_container(name)
                try:
                    print(f'restarting {name}')
                    rc = container.restart()
                    print(rc)
                except docker.errors.APIError as e:
                    return jsonify({'error': e})
        return jsonify({'result': 'OK'})

@app.route('/containers')
@jwt_required()
def containers():
    containers = [x.attrs for x in client.containers.list()]

    return jsonify(containers)

@app.route('/stats')
@jwt_required()
def stats():
    disk = shutil.disk_usage('/var/lib/docker') # total=244934381568, used=13350301696, free=219070689280
    mem = psutil.virtual_memory()
    return jsonify({'mem': {'total': mem[0], 'avail': mem[1], 'percent': mem[2]}, 'disk': {'total': disk[0], 'used': disk[1], 'free': disk[2]}})
    

if __name__ == '__main__':
    app.run(debug=True)
