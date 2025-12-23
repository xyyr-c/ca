<template>
  <h2 class="titles">以下是您的证书情况</h2>
  <el-row :gutter="20">
    <el-col v-for="(cert, index) in certs" :key="cert.id" :span="8">
      <!-- 只有当证书的状态不为 2 时才显示 -->
      <el-card v-if="status[cert.id] !== 2" class="card" shadow="hover">
        <!-- 卡片内容 -->
        <div slot="header" class="clearfix">
          <span>证书 {{ certIds[cert.id] }}</span>
        </div>

        <el-form label-width="100px">
          <el-form-item :label="'创建时间 (' + cert.id + ')'" :prop="'created_at_' + cert.id">
            <el-input v-model="certTimes[cert.id]" :placeholder="'创建时间: ' + cert.created_at" disabled />
          </el-form-item>

          <el-form-item :label="'过期时间 (' + cert.id + ')'" :prop="'expire_time_' + cert.id">
            <el-input v-model="expireTimes[cert.id]" :placeholder="'过期时间: ' + cert.expire_time" disabled />
          </el-form-item>

          <el-form-item :label="'证书ID (' + cert.id + ')'" :prop="'id_' + cert.id">
            <el-input v-model="certIds[cert.id]" :placeholder="'证书ID: ' + cert.id" disabled />
          </el-form-item>
        </el-form>

        <!-- 操作按钮 -->
        <div class="card-actions">
          <el-button @click="downloadCa(cert.cert_path, cert.id)" size="small">下载证书</el-button>
          <el-button @click="flushed" size="small">刷新</el-button>
          <el-button @click="deleteCa(cert.id)" size="small">吊销证书</el-button>
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import axios from 'axios';

const certs = ref([])
const status = ref<any>({})
const certTimes = ref<any>({})
const expireTimes = ref<any>({})
const certIds = ref<any>({})

onMounted(() => {
  flushed()
})

const flushed = () => {
  axios.post('/api/cert/query', { withCredentials: true })
    .then((response) => {
      if (response.data.header.code == 200) {
        certs.value = response.data.certs
        certs.value = certs.value.filter(cert => cert.state !== 2);
        // 初始化证书的时间、ID、状态等信息
        certs.value.forEach((cert: any) => {
          certTimes.value[cert.id] = cert.created_at
          expireTimes.value[cert.id] = cert.expire_time
          certIds.value[cert.id] = cert.id
          status.value[cert.id] = cert.state
        })
      } else {
        alert("查询失败，请重试")
      }
    }).catch((error) => {
      alert("错误，请联系网站管理员")
    })
}

const downloadCa = (ca_id,cert_id) => {
    axios({
      method: 'get',
      url: '/api/cert/download',
      params: {
        cert_path: ca_id,
      },
      responseType: 'blob', // 设置响应类型为 blob
      withCredentials: true, // 设置跨域请求时是否需要使用凭证
    })
    .then(response => {
      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      // link.download = cert_id;  // 设置文件名
      link.click();  // 模拟点击下载链接
      URL.revokeObjectURL(link.href);  // 释放临时的 URL 对象
    })
   }

  //吊销ca证书
  const deleteCa = (cert_id) => {
    axios.post('/api/cert/revoke', {
      "cert_id": cert_id
    },{ withCredentials: true }).then(response => {
      // 处理删除逻辑
      console.log(response.data);
      if (response.data.header.message == "Success")
      {
        status.value[cert_id] = 2;
        //certs中删除该证书,可以使得卡片动态变化。
        certs.value = certs.value.filter(cert => cert.id !== cert_id)
      }
      else
      {
        alert("删除失败，请重试")
      }
    }).catch((error) => {
      alert("错误，请联系网站管理员")
    })
  }
</script>

<style scoped>
.card {
  margin-bottom: 20px;
}

.card-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  justify-content: flex-start;
}
.titles{
  font-size: 15px;
  font-weight: bold;
  margin-bottom: 10px;
  text-align: center;
}
</style>
