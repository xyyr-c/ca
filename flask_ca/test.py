#!/usr/bin/env python3
"""
小型CA系统 - 分函数版本
根据数据库中的申请者信息，使用CA私钥签发证书并保存为.cer文件
"""

import os
import sys
import datetime
import sqlite3
from typing import Optional, Dict, Any, Tuple
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import hashlib


# ============================
# 数据库相关函数
# ============================

def connect_database(db_path: str) -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
    """连接到数据库"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 返回字典格式
        cursor = conn.cursor()
        print(f"数据库连接成功: {db_path}")
        return conn, cursor
    except Exception as e:
        print(f"数据库连接失败: {e}")
        raise


def get_certificate_request(cursor, req_id: str) -> Optional[Dict[str, Any]]:
    """
    根据req_id查询证书申请信息
    只返回状态为2（通过）的申请
    """
    try:
        sql = """
        SELECT req_id, pub_key, country_code, region, city, 
               company, department, full_name, email, created_at
        FROM cert_requests 
        WHERE req_id = ? AND status = 1
        """

        cursor.execute(sql, (req_id,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        else:
            # 检查状态
            cursor.execute("SELECT status FROM certificate_requests WHERE req_id = ?", (req_id,))
            status_row = cursor.fetchone()
            if status_row:
                status = status_row['status']
                if status == 1:
                    print(f"请求 {req_id} 状态为待审，无法签发")
                elif status == 3:
                    print(f"请求 {req_id} 状态为拒绝，无法签发")
            else:
                print(f"未找到请求ID: {req_id}")
            return None

    except Exception as e:
        print(f"查询证书请求失败: {e}")
        return None


# ============================
# 密钥和证书操作函数
# ============================

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


def parse_public_key(pub_key_text: str):
    """解析申请者的公钥"""
    try:
        # 假设是PEM格式的公钥
        public_key = serialization.load_pem_public_key(
            pub_key_text.encode('utf-8'),
            backend=default_backend()
        )
        return public_key
    except Exception as e:
        print(f"解析公钥失败，将生成新的密钥对: {e}")
        # 生成新的密钥对
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        return private_key.public_key()


def create_certificate(request_info: Dict[str, Any], ca_private_key) -> x509.Certificate:
    """创建并签名证书"""

    # 解析申请者公钥
    public_key = parse_public_key(request_info['pub_key'])

    # 构建申请者主题
    subject_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME,
                           request_info.get('country_code', 'CN')),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME,
                           request_info.get('region', '')),
        x509.NameAttribute(NameOID.LOCALITY_NAME,
                           request_info.get('city', '')),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME,
                           request_info.get('company', '')),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME,
                           request_info.get('department', '')),
        x509.NameAttribute(NameOID.COMMON_NAME,
                           request_info.get('full_name', '')),
    ])

    # 添加邮箱（如果有）
    if request_info.get('email'):
        subject_name = subject_name.add_attribute(
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, request_info['email'])
        )

    # 构建颁发者（CA）
    issuer_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Local CA"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost CA"),
    ])

    # 生成序列号
    serial_bytes = hashlib.sha256(request_info['req_id'].encode()).digest()[:20]
    serial_number = int.from_bytes(serial_bytes, byteorder='big')

    # 设置有效期
    current_time = datetime.datetime.utcnow()
    valid_from = current_time - datetime.timedelta(days=1)  # 从昨天开始
    valid_to = current_time + datetime.timedelta(days=365)  # 一年有效期

    # 创建证书
    builder = x509.CertificateBuilder()

    builder = builder.subject_name(subject_name)
    builder = builder.issuer_name(issuer_name)
    builder = builder.public_key(public_key)
    builder = builder.serial_number(serial_number)
    builder = builder.not_valid_before(valid_from)
    builder = builder.not_valid_after(valid_to)

    # 添加基本扩展
    builder = builder.add_extension(
        x509.BasicConstraints(ca=False, path_length=None),
        critical=True,
    )

    builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            key_encipherment=True,
            content_commitment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    )

    # 签名证书
    certificate = builder.sign(
        private_key=ca_private_key,
        algorithm=hashes.SHA256(),
        backend=default_backend()
    )

    print(f"证书创建成功，序列号: {certificate.serial_number}")
    return certificate


# ============================
# 文件保存函数
# ============================

def save_certificate_as_cer(certificate: x509.Certificate,
                            req_id: str,
                            output_dir: str = "issued_certs") -> str:
    """将证书保存为.cer文件（DER编码）"""
    try:
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cert_{req_id}_{timestamp}.cer"
        filepath = os.path.join(output_dir, filename)

        # 保存为DER格式
        with open(filepath, "wb") as f:
            f.write(certificate.public_bytes(encoding=serialization.Encoding.DER))

        print(f"证书已保存为CER格式: {filepath}")
        return filepath

    except Exception as e:
        print(f"保存CER文件失败: {e}")
        raise


def save_certificate_as_pem(certificate: x509.Certificate,
                            req_id: str,
                            output_dir: str = "issued_certs") -> str:
    """将证书保存为.pem文件"""
    try:
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cert_{req_id}_{timestamp}.pem"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "wb") as f:
            f.write(certificate.public_bytes(encoding=serialization.Encoding.PEM))

        print(f"证书已保存为PEM格式: {filepath}")
        return filepath

    except Exception as e:
        print(f"保存PEM文件失败: {e}")
        raise


def save_certificate_summary(certificate: x509.Certificate,
                             request_info: Dict[str, Any],
                             output_dir: str = "issued_certs") -> str:
    """保存证书信息摘要"""
    try:
        os.makedirs(output_dir, exist_ok=True)

        filename = f"summary_{request_info['req_id']}.txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("证书签发信息\n")
            f.write("=" * 50 + "\n\n")

            f.write("申请者信息:\n")
            f.write(f"  请求ID: {request_info['req_id']}\n")
            f.write(f"  姓名: {request_info.get('full_name', '')}\n")
            f.write(f"  邮箱: {request_info.get('email', '')}\n")
            f.write(f"  组织: {request_info.get('company', '')}\n")
            f.write(f"  部门: {request_info.get('department', '')}\n")
            f.write(
                f"  地区: {request_info.get('country_code', '')} {request_info.get('region', '')} {request_info.get('city', '')}\n\n")

            f.write("证书信息:\n")
            f.write(f"  序列号: {certificate.serial_number}\n")
            f.write(f"  颁发者: {certificate.issuer.rfc4514_string()}\n")
            f.write(f"  主题: {certificate.subject.rfc4514_string()}\n")
            f.write(f"  生效时间: {certificate.not_valid_before}\n")
            f.write(f"  过期时间: {certificate.not_valid_after}\n")
            f.write(f"  签名算法: {certificate.signature_hash_algorithm.name}\n")

        print(f"证书摘要已保存: {filepath}")
        return filepath

    except Exception as e:
        print(f"保存证书摘要失败: {e}")
        return ""


def update_request_status(conn, cursor, req_id: str, certificate: x509.Certificate):
    """更新证书请求状态为已签发"""
    try:
        sql = """
        UPDATE certificate_requests 
        SET issued_at = ?, certificate_serial = ?, status = 4
        WHERE req_id = ?
        """

        cursor.execute(sql, (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            str(certificate.serial_number),
            req_id
        ))
        conn.commit()

        print(f"数据库状态已更新: {req_id}")

    except Exception as e:
        print(f"更新数据库状态失败: {e}")


# ============================
# 主流程函数
# ============================

def issue_certificate(db_path: str,
                      ca_key_path: str,
                      req_id: str,
                      output_dir: str = "issued_certs") -> bool:
    """
    签发证书的主函数

    Args:
        db_path: 数据库文件路径
        ca_key_path: CA私钥文件路径
        req_id: 请求ID
        output_dir: 输出目录

    Returns:
        成功返回True，失败返回False
    """
    print(f"\n开始签发证书: {req_id}")
    print("=" * 50)

    # 1. 连接数据库
    conn, cursor = connect_database(db_path)

    try:
        # 2. 加载CA私钥
        ca_private_key = load_ca_private_key(ca_key_path)
        if not ca_private_key:
            print("无法加载CA私钥")
            return False

        # 3. 查询证书请求
        request_info = get_certificate_request(cursor, req_id)
        if not request_info:
            print("未找到有效的证书请求")
            return False

        # 4. 创建证书
        certificate = create_certificate(request_info, ca_private_key)

        # 5. 保存证书文件
        cer_file = save_certificate_as_cer(certificate, req_id, output_dir)
        pem_file = save_certificate_as_pem(certificate, req_id, output_dir)
        summary_file = save_certificate_summary(certificate, request_info, output_dir)

        # 6. 更新数据库状态
        update_request_status(conn, cursor, req_id, certificate)

        print(f"\n证书签发完成!")
        print(f"  CER文件: {cer_file}")
        print(f"  PEM文件: {pem_file}")
        print(f"  摘要文件: {summary_file}")

        return True

    except Exception as e:
        print(f"签发证书过程中发生错误: {e}")
        return False

    finally:
        # 关闭数据库连接
        cursor.close()
        conn.close()
        print("数据库连接已关闭")


def batch_issue_certificates(db_path: str,
                             ca_key_path: str,
                             req_ids: list,
                             output_dir: str = "issued_certs") -> Dict[str, Any]:
    """批量签发证书"""
    results = {
        'total': len(req_ids),
        'success': [],
        'failed': []
    }

    # 批量签发时，只连接一次数据库
    conn, cursor = connect_database(db_path)
    ca_private_key = load_ca_private_key(ca_key_path)

    if not ca_private_key:
        print("无法加载CA私钥，批量签发终止")
        cursor.close()
        conn.close()
        return results

    try:
        for req_id in req_ids:
            print(f"\n处理请求: {req_id}")

            try:
                # 查询证书请求
                request_info = get_certificate_request(cursor, req_id)
                if not request_info:
                    results['failed'].append({'req_id': req_id, 'reason': '无效的请求'})
                    continue

                # 创建证书
                certificate = create_certificate(request_info, ca_private_key)

                # 保存文件
                cer_file = save_certificate_as_cer(certificate, req_id, output_dir)
                save_certificate_as_pem(certificate, req_id, output_dir)
                save_certificate_summary(certificate, request_info, output_dir)

                # 更新数据库
                update_request_status(conn, cursor, req_id, certificate)

                results['success'].append({
                    'req_id': req_id,
                    'cer_file': cer_file,
                    'serial': str(certificate.serial_number)
                })

            except Exception as e:
                results['failed'].append({'req_id': req_id, 'reason': str(e)})

        # 提交所有更新
        conn.commit()

    finally:
        cursor.close()
        conn.close()
        print("\n数据库连接已关闭")

    return results


# ============================
# 工具函数
# ============================

def generate_ca_key_pair(private_key):
    """生成CA密钥对和自签名证书"""

    # 创建自签名证书
    subject = issuer = x509.Name([
        # 必填字段
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),  # 国家 (C)
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),  # 省/州 (ST)
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),  # 城市/地区 (L)
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "My Company"),  # 组织 (O)
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "IT Department"),  # 部门 (OU)
        x509.NameAttribute(NameOID.COMMON_NAME, "myapp.example.com"),  # 通用名 (CN)
        x509.NameAttribute(NameOID.EMAIL_ADDRESS, "admin@example.com"),  # 邮箱
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=3650)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True,
    ).sign(private_key, hashes.SHA256(), default_backend())

    # 保存证书
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print(f"CA证书已保存: {cert_path}")

    return private_key, cert


def print_certificate_info(cert_path: str):
    """打印证书信息"""
    try:
        with open(cert_path, "rb") as f:
            if cert_path.endswith('.cer'):
                cert = x509.load_der_x509_certificate(f.read(), default_backend())
            else:
                cert = x509.load_pem_x509_certificate(f.read(), default_backend())

        print("\n证书信息:")
        print(f"  序列号: {cert.serial_number}")
        print(f"  颁发者: {cert.issuer.rfc4514_string()}")
        print(f"  主题: {cert.subject.rfc4514_string()}")
        print(f"  生效时间: {cert.not_valid_before}")
        print(f"  过期时间: {cert.not_valid_after}")

    except Exception as e:
        print(f"读取证书失败: {e}")


# ============================
# 主程序
# ============================

def main():
    """主函数示例"""

    # 配置
    DB_PATH = "certificate_system.db"
    CA_KEY_PATH = "localhost.key"
    OUTPUT_DIR = "issued_certificates"

    # 如果CA私钥不存在，先生成
    if not os.path.exists(CA_KEY_PATH):
        print("未找到CA私钥，正在生成...")
        generate_ca_key_pair(CA_KEY_PATH, "localhost.crt")

    # 示例1: 签发单个证书
    REQ_ID = "REQ20231201001"

    print("=" * 60)
    print("小型CA证书签发系统")
    print("=" * 60)

    success = issue_certificate(DB_PATH, CA_KEY_PATH, REQ_ID, OUTPUT_DIR)

    if success:
        print(f"\n✓ 证书签发成功: {REQ_ID}")
    else:
        print(f"\n✗ 证书签发失败: {REQ_ID}")

    # 示例2: 批量签发（取消注释使用）
    """
    req_ids = ["REQ001", "REQ002", "REQ003"]
    results = batch_issue_certificates(DB_PATH, CA_KEY_PATH, req_ids, OUTPUT_DIR)

    print(f"\n批量签发结果:")
    print(f"  总计: {results['total']}")
    print(f"  成功: {len(results['success'])}")
    print(f"  失败: {len(results['failed'])}")

    if results['failed']:
        print("\n失败的请求:")
        for fail in results['failed']:
            print(f"  - {fail['req_id']}: {fail['reason']}")
    """


def quick_issue(req_id: str):
    """快速签发证书的便捷函数"""
    DB_PATH = "certificate_system.db"
    CA_KEY_PATH = "localhost.key"
    OUTPUT_DIR = "issued_certificates"

    if not os.path.exists(CA_KEY_PATH):
        print("错误: 未找到CA私钥文件")
        print("请先运行 main() 生成CA密钥对")
        return False

    return issue_certificate(DB_PATH, CA_KEY_PATH, req_id, OUTPUT_DIR)


if __name__ == "__main__":
    # 安装所需库: pip install cryptography

    # 使用示例1: 直接运行主函数
    # main()

    # 使用示例2: 命令行参数
    if len(sys.argv) > 1:
        req_id = sys.argv[1]
        if quick_issue(req_id):
            print(f"\n证书签发完成: {req_id}")
            sys.exit(0)
        else:
            print(f"\n证书签发失败: {req_id}")
            sys.exit(1)
    else:
        print("使用方法:")
        print(f"  python {sys.argv[0]} <req_id>")
        print("示例:")
        print(f"  python {sys.argv[0]} REQ20231201001")
        sys.exit(1)