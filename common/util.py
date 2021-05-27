import os, random, hashlib, time, copy

def pformat(path, sep='/'):
    return os.path.join(*path.replace(':', '{{colon}}').split(sep)).replace('{{colon}}', ':')

def generate_fingerprint(length=12, full=False):
    ha = hashlib.sha256(str(time.time()+random.random()
                            ).encode('utf-8')).hexdigest()
    if full:
        return ha
    return ''.join([random.choice(ha) for i in range(length)])


def failure(reason):
    return {
        'result': 'failure',
        'reason': reason
    }

def condition(c, t, f):
    if c:
        return t
    else:
        return f

def get_at_dict_path(dct, path, sep='.'):
    parts = path.split('.')
    jnr = ''
    for p in parts:
        try:
            int(p)
            jnr += f'[{str(p)}]'
        except ValueError:
            jnr += f'["{str(p)}"]'
    return eval(f'dct{jnr}', {'dct': dct})

def set_at_dict_path(dct, path, value, sep='.'):
    parts = path.split('.')
    jnr = ''
    for p in parts:
        try:
            int(p)
            jnr += f'[{str(p)}]'
        except ValueError:
            jnr += f'["{str(p)}"]'
    exec(f'dct{jnr} = value', {'dct': dct, 'value': value})
    return copy.deepcopy(dct)

def get_at_base_obj_path(dct, path, sep='.'):
    parts = path.split('.')
    jnr = f'.{parts[0]}'
    if len(parts) > 1:
        for p in parts[1:]:
            for p in parts:
                try:
                    int(p)
                    jnr += f'[{str(p)}]'
                except ValueError:
                    jnr += f'["{str(p)}"]'
    return eval(f'dct{jnr}', {'dct': dct})

def set_at_base_obj_path(dct, path, value, sep='.'):
    parts = path.split('.')
    jnr = f'.{parts[0]}'
    if len(parts) > 1:
        for p in parts[1:]:
            try:
                int(p)
                jnr += f'[{str(p)}]'
            except ValueError:
                jnr += f'["{str(p)}"]'
    exec(f'dct{jnr} = value', {'dct': dct, 'value': value})
    return copy.copy(dct)

def error(reason):
    return {'result': 'error', 'reason': reason}