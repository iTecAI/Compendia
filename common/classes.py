import time
from json import JSONDecodeError
import json, os, time, copy, threading, shutil
from .util import *

class BaseObject:
    def __init__(self, db=None, path=None, update_timeout=0.25, **kwargs):
        self.kwargs = kwargs
        if '_update_' in self.kwargs.keys():
            self._update_ = self.kwargs['_update_']
        else:
            self._update_ = {
                'self': (True, time.time()+update_timeout)
            }
        self._db_ = db
        self._path_ = path
        self.__base_object_type__ = 'BaseObject'
        self.update_timeout = update_timeout
    
    def update(self, endpoint='self'):
        self._update_[endpoint] = (True, time.time()+self.update_timeout)
        self.save()
    
    def check_update(self, endpoint='self'):
        if self._update_[endpoint][0]:
            if time.time() > self._update_[endpoint][1]:
                self._update_[endpoint] = (False, 0)
                self.save()
            return True
        else:
            return False

    def to_dict(self):
        tld = {}
        svars = vars(self)
        for key in svars.keys():
            if key in ['kwargs', '_path_', '_db_']:
                continue
            if type(svars[key]) == dict:
                tld[key] = self._loop_dict(svars[key])
            elif type(svars[key]) in [list, tuple, set]:
                tld[key] = self._loop_list(list(svars[key]))
            elif type(svars[key]) in [str, int, bool]:
                tld[key] = svars[key]
            else:
                try:
                    if issubclass(type(svars[key]), BaseObject):
                        tld[key] = svars[key].to_dict()
                    else:
                        tld[key] = svars[key]
                except TypeError:
                    tld[key] = svars[key]
        return tld

    def _loop_dict(self, dct):
        tld = {}
        for k in dct.keys():
            if k in ['kwargs', '_path_', '_db_']:
                continue
            if type(dct[k]) == dict:
                tld[k] = self._loop_dict(dct[k])
            elif type(dct[k]) in [list, tuple, set]:
                tld[k] = self._loop_list(list(dct[k]))
            else:
                try:
                    if issubclass(type(dct[k]), BaseObject):
                        tld[k] = dct[k].to_dict()
                    else:
                        tld[k] = dct[k]
                except TypeError:
                    tld[k] = dct[k]
        return tld

    def _loop_list(self, lst):
        tld = []
        for i in lst:
            if type(i) == dict:
                tld.append(self._loop_dict(i))
            elif type(i) in [list, tuple, set]:
                tld.append(self._loop_list(list(i)))
            else:
                try:
                    if issubclass(type(i), BaseObject):
                        tld.append(i.to_dict())
                    else:
                        tld.append(i)
                except TypeError:
                    tld.append(i)
        return tld
    
    def save(self, db=None, path=None):
        if db and path:
            db.set(path, self)
        elif self._db_ and self._path_:
            self._db_.set(self._path_, self)
        else:
            raise ValueError('DB and Path must be specified.')

def DefaultsDict(dct, defaults={}):
    for key in defaults.keys():
        if key in dct.keys():
            pass
        else:
            if defaults[key] == '$required':
                raise TypeError(
                    f'The {key} argument is required, but was not included.')
            else:
                dct[key] = copy.deepcopy(defaults[key])
    return copy.deepcopy(dct)

class DBAccess:
    def cache_check_thread(self):
        while True:
            for c in list(self.cache.keys()):
                if self.cache[c]['last_update'] + self.cache_timeout < time.time():
                    del self.cache[c]
            time.sleep(2)

    def __init__(self, top, allowed_exts=['.json', '.ini', '.cfg'], indent=None, cache_timeout=30):
        self.top = pformat(top)
        self.allowed_exts = allowed_exts
        self.indent = indent
        self.cache = {}
        self.cache_timeout = cache_timeout
        self.check_thread = threading.Thread(
            name=f'db-check-{self.top}', target=self.cache_check_thread, daemon=True)
        self.check_thread.start()

    def _get(self, path):
        if path in self.cache.keys():
            return copy.deepcopy(self.cache[path])['value']
        parts = path.split('.')
        if not os.path.isfile(self.top):
            top = self.top+''
            _file = None
            c = 0
            filetop = None
            for p in parts:
                if len(p) == 0:
                    continue
                items = os.listdir(top)
                if p in items:
                    top = os.path.join(top, p)
                else:
                    for i in items:
                        if p == os.path.splitext(i)[0] and os.path.splitext(i)[1] in self.allowed_exts:
                            _file = os.path.join(top, i)
                    if _file:
                        if len(parts) > c + 1:
                            filetop = c+1
                        else:
                            with open(_file, 'r') as f:
                                self.cache[path] = {
                                    'value': json.loads(f.read()),
                                    'last_update': time.time()
                                }
                                f.seek(0)
                                return json.loads(f.read())
                        break
                    else:
                        raise FileNotFoundError(f'Could not locate file {p}.')
                c += 1
            if filetop == None:
                files = {
                    os.path.split(os.path.splitext(os.path.join(self.top, pformat(path, sep='.'), n))[0])[
                        1]: os.path.join(self.top, pformat(path, sep='.'), n).replace('\\', '/')
                    for n in os.listdir(os.path.join(self.top, pformat(path, sep='.')))
                }
                self.cache[path] = {
                    'value': files.copy(),
                    'last_update': time.time()
                }
                return files
            parts = parts[filetop:]
        else:
            _file = self.top+''
        with open(_file, 'r') as f:
            j_loaded = json.loads(f.read())
            for p in parts:
                if p in j_loaded.keys():
                    j_loaded = copy.deepcopy(j_loaded[p])
                else:
                    raise KeyError(f'Could not find key {p} in {_file}.')
            self.cache[path] = {
                'value': copy.deepcopy(j_loaded),
                'last_update': time.time()
            }
            return j_loaded

    def get(self, path, raw=False):
        ret = self._get(path)
        if '' in self.cache.keys():
            del self.cache['']
        if type(ret) == dict and not raw:
            if '__base_object_type__' in ret.keys():
                try:
                    return globals()[ret['__base_object_type__']](db=self, path=path, **ret)
                except KeyError:
                    return ret
        return ret

    def set(self, path, value):
        if issubclass(type(value), BaseObject):
            value = value.to_dict()
        self.cache[path] = {
            'value': copy.deepcopy(value),
            'last_update': time.time()
        }
        parts = path.split('.')
        for p in range(1, len(parts)+1):
            if '.'.join(parts[:p]) in self.cache.keys():
                del self.cache['.'.join(parts[:p])]
        if not os.path.isfile(self.top):
            top = self.top+''
            _file = None
            c = 0
            filetop = None
            for p in parts:
                items = os.listdir(top)
                if p in items:
                    top = os.path.join(top, p)
                else:
                    for i in items:
                        if p == os.path.splitext(i)[0] and os.path.splitext(i)[1] in self.allowed_exts:
                            _file = os.path.join(top, i)
                    if _file:
                        if len(parts) > c + 1:
                            filetop = c+1
                        else:
                            with open(_file, 'w') as f:
                                try:
                                    f.write(json.dumps(
                                        value, indent=self.indent))
                                    return
                                except JSONDecodeError:
                                    raise ValueError(
                                        f'Cannot set an entire file to a non-JSON value {str(value)}')
                        break
                    else:
                        with open(os.path.join(top, p+self.allowed_exts[0]), 'w') as f:
                            try:
                                f.write(json.dumps(value, indent=self.indent))
                                return
                            except JSONDecodeError:
                                raise ValueError(
                                    f'Cannot set an entire file to a non-JSON value {str(value)}')
                c += 1
            if filetop == None:
                with open(os.path.join(self.top, pformat(path, sep='.')+self.allowed_exts[0]), 'w') as f:
                    f.write(json.dumps(value, indent=self.indent))
                return
            parts = parts[filetop:]
        else:
            _file = self.top+''
        with open(_file, 'r') as f:
            j_loaded = json.loads(f.read())
            ind_str = '["'+'"]["'.join([str(p) for p in parts])+'"]'
            try:
                exec(f'j_loaded{ind_str} = value', {
                     'j_loaded': j_loaded, 'value': value})
            except KeyError:
                raise KeyError(
                    f'Could not find key path {".".join(parts)} in file {_file}')
        with open(_file, 'w') as f:
            f.write(json.dumps(j_loaded, indent=self.indent))

    def delete(self, path):
        if path in self.cache.keys():
            del self.cache[path]
        parts = path.split('.')
        if not os.path.isfile(self.top):
            top = self.top+''
            _file = None
            c = 0
            filetop = None
            for p in parts:
                items = os.listdir(top)
                if p in items:
                    top = os.path.join(top, p)
                else:
                    for i in items:
                        if p == os.path.splitext(i)[0] and os.path.splitext(i)[1] in self.allowed_exts:
                            _file = os.path.join(top, i)
                    if _file:
                        if len(parts) > c + 1:
                            filetop = c+1
                        else:
                            try:
                                os.remove(_file)
                            except:
                                raise OSError(
                                    f'Unexpected error occurred while removing {_file}')
                        break
                    else:
                        raise FileNotFoundError(f'Could not locate file {p}.')
                c += 1
            if filetop == None:
                if _file:
                    try:
                        os.remove(_file)
                    except KeyError:
                        raise FileNotFoundError(
                            f'Could not remove file {_file}')
                else:
                    try:
                        shutil.rmtree(os.path.join(
                            self.top, pformat(path, sep='.')))
                        return
                    except KeyError:
                        raise OSError(
                            f'Could not remove folder at {os.path.join(self.top, pformat(path, sep="."))}')
            parts = parts[filetop:]
        else:
            _file = self.top+''
        with open(_file, 'r') as f:
            j_loaded = json.loads(f.read())
            ind_str = '["'+'"]["'.join([str(p) for p in parts])+'"]'
            try:
                exec(f'del j_loaded{ind_str}', {'j_loaded': j_loaded})
            except KeyError:
                raise KeyError(
                    f'Could not find key path {".".join(parts)} in file {_file}')
        with open(_file, 'w') as f:
            f.write(json.dumps(j_loaded, indent=self.indent))

class Client(BaseObject):
    def __init__(self, db=None, path=None, update_timeout=0.25, **kwargs):
        super().__init__(db=db, path=path, update_timeout=update_timeout, **kwargs)
        self.__base_object_type__ = 'Client'
        self.kwargs = DefaultsDict(self.kwargs, {
            'fingerprint': '$required',
            'login': None,
            'recent_access': [],
            'last_request': time.time()
        })
        self.fingerprint = self.kwargs['fingerprint']
        self.login = self.kwargs['login']
        self.recent_access = self.kwargs['recent_access']
        self.last_request = self.kwargs['last_request']

class User(BaseObject):
    def __init__(self, db=None, path=None, update_timeout=0.25, **kwargs):
        super().__init__(db=db, path=path, update_timeout=update_timeout, **kwargs)
        self.__base_object_type__ = 'User'
        self.kwargs = DefaultsDict(self.kwargs, {
            'id': generate_fingerprint(full=True),
            'username': '$required',
            'objects': {},
            'current_client': '$required'
        })
        self.id = self.kwargs['id']
        self.username = self.kwargs['username']
        self.objects = self.kwargs['objects']
        self.current_client = self.kwargs['current_client']