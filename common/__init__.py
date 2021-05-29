from .util import *
import os
from .classes import *

class ConfigurationError(Exception):
    pass

class Server:
    def __init__(self, config_path):
        self.config = DBAccess(config_path)
        for root in ['clients', 'articles', 'maps', 'users']:
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