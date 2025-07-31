import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('../views/Home.vue')
    },
    {
      path: '/upload',
      name: 'Upload',
      component: () => import('../views/Upload.vue')
    },
    {
      path: '/files',
      name: 'Files',
      component: () => import('../views/Files.vue')
    },
    {
      path: '/files/preview/:id',
      name: 'FilePreview',
      component: () => import('../views/FilePreview.vue')
    },
    {
      path: '/projects',
      name: 'Projects',
      component: () => import('../views/Projects.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/projects/:id',
      name: 'ProjectDetail',
      component: () => import('../views/ProjectDetail.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/Settings.vue')
    }
  ]
})

// Basic route guard for authentication
router.beforeEach((to, from, next) => {
  // For now, we'll allow all routes since there's no authentication system
  // In a real implementation, you would check user authentication here
  if (to.meta.requiresAuth) {
    // TODO: Add actual authentication check
    // For now, just proceed
    next()
  } else {
    next()
  }
})

export default router 