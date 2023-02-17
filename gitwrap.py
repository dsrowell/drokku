#!/usr/bin/env python

import os
import sys
import yaml
from caddy import configure_app, remove_app
import boto3
import docker

START_PORT = 32000
APP = os.getenv('APP')

class Docker(object):

    def __init__(self, app, config):
        self.client = docker.from_env()
        self.app = app
        self.config = config

    def stop(self):
    
def stop(app):
    os.system(f'sudo docker stop {app}')

def remove(app):
    os.system(f'sudo docker rm {app}')

def build(app):
    dir = os.getenv('BUILD_CONTEXT', '.')
    cmd = f'sudo docker build -t {app} {dir}'
    print(f'build: {cmd}')
    os.system(f'sudo docker build -t {app} {dir}')

def configure_aws():
    config = get_global_config()
    aws = config['aws']
    key = aws['aws_access_key_id']
    secret = aws['aws_secret_access_key']
    awsdir = os.path.expanduser('~/.aws')
    if not os.path.exists(awsdir):
        os.makedirs(awsdir)
    cred = f'''[default]
aws_access_key_id = {key}
aws_secret_access_key = {secret}
'''
    with open(f'{awsdir}/credentials', 'w') as f:
        f.write(cred)

def add_cname_record(source):
    config = get_global_config()
    host = config['host']['name']
    zoneid = config['host']['zoneid']
    domain = config['host']['domain']
    dest = f'{host}.{domain}'

    try:
        client = boto3.client('route53')
        print(f'adding {source} => {dest}')
        rc = client.change_resource_record_sets(
            HostedZoneId = zoneid,
            ChangeBatch = {
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': f'{source}.{domain}',
                            'Type': 'CNAME',
                            'TTL': 300,
                            'ResourceRecords': [{'Value': dest}]
                        }
                    }
                ]
            })
        print('cname:', rc)
    except Exception as e:
        print('exception adding cname:', e)

def remove_cname_record(source):
    config = get_global_config()
    host = config['host']['name']
    zoneid = config['host']['zoneid']
    domain = config['host']['domain']
    dest = f'{host}.{domain}'

    try:
        client = boto3.client('route53')
        print(f'adding {source} => {dest}')
        rc = client.change_resource_record_sets(
            HostedZoneId = zoneid,
            ChangeBatch = {
                'Changes': [
                    {
                        'Action': 'DELETE',
                        'ResourceRecordSet': {
                            'Name': f'{source}.{domain}',
                            'Type': 'CNAME',
                            'TTL': 300,
                            'ResourceRecords': [{'Value': dest}]
                        }
                    }
                ]
            })
        print('cname:', rc)
    except Exception as e:
        print('exception removing cname:', e)

def run(app, ports, env):
    print('run ports:', ports)
    print('run ports keys:', ports.keys())
    port_str = ''
    for port in ports.keys():
        port_str += f' -p 127.0.0.1:{port}:{ports[port]}'

    env_str = ''
    for e in env.keys():
        env_str += f' -e {e}={env[e]}'

    print(f'sudo docker run -d {port_str.strip()} {env_str.strip()} --name {app} {app}')
    os.system(f'sudo docker run -d {port_str.strip()} {env_str.strip()} --name {app} {app}')

def get_global_config():
    return get_config('_global')

def save_global_config(config):
    save_config('_global', config)

def get_config(app):
    filename = f'/home/git/data/{app}.yml'
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {}
    return config

def save_config(app, config):
    with open(f'/home/git/data/{app}.yml', 'w') as f:
        yaml.dump(config, f)

def get_open_port(app):
    config = get_global_config()
    if 'ports' not in config:
        config['ports'] = {}
    if config['ports'] is None:
        config['ports'] = {}
    print('ports:', config['ports'])
    apps = config['ports'].keys()
    if app not in apps:
        ports = [config['ports'][x] for x in apps]
        print('ports:', ports)
        port = START_PORT
        while port in ports:
            port += 1
        config['ports'][app] = port
        save_global_config(config)
    else:
        port = config['ports'][app]
    return port

if __name__ == '__main__':

    cmd = 'add'
    app = sys.argv[1]
    if len(sys.argv) > 2:
        cmd = sys.argv[2]
    config = get_config(app)
    port = get_open_port(app)
    
    stop(app)
    remove(app)
    if cmd == 'add':
        build(app)
        print('env:', config['environment'])
        run(app, {port: config['port']}, config['environment'])
        add_cname_record(app)
        configure_app(app, port)
    elif cmd == 'delete':
        remove_cname_record(app)
        remove_app(app)
