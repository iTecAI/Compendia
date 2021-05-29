import bs4
from bs4.element import Tag
from fastapi import APIRouter, Request, Response
from starlette.status import *
from common import *
from pydantic import BaseModel
from typing import *
import markdown2
from bs4 import BeautifulSoup

router = APIRouter()


@router.get('/')
async def get_list_objects(request: Request, response: Response):
    objs = []
    client: Client = SERVER.clients.get(request.state.fingerprint)
    if client.login:
        owned_objects = SERVER.users.get(f'{client.login}.editable_objects')
    else:
        owned_objects = []
    for obj in SERVER.articles.get(''):
        item: Article = SERVER.articles.get(obj)
        if item.public or item.id in owned_objects:
            objs.append({
                'id': item.id,
                'name': item.name,
                'thumbnail': item.thumbnail,
                'type': 'article',
                'can_edit': item.id in owned_objects,
                'tags': item.tags,
                'public': item.public
            })

    return objs


@router.get('/tags')
async def get_list_tags(request: Request, response: Response):
    tags = set()
    client: Client = SERVER.clients.get(request.state.fingerprint)
    if client.login:
        owned_objects = SERVER.users.get(f'{client.login}.editable_objects')
    else:
        owned_objects = []
    for obj in SERVER.articles.get(''):
        item: Article = SERVER.articles.get(obj)
        if item.public or item.id in owned_objects:
            for t in item.tags:
                tags.add(t)
    return list(tags)


@router.get('/articles/{aid}')
async def get_article(request: Request, response: Response, aid: str):
    client: Client = SERVER.clients.get(request.state.fingerprint)
    if client.login:
        owned_objects = SERVER.users.get(f'{client.login}.editable_objects')
    else:
        owned_objects = []
    try:
        article: Article = SERVER.articles.get(aid)
    except (KeyError, FileNotFoundError):
        response.status_code = 404
        return error(f'Object {aid} does not exist, or you do not have access to it.')

    if article.public or article.id in owned_objects:
        adict = article.to_dict()
        adict['editable'] = article.id in owned_objects
        return adict
    else:
        response.status_code = 404
        return error(f'Object {aid} does not exist, or you do not have access to it.')


@router.post('/articles/new')
async def post_new_article(request: Request, response: Response):
    client: Client = SERVER.clients.get(request.state.fingerprint)
    if client.login:
        new_article = Article(db=SERVER.articles)
        new_article._path_ = new_article.id+''
    else:
        response.status_code = HTTP_405_METHOD_NOT_ALLOWED
        return error('Only logged in users can create Articles.')
    new_article.update()
    user: User = SERVER.users.get(client.login)
    user.editable_objects.append(new_article.id)
    user.update()
    return {'result': 'success', 'article_id': new_article.id}


class ModifyArticleModel(BaseModel):
    value: Any


@router.post('/articles/{aid}/modify/{path}')
async def post_modify_article(request: Request, response: Response, aid: str, path: str, model: ModifyArticleModel):
    client: Client = SERVER.clients.get(request.state.fingerprint)
    if client.login:
        owned_objects = SERVER.users.get(f'{client.login}.editable_objects')
    else:
        owned_objects = []

    try:
        article: Article = SERVER.articles.get(aid)
    except (KeyError, FileNotFoundError):
        response.status_code = 404
        return error(f'Object {aid} does not exist, or you do not have access to it.')
    if article.public or article.id in owned_objects:
        try:
            setattr(article, path, model.value)
            article.update()
            return article.to_dict()
        except AttributeError:
            response.status_code = 404
            return error(f'{path} is not an Article attribute.')
    else:
        response.status_code = 404
        return error(f'Object {aid} does not exist, or you do not have access to it.')


@router.post('/articles/{aid}/delete')
async def post_delete_article(request: Request, response: Response, aid: str):
    client: Client = SERVER.clients.get(request.state.fingerprint)
    if client.login:
        owned_objects = SERVER.users.get(f'{client.login}.editable_objects')
    else:
        owned_objects = []

    if aid in owned_objects:
        try:
            SERVER.articles.delete(aid)
        except (KeyError, FileNotFoundError):
            pass
        [SERVER.clients.get(c).update() for c in SERVER.clients.get('')]
        return {'result': 'success'}
    else:
        response.status_code = 404
        return error(f'Object {aid} does not exist, or you do not own it.')

class TagModel(BaseModel):
    name: str
@router.post('/articles/{aid}/tags/delete')
async def post_article_delete_tag(request: Request, response: Response, aid: str, model: TagModel):
    client: Client = SERVER.clients.get(request.state.fingerprint)
    if client.login:
        owned_objects = SERVER.users.get(f'{client.login}.editable_objects')
    else:
        owned_objects = []

    if aid in owned_objects:
        try:
            article: Article = SERVER.articles.get(aid)
        except (KeyError, FileNotFoundError):
            response.status_code = 404
            return error(f'Object {aid} does not exist, or you do not own it.')
        while True:
            try:
                article.tags.remove(model.name)
            except ValueError:
                break
        article.update()
        return {'result': 'success'}
    else:
        response.status_code = 404
        return error(f'Object {aid} does not exist, or you do not own it.')

@router.post('/articles/{aid}/tags/new')
async def post_article_new_tag(request: Request, response: Response, aid: str, model: TagModel):
    client: Client = SERVER.clients.get(request.state.fingerprint)
    if client.login:
        owned_objects = SERVER.users.get(f'{client.login}.editable_objects')
    else:
        owned_objects = []

    if aid in owned_objects:
        try:
            article: Article = SERVER.articles.get(aid)
        except (KeyError, FileNotFoundError):
            response.status_code = 404
            return error(f'Object {aid} does not exist, or you do not own it.')
        if not model.name in article.tags:
            article.tags.append(model.name)
        article.update()
        return {'result': 'success'}
    else:
        response.status_code = 404
        return error(f'Object {aid} does not exist, or you do not own it.')

class ContentModel(BaseModel):
    content: str
@router.post('/articles/{aid}/set_content')
async def post_article_set_content(request: Request, response: Response, aid: str, model: ContentModel):
    client: Client = SERVER.clients.get(request.state.fingerprint)
    if client.login:
        owned_objects = SERVER.users.get(f'{client.login}.editable_objects')
    else:
        owned_objects = []

    if aid in owned_objects:
        try:
            article: Article = SERVER.articles.get(aid)
        except (KeyError, FileNotFoundError):
            response.status_code = 404
            return error(f'Object {aid} does not exist, or you do not own it.')
        article.markdown_content = model.content
        article.html_content = markdown2.markdown(model.content, extras=[
            'tables',
            'cuddled-lists',
            'break-on-newline',
            'code-friendly',
            'fenced-code-blocks',
            'footnotes',
            'header-ids',
            'spoiler',
            'target-blank-links',
            'numbering',
            'task-list'
        ])
        soup = BeautifulSoup(markup=article.html_content, features='html.parser')
        all_headings = soup.select('h1, h2, h3, h4, h5, h6, h7, h8')
        article.heading_ids = [{
            'level': int(h.name.strip('h')),
            'id': h['id'],
            'text': str(h.string)
        } for h in all_headings]
        article.update()
        return {'result': 'success'}
    else:
        response.status_code = 404
        return error(f'Object {aid} does not exist, or you do not own it.')

@router.get('/articles/headings')
async def get_all_headings(request: Request, response: Response):
    articles = {}
    client: Client = SERVER.clients.get(request.state.fingerprint)
    if client.login:
        owned_objects = SERVER.users.get(f'{client.login}.editable_objects')
    else:
        owned_objects = []
    for obj in SERVER.articles.get(''):
        item: Article = SERVER.articles.get(obj)
        if item.public or item.id in owned_objects:
            articles[item.id] = {
                'name': item.name,
                'headings': item.heading_ids
            }

    return articles