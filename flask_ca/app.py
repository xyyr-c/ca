from dbutils.pooled_db import PooledDB
from flask import Flask, jsonify, request, session, send_from_directory
from flask_session import Session
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
import os
import redis
import pymysql
import bcrypt
from flask_cors import CORS
from csr import *

POOL = PooledDB(
    creator=pymysql,
    maxconnections=5,
    blocking=True,
    maxusage=None,
    setsession=[],
    ping = 0,
    host='127.0.0.1',  # 连接名称，默认127.0.0.1
    user='root',  # 用户名
    passwd='root',  # 密码
    port=3306,  # 端口，默认为3306
    db='CertAuth',  # 数据库名称
    charset='utf8mb4',  # 字符编码
    autocommit=True  # 增加自动提交
)
app = Flask(__name__)
CORS(app,supports_credentials=True)  # 跨域支持
app.config['SECRET_KEY'] = 'Xyyrdghasoaifdjsad'  # 请替换为一个更安全的随机字符串

# 配置 Flask-Session
app.config['SESSION_TYPE'] = 'redis'  # 使用 Redis 存储 Session
app.config['SESSION_PERMANENT'] = False  # Session 不持久化
app.config['SESSION_USE_SIGNER'] = True  # 使用签名
app.config['SESSION_KEY_PREFIX'] = 'myapp:'  # 可选：Session 键的前缀
app.config['SESSION_REDIS'] = redis.StrictRedis(host='localhost', port=6379)  # Redis 连接配置
app.config['SESSION_COOKIE_NAME'] = 'my_session'  # 设置 Session 的 Cookie 名称
app.config['SESSION_COOKIE_HTTPONLY'] = True  # 禁止 JavaScript 访问 Cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # 跨域请求时允许携带 Cookie
app.config['SESSION_COOKIE_SECURE'] = True  # 如果是 HTTPS 环境设置为 True
# app.config['SESSION_COOKIE_DOMAIN'] = '10.33.25.216'  # 或者设置为公网 IP

Session(app)

@app.route('/api/auth/register', methods=["POST"])
def register():
    resp = {}
    conn = POOL.connection()
    cursor = conn.cursor()
    name = request.get_json()['username']
    pwd = request.get_json()['password']
    # 查看用户是否存在
    cursor.execute("SELECT * FROM accounts WHERE username = %s", (name,))
    user = cursor.fetchone()

    if user:
        resp['msg'] = "用户已存在！"
        resp['status'] = "error"
    else:
        # 使用 bcrypt 或其他算法生成密码哈希
        hashed_pwd = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt())
        # 插入新用户，存储哈希后的密码
        cursor.execute("INSERT INTO accounts (username, pass_hash) VALUES (%s, %s)", (name, hashed_pwd))
        resp['msg'] = "注册成功！"
        resp['status'] = "success"

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify(resp)

@app.route("/api/auth/login", methods=["POST"])
def login():
    resp = {}
    conn = POOL.connection()
    cursor = conn.cursor()

    name = request.get_json()['username']
    pwd = request.get_json()['password']
    print(request.get_json())
    # 从数据库查询用户信息
    try:
        cursor.execute("SELECT * FROM accounts WHERE username = %s", (name,))
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
    user = cursor.fetchone()
    print(user)
    # print(user[3])
    # print(pwd)
    # hashed_pwd = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt())
    # print(hashed_pwd)
    if user:
        if user[5]: # 第六列是角色
            resp['role'] = "1"
        else:
            resp['role'] = "0"
        stored_password = user[3]  # 第四列是密码
        # 验证密码是否匹配
        if bcrypt.checkpw(pwd.encode('utf-8'), stored_password.encode('utf-8')):
            session['user'] = user
            resp['status'] = "success"
        else:
            resp['status'] = "error"
    else:
        resp['status'] = "error"

    cursor.close()
    conn.close()
    return jsonify(resp)
@app.route('/api/auth/logout', methods=["POST"])
def logout():
    resp = {}
    session.pop('user', None)  # 清除 Session
    resp['status'] = "success"
    return jsonify(resp)
# def test():
#     """
#     默认管理员的插入
#     :return:
#     """
#     pwd = "admin123!"
#     hashed_pwd = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt())
#     print(hashed_pwd)

@app.route("/api/ca/csr_info", methods=['POST'])
def csr_submit_info():
    resp = {}
    conn = POOL.connection()
    cursor = conn.cursor()
    try:
        csr_info = request.get_json()
        resp = csr_submit1(cursor, csr_info)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify(resp)
    except Exception as e:
        print(e)
        return jsonify(msg="出错了，请检查")
@app.route("/api/gen_rsa", methods=['POST'])
def csr_submit_public_key():
    resp = generate_rsa_keys_using_cryptography()
    return jsonify(resp)
@app.route("/api/pub",methods=['POST'])
def csr_submit_pub():
    resp = {}
    conn = POOL.connection()
    cursor = conn.cursor()
    request_info = request.get_json()
    csr_id = request_info.get('csr_id')
    pub_key = request_info.get('public_key')
    # print(request_info)
    try:
        cursor.execute(f"SELECT * FROM cert_requests WHERE req_id = {csr_id}")
        csr = cursor.fetchone()
        print(csr)
    except Exception as e:
        resp['header'] = {'code': 500, 'message': 'SelectCSRByID Error'}
        return resp

    update_sql = """
            UPDATE cert_requests
            SET pub_key = %s
            WHERE req_id = %s"""
    cursor.execute(update_sql, (pub_key, csr_id))

    resp['header'] = {'code': 200, 'message': 'Success'}
    return jsonify(resp)
@app.route("/api/ca/read_csr",methods=['POST'])
def csr_file_read():
    resp = {}
    csr_file = request.files['csr']
    csr_data = csr_file.read()
    # print(csr_data)
 # 加载CSR
    try:
        csr = x509.load_pem_x509_csr(csr_data, default_backend())
    except:
        csr = x509.load_der_x509_csr(csr_data, default_backend())

    # 提取关键字段
    subject = csr.subject
    csr_info = {
        'country': subject.get_attributes_for_oid(NameOID.COUNTRY_NAME)[0].value if subject.get_attributes_for_oid(
            NameOID.COUNTRY_NAME) else '',
        'province': subject.get_attributes_for_oid(NameOID.STATE_OR_PROVINCE_NAME)[
            0].value if subject.get_attributes_for_oid(NameOID.STATE_OR_PROVINCE_NAME) else '',
        'locality': subject.get_attributes_for_oid(NameOID.LOCALITY_NAME)[
            0].value if subject.get_attributes_for_oid(NameOID.LOCALITY_NAME) else '',
        'organization': subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[
            0].value if subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME) else '',
        'organizational_unit': subject.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)[
            0].value if subject.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME) else '',
        'common_name': subject.get_attributes_for_oid(NameOID.COMMON_NAME)[
            0].value if subject.get_attributes_for_oid(NameOID.COMMON_NAME) else '',
        'email_address': subject.get_attributes_for_oid(NameOID.EMAIL_ADDRESS)[0].value if subject.get_attributes_for_oid(
            NameOID.EMAIL_ADDRESS) else '',
    }
    # print(csr_info)
    conn = POOL.connection()
    cursor = conn.cursor()
    try:
        resp = csr_submit1(cursor, csr_info)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify(resp)
    except Exception as e:
        print(e)
        return jsonify(msg="出错了，请检查")





if __name__ == '__main__':
    # for rule in app.url_map.iter_rules():
    #     print(rule)
    app.run(
        host='0.0.0.0', 
        port=8080, debug=True,
        ssl_context=('./localhost.crt',
                     './localhost.key')
    )
