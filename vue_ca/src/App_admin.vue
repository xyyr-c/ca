<template>
  <div class="app">
    <!-- 头部区 -->
    <div class="header">
      <h4>CA证书管理系统-管理员</h4>
    </div>

    <!-- 导航区 -->
    <div class="navigate">
      <div class="admin-info">
        <span>欢迎，管理员 {{ username }}</span>
      </div>
      <button class="logout-btn" @click="logout">退出登录</button>
    </div>

    <!-- 展示区 -->
    <div class="main-content">
      <!-- 证书管理视图 -->
      <div class="certificate-management">
        <!-- 用户选择区域 -->
        <div class="user-selection">
          <div class="selection-header">
            <h3>用户证书管理</h3>
            <div class="search-box">
              <input
                type="text"
                v-model="searchQuery"
                placeholder="搜索用户、姓名或证书序列号..."
                @input="filterCertificates"
              >
              <button class="search-btn" @click="filterCertificates">
                <span class="icon">🔍</span>
              </button>
            </div>
          </div>

          <div class="user-filter">
            <div class="filter-options">
              <label>
                <input type="radio" v-model="selectedUser" value="all">
                所有用户
              </label>
              <div class="user-dropdown">
                <select v-model="selectedUser" @change="onUserChange">
                  <option value="">全部用户</option>
                  <option v-for="user in userList" :key="user.uid" :value="user.username">
                    {{ user.username }} ({{ user.email }})
                  </option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- 证书列表区域 -->
        <div class="certificate-list-container">
          <div class="list-header">
            <div class="stats">
              <span>共 {{ filteredCertificates.length }} 张证书</span>
              <span class="status-filter">
                状态筛选:
                <select v-model="statusFilter" @change="filterCertificates">
                  <option value="all">全部</option>
                  <option value="1">待审核</option>
                  <option value="2">已激活</option>
                  <option value="3">已吊销</option>
                  <option value="expired">已过期</option>
                </select>
              </span>
            </div>
            <button class="refresh-btn" @click="fetchCertificates">
              <span class="icon">🔄</span> 刷新列表
            </button>
          </div>

          <div class="certificate-table">
            <table>
              <thead>
                <tr>
                  <th>请求ID</th>
                  <th>用户</th>
                  <th>姓名</th>
                  <th>邮箱</th>
                  <th>组织/部门</th>
                  <th>颁发日期</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="cert in paginatedCertificates" :key="cert.req_id"
                    :class="{
                      'status-pending': cert.status === 1,
                      'status-active': cert.status === 2 && !isExpired(cert),
                      'status-revoked': cert.status === 3,
                      'status-expired': isExpired(cert) && cert.status !== 3
                    }">
                  <td>{{ cert.req_id }}</td>
                  <td>
                    <div class="user-cell">
                      <span class="username">{{ cert.username }}</span>
                    </div>
                  </td>
                  <td>{{ cert.full_name }}</td>
                  <td>{{ cert.email }}</td>
                  <td>
                    <div v-if="cert.company || cert.department">
                      {{ cert.company }}{{ cert.department ? '/' + cert.department : '' }}
                    </div>
                    <div v-else class="text-muted">-</div>
                  </td>
                  <td>{{ formatDate(cert.created_time) }}</td>
                  <td>
                    <span class="status-badge" :class="getStatusClass(cert)">
                      {{ getStatusText(cert) }}
                    </span>
                  </td>
                  <td>
                    <div class="action-buttons">
                      <button
                        v-if="cert.status === 1"
                        class="btn-approve"
                        @click="approveCertificate(cert.req_id)"
                        title="审核通过"
                      >
                        通过
                      </button>
                      <button
                        v-if="cert.status === 2 && !isExpired(cert)"
                        class="btn-revoke"
                        @click="revokeCertificate(cert.req_id)"
                        title="吊销证书"
                      >
                        吊销
                      </button>
                      <button
                        class="btn-view"
                        @click="viewCertificateDetails(cert)"
                        title="查看详情"
                      >
                        详情
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="filteredCertificates.length === 0">
                  <td colspan="8" class="no-data">
                    📭 暂无证书数据
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 分页 -->
          <div class="pagination" v-if="filteredCertificates.length > 0">
            <button
              :disabled="currentPage === 1"
              @click="currentPage--"
              class="page-btn"
            >
              上一页
            </button>
            <span class="page-info">
              第 {{ currentPage }} 页 / 共 {{ totalPages }} 页
            </span>
            <button
              :disabled="currentPage === totalPages"
              @click="currentPage++"
              class="page-btn"
            >
              下一页
            </button>
          </div>
        </div>
      </div>

      <!-- 证书详情模态框 -->
      <div v-if="selectedCertificate" class="modal-overlay" @click.self="closeModal">
        <div class="modal-content">
          <div class="modal-header">
            <h3>证书详情</h3>
            <button class="modal-close" @click="closeModal">×</button>
          </div>
          <div class="modal-body">
            <div class="cert-details">
              <div class="detail-row">
                <span class="detail-label">请求ID:</span>
                <span class="detail-value">{{ selectedCertificate.req_id }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">用户ID:</span>
                <span class="detail-value">{{ selectedCertificate.uid }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">用户名:</span>
                <span class="detail-value">{{ selectedCertificate.username }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">姓名:</span>
                <span class="detail-value">{{ selectedCertificate.full_name }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">邮箱:</span>
                <span class="detail-value">{{ selectedCertificate.email }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">国家:</span>
                <span class="detail-value">{{ selectedCertificate.country_code || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">省/州:</span>
                <span class="detail-value">{{ selectedCertificate.region || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">城市:</span>
                <span class="detail-value">{{ selectedCertificate.city || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">组织:</span>
                <span class="detail-value">{{ selectedCertificate.company || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">部门:</span>
                <span class="detail-value">{{ selectedCertificate.department || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">创建时间:</span>
                <span class="detail-value">{{ formatDateTime(selectedCertificate.created_time) }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">有效时间:</span>
                <span class="detail-value">{{ formatDateTime(selectedCertificate.modified_time) || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">吊销时间:</span>
                <span class="detail-value">{{ formatDateTime(selectedCertificate.removed_time) || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">状态:</span>
                <span class="detail-value">
                  <span class="status-badge" :class="getStatusClass(selectedCertificate)">
                    {{ getStatusText(selectedCertificate) }}
                  </span>
                </span>
              </div>
              <div class="detail-row">
                <span class="detail-label">公钥:</span>
                <span class="detail-value public-key">{{ selectedCertificate.pub_key }}</span>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-download" @click="downloadCa(selectedCertificate.req_id)">
              下载证书
            </button>
            <button class="btn-cancel" @click="closeModal">关闭</button>
          </div>
        </div>
      </div>

      <!-- 操作确认模态框 -->
      <div v-if="showConfirmModal" class="modal-overlay">
        <div class="modal-content confirm-modal">
          <div class="modal-header">
            <h3>{{ confirmAction === 'approve' ? '审核通过' : '吊销证书' }}</h3>
          </div>
          <div class="modal-body">
            <p>{{ confirmMessage }}</p>
          </div>
          <div class="modal-footer">
            <button class="btn-confirm" @click="executeAction">
              {{ confirmAction === 'approve' ? '确认通过' : '确认吊销' }}
            </button>
            <button class="btn-cancel" @click="cancelAction">取消</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup name="App">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
// 用户信息
const username = ref(sessionStorage.getItem("username") || "管理员")

// 用户列表（从后端获取）
const userList = ref<Array<{
  uid: number;
  username: string;
  email: string | null;
  role: number | null;
}>>([])

// 证书数据（从后端获取）
const certificates = ref<Array<{
  req_id: number;
  created_time: string;
  modified_time: string | null;
  removed_time: string | null;
  uid: number;
  status: number; // 1-待审 2-通过 3-吊销
  pub_key: string;
  country_code: string | null;
  region: string | null;
  city: string | null;
  company: string | null;
  department: string | null;
  full_name: string;
  email: string | null;
  username?: string; // 从accounts表关联获取
}>>([])

// 筛选条件
const selectedUser = ref('all')
const searchQuery = ref('')
const statusFilter = ref('all')
const currentPage = ref(1)
const pageSize = 10

// 选中的证书
const selectedCertificate = ref<any>(null)
const showConfirmModal = ref(false)
const confirmAction = ref('')
const confirmMessage = ref('')
const pendingActionCertId = ref<number | null>(null)

// 计算属性
const filteredCertificates = computed(() => {
  let filtered = certificates.value

  // 按用户筛选
  if (selectedUser.value && selectedUser.value !== 'all') {
    filtered = filtered.filter(cert => cert.username === selectedUser.value)
  }

  // 按状态筛选
  if (statusFilter.value && statusFilter.value !== 'all') {
    if (statusFilter.value === 'expired') {
      filtered = filtered.filter(cert => isExpired(cert) && cert.status !== 3)
    } else {
      filtered = filtered.filter(cert => cert.status.toString() === statusFilter.value)
    }
  }

  // 搜索筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(cert =>
      (cert.username && cert.username.toLowerCase().includes(query)) ||
      (cert.full_name && cert.full_name.toLowerCase().includes(query)) ||
      (cert.email && cert.email.toLowerCase().includes(query)) ||
      cert.req_id.toString().includes(query)
    )
  }

  return filtered
})

const totalPages = computed(() => {
  return Math.ceil(filteredCertificates.value.length / pageSize)
})

const paginatedCertificates = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return filteredCertificates.value.slice(start, end)
})

// 方法
const fetchCertificates = async () => {
  try {
    const response = await axios.get('/api/admin/certificates', {
      withCredentials: true
    })

    if (response.data.status === 'success') {
      certificates.value = response.data.data || []
      // console.log('证书数据:', certificates.value)
      // 获取用户列表用于筛选
      await fetchUserList()
    } else {
      console.error('获取证书数据失败:', response.data.message)
      alert('获取证书数据失败: ' + (response.data.message || '未知错误'))
    }
  } catch (error) {
    console.error('获取证书数据失败:', error)
    alert('获取证书数据失败，请稍后重试')
  }
}

// 查询用户数据的函数
const fetchUserList = async () => {
  try {
    // 这里应该调用API获取所有用户数据
    const response = await axios.get('/api/admin/users', {
      withCredentials: true
    })

    if (response.data.status === 'success') {
      userList.value = response.data.data || []
      // console.log('用户列表:', userList.value)
    } else {
      console.error('获取用户列表失败:', response.data.message)
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

const filterCertificates = () => {
  currentPage.value = 1 // 重置到第一页
}

const onUserChange = () => {
  filterCertificates()
}

const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const formatDateTime = (dateTimeString: string | null) => {
  if (!dateTimeString) return '-'
  const date = new Date(dateTimeString)
  // console.log(dateTimeString)
  // console.log('日期时间字符串:', date.toLocaleString('zh-CN', {
  //   year: 'numeric',
  //   month: '2-digit',
  //   day: '2-digit',
  //   hour: '2-digit',
  //   minute: '2-digit',
  //   second: '2-digit'
  // }));
  return date.toLocaleString('zh-CN', {
    timeZone: 'UTC',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 判断证书是否过期（假设证书有效期为2年）
const isExpired = (cert: any) => {
  let createdDate = new Date(cert.created_time)
  if (!cert.created_time) return false
  if(cert.modified_time!=null)  createdDate= new Date(cert.modified_time)
  const expiryDate = new Date(createdDate)
  expiryDate.setFullYear(expiryDate.getFullYear() + 2) // 有效期2年
  console.log('证书过期时间:', expiryDate,cert.modified_time)
  return new Date() > expiryDate
}

const getStatusClass = (cert: any) => {
  if (cert.status === 3) return 'status-revoked'
  if (isExpired(cert)) return 'status-expired'
  if (cert.status === 2) return 'status-active'
  if (cert.status === 1) return 'status-pending'
  return ''
}

const getStatusText = (cert: any) => {
  if (cert.status === 3) return '已吊销'
  if (isExpired(cert)) return '已过期'

  const statusMap: {[key: number]: string} = {
    1: '待审核',
    2: '已激活',
    3: '已吊销'
  }
  return statusMap[cert.status] || '未知状态'
}
// 赋值
const viewCertificateDetails = (cert: any) => {
  selectedCertificate.value = cert
}

const closeModal = () => {
  selectedCertificate.value = null
}

const approveCertificate = (certId: number) => {
  pendingActionCertId.value = certId
  confirmAction.value = 'approve'
  confirmMessage.value = '您确定要通过此证书的审核吗？'
  showConfirmModal.value = true
}

const revokeCertificate = (certId: number) => {
  pendingActionCertId.value = certId
  confirmAction.value = 'revoke'
  confirmMessage.value = '您确定要吊销此证书吗？此操作不可撤销。'
  showConfirmModal.value = true
}

const executeAction = async () => {
  try {
    if (confirmAction.value === 'approve') {
      // 调用审核通过API
      await axios.post(`/api/admin/certificates/${pendingActionCertId.value}/approve`, {}, {
        withCredentials: true
      })

      // 更新本地状态
      updateCertificateStatus(pendingActionCertId.value, 2)
      ElMessage.info('证书审核通过成功');
    } else if (confirmAction.value === 'revoke') {
      // 调用吊销API
      await axios.post(`/api/admin/certificates/${pendingActionCertId.value}/revoke`, {}, {
        withCredentials: true
      })

      // 更新本地状态
      updateCertificateStatus(pendingActionCertId.value, 3)
      ElMessage.info('证书吊销成功')
    }

    showConfirmModal.value = false
    fetchCertificates() // 刷新数据
  } catch (error: any) {
    console.error('操作失败:', error)
    alert('操作失败: ' + (error.response?.data?.message || '请稍后重试'))
  }
}

const updateCertificateStatus = (certId: number, status: number) => {
  const index = certificates.value.findIndex(cert => cert.req_id === certId)
  if (index !== -1) {
    certificates.value[index].status = status
    certificates.value[index].modified_time = new Date().toISOString()

    if (status === 3) {
      certificates.value[index].removed_time = new Date().toISOString()
    }
  }
}

const cancelAction = () => {
  showConfirmModal.value = false
  pendingActionCertId.value = null
}

const downloadCa = (cert_id) => {
    axios({
      method: 'get',
      url: '/api/download',
      params: {
        cert_path: cert_id,
      },
      responseType: 'blob', // 设置响应类型为 blob
      withCredentials: true, // 设置跨域请求时是否需要使用凭证
    })
    .then(response => {
      // 检查响应状态码
      if (response.status === 200) {
        const blob = new Blob([response.data], { type: response.headers['content-type'] });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = cert_id + '.cer' ;  // 设置文件名
        link.click();  // 模拟点击下载链接
        URL.revokeObjectURL(link.href);  // 释放临时的 URL 对象
      } else {
        // 如果状态码不是200，尝试解析错误信息
        const reader = new FileReader();
        reader.onload = () => {
          try {
            const errorData = JSON.parse(reader.result);
            alert(`下载失败：${errorData.description || '未知错误'}`);
          } catch (e) {
            alert('下载失败：未知错误');
          }
        };
        reader.readAsText(response.data);
      }
    })
    .catch(error => {
      // 网络错误或请求发送失败
      if (error.response) {
        // 服务器返回了错误状态码（如404, 500等）
        if (error.response.data instanceof Blob) {
          // 如果错误响应是Blob，尝试解析为JSON
          const reader = new FileReader();
          reader.onload = () => {
            try {
              const errorData = JSON.parse(reader.result);
              alert(`下载失败：${errorData.description || '未知错误'}`);
            } catch (e) {
              alert('下载失败：未知错误');
            }
          };
          reader.readAsText(error.response.data);
        } else {
          alert(`下载失败：${error.response.data.description || '未知错误'}`);
        }
      } else if (error.request) {
        alert('下载失败：网络错误，请检查网络连接');
      } else {
        alert('下载失败：请求发送失败');
      }
    });
}

// 登录检查
const user_test = () => {
  const username = sessionStorage.getItem("username")
  if (username == null) {
    alert("您还没有登录，请先登录！")
    setTimeout(function() {
      window.location.replace("/login");
    }, 0)
  }
}

const logout = () => {
  const username = sessionStorage.getItem("username")
  if (username == null) {
    alert("您还没有登录，请先登录！")
    setTimeout(function() {
      window.location.replace("/login");
    }, 0)
    return
  }

  axios.post('/api/auth/logout', {
    "username": username
  }, { withCredentials: true }).then(response => {
    console.log(response.data);
    if (response.data.status == "success") {
      sessionStorage.clear()
      window.location.href = "/login"
    } else {
      window.location.href = '/login'
    }
  }).catch(error => {
    console.error("登出失败:", error);
    alert("出错了，请联系网站管理员修复。")
  })
}

// 生命周期
onMounted(() => {
  user_test()
  fetchCertificates()
})
</script>

<style scoped>
/* 重置样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: "微软雅黑", sans-serif;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 头部样式 */
.header {
  background: linear-gradient(135deg, #2c3e50, #34495e);
  color: #ffc268;
  padding: 20px 0;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header h4 {
  font-size: 28px;
  font-weight: 900;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
  letter-spacing: 2px;
}

/* 导航区样式 */
.navigate {
  background-color: #f8f9fa;
  padding: 15px 100px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.05);
}

.admin-info {
  font-size: 16px;
  color: #666;
  font-weight: 500;
}

/* 退出登录按钮样式 */
.logout-btn {
  padding: 10px 25px;
  background: linear-gradient(135deg, #dc3545, #c82333);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(220, 53, 69, 0.2);
  font-family: "微软雅黑", sans-serif;
}

.logout-btn:hover {
  background: linear-gradient(135deg, #c82333, #bd2130);
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(220, 53, 69, 0.3);
  color: white;
}

.logout-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(220, 53, 69, 0.2);
}

/* 主内容区样式 */
.main-content {
  flex: 1;
  margin: 20px auto;
  border-radius: 12px;
  width: 95%;
  max-width: 1400px;
  border: 1px solid #e0e0e0;
  background-color: white;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
  padding: 25px;
  overflow: auto;
}

/* 证书管理样式 */
.certificate-management {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
}

/* 用户选择区域 */
.user-selection {
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  padding: 20px;
  border-radius: 10px;
  border: 1px solid #dee2e6;
}

.selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.selection-header h3 {
  color: #2c3e50;
  font-size: 20px;
}

.search-box {
  display: flex;
  gap: 10px;
  align-items: center;
}

.search-box input {
  padding: 10px 15px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  width: 300px;
  font-size: 14px;
}

.search-btn {
  padding: 10px 15px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.search-btn:hover {
  background: #2980b9;
}

/* 用户筛选区域 */
.user-filter {
  margin-top: 15px;
}

.filter-options {
  display: flex;
  gap: 30px;
  align-items: center;
}

.filter-options label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #495057;
}

.user-dropdown select {
  padding: 8px 15px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  background: white;
  min-width: 250px;
  cursor: pointer;
}

/* 证书列表容器 */
.certificate-list-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 10px;
  border: 1px solid #dee2e6;
  overflow: hidden;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.stats {
  display: flex;
  gap: 20px;
  align-items: center;
}

.status-filter select {
  padding: 6px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  margin-left: 10px;
}

.refresh-btn {
  padding: 8px 15px;
  background: #2ecc71;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.3s;
}

.refresh-btn:hover {
  background: #27ae60;
}

/* 证书表格 */
.certificate-table {
  flex: 1;
  overflow: auto;
}

.certificate-table table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1000px;
}

.certificate-table th {
  background: #2c3e50;
  color: white;
  padding: 15px;
  text-align: left;
  font-weight: 600;
  position: sticky;
  top: 0;
}

.certificate-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #e0e0e0;
}

.certificate-table tr:hover {
  background-color: #f5f5f5;
}

/* 状态相关样式 */
.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.status-pending {
  background-color: #fff3cd;
}

.status-pending .status-badge.status-pending {
  background-color: #ffc107;
  color: #856404;
}

.status-active {
  background-color: #d4edda;
}

.status-active .status-badge.status-active {
  background-color: #28a745;
  color: white;
}

.status-revoked {
  background-color: #f8d7da;
}

.status-revoked .status-badge.status-revoked {
  background-color: #dc3545;
  color: white;
}

.status-expired {
  background-color: #e2e3e5;
}

.status-expired .status-badge.status-expired {
  background-color: #6c757d;
  color: white;
}

.expired {
  color: #dc3545;
  font-weight: 600;
}

/* 用户信息单元格 */
.user-cell {
  display: flex;
  flex-direction: column;
}

.username {
  font-weight: 600;
  color: #2c3e50;
}

.email {
  font-size: 12px;
  color: #6c757d;
  margin-top: 2px;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 8px;
}

.action-buttons button {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-approve {
  background: #28a745;
  color: white;
}

.btn-approve:hover {
  background: #218838;
}

.btn-revoke {
  background: #dc3545;
  color: white;
}

.btn-revoke:hover {
  background: #c82333;
}

.btn-view {
  background: #6c757d;
  color: white;
}

.btn-view:hover {
  background: #5a6268;
}

/* 分页样式 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-top: 1px solid #dee2e6;
}

.page-btn {
  padding: 8px 20px;
  border: 1px solid #ced4da;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.page-btn:hover:not(:disabled) {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #6c757d;
  font-weight: 500;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 10px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #2c3e50;
  color: white;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.modal-close {
  background: none;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 24px;
  height: 24px;
}

.modal-body {
  padding: 20px;
  max-height: 60vh;
  overflow-y: auto;
}

.modal-footer {
  padding: 15px 20px;
  background: #f8f9fa;
  border-top: 1px solid #dee2e6;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 证书详情样式 */
.cert-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-label {
  width: 100px;
  font-weight: 600;
  color: #495057;
  flex-shrink: 0;
}

.detail-value {
  flex: 1;
  color: #212529;
}

.public-key {
  word-break: break-all;
  font-family: monospace;
  font-size: 12px;
  background: #f8f9fa;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #dee2e6;
}

/* 确认模态框 */
.confirm-modal .modal-body {
  text-align: center;
  font-size: 16px;
  color: #495057;
}

.btn-confirm {
  padding: 10px 20px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.btn-confirm:hover {
  background: #c82333;
}

.btn-cancel {
  padding: 10px 20px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-cancel:hover {
  background: #5a6268;
}

.btn-download {
  padding: 10px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.btn-download:hover {
  background: #2980b9;
}

/* 无数据样式 */
.no-data {
  text-align: center;
  padding: 40px !important;
  color: #6c757d;
  font-size: 16px;
}

.text-muted {
  color: #6c757d;
  font-style: italic;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header h4 {
    font-size: 20px;
  }

  .navigate {
    padding: 15px 20px;
    flex-direction: column;
    gap: 10px;
  }

  .main-content {
    width: 98%;
    margin: 10px auto;
    padding: 15px;
  }

  .selection-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .search-box input {
    width: 100%;
  }

  .filter-options {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .list-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }

  .stats {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}

@media (max-width: 480px) {
  .header h4 {
    font-size: 18px;
  }

  .logout-btn {
    padding: 8px 16px;
    font-size: 12px;
  }

  .action-buttons {
    flex-direction: column;
  }

  .modal-content {
    width: 95%;
  }
}
</style>
