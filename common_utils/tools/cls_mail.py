# -*- coding: utf-8 -*-
import re, time, poplib, smtplib, datetime
from email.header import Header
from email.parser import Parser
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr


class EmailCLS(object):
    """发送邮件"""

    def __init__(self, CONFIG, recipients=[]):
        self.mail_account = CONFIG.get('mail_account')      #发送帐号
        self.mail_host = CONFIG.get('mail_host')            #邮件服务器地址
        self.mail_password = CONFIG.get('mail_password')    #邮箱密码
        self.mail_port = CONFIG.get('mail_port')            #发送端口
        self.display_name = CONFIG.get('display_name')      #发送人姓名
        self.mail_sender = self.mail_account                #发送者
        self.recipients = recipients                        #收件人

    def _format_addr(self):
        """格式化发送者信息"""
        if self.display_name:
            name, addr = parseaddr(u'%s <%s>' % (self.display_name, self.mail_account))
            if isinstance(addr, bytes):
                addr = addr.decode()
            return formataddr((Header(name, 'utf-8').encode(), addr))
        return self.mail_account

    def send_text(self, title, msg):
        """发送文本"""
        message = MIMEText(msg, "plain", "utf-8")
        message["From"] = self._format_addr()
        message["To"] = ",".join(self.recipients)
        message["Subject"] = Header(title, "utf-8")
        try:
            # 登录，并发送邮件, SMTP() smtp_port:25
            smtpObj = smtplib.SMTP_SSL(self.mail_host, self.mail_port)
            smtpObj.login(self.mail_account, self.mail_password)
            smtpObj.sendmail(self.mail_sender, self.recipients, message.as_string())
            smtpObj.quit()
            return True, None
        except smtplib.SMTPException as excep:
            return False,  'error:' + str(excep)

    def send_html(self, title, msg_html):
        """发送HTML"""
        message = MIMEText(msg_html, "html", "utf-8")
        message["From"] = self._format_addr()
        message["To"] = ",".join(self.recipients)
        message["Subject"] = Header(title, "utf-8")
        try:
            smtpObj = smtplib.SMTP_SSL(self.mail_host, self.mail_port)
            smtpObj.login(self.mail_account, self.mail_password)
            smtpObj.sendmail(self.mail_sender, self.recipients, message.as_string())
            smtpObj.quit()
            return True, None
        except smtplib.SMTPException as excep:
            return False,  'error:' + str(excep)

    def send_accessory(self, title, msg_html, file_path=None, file_name=None, imgs=[]):
        """发送HTML（携带附件）"""
        msg_content = MIMEText(msg_html, "html", "utf-8")
        message = MIMEMultipart("related")
        message.attach(msg_content)
        if imgs:
            for img in imgs:
                msg_image = MIMEImage(open(img, "rb").read())
                msg_image.add_header("Content-ID", "<image_id_1>")
                message.attach(msg_image)
        if file_name:
            file_path = file_path + file_name
            msg_file = MIMEText(open(file_path, "r").read(), "base64", "utf-8")
            msg_file["Content-Type"] = "application/octet-stream"
            msg_file["Content-Disposition"] = "attachment; filename=\"%s\"" % file_name
            message.attach(msg_file)
        message["From"] = self._format_addr()
        message["To"] = ",".join(self.recipients)
        message["Subject"] = Header(title, "utf-8")
        try:
            smtpObj = smtplib.SMTP_SSL(self.mail_host, self.mail_port)
            smtpObj.login(self.mail_account, self.mail_password)
            smtpObj.sendmail(self.mail_sender, self.recipients, message.as_string())
            smtpObj.quit()
            return True, 'success'
        except smtplib.SMTPException as excep:
            return False,  'error:' + str(excep)


class MailReadCls(object):
    """读取邮件"""

    def __init__(self, account, password):
        self.account = account
        self.password = password

    @classmethod
    def getTimeStamp(cls, date):
        """解析时区：Sat, 26 Sep 2020 17:48:45 +0800"""
        localtimestamp = None
        result = re.search(r"[\-\+]\d+", date)
        if result:
            time_area = result.group()
            symbol = time_area[0]
            offset = int(time_area[1]) + int(time_area[2])
            if symbol == "+":
                format_str = '%a, %d %b %Y %H:%M:%S ' + time_area
                if "UTC" in date:
                    format_str = '%a, %d %b %Y %H:%M:%S ' + time_area + ' (UTC)'
                if "GMT" in date:
                    format_str = '%a, %d %b %Y %H:%M:%S ' + time_area + ' (GMT)'
                if "CST" in date:
                    format_str = '%a, %d %b %Y %H:%M:%S ' + time_area + ' (CST)'
                utcdatetime = time.strptime(date, format_str)
                tempsTime = time.mktime(utcdatetime)
                tempsTime = datetime.datetime.fromtimestamp(tempsTime)
                if offset >= 8:
                    offset = offset - 8
                tempsTime = tempsTime + datetime.timedelta(hours=offset)
                localtimestamp = tempsTime.strftime("%Y-%m-%d %H:%M:%S")
            else:
                format_str = '%a, %d %b %Y %H:%M:%S ' + time_area
                utcdatetime = time.strptime(date, format_str)
                tempsTime = time.mktime(utcdatetime)
                tempsTime = datetime.datetime.fromtimestamp(tempsTime)
                tempsTime = tempsTime + datetime.timedelta(hours=(offset + 8))
                localtimestamp = tempsTime.strftime("%Y-%m-%d %H:%M:%S")
        return localtimestamp

    @classmethod
    def guess_charset(cls, msg):
        """获取编码类型"""
        charset = msg.get_charset()
        if charset is None:
            content_type = msg.get('Content-Type', '').lower()
            pos = content_type.find('charset=')
            if pos >= 0:
                charset = content_type[pos + 8:].strip()
        return charset

    @classmethod
    def decode_str(cls, s):
        value, charset = decode_header(s)[0]
        if charset:
            value = value.decode(charset)
        return value

    @classmethod
    def parsing(cls, part):
        content_type = part.get_content_type()
        if content_type == 'text/plain' or content_type == 'text/html':
            content = part.get_payload(decode=True)
            charset = cls.guess_charset(part)
            if charset:
                content = content.decode(charset)
            return content
        else:
            return content_type

    @classmethod
    def get_info(cls, msg):
        mail_data = {}
        for header in ['From', 'To', 'Subject', 'Date']:
            value = msg.get(header, '')
            if value:
                if header == 'Subject':
                    value = cls.decode_str(value)
                elif header == 'Date':
                    value = cls.getTimeStamp(value)
                else:
                    hdr, addr = parseaddr(value)
                    name = cls.decode_str(hdr)
                    value = u'%s <%s>' % (name, addr)
            mail_data[header] = value
        msg_content = ''
        # 判断消息是否由多部分组成
        if msg.is_multipart():
            parts = msg.get_payload()
            for n, part in enumerate(parts):
                msg_content += cls.parsing(part)
        else:
            msg_content += cls.parsing(msg)
        mail_data['msg_content'] = msg_content
        return mail_data

    def getmail(self, latest=False):
        mail_msg_ls = []
        pop3_server = 'pop.qq.com'
        server = poplib.POP3_SSL(pop3_server)
        server.user(self.account)
        server.pass_(self.password)
        mail_count = server.stat()[0]
        print('读取到邮件条数：%s' % mail_count)
        if mail_count == 0:
            server.quit()
            return
        # 返回邮箱的状态，邮件编号和octets
        resp, mails, octets = server.list()
        if latest:
            # 取最新的邮件
            mails = mails[-1:]
            # index = len(mails)
        for mail_c in mails:
            mail_data = mail_c.decode()
            mail_index = int(mail_data.split(' ', 1)[0])
            mail_id = int(mail_data.split(' ', 1)[1])
            resp, lines, octets = server.retr(mail_index)
            msg_content = b'\r\n'.join(lines).decode('utf-8')
            msg = Parser().parsestr(msg_content)
            mailData = self.get_info(msg)
            mailData['mail_id'] = mail_id
            mail_msg_ls.append(mailData)
        server.quit()
        return mail_msg_ls


# username1 = "@qq.com"
# password1 = "aruoevonlinibbbe"
# username2 = "@qq.com"
# password2 = "qygosngogcbybhee"
#
# config = {
#     'mail_account': username2,
#     'mail_password': password2,
#     'display_name': '',
#     'mail_host': 'smtp.qq.com',
#     'mail_port': 465,
# }
# print(EmailCLS(config, recipients=['@qq.com']).send_text('', '666'))
# msg = MailReadCls.getmail(config.get('mail_account'), config.get('mail_password'), latest=True)
# for m in msg:
#     for k, v in m.items():
#         print(k, v)
#     print('*_'*50)

