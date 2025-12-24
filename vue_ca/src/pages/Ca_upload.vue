<template>
  <div class="stepT">
      <el-row :gutter="40">
        <el-col :span="40">
          <div class="grid-content">
            <el-card class="box-card">
              <div class="tap">
                <p align="left">
                  <b>您需要提供您的必要信息，以便验证该证书是否为我们颁发。</b>
                </p>
                <p align="left">
                  <i class="el-icon-info"></i> 请上传您的文件
                </p>
              </div>
              <el-upload
                class="upload-demo"
                drag
                action=""
                :http-request="upload_cer"
                :before-upload="beforeUpload"
                name="cer"
                ref="file_list"
                :auto-upload="true"
                :limit="1"
              >
                <i class="el-icon-upload"></i>
                <div class="el-upload__text">
                  将文件拖到此处，或<em>点击上传</em>
                </div>
                <div class="el-upload__tip" slot="tip">
                  支持上传任意文件，大小不要超过 10 MB
                </div>
              </el-upload>
            </el-card>
          </div>
        </el-col>
      </el-row>
  </div>
</template>

<script setup lang="ts" name="Ca_submit">
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const file_list = ref()

// 上传文件的属性定义
interface UploadFileParam {
  file: File;  // 上传的文件对象
  onSuccess: (response: any) => void;
  onError: (error: any) => void;
  [key: string]: any;
}

// 文件上传前的校验：限制大小不超过10MB
const beforeUpload = (file: File) => {
  const maxSize = 10 * 1024 * 1024 // 10MB
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 10 MB')
    return false
  }
  return true
}

function upload_cer(param: UploadFileParam) {
  const formData = new FormData()
  formData.append('cert', param.file)

  axios.post('/api/cert/auth_cer', formData, { withCredentials: true })
    .then((response) => {
      console.log(response.data)
      if (response.data.header.code == 200) {
        file_list.value.clearFiles()
        ElMessage.success("验证成功，您所提交的文件是我们签发的。")
      } else {
        ElMessage.error("上传失败，请检查文件类型重新上传。")
      }
    }).catch((error) => {
      ElMessage.error("上传失败，请检查文件类型重新上传。")
    })
}
</script>

<style scoped>
.stepT {
  width: 80%;
  margin: 30px auto 30px;
}
.tap p {
  font-size: 14px;
  color: #303133;
  margin-left: 20px;
}
body {
  margin: 0;
}

::v-deep .upload-demo .el-upload-dragger {
  height: 300px;
  width: 100%;
}
.el-upload__text {
  height: auto;
  line-height: 1.5;
  margin-top: 90px;
}
.box-card {
  width: 1200px;
  height: 500px;
}
</style>
