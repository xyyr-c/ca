import {createRouter,createWebHistory,createWebHashHistory} from 'vue-router'

import Ca_search from '@/pages/Ca_search.vue'
import Ca_submit from '@/pages/Ca_submit.vue'
import Ca_upload from '@/pages/Ca_upload.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes:[
    {
      name:'search', //路由名称
      path: '/Ca_search',
      component: Ca_search
    },
    {
      name:'submit', //路由名称
      path: '/Ca_submit',
      component: Ca_submit
    },
    {
      name:'upload', //路由名称
      path: '/Ca_upload',
      component: Ca_upload
    },

  ]
})

export default router;
