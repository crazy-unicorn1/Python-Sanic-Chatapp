import os, json
import shortuuid
import base64
from sanic import Sanic, response, request
from sanic_cors import CORS
from importlib import import_module
from constants import SITE_CONFIG_CACHE, ASSETS_FOLDER, PUBLIC_FOLDER, CHAT_NAMESPACE_CONNECTIONS, SERVICECHAT_NAMESPACE_CONNECTIONS
from common_utils import xtjson
from site_exts import db, socketio
from sanic_session import Session, InMemorySessionInterface, RedisSessionInterface
import asyncio_redis
from aiofiles import os as async_os

class Redis:
    """
    A simple wrapper class that allows you to share a connection
    pool across your application.
    """
    _pool = None

    async def get_redis_pool(self):
        if not self._pool:
            self._pool = await asyncio_redis.Pool.create(
                host='localhost', port=6379, poolsize=10
            )

        return self._pool
    

def create_app(config):
    app = Sanic(__name__)
    CORS(app, supports_credentials=True)

    app.config['SESSION_COOKIE_NAME'] = 'session'
    app.config['SESSION_EXPIRE_SECONDS'] = None   
    app.config.DEBUG = True
    app.config.WTF_CSRF_ENABLED = True
    app.config.update_config(config)

    app.config.WEBSOCKET_MAX_SIZE = 2 ** 20
    app.config.WEBSOCKET_MAX_QUEUE = 128
    app.config.WEBSOCKET_READ_LIMIT = 2 ** 16
    app.config.WEBSOCKET_WRITE_LIMIT = 2 ** 16
    app.config.WEBSOCKET_PING_INTERVAL = 600
    app.config.WEBSOCKET_PING_TIMEOUT = 600

    redis = Redis()
    Session(app, interface=RedisSessionInterface(redis.get_redis_pool))

    db.init_app(config)

    def init_data():
        SiteConfig = getattr(db.database, 'site_config_table')
        site_data = SiteConfig.find_one({'project_name': config.PROJECT_NAME}) or {}
        if not site_data:
            site_data['uuid'] = shortuuid.uuid()
            site_data['project_name'] = config.PROJECT_NAME
            site_data['secret_key'] = base64.b64encode(os.urandom(66)).decode()
            site_data['cms_prefix'] = ''
            site_data['site_domain'] = ''
            site_data['control_file_type_state'] = False
            site_data['control_file_types'] = []
            site_data['automati_creply'] = ''
            site_data['reception_count'] = 10
            site_data['control_file_size'] = 10485760
            site_data['clew_text'] = ''
            SiteConfig.insert_one(site_data)
        result_config = {
            'SECRET_KEY': site_data.get('secret_key'),
        }
        return result_config
    app.config.update(init_data())

    project_static_root = os.path.join("static", config.PROJECT_NAME, ASSETS_FOLDER)
    os.makedirs(project_static_root, exist_ok=True)

    from models.cms_table import SiteConfigModel
    from models.site_table import SiteTable
    SiteConfigModel.update_site_config()
    SiteTable.update_site_config()

    registed_view = import_module(f'{config.PROJECT_NAME}.register_view')

    # Check if the required blueprints exist in the imported modules
    for bp_name in ['front_bp', 'cms_bp', 'common_bp']:
        if not hasattr(registed_view, bp_name):
            print(f'Missing {bp_name} blueprint in view modules!')
            exit()

    # Register the blueprints with the Sanic app
    for bp_name in ['front_bp', 'common_bp', 'cms_bp']:
        bp = getattr(registed_view, bp_name)
        app.blueprint(bp)

    from views.api_views.api_view import ChatSocketIOCls, ServiceSocketIoCls

    chat_server = ChatSocketIOCls()
    serviceChat_server = ServiceSocketIoCls()

    @app.websocket('/chat')
    async def websocket_chat_handler(request, ws):
        if request.ctx.session.sid not in CHAT_NAMESPACE_CONNECTIONS:
            CHAT_NAMESPACE_CONNECTIONS[request.ctx.session.sid] = ws
            chat_server.on_connect(request)
        try:
            while True:
                data_str = await ws.recv()
                CHAT_NAMESPACE_CONNECTIONS[request.ctx.session.sid] = ws
                data_json = json.loads(data_str)
                event_id = data_json.get("event_id")
                data = data_json.get("data")
                print("----------- chat -----------", event_id, data)
                await chat_server.on_process_message(request, event_id=event_id, msg=data)
        except Exception as e:
            # Print the error message associated with the exception
            print("An error occurred:", e)
            await chat_server.on_disconnect(request)
            if request.ctx.session.sid in CHAT_NAMESPACE_CONNECTIONS:
                CHAT_NAMESPACE_CONNECTIONS.pop(request.ctx.session.sid)

        finally:
            # Disconnection event
            await chat_server.on_disconnect(request)
            if request.ctx.session.sid in CHAT_NAMESPACE_CONNECTIONS:
                CHAT_NAMESPACE_CONNECTIONS.pop(request.ctx.session.sid)

    @app.websocket('/serviceChat')
    async def websocket_serviceChat_handler(request, ws):
        if request.ctx.session.sid not in SERVICECHAT_NAMESPACE_CONNECTIONS:
            SERVICECHAT_NAMESPACE_CONNECTIONS[request.ctx.session.sid] = ws
            await serviceChat_server.on_connect(request)
        try:
            while True:
                data_str = await ws.recv()
                SERVICECHAT_NAMESPACE_CONNECTIONS[request.ctx.session.sid] = ws
                data_json = json.loads(data_str)
                event_id = data_json.get("event_id")
                data = data_json.get("data")
                print("--------- service ---------", event_id, data)
                await serviceChat_server.on_process_message(request, event_id=event_id, msg=data)
        except Exception as e:
            # Print the error message associated with the exception
            print("An error occurred:", e)
            await serviceChat_server.on_disconnect(request)
            if request.ctx.session.sid in SERVICECHAT_NAMESPACE_CONNECTIONS:
                SERVICECHAT_NAMESPACE_CONNECTIONS.pop(request.ctx.session.sid)

        finally:
            # Disconnection event
            await serviceChat_server.on_disconnect(request)
            if request.ctx.session.sid in SERVICECHAT_NAMESPACE_CONNECTIONS:
                SERVICECHAT_NAMESPACE_CONNECTIONS.pop(request.ctx.session.sid)

    @app.route('/static/<filename:path>')
    async def static(request, filename):
        if 'private' in filename or 'project_' in filename or 'easychat' in filename:
            return response.text('Forbidden', status=403)
        project_static_file = os.path.join("static", filename)
        if os.path.isdir(project_static_file):
            return response.text('Forbidden', status=403)
        if os.path.exists(project_static_file):
            return await response.file(project_static_file)
        return response.text('Not Found', status=404)

    @app.route('/.well-known/pki-validation/<filename:path>')
    async def ssl_verify(request, filename):
        project_static_file = os.path.join("static", config.PROJECT_NAME, filename)
        if os.path.isdir(project_static_file):
            return response.text('Forbidden', status=403)
        if os.path.exists(project_static_file):
            return await response.file(project_static_file)
        return response.text('Not Found', status=404)

    @app.route('/test')
    async def test(request):
        project_static_file = os.path.join("templates", "common" , "1.html")
        if os.path.isdir(project_static_file):
            return response.text('Forbidden', status=403)
        if os.path.exists(project_static_file):
            return await response.file(project_static_file)
        return response.text('Not Found', status=404)

    @app.route('/assets/<filename:path>')
    async def assets(request, filename):
        project_static_file = os.path.join("static", config.PROJECT_NAME, ASSETS_FOLDER, filename)
        if os.path.isdir(project_static_file):
            return response.text('Forbidden', status=403)
        if os.path.exists(project_static_file):
            return await response.file_stream(
                project_static_file,
                chunk_size=8388608,
                mime_type="application/metalink4+xml",
                headers={
                    "Content-Disposition": 'Attachment;',
                    "Content-Type": "application/metalink4+xml",
            })
            #return await response.file(project_static_file)
        return response.text('Not Found', status=404)

    @app.route('/public/<filename:path>')
    async def public(request, filename):
        project_static_file = os.path.join("static", config.PROJECT_NAME, PUBLIC_FOLDER, filename)
        if os.path.isdir(project_static_file):
            return response.text('Forbidden', status=403)
        if os.path.exists(project_static_file):
            return await response.file_stream(
                project_static_file,
                chunk_size=8388608,
                mime_type="application/metalink4+xml",
                headers={
                    "Content-Disposition": 'Attachment;',
                    "Content-Type": "application/metalink4+xml",
            })
            # file_stat = await async_os.stat(project_static_file)
            # headers = {"Content-Length": str(file_stat.st_size)}

            # return await response.file_stream(
            #     project_static_file,
            #     headers=headers,
            # )
            return await response.file(project_static_file)
        return response.text('Not Found', status=404)

    @app.route(r"/(?P<textname>.+)\.txt")
    async def txtfile(request, textname):
        data = ''
        if textname == 'robots':
            if hasattr(SITE_CONFIG_CACHE, 'robots'):
                data = getattr(SITE_CONFIG_CACHE, 'robots')
        if not data:
            return response.text('Not Found', status=404)
        return response.text(data, content_type='text/plain; charset=utf-8')

    @app.route('/favicon.ico')
    async def icon(request):
        return response.text('')

    def is_xhr(request):
        X_Requested_With = request.headers.get('X-Requested-With')
        if not X_Requested_With or X_Requested_With.lower() != 'xmlhttprequest':
            return
        return True

    @app.exception(401)
    async def cms_no_auth(request, exception):
        if is_xhr(request):
            return xtjson.json_unauth_error('401,没有权限！')
        return response.text('401,没有权限', status=401)

    @app.exception(403)
    async def cms_not_file(request, exception):
        if is_xhr(request):
            return xtjson.json_params_error()
        return response.text('403,资源不可用！', status=403)

    @app.exception(404)
    async def cms_not_fount(request, exception):
        if is_xhr(request):
            return xtjson.json_params_error('404')
        if hasattr(SITE_CONFIG_CACHE, 'html_404'):
            return await response.file(SITE_CONFIG_CACHE.html_404, status=404)
        return await response.file('common/404.html', status=404)

    @app.exception(405)
    async def error_method(request, exception):
        if is_xhr(request):
            return xtjson.json_method_error('405, 请求方法错误！')
        return response.text('405,请求方法错误', status=405)

    @app.exception(500)
    async def error_method500(request, exception):
        if is_xhr(request):
            return xtjson.json_method_error('500, 服务器出错！')
        return response.text('500,服务器出错!', status=500)

    return app
