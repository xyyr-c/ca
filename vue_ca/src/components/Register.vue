<template>
  <div class="container">
  <form @submit.prevent="handleSubmit">
    <h1>注册</h1>
    <input type="text" v-model="username" placeholder="请输入用户名" />
    <input type="password" v-model="password" placeholder="请输入密码" />
    <input type="submit" value="注册" />
    <a href="/">已有账号？返回登录</a>
  </form>
  </div>
</template>


<script lang="ts" setup name="register">
  import { ref } from 'vue'
  import axios,{AxiosError} from 'axios'

  let username = ref('');
  let password = ref('');
  function validatePassword(password) {
  // 正则表达式：至少8位，包含大写字母、小写字母和标点符号
  const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*[\W_]).{8,}$/;

  if (!passwordPattern.test(password)) {
    return true; // 为了调试方便，暂时取消密码强度限制。
  }
  return true;
}
  const to_login = () => {
    window.location.href = "/login"
  }
  const handleSubmit = () => {
    console.log('Username:', username.value);
    console.log('Password:', password.value);
    if(validatePassword(password.value)){
    axios.post('/api/auth/register', {
      "username": username.value,
      "password": password.value
    }).then(response => {
      console.log(response.data);
      if (response.data.status == "success")
      {
        alert(response.data.msg)
        window.location.href = "/"
      }
      else
      {
        alert(response.data.msg)
        username.value = ""
        password.value = ""
      }
    }).catch(error => {
      // 处理登录失败逻辑
      alert("出错了，请联系网站管理员修复。")
      username.value = ""
      password.value = ""
    })}
    else{
    password.value = ""
    alert("密码必须至少8位，且包含大小写字母和标点符号！")
  }
};

</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.container {
  background-image: url('/333.jpg');
  background-size: cover;
  background-position: center center;
  font-family: 'Arial', sans-serif;
  background-color: #f3f4f6;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
}


form {
  background-color: #17229e;
  padding: 3rem 4rem;
  border-radius: 12px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 500px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

input[type="text"],
input[type="password"] {
  width: 100%;
  padding: 14px 18px;
  margin-bottom: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 18px;
  transition: border-color 0.3s ease;
}

input[type="text"]:focus,
input[type="password"]:focus {
  border-color: #007bff;
  outline: none;
}

input[type="submit"] {
  background-color: #007bff;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 14px 18px;
  font-size: 18px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  width: 100%;
  margin-bottom: 15px;
}

input[type="submit"]:hover {
  background-color: #0056b3;
}

a {
  display: inline-block;
  margin-top: 15px;
  color: #007bff;
  text-decoration: none;
  font-size: 16px;
}

a:hover {
  text-decoration: underline;
}

h1 {
  margin-bottom: 25px;
  color: #f8f6f6;
  font-size: 28px;
  text-align: center;
}

</style>
