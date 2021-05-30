from .util import *
import os
from .classes import *
import base64

class ConfigurationError(Exception):
    pass

class Server:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = DBAccess(config_path)
        for root in ['clients', 'articles', 'maps', 'users', 'images']:
            os.makedirs(pformat(self.config.get('database.path')+f'/{root}'), exist_ok=True)
        
        self.clients = DBAccess(pformat(self.config.get('database.path')+'/clients'), indent=4)
        self.articles = DBAccess(pformat(self.config.get('database.path')+'/articles'), indent=4)
        self.maps = DBAccess(pformat(self.config.get('database.path')+'/maps'), indent=4)
        self.users = DBAccess(pformat(self.config.get('database.path')+'/users'), indent=4)

try:
    cfg_path = os.environ['config']
except:
    raise EnvironmentError('Failed to locate config envvar.')

SERVER = Server(cfg_path)

def get_uid(username):
    for i in SERVER.users.get(''):
        if SERVER.users.get(i).username == username:
            return i
    raise KeyError

def parse_data_uri(uri):
    return {
        'extension': uri.split('/')[1].split(';')[0],
        'data': uri.split(',')[1]
    }

def add_image(uri, iid):
    data = parse_data_uri(uri)
    with open(os.path.join(SERVER.config.get('database.path'),'images',iid+'.'+data['extension']), 'wb') as f:
        f.write(base64.b64decode(data['data'].encode('utf-8')))
    return iid+'.'+data['extension']

def del_image(iid):
    for i in os.listdir(os.path.join(SERVER.config.get('database.path'), 'images')):
        if os.path.splitext(i)[0] == iid:
            os.remove(os.path.join(SERVER.config.get('database.path'), 'images', i))