import requests

def get_config(ip):
    config = None
    r = requests.get(f'http://{ip}:2019/config/')
    r.raise_for_status()
    return r.json()

def make_app_http_servers(ip):

    config = get_config(ip)

    if config is None:
        print('config is None, creating apps...')
        r = requests.post(f'http://{ip}:2019/config/', json={'apps':{}})
        r.raise_for_status()

    if config is not None and 'apps' in config and 'http' in config['apps'] and 'servers' in config['apps']['http']:
        print('servers are in config apps')
        return

    print('creating servers...')
    r = requests.post(f'http://{ip}:2019/config/apps', json={'http':{'servers':{}}})
    r.raise_for_status()

    config = get_config(ip)
    return config

def update_caddy_config(ip, task, domain):

    config = get_config(ip)
    server = list(config['apps']['http']['servers'])[0]
    name = task['name']
    port = task['port']
    upstreams = [{'dial':f'{ip}:{port}'} for ip in task['ips']]
    #config = {
    #  'listen': [':80', ':443'],
    #  'routes': [
    #    {
    #      'match': [
    #        {
    #          'host': [
    #            f'{name}.{domain}'
    #          ]
    #        }
    #      ],
    #      'handle': [{
    #        'handler': 'reverse_proxy',
    #        #'load_balancing': {
    #        #  'selection_policy': {
    #        #    'policy': 'round_robin'
    #        #  }
    #        #},
    #        'upstreams': upstreams
    #      }]
    #    }
    #  ]
    #}
    route = {
      'match': [
        {
          'host': [
            f'{name}.{domain}'
          ]
        }
      ],
      'handle': [{
        'handler': 'reverse_proxy',
        'upstreams': upstreams
      }]
    }
    url = f'http://{ip}:2019/config/apps/http/servers/{server}/routes/'
    print(url, route)
    r = requests.post(url, json=route)
    print(r.text)
    print(r.status_code)


def configure_app(name, port):
    domain = 'simcenter.cloud'
    localhost = '127.0.0.1'
    ip = localhost
    task = {'name': name, 'ips': [localhost], 'port': port}

    make_app_http_servers(ip)
    update_caddy_config(ip, task, domain)

def remove_app(name):
    domain = 'simcenter.cloud'
    localhost = '127.0.0.1'
    ip = localhost

    config = get_config(ip)
    server = list(config['apps']['http']['servers'])[0]
    i = 0
    found = False
    print('routes:')
    print(config['apps']['http']['servers'][server]['routes'])
    for route in config['apps']['http']['servers'][server]['routes']:
        if 'match' in route and len(route['match']) == 1 and 'host' in route['match'][0] and len(route['match'][0]['host']) == 1 and route['match'][0]['host'][0] == f'{name}.{domain}':
            print(f'found {name}.{domain}')
            found = True
            break
        i += 1
    #newroutes = [route for route in config['apps']['http']['servers'][server]['routes'] if 'match' in route and 'host' in route['match'] and len(route['match']['host']) == 1 and route['match']['host'][0] != f'{name}.{domain}']
            
    #url = f'http://{ip}:2019/config/apps/http/servers/{server}/routes'
    #r = requests.put(url, json=newroutes)
    print(f'found {name}: {found} {i}')
    if found:
        url = f'http://{ip}:2019/config/apps/http/servers/{server}/routes/{i}'
        r = requests.delete(url)
        print(r.text)
        print(r.status_code)


if __name__ == '__main__':

    domain = 'simcenter.cloud'
    ip = '127.0.0.1'
    task = {'name': 'diag', 'ips': ['127.0.0.1'], 'port': 32001}

    #update_caddy_config(ip, task, domain)
    remove_app('hastebin')
