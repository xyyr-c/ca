<template>
  <div class="step-container">
    <el-row :gutter="40" justify="center">
      <el-col :xl="16" :lg="18" :md="20" :sm="22" :xs="24">
        <div class="grid-content">
          <el-card class="upload-card" shadow="hover">
            <div class="header-section">
              <div class="title-container">
                <el-icon class="title-icon">
                  <User />
                </el-icon>
                <div class="title-content">
                  <h2 class="main-title">个人信息上传</h2>
                  <div class="user-info" v-if="username">
                    <span class="welcome-text">欢迎，{{ username }}</span>
                  </div>
                  <p class="sub-title">上传您的个人信息文件用于认证或注册</p>
                </div>
              </div>

              <div class="info-section">
                <el-alert
                  title="请确保您上传的个人信息文件准确、完整"
                  type="info"
                  :closable="false"
                  show-icon
                />
                <div class="upload-tips">
                  <el-icon class="tip-icon">
                    <InfoFilled />
                  </el-icon>
                  <span>请上传包含您个人信息的文件</span>
                </div>
              </div>
            </div>

            <div class="upload-section">
              <el-upload
                class="custom-upload"
                drag
                action=""
                :http-request="upload_cer"
                :before-upload="beforeUpload"
                name="cer"
                ref="file_list"
                :auto-upload="true"
                :limit="1"
                :on-exceed="handleExceed"
                :disabled="!username"
              >
                <div class="upload-area">
                  <div class="upload-icon">
                    <el-icon class="upload-cloud">
                      <UploadFilled />
                    </el-icon>
                  </div>
                  <div class="upload-text">
                    <p class="primary-text">拖放文件到此处</p>
                    <p class="secondary-text">或 <span class="browse-link">浏览文件</span></p>
                  </div>
                </div>

                <template #tip>
                  <div class="upload-tip">
                    <el-icon class="tip-icon-small">
                      <Warning />
                    </el-icon>
                    <span>支持所有文件类型，最大 10 MB</span>
                  </div>
                </template>
              </el-upload>

              <!-- 如果未获取到用户名，显示提示 -->
              <div v-if="!username" class="no-user-warning">
                <el-alert
                  title="未检测到用户信息"
                  type="warning"
                  :closable="false"
                  show-icon
                >
                  <template #default>
                    <p class="warning-text">
                      请先登录系统，或确保sessionStorage中包含用户名信息
                    </p>
                  </template>
                </el-alert>
              </div>

              <div class="file-info" v-if="currentFile">
                <div class="file-details">
                  <el-icon class="file-icon">
                    <Document />
                  </el-icon>
                  <div class="file-meta">
                    <p class="file-name">{{ currentFile.name }}</p>
                    <p class="file-size">{{ formatFileSize(currentFile.size) }}</p>
                  </div>
                  <el-button
                    type="danger"
                    text
                    circle
                    @click="removeFile"
                    class="remove-btn"
                  >
                    <el-icon>
                      <Close />
                    </el-icon>
                  </el-button>
                </div>
              </div>

              <div class="privacy-notice">
                <el-alert
                  title="隐私保护声明"
                  type="warning"
                  :closable="false"
                  show-icon
                >
                  <template #default>
                    <p class="privacy-text">
                      我们承诺对您上传的个人信息文件严格保密，仅用于认证目的。请勿上传敏感密码或支付信息。
                    </p>
                  </template>
                </el-alert>
              </div>
            </div>
          </el-card>

          <div class="instruction-card">
            <el-card shadow="never">
              <template #header>
                <div class="instruction-header">
                  <el-icon>
                    <QuestionFilled />
                  </el-icon>
                  <span>上传说明</span>
                </div>
              </template>
              <div class="instruction-content">
                <div class="info-items">
                  <div class="info-item">
                    <el-icon class="info-icon">
                      <DocumentChecked />
                    </el-icon>
                    <div class="info-content">
                      <h4>文件要求</h4>
                      <p>支持所有格式的个人信息文件，如PDF、Word、图片等，大小不超过10MB</p>
                    </div>
                  </div>
                  <div class="info-item">
                    <el-icon class="info-icon">
                      <Lock />
                    </el-icon>
                    <div class="info-content">
                      <h4>隐私安全</h4>
                      <p>您的个人信息将受到加密保护，仅用于指定的认证流程</p>
                    </div>
                  </div>
                  <div class="info-item">
                    <el-icon class="info-icon">
                      <Clock />
                    </el-icon>
                    <div class="info-content">
                      <h4>处理时间</h4>
                      <p>个人信息上传后通常在1-3个工作日内完成处理</p>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts" name="PersonalInfoUpload">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import {
  User,
  UploadFilled,
  InfoFilled,
  Warning,
  Close,
  QuestionFilled,
  Document,
  DocumentChecked,
  Lock,
  Clock
} from '@element-plus/icons-vue'

const file_list = ref()
const currentFile = ref<File | null>(null)
const username = ref<string | null>(null)

// 从sessionStorage获取用户名
onMounted(() => {
  const savedUsername = sessionStorage.getItem("username")
  if (savedUsername) {
    username.value = savedUsername
    console.log(`已获取用户名: ${username.value}`)
  } else {
    ElMessage.warning('未找到用户信息，请先登录')
    console.warn('sessionStorage中没有找到username')
  }
})

// 上传文件的属性定义
interface UploadFileParam {
  file: File;
  onSuccess: (response: any) => void;
  onError: (error: any) => void;
  [key: string]: any;
}

// 文件上传前的校验
const beforeUpload = (file: File) => {
  // 检查用户名是否存在
  if (!username.value) {
    ElMessage.error('未获取到用户信息，请重新登录')
    return false
  }

  const maxSize = 10 * 1024 * 1024 // 10MB

  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 10 MB')
    return false
  }

  currentFile.value = file
  return true
}

// 处理文件超出限制
const handleExceed = () => {
  ElMessage.warning('只能上传一个文件，请先移除当前文件')
}

// 移除文件
const removeFile = () => {
  file_list.value.clearFiles()
  currentFile.value = null
  ElMessage.info('已移除文件')
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function upload_cer(param: UploadFileParam) {
  // 验证用户名是否存在
  if (!username.value) {
    ElMessage.error('未获取到用户信息，请重新登录')
    return
  }

  const formData = new FormData()
  formData.append('cert', param.file)
  formData.append('username', username.value) // 添加用户名到FormData

  axios.post('/api/cert/auth_cer', formData, { withCredentials: true })
    .then((response) => {
      console.log('上传文件:', formData)
      if (response.data.header.code === 200) {
        file_list.value.clearFiles()
        currentFile.value = null

        ElMessage.success({
          message: '个人信息文件上传成功！',
          duration: 5000
        })

        // 可以在这里添加上传成功后的其他操作
        console.log('文件上传成功，返回数据:', response.data.data)
      } else {
        ElMessage.error(response.data.header.message || '上传失败，请检查文件格式后重新上传。')
      }
    }).catch((error) => {
      loading.close()
      if (error.response) {
        // 服务器返回错误状态码
        ElMessage.error(error.response.data?.header?.message || '上传失败，请检查文件格式后重试。')
      } else if (error.request) {
        // 请求已发送但没有收到响应
        ElMessage.error('网络连接失败，请检查网络连接。')
      } else {
        // 请求设置出错
        ElMessage.error('上传失败，请重试。')
      }
      console.error('上传错误:', error)
    })
}
</script>

<style scoped>
.step-container {
  width: 100%;
  min-height: calc(100vh - 120px);
  padding: 30px 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
}

.upload-card {
  border-radius: 16px;
  border: none;
  margin-bottom: 30px;
  background: white;
}

.header-section {
  margin-bottom: 30px;
}

.title-container {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.title-icon {
  font-size: 36px;
  color: #409eff;
  background: #ecf5ff;
  padding: 12px;
  border-radius: 12px;
}

.title-content {
  flex: 1;
}

.main-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.user-info {
  margin-top: 8px;
}

.welcome-text {
  font-size: 14px;
  color: #409eff;
  font-weight: 500;
  background: #ecf5ff;
  padding: 4px 12px;
  border-radius: 12px;
  display: inline-block;
}

.sub-title {
  margin: 4px 0 0 0;
  font-size: 14px;
  color: #909399;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.upload-tips {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f0f9ff;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.tip-icon {
  color: #409eff;
}

.upload-section {
  margin: 40px 0;
}

.custom-upload :deep(.el-upload-dragger) {
  height: 280px;
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  background: #fafafa;
  transition: all 0.3s ease;
  padding: 40px 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.custom-upload :deep(.el-upload-dragger:hover) {
  border-color: #409eff;
  background: #f0f9ff;
}

.custom-upload :deep(.el-upload-dragger.is-disabled) {
  opacity: 0.6;
  cursor: not-allowed;
}

.upload-area {
  text-align: center;
  color: #606266;
}

.upload-icon {
  margin-bottom: 24px;
}

.upload-cloud {
  font-size: 64px;
  color: #409eff;
}

.upload-text {
  line-height: 1.6;
}

.primary-text {
  font-size: 18px;
  font-weight: 500;
  margin: 0 0 8px 0;
  color: #303133;
}

.secondary-text {
  font-size: 14px;
  margin: 0;
  color: #909399;
}

.browse-link {
  color: #409eff;
  cursor: pointer;
  font-weight: 500;
}

.upload-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 20px;
  font-size: 14px;
  color: #909399;
}

.tip-icon-small {
  font-size: 14px;
}

.no-user-warning {
  margin-top: 30px;
}

.warning-text {
  margin: 5px 0 0 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.file-info {
  margin-top: 30px;
  animation: fadeIn 0.5s ease;
}

.file-details {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f6f9ff;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
}

.file-icon {
  font-size: 36px;
  color: #409eff;
  background: white;
  padding: 8px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.file-meta {
  flex: 1;
}

.file-name {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.file-size {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.remove-btn:hover {
  background: rgba(245, 108, 108, 0.1);
}

.privacy-notice {
  margin-top: 30px;
}

.privacy-text {
  margin: 5px 0 0 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.instruction-card {
  margin-top: 30px;
}

.instruction-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409eff;
  font-weight: 500;
}

.instruction-content {
  padding: 10px 0;
}

.info-items {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.info-icon {
  font-size: 24px;
  color: #409eff;
  background: #ecf5ff;
  padding: 10px;
  border-radius: 8px;
  flex-shrink: 0;
}

.info-content h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #303133;
}

.info-content p {
  margin: 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式调整 */
@media (max-width: 768px) {
  .step-container {
    padding: 20px 16px;
  }

  .upload-card {
    padding: 20px;
  }

  .custom-upload :deep(.el-upload-dragger) {
    height: 240px;
    padding: 30px 16px;
  }

  .upload-cloud {
    font-size: 48px;
  }

  .primary-text {
    font-size: 16px;
  }

  .file-details {
    padding: 16px;
  }

  .info-items {
    gap: 16px;
  }

  .info-item {
    gap: 12px;
  }
}
</style>
