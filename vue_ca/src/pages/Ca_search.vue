<template>
  <h2 class="titles">以下是您的证书情况</h2>
  <el-row :gutter="20">
    <el-col v-for="(cert, index) in certs" :key="cert.req_id" :span="8">
      <!-- 只有当证书的状态不为1时才显示 -->
      <el-card v-if="status[cert.req_id] !== 1" class="card" shadow="hover">
        <!-- 卡片内容 -->
        <div slot="header" class="clearfix">
          <span>证书 {{ certIds[cert.req_id] }}</span>
        </div>

        <el-form label-width="100px">
          <el-form-item :label="'创建时间 (' + cert.req_id + ')'" :prop="'created_at_' + cert.req_id">
            <el-input v-model="certTimes[cert.req_id]" :placeholder="'创建时间: ' + cert.created_time" disabled />
          </el-form-item>

          <el-form-item :label="'过期时间 (' + cert.req_id + ')'" :prop="'expire_time_' + cert.req_id">
            <el-input v-model="expireTimes[cert.req_id]" :placeholder="'过期时间: ' + cert.removed_time" disabled />
          </el-form-item>

          <el-form-item :label="'证书ID (' + cert.req_id + ')'" :prop="'id_' + cert.req_id">
            <el-input v-model="certIds[cert.req_id]" :placeholder="'证书ID: ' + cert.req_id" disabled />
          </el-form-item>
        </el-form>

        <!-- 操作按钮 -->
        <div class="card-actions">
          <el-button @click="downloadCa(cert.req_id)" size="small">下载证书</el-button>
          <el-button @click="flushed" size="small">刷新</el-button>
          <el-button @click="deleteCa(cert.req_id)" size="small">吊销证书</el-button>
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
        console.log(certs.value)
        certs.value = certs.value.filter(cert => cert.status !== 1);
        // 初始化证书的时间、ID、状态等信息
        certs.value.forEach((cert: any) => {
          certTimes.value[cert.req_id] = cert.created_time
          expireTimes.value[cert.req_id] = cert.remove_time
          certIds.value[cert.req_id] = cert.req_id
          status.value[cert.req_id] = cert.status
        })
      } else {
        alert("查询失败，请重试")
      }
    }).catch((error) => {
      alert("错误，请联系网站管理员")
    })
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
      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = cert_id + '.cer' ;  // 设置文件名
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
        status.value[cert_id] = 3;
        //certs中删除该证书,可以使得卡片动态变化。
        certs.value = certs.value.filter(cert => cert.req_id !== cert_id)
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
