from common import *
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from starlette.status import *
from endpoints import Routers
import os
import logging
import time

logger = logging.getLogger('uvicorn')

app = FastAPI()

# Setup routers
app.include_router(Routers.root, prefix='/api', tags=['root'])
app.include_router(Routers.objects, prefix='/api/objects', tags=['objects'])

app.mount('/s', StaticFiles(directory='web'), name='static')

PAGE_ALIASES = ['/']

@app.middleware("http")
async def fingerprint_middleware(request: Request, call_next):
    if request.url.path.startswith('/api'):
        if not 'x-fingerprint' in request.headers.keys():
            return JSONResponse({'result': 'error', 'reason': 'must include the X-Fingerprint header in all API requests.'})
        else:
            fp = request.headers['x-fingerprint']
            try:
                val = SERVER.clients.get(f'{fp}.last_request')
                if time.time() - 5 > val:
                    SERVER.clients.set(f'{fp}.last_request', round(time.time()))
            except (FileNotFoundError, KeyError):
                Client(SERVER.clients, fp, fingerprint=fp).save()
            request.state.fingerprint = fp
            response = await call_next(request)
            return response
    else:
        response = await call_next(request)
        return response

@app.get('/')
async def get_page_index():
    return FileResponse(path=pformat('web/index.html'), media_type='text/html')

@app.get('/article/{aid}')
async def get_article_page(request: Request, aid: str):
    response = FileResponse(pformat('web/article_viewer.html'), media_type='text/html')
    response.set_cookie('ARTICLE_ID', aid, path=f'/article/{aid}', httponly=False, samesite='strict')
    return response
    