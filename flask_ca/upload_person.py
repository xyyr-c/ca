import os
from flask import Flask, request, jsonify, session

# 文件存储根目录
UPLOAD_ROOT = 'user_uploads'
os.makedirs(UPLOAD_ROOT, exist_ok=True)

# 允许的文件扩展名（可选，根据需求调整）
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx',
    'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', '7z'
}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_user_folder(username):
    """获取或创建用户文件夹"""
    user_folder = os.path.join(UPLOAD_ROOT, username)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder