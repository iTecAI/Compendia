from fastapi import APIRouter, Request, Response
from starlette.status import *
from common import *
from pydantic import BaseModel
from hashlib import sha256

router = APIRouter()

@router.get('/status')
async def get_client_status(request: Request, response: Response):
    client: Client = SERVER.clients.get(request.state.fingerprint)
    if client.login:
        userupdate = SERVER.users.get(client.login).check_update()
    else:
        userupdate = False
    return {
        'updates': {
            'client': client.check_update(),
            'user': userupdate,
            'articles': {i: SERVER.articles.get(i).check_update() for i in SERVER.articles.get('')},
            'maps': {i: SERVER.maps.get(i).check_update() for i in SERVER.maps.get('')}
        },
        'fingerprint': client.fingerprint,
        'login': client.login,
        'recent': client.recent_access
    }

class LoginModel(BaseModel):
    username: str
    hashword: str
@router.post('/login')
async def post_login(request: Request, response: Response, model: LoginModel):
    client = SERVER.clients.get(request.state.fingerprint)
    if client.login:
        response.status_code = HTTP_405_METHOD_NOT_ALLOWED
        return error('Client is logged in.');
    for i in SERVER.config.get('logins'):
        try:
            if i['username'] == model.username:
                if sha256(i['password'].encode('utf-8')).hexdigest() == model.hashword:
                    try:
                        uid = get_uid(model.username)
                        c_user = SERVER.users.get(uid)
                        c_user.current_client = request.state.fingerprint
                        c_user.save()
                    except KeyError:
                        new_user = User(db=SERVER.users, username=model.username, current_client=request.state.fingerprint)
                        new_user._path_ = new_user.id+''
                        uid = new_user.id
                        new_user.save()
                    client.login = uid
                    client.update()
                    return {'result': 'success'}
                else:
                    response.status_code = 403
                    return error(f'Incorrect password for "{model.username}"')
        except KeyError:
            raise ConfigurationError(f'Failed to read login entry "{str(i)}". Missing username or password key.')
    response.status_code = 404
    return error(f'Username "{model.username}" not found on this server. Please enter it into the logins key of the server\'s configuration file.')

@router.post('/logout')
async def post_logout(request: Request, response: Response):
    client = SERVER.clients.get(request.state.fingerprint)
    if client.login:
        user = SERVER.users.get(client.login)
        user.current_client = None
        user.save()
        client.login = None
        client.update()
        return {'result': 'success'}
    else:
        response.status_code = HTTP_405_METHOD_NOT_ALLOWED
        return error('Client is not logged in.');