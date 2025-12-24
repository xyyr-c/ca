import time

from dbutils.pooled_db import PooledDB
from flask import Flask, jsonify, request, session, send_file,abort
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
from upload_person import *
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
    autocommit=True,  # 增加自动提交
    cursorclass=pymysql.cursors.DictCursor

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
# 注册
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
# 登录
@app.route("/api/auth/login", methods=["POST"])
def login():
    resp = {}
    conn = POOL.connection()
    cursor = conn.cursor()

    name = request.get_json()['username']
    pwd = request.get_json()['password']
    # print(request.get_json())
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
        if user['role']: # 用字典获取
            resp['role'] = "1"
        else:
            resp['role'] = "0"
        stored_password = user['pass_hash']  # 用字典获取
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
# 退出
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

# 提交csr信息
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

#生成公钥
@app.route("/api/gen_rsa", methods=['POST'])
def csr_submit_public_key():
    resp = generate_rsa_keys_using_cryptography()
    return jsonify(resp)
#提交公钥
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
        # print(csr)
    except Exception as e:
        resp['header'] = {'code': 500, 'message': 'SelectCSRByID Error'}
        return resp

    update_sql = """
            UPDATE cert_requests
            SET pub_key = %s
            WHERE req_id = %s"""
    cursor.execute(update_sql, (pub_key, csr_id))
    generate_cert(cursor, csr_id)
    resp['header'] = {'code': 200, 'message': 'Success'}
    cursor.close()
    conn.close()
    return jsonify(resp)

# 读取csr文件
@app.route("/api/ca/read_csr",methods=['POST'])
def csr_file_read():
    resp = {}
    csr_file = request.files['csr']
    csr_data = csr_file.read()
    print(csr_data)
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


# 查询用户证书
@app.route("/api/cert/query",methods=['POST'])
def csr_search():
    resp = {}
    conn = POOL.connection()
    cursor = conn.cursor()
    user = session.get('user')
    user_id = user['uid']
    cursor.execute(f"SELECT * FROM cert_requests WHERE uid = {user_id}")
    columns = [col[0] for col in cursor.description]
    certs = cursor.fetchall()
    resp['certs'] = certs
    resp['header'] = {'code': 200, 'message': 'Success'}
    return jsonify(resp)

# 证书文件下载
@app.route("/api/download",methods=['GET'])
def cer_download():
    file_path = f"./certificate/{request.args.get('cert_path')}.cer"
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return jsonify({
            'code': 404,
            'description': "文件不存在"
        }), 404  # 注意：返回404状态码

    # 检查是否是文件
    if not os.path.isfile(file_path):
        return jsonify({
            'code': 404,
            'description': "文件不存在"
        }), 404

    try:
        # 发送文件给客户端
        return send_file(
            file_path,
            as_attachment=True,  # 作为附件下载
            download_name=f"{os.path.basename(file_path)}",  # 下载时显示的文件名，注意这里去掉了路径，只保留文件名
            mimetype='application/octet-stream'  # 二进制流
        )
    except Exception as e:
        return jsonify({
            'code': 500,
            'description': "文件发送错误"
        }), 500
# 吊销证书
@app.route("/api/cert/revoke",methods=['POST'])
def cer_revoke():
    resp = {}
    conn = POOL.connection()
    cursor = conn.cursor()
    request_info = request.get_json()
    req_id = request_info.get('cert_id')
    revoted_time = datetime.now()
    print(revoted_time)
    try:
        update_sql = """
                UPDATE cert_requests
                SET status = 3 ,removed_time = %s
                WHERE req_id = %s"""
        cursor.execute(update_sql, (revoted_time,req_id,))
        resp['header'] = {'code':200,"message":'Success'}
        return jsonify(resp)
    except Exception as e:
        print(e)
        resp['header'] = {'code': 500, 'message': 'revoke error'}
        return jsonify(resp)
@app.route('/api/admin/users')
def user_search():
    resp = {}
    conn = POOL.connection()
    cursor = conn.cursor()
    try:
        # 查询所有用户
        cursor.execute("SELECT uid, username, email, role FROM accounts")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "success",
            "data": users
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# 获取证书列表（关联用户信息）
@app.route('/api/admin/certificates', methods=['GET'])
def get_certificates():
    try:
        conn = POOL.connection()
        cursor = conn.cursor()

        # 关联查询证书和用户信息
        cursor.execute("""
            SELECT 
                cr.req_id,
                cr.created_time,
                cr.modified_time,
                cr.removed_time,
                cr.uid,
                cr.status,
                cr.pub_key,
                cr.country_code,
                cr.region,
                cr.city,
                cr.company,
                cr.department,
                cr.full_name,
                cr.email,
                a.username
            FROM cert_requests cr
            LEFT JOIN accounts a ON cr.uid = a.uid
            ORDER BY cr.created_time DESC
        """)

        certificates = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "data": certificates
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/admin/certificates/<int:cert_id>/approve', methods=['POST'])
def approve_certificate(cert_id):
    try:
        conn = POOL.connection()
        cursor = conn.cursor()

        # 更新证书状态为通过（状态2），并设置修改时间
        update_query = """
            UPDATE cert_requests 
            SET status = 2, modified_time = NOW() + INTERVAL 2 YEAR
            WHERE req_id = %s AND status = 1
        """
        cursor.execute(update_query, (cert_id,))
        conn.commit()

        affected_rows = cursor.rowcount

        cursor.close()
        conn.close()

        if affected_rows > 0:
            return jsonify({
                "status": "success",
                "message": "证书审核通过成功"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "证书不存在或状态不是待审核"
            }), 400

    except Exception as e:
        print(f"审核证书错误: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/admin/certificates/<int:cert_id>/revoke', methods=['POST'])
def revoke_certificate(cert_id):
    try:
        conn = POOL.connection()
        cursor = conn.cursor()

        # 更新证书状态为吊销（状态3），并设置吊销时间
        update_query = """
            UPDATE cert_requests 
            SET status = 3, removed_time = NOW()
            WHERE req_id = %s AND status = 2
        """
        cursor.execute(update_query, (cert_id,))
        conn.commit()

        affected_rows = cursor.rowcount

        cursor.close()
        conn.close()

        if affected_rows > 0:
            return jsonify({
                "status": "success",
                "message": "证书吊销成功"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "证书不存在或状态不是已激活"
            }), 400

    except Exception as e:
        print(f"吊销证书错误: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/cert/auth_cer', methods=['POST'])
def upload_personal_info():
    """
    处理个人信息文件上传
    前端字段名为 'cert'（FormData中append的字段）
    """
    # 检查是否有文件
    if 'cert' not in request.files:
        return jsonify({
            'header': {
                'code': 400,
                'message': '没有选择文件'
            }
        }), 400

    file = request.files['cert']

    # 检查文件名是否为空
    if file.filename == '':
        return jsonify({
            'header': {
                'code': 400,
                'message': '没有选择文件'
            }
        }), 400
    username = request.form.get('username')
    original_filename = file.filename
    file_extension = os.path.splitext(original_filename)[1]

    # 获取用户文件夹
    user_folder = get_user_folder(username)

    # 完整文件路径
    file_path = os.path.join(user_folder, original_filename)

    try:
        # 保存文件
        file.save(file_path)
        # 记录文件信息（可选，可以保存到数据库）
        file_info = {
            'original_filename': original_filename,
            'saved_filename': original_filename,
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'upload_time': datetime.now().isoformat(),
            'username': username,
            'file_type': file_extension[1:].lower() if file_extension else 'unknown'
        }

        # 这里可以保存file_info到数据库

        print(f"文件已保存: {file_info}")  # 调试信息

        return jsonify({
            'header': {
                'code': 200,
                'message': '个人信息文件上传成功'
            },
            'data': {
                'filename': original_filename,
                'saved_as': original_filename,
                'upload_time': file_info['upload_time'],
                'file_size': file_info['file_size']
            }
        }), 200

    except Exception as e:
        print(f"文件保存失败: {str(e)}")
        return jsonify({
            'header': {
                'code': 500,
                'message': f'文件保存失败: {str(e)}'
            }
        }), 500


if __name__ == '__main__':
    # for rule in app.url_map.iter_rules():
    #     print(rule)
    app.run(
        host='0.0.0.0', 
        port=8080, debug=True,
        ssl_context=('./localhost.crt',
                     './localhost.key')
    )
