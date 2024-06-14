import os
import json
from sanic import Sanic, response
from sanic_session import Session, InMemorySessionInterface
from sanic.request import Request
from common_utils.utils_funcs import front_update_language, update_language
from constants import ASSETS_FOLDER, LANGUAGE, CMS_USER_SESSION_KEY, PUBLIC_FOLDER, LANGUAGE_JSON, CMS_LANGUAGE_JSON
from project_kfShare import ProjectConfig
from create_app import create_app, request

app = create_app(ProjectConfig)

# Load LANGUAGE_JSON
jdata = open(os.path.join('static', 'easychat', 'assets', 'LANGUAGE', 'frontChat.json'), 'r', encoding='utf-8').read()
jdata = json.loads(jdata)
jdatas = {}
index_dict = {}
for index, jd in enumerate(jdata):
    index = 'l' + str(index)
    index_dict[index] = len(jd.get('zh'))
    jdatas[index] = jd
ddd = sorted(index_dict.items(), key=lambda x: x[1], reverse=True)
for dv in ddd:
    LANGUAGE_JSON.append(jdatas.get(dv[0]))

# Load CMS_LANGUAGE_JSON
jdata1 = open(os.path.join('static', 'easychat', 'assets', 'LANGUAGE', 'cmsLanguage.json'), 'r', encoding='utf-8').read()
jdata1 = json.loads(jdata1)
jdatas1 = {}
index_dict1 = {}
for index, jd in enumerate(jdata1):
    index = 'l' + str(index)
    index_dict1[index] = len(jd.get('zh'))
    jdatas1[index] = jd
ddd1 = sorted(index_dict1.items(), key=lambda x: x[1], reverse=True)
for dv in ddd1:
    CMS_LANGUAGE_JSON.append(jdatas1.get(dv[0]))

@app.route('/assets/chat/<filename:path>')
async def assetsChat(request, filename):
    if not filename or not filename.strip():
        return response.text('Forbidden', status=403)
    if 'private' in filename or 'project_' in filename or 'backup' in filename:
        return response.text('Forbidden', status=403)
    project_static_file = os.path.join('static', 'easychat', ASSETS_FOLDER, filename)
    if project_static_file.endswith('js/app.js') or project_static_file.endswith('js/socketioApp.js') or \
            project_static_file.endswith('js/xtalert.js'):
        user_uuid = request.ctx.session.get(CMS_USER_SESSION_KEY)
        if user_uuid:
            from models.cms_user import CmsUserModel
            current_admin_dict = CmsUserModel.find_one({'uuid': user_uuid}) or {}
            language1 = current_admin_dict.get('language') or LANGUAGE.zh_CN
            with open(project_static_file, 'r', encoding='utf-8') as f:
                dataf = f.read()
                dataf = update_language(language1, dataf)
            return response.text(dataf, content_type='text/plain; charset=utf-8')

    if os.path.exists(project_static_file):
        return await response.file(project_static_file)
    return response.text('Forbidden', status=403)

@app.route('/public/chat/<filename:path>')
async def publicChat(request, filename):
    if not filename or not filename.strip():
        return response.text('Forbidden', status=403)
    if 'private' in filename or 'project_' in filename:
        return response.text('Forbidden', status=403)
    project_static_file = os.path.join('static', 'easychat', PUBLIC_FOLDER, filename)
    if project_static_file.endswith('js/app.js') or project_static_file.endswith('js/socketioApp.js') or \
            project_static_file.endswith('js/xtalert.js') or project_static_file.endswith('js/pickerDate.js'):
        language1 = request.args.get('language') or LANGUAGE.zh_CN
        with open(project_static_file, 'r', encoding='utf-8') as f:
            dataf = f.read()
            dataf = front_update_language(language1, dataf)
        return response.text(dataf, content_type='text/plain; charset=utf-8')

    if os.path.exists(project_static_file):
        return await response.file(project_static_file)
    return response.text('Forbidden', status=403)

if __name__ == '__main__':
    import logging
    from sanic.log import logger
    logger.setLevel(logging.INFO)  # Adjust log level as needed
    app.run(host="0.0.0.0", port=5021, debug=True)

