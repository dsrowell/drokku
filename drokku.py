#!/usr/bin/env python
import os
import sys
import docker
import yaml
from caddy import configure_app, remove_app
from cname import configure_aws, add_cname_record, remove_cname_record
import time

DROKKU_DIR = os.path.expanduser('~')
START_PORT = 32001

class Drokku(object):

    def __init__(self, name):
        self.client = docker.from_env()
        self.name = name

    def set_context(self):
        self.app_dir = os.path.join(DROKKU_DIR, f'{self.name}.git')
        self.context_dir = os.getenv('BUILD_CONTEXT')
        self.get_config()
        
    def get_global_config(self):
        filename = os.path.join(DROKKU_DIR, 'drokku.yml')
        return yaml.safe_load(open(filename, 'r'))

    def get_config(self):
        filename = os.path.join(self.app_dir, 'app.yml')
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                config = yaml.safe_load(f)
        else:
            config = {}
        if 'port' not in config or config['port'] is None:
            port = self.get_port_from_dockerfile()
            if port is not None:
                config['port'] = port
        self.config = config
        print(f'config: {self.config}')
        return self.config

    def get_port_from_dockerfile(self):
        port = None
        filename = os.path.join(self.context_dir, 'Dockerfile')
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                lines = f.readlines()
            for line in lines:
                if 'EXPOSE' in line:
                    port = line.split()[1] if len(line.split()) > 1 else None
                    break
        return port

    def get(self):
        try:
            return self.client.containers.get(self.name)
        except Exception as e:
            pass
        return None

    def stop(self):
        return self.get().stop() if self.get() else None

    def remove(self):
        print('removing...')
        return self.get().remove() if self.get() else None

    def env_from_options(self):
        print('env_from_options')
        env = []
        option_count = int(os.getenv('GIT_PUSH_OPTION_COUNT', '0'))
        print(f'option count: {option_count}')
        for i in range(0, option_count):
            opt = os.getenv(f'GIT_PUSH_OPTION_{i}')
            print(f'option: {opt}')
            parts = opt.split('=', 1)
            print(f'parts: {parts}')
            if parts[0] == 'env':
                env.append(parts[1])
                print(f'env: {env}')
        return env
        
    def run(self):
        print('running...')
        config = self.get_config()
        port = config['port']
        host_port = self.get_host_port()
        ports = {f'{port}/tcp': ('127.0.0.1', host_port)}
        print('getting environment...')
        environment = self.env_from_options()
        print(f'env1: {environment}')
        environment += config['environment'] if 'environment' in config else []
        print(f'env2: {environment}')

        print(f'ports: {ports}, env: {environment}')
        container = self.client.containers.run(self.name, name=self.name, hostname=self.name, ports=ports, environment=environment, detach=True)
        self.host_port = host_port

    def start(self):
        print('starting...')
        self.get().start()

    def build(self):
        print('building...')
        self.client.images.build(path=self.context_dir, rm=True, tag=self.name)

    def get_host_port(self):
        print('get_host_port')
        host_port_filename = os.path.join(self.app_dir, 'HOST_PORT')
        if os.path.exists(host_port_filename):
            print(f'HOST_PORT {host_port_filename} exists')
            return int(open(host_port_filename).read().strip())
        # else find one
        print('HOST_PORT does not exist')
        ports_in_use = []
        dirs = [f.path for f in os.scandir(DROKKU_DIR) if f.is_dir() and f.name.endswith('.git')]
        for d in dirs:
            filename = os.path.join(d, 'HOST_PORT')
            print(f'looking for HOST_PORT in {filename}')
            if os.path.exists(filename):
                print(f'found HOST_PORT in {filename}')
                ports_in_use.append(int(open(filename).read().strip()))
        print(f'ports_in_use: {ports_in_use}')
        candidate = START_PORT
        while candidate in ports_in_use:
            candidate += 1
        print(f'writing {candidate} to {host_port_filename}')
        open(host_port_filename, 'w').write(str(candidate))
        return candidate

if __name__ == '__main__':

    app = sys.argv[1]
    d = Drokku(app)

    config = d.get_global_config()
    configure_aws(config)

    # create, stop, start, restart, destroy
    cmd = sys.argv[2] if len(sys.argv) > 2 else 'add'

    print(f'cmd: {cmd}')
    if cmd != 'destroy':
        d.set_context()

    if cmd in ['stop', 'create', 'restart', 'destroy']:
        d.stop()
    if cmd in ['create', 'destroy']:
        d.remove()
    if cmd in ['start', 'restart']:
        d.start()
    if cmd in ['create']:
        d.build()
        d.run()
        add_cname_record(config, app)
        configure_app(app, d.host_port)
    if cmd in ['destroy']:
        remove_cname_record(config, app)
        remove_app(app)

    if cmd != 'destroy':
        c = d.get()
        print(c.id, c.name, c.status)
