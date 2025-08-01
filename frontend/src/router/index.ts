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
      component: () => import('../views/Projects.vue')
    },
    {
      path: '/projects/:id',
      name: 'ProjectDetail',
      component: () => import('../views/ProjectDetail.vue')
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/Settings.vue')
    }
  ]
})

export default router 