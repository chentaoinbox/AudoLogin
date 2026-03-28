import requests
import re
import gzip
import os
from urllib.parse import urljoin, urlparse, parse_qs, quote
import chardet
import json
import logging

class AutoLogin:
    def __init__(self, username, password, base_url="http://10.10.9.9", log_file=None):
        """
        初始化 Portal 认证客户端
        :param username: 用户名
        :param password: 密码
        :param base_url: Portal 服务器地址
        :param log_file: 日志文件路径，指定后将所有日志写入文件（包含 INFO 级别），不指定则不写文件
        """
        self.username = username
        self.password = password
        self.base_url = base_url
        self.session = requests.Session()
        self.session.cookies.clear()

        # 配置日志
        self.logger = logging.getLogger('AutoLogin')
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            # 控制台处理器：只显示 WARNING 及以上
            console = logging.StreamHandler()
            console.setLevel(logging.WARNING)
            console.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(console)

            # 文件处理器：记录所有级别
            if log_file:
                # 确保日志目录存在
                log_dir = os.path.dirname(log_file)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                self.logger.addHandler(file_handler)

        self._init_headers()

    def _init_headers(self):
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })

    @staticmethod
    def _encode_uri_component(s):
        safe_chars = "-_.!~*'()"
        return quote(s, safe=safe_chars)

    @staticmethod
    def _double_encode(s):
        return AutoLogin._encode_uri_component(AutoLogin._encode_uri_component(s))

    @staticmethod
    def _rsa_encrypt_string(key_e_hex, key_n_hex, s):
        a = [ord(c) for c in s]
        n = int(key_n_hex, 16)
        modulus_bytes = (n.bit_length() + 7) // 8
        chunk_size = modulus_bytes - 1

        while len(a) % chunk_size != 0:
            a.append(0)

        block_int = 0
        for i in range(0, len(a), 2):
            low = a[i] if i < len(a) else 0
            high = a[i+1] if i+1 < len(a) else 0
            digit = low + (high << 8)
            block_int |= digit << (16 * (i // 2))

        e = int(key_e_hex, 16)
        encrypted_int = pow(block_int, e, n)
        return format(encrypted_int, 'x')

    @staticmethod
    def _decode_json_response(resp):
        content = resp.content
        content_type = resp.headers.get('Content-Type', '')
        charset = None
        if 'charset=' in content_type:
            charset = content_type.split('charset=')[-1].split(';')[0].strip().lower()
        if not charset:
            charset = chardet.detect(content)['encoding'] or 'gb18030'
        text = content.decode(charset, errors='replace')
        return json.loads(text)

    def _get_portal_page(self):
        # 1. 根路径
        r = self.session.get(self.base_url, allow_redirects=False)
        if r.status_code != 302:
            raise Exception(f"根路径未返回302，状态码: {r.status_code}")
        loc1 = r.headers.get('Location')

        # 2. redirectortosuccess.jsp
        r = self.session.get(loc1, allow_redirects=False)
        if r.status_code != 302:
            raise Exception(f"redirectortosuccess.jsp 未返回302，状态码: {r.status_code}")
        loc2 = r.headers.get('Location')

        # 3. 外网页面
        r = self.session.get(loc2, allow_redirects=False)
        if r.status_code != 200:
            raise Exception(f"外网页面未返回200，状态码: {r.status_code}")

        data = r.content
        if data[:2] == b'\x1f\x8b':
            data = gzip.decompress(data)

        content_type = r.headers.get('Content-Type', '')
        charset = None
        if 'charset=' in content_type:
            charset = content_type.split('charset=')[-1].split(';')[0].strip().lower()
        if not charset:
            charset = chardet.detect(data)['encoding'] or 'gb18030'
        html = data.decode(charset, errors='replace')

        # 提取最终 URL
        pattern = r"(?:top\.self\.location\.href|location\.href)\s*=\s*['\"]([^'\"]+)['\"]"
        m = re.search(pattern, html)
        if not m:
            raise Exception("未找到 JS 跳转 URL")
        final_url = m.group(1)
        if not final_url.startswith('http'):
            final_url = urljoin(loc2, final_url)

        # 4. 最终 Portal 页面
        r = self.session.get(final_url, headers={"Referer": loc2})
        if r.status_code != 200:
            raise Exception(f"最终页面状态码: {r.status_code}")

        final_data = r.content
        if final_data[:2] == b'\x1f\x8b':
            final_data = gzip.decompress(final_data)

        content_type = r.headers.get('Content-Type', '')
        charset = None
        if 'charset=' in content_type:
            charset = content_type.split('charset=')[-1].split(';')[0].strip().lower()
        if not charset:
            charset = chardet.detect(final_data)['encoding'] or 'gb18030'
        final_html = final_data.decode(charset, errors='replace')

        return final_html, final_url

    def login(self):
        """执行登录，返回 (success, message)"""
        try:
            final_html, portal_url = self._get_portal_page()
            self.logger.info("成功获取登录页面")
        except Exception as e:
            self.logger.error(f"获取页面失败: {e}")
            return False, f"获取页面失败: {e}"

        parsed = urlparse(portal_url)
        query_string = parsed.query
        query_params = parse_qs(query_string)
        mac = query_params.get('mac', [''])[0]

        base_api = f"{parsed.scheme}://{parsed.netloc}/eportal/InterFace.do"

        # pageInfo 请求
        page_info_url = f"{base_api}?method=pageInfo"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': portal_url,
            'Origin': f"{parsed.scheme}://{parsed.netloc}",
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        resp = self.session.post(page_info_url, data={'queryString': query_string}, headers=headers)
        if resp.status_code != 200:
            msg = f"pageInfo 请求失败，状态码: {resp.status_code}"
            self.logger.error(msg)
            return False, msg
        try:
            page_info = self._decode_json_response(resp)
            self.logger.info("pageInfo 响应解析成功")
        except Exception as e:
            self.logger.error(f"pageInfo 解析失败: {e}")
            return False, f"pageInfo 解析失败: {e}"

        # 提取参数
        public_key_exponent = page_info.get('publicKeyExponent', '')
        public_key_modulus = page_info.get('publicKeyModulus', '')
        password_encrypt = page_info.get('passwordEncrypt', 'false')

        # 提取默认服务
        services = page_info.get('service', {})
        default_service_name = None
        for svc_name, svc_info in services.items():
            if svc_info.get('serviceDefault') == 'true':
                default_service_name = svc_info['serviceName']
                break
        if not default_service_name and services:
            first_svc = list(services.values())[0]
            default_service_name = first_svc['serviceName']

        # getServices（可选）
        get_services_url = f"{base_api}?method=getServices&queryString={query_string}"
        resp = self.session.post(get_services_url, data='', headers=headers)
        if resp.status_code == 200:
            try:
                self._decode_json_response(resp)
                self.logger.info("服务列表获取成功")
            except:
                pass

        # 检查是否已在线
        get_online_url = f"{base_api}?method=getOnlineUserInfo"
        resp = self.session.post(get_online_url, data={'userIndex': ''}, headers=headers)
        if resp.status_code == 200:
            try:
                online_info = self._decode_json_response(resp)
                if online_info.get('result') == 'success' and online_info.get('userIndex'):
                    self.logger.info("已经在线，不需要登录")
                    return True, "已经在线"
            except:
                pass

        # 加密密码
        password = self.password
        if password_encrypt == "true":
            if len(password) < 150:
                pwd_to_encrypt = password + ">" + mac
            else:
                pwd_to_encrypt = password
            reversed_pwd = pwd_to_encrypt[::-1]
            encrypted_pwd = self._rsa_encrypt_string(public_key_exponent, public_key_modulus, reversed_pwd)
            encrypted_pwd = self._double_encode(encrypted_pwd)
            self.logger.debug("密码已加密")
        else:
            encrypted_pwd = password

        # 构造 POST 数据
        username_enc = self._double_encode(self.username)
        service_enc = self._double_encode(default_service_name)
        query_string_enc = self._double_encode(query_string)
        password_encrypt_enc = self._double_encode(password_encrypt)

        post_data = (
            f"userId={username_enc}&password={encrypted_pwd}&service={service_enc}"
            f"&queryString={query_string_enc}&operatorPwd=&operatorUserId=&validcode="
            f"&passwordEncrypt={password_encrypt_enc}"
        )

        login_url = f"{base_api}?method=login"
        resp = self.session.post(login_url, data=post_data, headers=headers)

        if resp.status_code != 200:
            msg = f"登录请求失败，状态码: {resp.status_code}"
            self.logger.error(msg)
            return False, msg

        try:
            login_result = self._decode_json_response(resp)
        except Exception as e:
            self.logger.error(f"登录响应解析失败: {e}")
            return False, f"登录响应解析失败: {e}"

        if login_result.get('result') == 'success':
            user_index = login_result.get('userIndex')
            if user_index:
                resp = self.session.post(get_online_url, data={'userIndex': user_index}, headers=headers)
                if resp.status_code == 200:
                    try:
                        self._decode_json_response(resp)
                    except:
                        pass
            self.logger.info("登录成功")
            return True, "登录成功"
        else:
            msg = login_result.get('message', '未知错误')
            self.logger.error(f"登录失败: {msg}")
            return False, msg


if __name__ == "__main__":
    # 使用示例：将日志写入文件 portal.log，控制台只显示错误
    auth = AutoLogin(username="username", password="password", log_file="portal.log")
    success, msg = auth.login()
    print(msg)  # 控制台仅输出最终结果