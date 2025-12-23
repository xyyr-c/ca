<template>
  <login/>
</template>

<script lang="ts">
  import login from './components/Login.vue'

  export default {
    name:'App', //组件名
    components:{login} //注册组件
  }
</script>
