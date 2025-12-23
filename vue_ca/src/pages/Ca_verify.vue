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
                  <i class="el-icon-info"></i> 请提交您的cer证书文件
                </p>
              </div>
              <el-upload
                class="upload-demo"
                drag
                action=""
                :http-request="upload_cer"
                accept=".cer"
                name="cer"
                ref = "file_list"
                :auto-upload="true"
                :limit= "1"
              >
                <i class="el-icon-upload"></i>
                <div class="el-upload__text">
                  将文件拖到此处，或<em>点击上传</em>
                </div>
                <div class="el-upload__tip" slot="tip">
                  请上传 cer 文件，大小不要超过 100 KB
                </div>
              </el-upload>
            </el-card>
          </div>
        </el-col>
      </el-row>
  </div>
</template>


<script setup lang="ts" name="Ca_submit">
  import {ref,reactive} from 'vue'
  import axios from 'axios'
  const file_list = ref([])

    // 上传cer文件的属性定义
    interface UploadFileParam {
      file: File;  // 上传的文件对象
      onSuccess: (response: any) => void;  // 上传成功的回调
      onError: (error: any) => void;  // 上传失败的回调
      [key: string]: any;  // 可以有其他可选属性
    }

    function upload_cer (param: UploadFileParam) {
      const formData = new FormData();
      formData.append('cert', param.file);  // 上传文件字段名为 'cert'
      // console.log(param.file)
      axios.post('/api/cert/auth_cer', formData, { withCredentials: true }
    ).then((response) => {
      console.log(response.data);
    if (response.data.header.code == 200)
      {
        file_list.value.clearFiles()
        alert("验证成功，您所提交的文件是我们签发的。")
      }
      else
      {
        alert("上传失败，请检查文件类型重新上传。")
      }
  }).catch((error) => {
    alert("上传失败，请检查文件类型重新上传。")
  });
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

::v-deep .upload-demo  .el-upload-dragger {
    height: 300px; /* 调整高度 */
    width: 100%; /* 调整宽度 */
}
.el-upload__text {
  height: auto; /* 调整文本区域的高度 */
  line-height: 1.5; /* 调整文本区域的行高 */
  margin-top: 90px; /* 调整文本区域的上边距 */
}
.box-card{
  width: 1200px;
  height: 500px;
}


</style>
