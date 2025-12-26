import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import VueSetupExtend from 'vite-plugin-vue-setup-extend'
import fs from 'fs'
//每次替换从代理替换即可。
// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    VueSetupExtend(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    port: 443,
    host: "0.0.0.0",
    https:
    {
      key: fs.readFileSync("./https/test.pkey"),
      cert: fs.readFileSync("./https/test.cer"),
    },
    proxy: {
        '/api':
        {
          target: 'https://127.0.0.1:8080',
          changeOrigin: true,
          secure:false,
        },
     },
  },}

)
