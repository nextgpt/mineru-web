import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('../views/Home.vue'),
      meta: {
        title: '首页',
        requiresAuth: false
      }
    },
    {
      path: '/projects',
      name: 'Projects',
      component: () => import('../views/Projects.vue'),
      meta: {
        title: '项目管理',
        requiresAuth: false
      }
    },
    {
      path: '/upload',
      name: 'Upload',
      component: () => import('../views/Upload.vue'),
      meta: {
        title: '文件上传',
        requiresAuth: false
      }
    },
    {
      path: '/files',
      name: 'Files',
      component: () => import('../views/Files.vue'),
      meta: {
        title: '文件管理',
        requiresAuth: false
      }
    },
    {
      path: '/files/preview/:id',
      name: 'FilePreview',
      component: () => import('../views/FilePreview.vue'),
      meta: {
        title: '文档预览',
        requiresAuth: false
      }
    },
    {
      path: '/preview/:id',
      name: 'TenderPreview',
      component: () => import('../views/FilePreview.vue'),
      meta: {
        title: '招标文档预览',
        requiresAuth: false
      }
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/Settings.vue'),
      meta: {
        title: '设置',
        requiresAuth: false
      }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      redirect: '/'
    }
  ]
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - 招标文件智能生成标书系统`
  } else {
    document.title = '招标文件智能生成标书系统'
  }

  // 权限控制 (目前系统不需要登录，但保留扩展性)
  if (to.meta?.requiresAuth) {
    // 这里可以添加用户认证逻辑
    // const isAuthenticated = checkUserAuth()
    // if (!isAuthenticated) {
    //   ElMessage.error('请先登录')
    //   next('/login')
    //   return
    // }
  }

  // 路由参数验证
  if (to.name === 'FilePreview' || to.name === 'TenderPreview') {
    const projectId = to.params.id as string
    if (!projectId || projectId.trim() === '') {
      ElMessage.error('无效的项目ID')
      next('/projects')
      return
    }
  }

  next()
})

// 路由错误处理
router.onError((error) => {
  console.error('Router error:', error)
  ElMessage.error('页面加载失败，请刷新重试')
})

export default router 