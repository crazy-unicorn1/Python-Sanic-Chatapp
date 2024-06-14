# -*- coding: utf-8 -*-
import os, datetime, click, time, requests
from app_kfShare import app, ProjectConfig, PUBLIC_FOLDER
# from app_kfDemo import app, ProjectConfig, PUBLIC_FOLDER
from common_utils.lqredis import SiteRedis
from common_utils.mongodb.mongo_admin import MongoManage, CONFIG
from constants import PermissionCls, OnlineStatu
from models.cms_user import CmsUserModel
from models.cms_table import SiteConfigModel
from models.site_table import SiteTable
from models.kefu_table import CustomerTable, ChatConversationTable, ChatContentTable, BlacklistTable, LeavingMessageTable, QuickReplyTable, FinishListTable, IpTable
from modules.site_module.ftpCls import FtpCls
from modules.site_module.botCls import sendTelMag



@click.group()
def mainFunc():
    pass


@mainFunc.command()
@click.option('--login_account', '-t')
@click.option('--password', '-p')
def init_admin(login_account, password):
    """ 初始化admin用户 """
    if not login_account.strip():
        print('请输入登录账户!')
        return '请输入登录账户!'
    if not password:
        password = 'admin123'
    # CmsUserModel.delete_many({})
    user_data = {
        'account': login_account.strip(),
        'password': CmsUserModel.encry_password(password.strip()),
        'username': '系统管理员账户2',
        'statu': True,
        'permissions': [PermissionCls.SUPERADMIN],
        'role_code': PermissionCls.SUPERADMIN,
        '_current_login': '',
        'online_statu': OnlineStatu.online,
        'is_activate': False,
    }
    CmsUserModel.insert_one(user_data)
    print('%s: success!' % login_account)
    return '%s: 用户添加成功!'%login_account


@mainFunc.command()
def init_index():
    """创建索引"""
    from models.kefu_table import CacheDataTable
    for MCLS in [CmsUserModel, SiteConfigModel, CustomerTable, ChatConversationTable, ChatContentTable, BlacklistTable, SiteTable, LeavingMessageTable, CacheDataTable]:
        indexs = MCLS.index_information()
        for k, v in MCLS.fields().items():
            if not hasattr(v, 'is_index'):
                continue
            if not getattr(v, 'is_index'):
                continue
            if not indexs.get('%s_1' % k) and v.is_index:
                if v.unique:
                    print(k, MCLS.create_index(k, unique=True))
                else:
                    print(k, MCLS.create_index(k))


@mainFunc.command()
def remove_project_data():
    """清空整个项目所有数据库内的数据"""
    instruction = input('该操作会清除当前项目下所有的数据,指令（Y/N），回复确认操作Y，其它拒绝操作!')
    if instruction.strip() != 'Y':
        exit()
    for key in SiteRedis.get_keys():
        if key.decode().startswith(ProjectConfig.PROJECT_NAME):
            SiteRedis.dele(key)
    p_db = MongoManage(username=CONFIG.root_username, password=CONFIG.root_password)
    print(p_db.drop_database(ProjectConfig.MONGODB_DB))
    return '操作成功!'


@mainFunc.command()
def update_primary_key():
    """更细项目字段主键"""
    print('更新项目字段主键KEY')
    for _k in SiteRedis.get_keys():
        _k = _k.decode()
        if ProjectConfig.PROJECT_NAME in _k and '_field' in _k:
            SiteRedis.dele(_k)
    import models
    for n in dir(models):
        if n.startswith('__') or n == 'db' or n == 'dbModel' or n == 'MongoBase':
            continue
        n_f = getattr(models, n)
        for c in dir(n_f):
            if c == 'dbModel':
                continue
            MCLS = getattr(n_f, c)
            if not hasattr(MCLS, '__tablename__') or not getattr(MCLS, '__tablename__'):
                continue
            table_name = getattr(MCLS, '__tablename__')
            for db_field, v_Cls in MCLS.fields().items():
                if not hasattr(v_Cls, 'field_type'):
                    continue
                if v_Cls.primary_key:
                    v_dict = MCLS.find_one({}, sort=[[db_field, -1]])
                    if v_dict:
                        kk_v = v_dict.get(db_field) or 0
                        _redis_check_key = '%s_%s_%s_%s_field' % (ProjectConfig.PROJECT_NAME, ProjectConfig.MONGODB_DB, table_name, db_field)
                        SiteRedis.set(_redis_check_key, kk_v)
                        print(table_name, db_field, kk_v)
    print('项目字段主键KEY更新完毕！')


@mainFunc.command()
def update_secret_key():
    import base64
    from models.cms_table import SiteConfigModel
    site_data = SiteConfigModel.find_one({'project_name': app.config.get("PROJECT_NAME")}) or {}
    new_secret_key = base64.b64encode(os.urandom(66)).decode()
    site_data['secret_key'] = new_secret_key
    SiteConfigModel.save(site_data)
    print('success!')

@mainFunc.command()
def backup_datas():
    while True:
        print('backup polling...')
        time.sleep(30)
        crr_date = datetime.datetime.now()
        if crr_date.hour < 17:
            continue

        crrDate = crr_date.strftime('%Y%m%d')
        folder = app.root_path + '/static/' + ProjectConfig.PROJECT_NAME + '/assets/backup/' + crrDate
        if os.path.exists(folder):
            continue

        os.makedirs(folder)
        cmd = 'chmod 777 ' + folder
        os.system(cmd)

        for c in [SiteConfigModel, CmsUserModel, QuickReplyTable, IpTable, SiteTable]:
            file_path = f'{folder}/{c.__tablename__}.json'
            cmd = f'/opt/mongodb/bin/mongoexport -h 127.0.0.1:27017 -u project_kfShare -p project_kfShare@13141152099 -d {ProjectConfig.PROJECT_NAME} -c {c.__tablename__} -o ' + file_path
            os.system(cmd)
        cmd = f'zip -r {folder}.zip {folder}'
        os.system(cmd)
        # print(22)
        # ftpcls = FtpCls(
        #     host='202.92.4.97',
        #     user='mnnqywkdhosting',
        #     pwd='iN3@TxLbupVR66A'
        # )
        # ftpcls.uploadFile(folder+'.zip', '/project_kfShare/'+crrDate+'.zip')
        # print(33)


@mainFunc.command()
def site_expire_warn():
    date_list = []
    while True:
        print('site_expire_warn polling...')
        crr_time = datetime.datetime.now()
        crr_5time = crr_time + datetime.timedelta(days=5)
        crr_Date = crr_time.strftime('%Y%m%d')

        if crr_time.hour < 6:
            time.sleep(60*10)
            continue

        if crr_Date in date_list:
            time.sleep(60*10)
            continue

        sitedatas = SiteTable.find_many({'finish_time': {'$lte': crr_5time, '$gte': crr_time}})
        if not sitedatas:
            time.sleep(60*10)
            continue

        for sitedata in sitedatas:
            finish_time = sitedata.get('finish_time')
            text = f'网站：{sitedata.get("site_name")}，即将到期，请注意提醒商户续费！\n到期时间：{finish_time.strftime("%Y-%m-%d %H:%M:%S")}'
            sendTelMag(text)

        date_list.append(crr_Date)
        time.sleep(60*60)


@mainFunc.command()
def test():
    from models.kefu_table import CacheDataTable

    CacheDataTable.insert_one({
        'mkey': '111'
    })
    return

    # from models.kefu_table import systemLogTable
    # print(CmsUserModel.find_one({'uuid':'GRcKDHWmw66jgvzwpy5ybY'}))
    # exit()
    #
    # for dd in systemLogTable.find_many({'note': '删除用户！'}):
    #     print(dd)
    # exit()
    #
    # dd = CmsUserModel.find_one({'account': 'adminkf999'})
    # CmsUserModel.update_one({'uuid': dd.get('uuid')}, {'$set': {'password': CmsUserModel.encry_password('QWEzxc@612')}})
    # return
    # dd = CmsUserModel.find_one({'account': 'admin123'})
    # CmsUserModel.update_one({'uuid': dd.get('uuid')}, {'$set': {'password': CmsUserModel.encry_password('QWEzxc@123456')}})
    # return
    # dd = CmsUserModel.find_one({'account': 'admin123'})
    # CmsUserModel.update_one({'uuid': dd.get('uuid')}, {'$set': {'password': CmsUserModel.encry_password('QWEzxc@689'), 'account': 'adminkf666'}})
    # dd = CmsUserModel.find_one({'account': 'admin666'})
    # CmsUserModel.update_one({'uuid': dd.get('uuid')}, {'$set': {'password': CmsUserModel.encry_password('QWEzxc@612'), 'account': 'adminkf999'}})
    # exit()
    # localpath = '/www/project_kfShare/static/project_kfShare/assets/backup/20240125'
    # for c in [SiteConfigModel, CmsUserModel, SiteTable, QuickReplyTable, IpTable]:
    #     c.delete_many({})
    #     print('toto:', c.__tablename__)
    #     c.delete_many({})
    #     cmd = f'/opt/mongodb/bin/mongoimport -h 127.0.0.1:27017 -d {ProjectConfig.PROJECT_NAME} -c {c.__tablename__} --file {localpath.replace(".zip", "")}/{c.__tablename__}.json'
    #     os.system(cmd)

    DD = SiteConfigModel.find_one({})
    SiteConfigModel.update_one({'uuid': DD.get('uuid')}, {'$set': {'site_domain': 'easychat.pro'}})
    # for dd in SiteTable.find_many({}):
    #     SiteTable.update_one({'uuid': dd.get('uuid')}, {'$set': {'use_domain': 'easychat.pro'}})


if __name__ == '__main__':
    mainFunc()
