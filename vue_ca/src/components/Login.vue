<template>
  <div class="container">
    <div class="header">
    <h1>小型CA系统</h1>
  </div>
  <form @submit.prevent="handleSubmit">
    <h1>登录</h1>
    <input type="text" v-model="username" placeholder="请输入用户名" />
    <input type="password" v-model="password" placeholder="请输入密码" />
    <input type="submit" value="登录" />
    <a href="/register">没有账号？立即注册</a>
  </form>
  </div>
</template>

<script lang="ts" setup name="login">
  import { ref } from 'vue'
  import axios,{AxiosError} from 'axios'
  import { useRouter } from 'vue-router'
  axios.defaults.withCredentials = true;

  let username = ref('');
  let password = ref('');
  const router = useRouter();  // Vue Router

  const handleSubmit = () => {
    console.log('Username:', username.value);
    console.log('Password:', password.value);

    let mySessionCookie = ref('');

    // 处理登录逻辑
    axios.post('/api/auth/login', {
      "username": username.value,
      "password": password.value
    },{ withCredentials: true }).then(response => {
      // 处理登录成功逻辑
      console.log(response.data);
      if (response.data.status == "success")
      {
        // document.cookie = "username=" + username.value + "; max-age=" + (7 * 24 * 60 * 60) + "; path=/";
        sessionStorage.setItem("username", username.value)
        mySessionCookie.value = document.cookie
        console.log("这里是cookie",mySessionCookie.value)
        console.log(sessionStorage.getItem("username"))
        window.location.href = "/user"
      }
      else
      {
        alert("用户名或密码错误")
        username.value = ""
        password.value = ""
      }
    }).catch(error => {
      // 处理登录失败逻辑
      alert("出错了，请联系网站管理员修复。")
      username.value = ""
      password.value = ""
    })
  }


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
  flex-direction: column; /* 使内容垂直排列 */
  height: 100vh;
  padding-top: 10px; /* 给顶部留出一些空白 */
}

.header {
  text-align: center;
  margin-bottom: 0px; /* 增加标题和表单之间的间距 */
}

.header h1 {
  font-size: 36px; /* 增大标题字体 */
  color: #fff;
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
