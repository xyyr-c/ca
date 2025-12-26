
from flask import Flask, jsonify, request, session, send_from_directory
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding
from datetime import datetime, timedelta
import pdb
import ipaddress
import os
import sys
import sqlite3
from typing import Optional, Dict, Any, Tuple
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import hashlib


def csr_submit1(cursor, req_data):
    """
    初步信息的插入
    """
    resp = {}

    # 获取用户上下文
    user = session.get('user')
    if not user:
        resp['header'] = {'code': 401, 'message': 'Unauthorized'}
        return resp

    # 构造新的证书请求，映射到正确的数据库字段
    new_csr = {
        'uid': user['uid'],  # 对应uid字段
        'status': 1,  # 对应status字段，1-待审
        'pub_key': req_data.get('public_key', ''),  # 对应pub_key字段
        'country_code': req_data.get('country'),  # 对应country_code字段
        'region': req_data.get('province'),  # 对应region字段
        'city': req_data.get('locality'),  # 对应city字段
        'company': req_data.get('organization'),  # 对应company字段
        'department': req_data.get('organizational_unit'),  # 对应department字段
        'full_name': req_data.get('common_name'),  # 对应full_name字段
        'email': req_data.get('email_address'),  # 对应email字段
    }

    # 获取当前时间
    current_time = datetime.now()

    # 写入数据库，包括时间字段
    try:
        sql = """INSERT INTO cert_requests 
                 (created_time, modified_time, removed_time, uid, status, pub_key, 
                  country_code, region, city, company, department, full_name, email) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        cursor.execute(sql, (
            current_time,  # created_time
            None,  # modified_time
            None,  # removed_time (初始为NULL)
            new_csr['uid'],
            new_csr['status'],
            new_csr['pub_key'],
            new_csr['country_code'],
            new_csr['region'],
            new_csr['city'],
            new_csr['company'],
            new_csr['department'],
            new_csr['full_name'],
            new_csr['email'],
        ))

        new_req_id = cursor.lastrowid  # 获取插入的ID

    except Exception as e:
        resp['header'] = {'code': 500, 'message': 'Insert certificate request error'}
        return resp
    # 构造响应
    resp['header'] = {'code': 200, 'message': 'Success'}
    resp["csr_id"] = new_req_id
    return resp
def generate_rsa_keys_using_cryptography():
    """
    使用 cryptography 库生成 RSA 密钥对
    返回: (private_key_pem, public_key_pem)
    """
    resp={}
    # 生成私钥
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,  # 可以是2048, 3072, 4096等
    )

    # 序列化私钥为 PEM 格式
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()  # 无密码保护
        # 如果需要密码保护:
        # encryption_algorithm=serialization.BestAvailableEncryption(b'your-password')
    )

    # 从私钥中提取公钥
    public_key = private_key.public_key()

    # 序列化公钥为 PEM 格式
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    resp["header"] = {'code': 200, 'message': 'Success'}
    resp["pr_key"] = private_key_pem.decode('utf-8')
    resp["pu_key"] = public_key_pem.decode('utf-8')

    return resp

def load_ca_private_key(key_path: str, password: Optional[bytes] = None):
    """加载CA私钥"""
    try:
        with open(key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=password,
                backend=default_backend()
            )
        print(f"CA私钥已加载: {key_path}")
        return private_key
    except Exception as e:
        print(f"加载CA私钥失败: {e}")
        return None
def generate_cert(cursor, req_id):
    try:
        sql = """
        SELECT req_id, pub_key, country_code, region, city, 
               company, department, full_name, email
        FROM cert_requests 
        WHERE req_id = %s AND status = 1
        """
        # pdb.set_trace()
        cursor.execute(sql, (req_id,))
        row = cursor.fetchone()
        print(row)
    except Exception as e:
        print(f"查询证书请求失败: {e}")
        return None
    private_key = load_ca_private_key("./localhost.key")
    public_key = serialization.load_pem_public_key(
        row['pub_key'].encode(),
        backend=default_backend()
    )
    # print(private_key)
    # 创建签名证书
    subject = x509.Name([
        # 必填字段
        x509.NameAttribute(NameOID.COUNTRY_NAME, row['country_code']),  # 国家 (C)
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, row['region']),  # 省/州 (ST)
        x509.NameAttribute(NameOID.LOCALITY_NAME, row['city']),  # 城市/地区 (L)
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, row['company']),  # 组织 (O)
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, row['department']),  # 部门 (OU)
        x509.NameAttribute(NameOID.COMMON_NAME, row['full_name']),  # 通用名 (CN)
        x509.NameAttribute(NameOID.EMAIL_ADDRESS, row['email']),  # 邮箱
    ])
    with open("localhost.crt", 'rb') as f:
        ca_cert_data = f.read()

    ca_cert = x509.load_pem_x509_certificate(ca_cert_data, default_backend())
    issuer = ca_cert.issuer

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        public_key
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=730)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True,
    ).sign(private_key, hashes.SHA256(), default_backend())

    # 保存证书
    with open(f"./certificate/{row['req_id']}.cer", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


