<template>
  <div class="stepT">
    <el-steps  :active="step" simple>

      <el-step title="CSR 信息填写" ></el-step>
      <el-step title="公钥上传" ></el-step>
      <el-step title="证书颁发" ></el-step>
    </el-steps>
    <!-- 提交 CSR 信息 -->
    <div v-if="step == 0" class="form1">
      <el-row :gutter="20">
        <el-col :span="10">
          <div class="grid-content">
            <el-card class="box-card">
              <div class="tap">
                <p align="left">
                  <b>您需要提供您的必要信息，以便我们核验您的身份。</b>
                </p>
                <p align="left">
                  <i class="el-icon-info"></i> 如果您有自己的 CSR
                  文件，可以直接拖拽至下方上传，我们会帮您解析。
                </p>
                <p align="left">
                  <i class="el-icon-info"></i>
                  当然，您可以选择直接填写右侧表单提交。
                </p>
              </div>
              <el-upload
                class="upload-demo"
                drag
                action=""
                :http-request="upload_csr"
                accept=".txt"
                name="file"
                :data="ruleForm"
                :auto-upload="true"
                :limit="1"
              >
                <i class="el-icon-upload"></i>
                <div class="el-upload__text">
                  将文件拖到此处，或<em>点击上传</em>
                </div>
                <div class="el-upload__tip" slot="tip">
                  请上传 csr 文件，大小不要超过 100 KB
                </div>
              </el-upload>
            </el-card>
          </div>
          </el-col>
        <el-col :span="12"
          ><div class="grid-content">
            <el-form
              :model="ruleForm"
              :rules="rules"
              reactive="ruleForm"
              label-width="100px"
              style="margin: 0 auto"
            >
              <el-form-item label="国家" prop="country">
                <el-input
                  type="text"
                  v-model="ruleForm.country"
                ></el-input>
              </el-form-item>
              <el-form-item label="省/州" prop="province">
                <el-input v-model="ruleForm.province"></el-input>
              </el-form-item>
              <el-form-item label="市" prop="locality">
                <el-input v-model="ruleForm.locality"></el-input>
              </el-form-item>
              <el-form-item label="公司/组织" prop="organization">
                <el-input v-model="ruleForm.organization"></el-input>
              </el-form-item>
              <el-form-item label="部门" prop="organization_unit_name">
                <el-input v-model="ruleForm.organization_unit_name"></el-input>
              </el-form-item>
              <el-form-item label="域名" prop="common_name">
                <el-input v-model="ruleForm.common_name"></el-input>
              </el-form-item>
              <el-form-item label="电子邮件" prop="email">
                <el-input v-model="ruleForm.email"></el-input>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="submitForm()">提交</el-button>
                <el-button @click="resetForm()">重置</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 提交公钥 -->
    <div v-if="step == 1">
      <div class="form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card class="box-card tag" shadow="hover">
              <el-card class="box-card-atuo" shadow="hover"

                :autosize="{ minRows: 15, maxRows: 15 }"
                placeholder="RSA公钥生成"
              >
              <el-card class="box-card-pub" shadow="hover" >
                <h4>这是生成的公钥 </h4>
                <el-input v-model="pu_key" :autosize="{ minRows: 15, maxRows: 15 }"></el-input>
              </el-card>
              <el-card class="box-card-pri" shadow="hover">
                <h4>这是生成的私钥，请自行保存，不要泄露给别人，本服务器不会存储您的私钥</h4>
                <el-input v-model="pr_key" :autosize="{ minRows: 15, maxRows: 15 }"></el-input>
              </el-card>
              </el-card>
              <el-button type="primary" @click="autoGetKey" class="but"
                >自动生成
                </el-button>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="box-card tag" shadow="hover">
              <el-input
                type="textarea"
                :autosize="{ minRows: 15, maxRows: 15 }"
                placeholder="请输入内容"
                v-model="pu_key_show"
              >
              </el-input>
              <el-button type="primary" class="but" @click="submitPublicKey"
                >手动提交</el-button
              >
            </el-card>
          </el-col>
        </el-row>
      </div>
    </div>
    <!-- 成功提交 -->
    <div v-if="step == 2">
      <el-card class="box-card2" shadow="hover">
        <div class="success1">成功</div>
        <div class="success2">恭喜您，证书申请成功！</div>
        <div class="success2">点击下方按钮下载您的证书</div>
        <button class="download" @click="downloadCa()">下载证书</button>
      </el-card>
    </div>
  </div>
</template>


<script setup lang="ts" name="Ca_submit">
  import {ref,reactive} from 'vue'
  import { ElSteps, ElStep, ElButton } from 'element-plus'
  import axios from 'axios'

  const step = ref(0)
  const csr_id = ref('')
  const pr_key = ref('')
  const pu_key = ref('')
  const pu_key_show = ref('')
  const ca_id = ref('')

    // 定义表单数据
  const ruleForm = reactive({
      country: '',
      province: '',
      locality: '',
      organization: '',
      organization_unit_name: '',
      common_name: '',
      email: '',
    }) as {
      country: string;
      province: string;
      locality: string;
      organization: string;
      organization_unit_name: string;
      common_name: string;
      email: string;
    };

    // 定义验证规则
  const rules = reactive({
      country: [
        { required: false, message: '请输入国家', trigger: 'blur' },  {
      pattern: /^[A-Za-z]{2}$/,
      message: '请输入两位字母的国家代码',
      trigger: 'blur'
     }
      ],
      province: [
        { required: false, message: '请输入省/州', trigger: 'blur' },
      ],
      locality: [
        { required: false, message: '请输入城市', trigger: 'blur' },
      ],
      organization: [
        { required: false, message: '请输入公司/组织', trigger: 'blur' },
      ],
      organization_unit_name: [
        { required: false, message: '请输入部门', trigger: 'blur' },
      ],
      common_name: [
        { required: true, message: '请输入域名', trigger: 'blur' },
      ],
      email: [
        { required: false, message: '请输入电子邮件', trigger: 'blur' },
        { type: 'email', message: '请输入有效的电子邮件地址', trigger: ['blur', 'change'] },
      ],

    });
    // 提交表单
  const submitForm = () => {
    // 处理表单提交逻辑
      axios.post('/api/ca/csr', {
      "country": ruleForm.country,
      "province": ruleForm.province,
      "locality": ruleForm.locality,
      "organization": ruleForm.organization,
      "common_name": ruleForm.common_name,
      "email_address": ruleForm.email,
      "organizational_unit": ruleForm.organization_unit_name,
    },{ withCredentials: true }).then(response => {

      console.log(response.data);
      if (response.data.header.code == 200)
      {
        csr_id.value = response.data.csr_id
        console.log(csr_id.value)
        step.value += 1
      }
      else
      {
        alert(response.data.msg)
      }
    }).catch(error => {
      // 处理登录失败逻辑
      alert("出错了，请联系网站管理员修复。")
    })
  };
    // 重置表单
    const resetForm = () => {
      ruleForm.country = '';
      ruleForm.province = '';
      ruleForm.locality = '';
      ruleForm.organization = '';
      ruleForm.organization_unit_name = '';
      ruleForm.common_name = '';
      ruleForm.email = '';
    };
    // 生成密钥对
    const autoGetKey=() =>
    {
      axios.post('/api/gen_rsa',
        { withCredentials: true }).then(response => {
          // 处理登出逻辑
          console.log(response.data);
          // console.log(response.data.header.code);
          if (response.data.header.code == 200)
            {
              pr_key.value = response.data.pr_key
              pu_key.value = response.data.pu_key
              pu_key_show.value = response.data.pu_key
              // console.log(pr_key.value)
              // console.log(pu_key.value)
            }
        }).catch(error => {
          alert("出错了，请联系网站管理员修复。")
        })
      }
    //提交公钥信息
    const submitPublicKey =() =>{
      axios.post('/api/audit/pass', {
        "public_key": pu_key_show.value,
        "csr_id": csr_id.value,
      },{ withCredentials: true }).then(response => {
        // 处理登录成功逻辑
        console.log(response.data);
        if (response.data.header.code == 200)
        {
          ca_id.value = response.data.cert_path
          step.value = 2
        }
        else
        {
          alert(response.data.msg)
        }
      }).catch(error => {
        // 处理登录失败逻辑
        alert("出错了，请联系网站管理员修复。")
      })
    }
    // 上传csr文件的属性定义
    interface UploadFileParam {
      file: File;  // 上传的文件对象
      onSuccess: (response: any) => void;  // 上传成功的回调
      onError: (error: any) => void;  // 上传失败的回调
      [key: string]: any;  // 可以有其他可选属性
    }
   //上传csr文件
    function upload_csr (param: UploadFileParam) {
      const formData = new FormData();
      formData.append('csr', param.file);  // 上传文件字段名为 'csr'

    axios.post('/api/ca/read_csr', formData,{ withCredentials: true })
   .then((response) => {
    console.log(response.data);
    if (response.data.header.code == 200)
      {
        alert("上传成功")
        csr_id.value = response.data.csr_id
        step.value+=1
      }
      else
      {
        alert("上传失败，请检查文件类型重新上传")
      }
  })
  .catch((error) => {
    alert("出错了，请联系网站管理员修复。")
  });
}
   //下载ca证书
   const downloadCa = () => {
    axios({
      method: 'get',
      url: '/api/cert/download',
      params: {
        cert_path: ca_id.value,
      },
      responseType: 'blob', // 设置响应类型为 blob
      withCredentials: true, // 设置跨域请求时是否需要使用凭证
    })
    .then(response => {
      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      // link.download = csr_id.value;  // 设置文件名
      link.click();  // 模拟点击下载链接
      URL.revokeObjectURL(link.href);  // 释放临时的 URL 对象
    })
   }
</script>

<style scoped>
.about {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: rgb(85, 84, 84);
  font-size: 18px;
}
.stepT {
  width: 80%;
  margin: 30px auto 30px;
}
.use {
  padding: 15px;
}
.code {
  background-color: #303133;
  color: aliceblue;
  padding: 20px;
  margin: 0 0 15px 10px;
}
.sslIcon {
  padding: 25px 0 0 0;
  font-size: 77px;
}
.el-card {
  margin-left: 10px;
  height: auto;
}
.tap p {
  font-size: 14px;
  color: #303133;
  margin-left: 20px;

}
body {
  margin: 0;
}
.but {
  margin-top: 10px;
  width: 100%;
}
.form1 {
  width: 100%;
  margin: 50px auto 50px auto;
  color: #606266;
}
.pk_input {
  height: 100px;
}
.tag {
  height: 450px;
}
.choise {
  height: 450px;
}
.icon {
  font-size: 77px;
  color: #67c23a;
}
.bg-purple {
  background: #d3dce6;
}
.info {
  margin-left: 30px;
  color: #303133;
}

.upload-demo  {
    height: 220px; /* 调整高度 */
}
::v-deep .upload-demo  .el-upload-dragger {
    height: 200px; /* 调整高度 */
    width: 100%; /* 调整宽度 */
}

.el-upload__text {
  height: auto; /* 调整文本区域的高度 */
  line-height: 1.5; /* 调整文本区域的行高 */
  margin-top: 40px; /* 调整文本区域的上边距 */
}
.box-card-atuo{
  width: 485px;
  height: 323px;
}
.box-card-pub{
  height: 140px;
}
.box-card-pri{
  height: 150px;
}
/* 成功标题 */
.success1 {
  color: #28a745; /* 成功的绿色 */
  font-size: 2rem; /* 设置较大的字体 */
  font-weight: bold; /* 字体加粗 */
  margin-bottom: 10px; /* 下边距 */
}

/* 成功副标题 */
.success2 {
  color: #333; /* 深色文字，保证可读性 */
  font-size: 1.2rem; /* 副标题较小的字体 */
  font-weight: normal; /* 正常字体 */
  line-height: 1.6; /* 行高 */
  margin-top: 0; /* 移除顶部边距 */
}
/* card 外部样式 */
.box-card2 {
  background-color: #f8f9fa; /* 浅灰色背景 */
  padding: 20px; /* 内边距 */
  border-radius: 10px; /* 圆角 */
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1); /* 阴影效果 */
  width: 1000px;
  height: 250px;
  margin: 20px auto; /* 自动水平居中 */
  text-align: center; /* 文本水平居中 */
  justify-content: center;
  flex-direction: column;
}
/* 按钮样式 */
.download {
  background-color: #409EFF;  /* 按钮背景色，蓝色 */
  color: #fff;                /* 按钮文字颜色，白色 */
  border: none;               /* 去除按钮默认边框 */
  padding: 10px 20px;         /* 按钮内边距，调整按钮大小 */
  font-size: 16px;            /* 字体大小 */
  font-weight: bold;          /* 字体加粗 */
  border-radius: 4px;         /* 圆角边框 */
  cursor: pointer;           /* 鼠标悬停时显示指针 */
  transition: background-color 0.3s, transform 0.2s;  /* 添加平滑过渡效果 */
  margin-top: 20px;
}

/* 悬停效果 */
.download:hover {
  background-color: #66b1ff;  /* 悬停时背景色变亮 */
}

/* 按钮点击效果 */
.download:active {
  transform: scale(0.98);  /* 点击时按钮略微缩小 */
  background-color: #2a8ad0; /* 点击时背景色加深 */
}

/* 禁用状态 */
.download:disabled {
  background-color: #d3d3d3; /* 灰色背景 */
  cursor: not-allowed;        /* 禁用时显示禁止符号 */
}
</style>
