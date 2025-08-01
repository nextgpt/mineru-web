<script setup lang="ts">
import { HomeFilled, Upload, Document, Setting, FolderOpened } from '@element-plus/icons-vue'
import { useRouter, useRoute } from 'vue-router'
import { computed } from 'vue'

const router = useRouter()
const route = useRoute()

const menuItems = [
  { icon: HomeFilled, path: '/', tooltip: '首页' },
  { icon: FolderOpened, path: '/projects', tooltip: '项目管理' },
  { icon: Document, path: '/files', tooltip: '文件管理' },
  { icon: Upload, path: '/upload', tooltip: '上传' }
]

const activeMenu = () => {
  const path = route.path
  // 特殊处理首页
  if (path === '/') return '/'
  // 其他页面需要完全匹配路径
  return menuItems.find(item => path === item.path)?.path || path
}

// 检查是否是设置页面
const isSettingsPage = () => route.path === '/settings'

// 检查是否需要显示侧边栏（主页、项目页面、项目详情页面不显示侧边栏）
const shouldShowSidebar = computed(() => {
  const path = route.path
  return !(path === '/' || path === '/projects' || path.startsWith('/projects/'))
})

// 检查是否是全屏页面
const isFullScreenPage = computed(() => {
  const path = route.path
  return path === '/' || path === '/projects' || path.startsWith('/projects/')
})
</script>

<template>
  <div class="mineru-layout" :class="{ 'full-screen': isFullScreenPage }">
    <!-- 侧边栏 -->
    <aside v-if="shouldShowSidebar" class="sidebar">
      <div class="logo-area">
        <img src="/logo.png" alt="logo" class="logo" />
      </div>
      <nav class="nav-menu">
        <div v-for="item in menuItems" :key="item.path" class="nav-item" :class="{active: activeMenu() === item.path}" @click="router.push(item.path)" :title="item.tooltip">
          <el-icon :size="24"><component :is="item.icon" /></el-icon>
        </div>
      </nav>
      <div class="sidebar-bottom">
        <el-icon class="sidebar-icon" :class="{active: isSettingsPage()}" @click="router.push('/settings')" title="设置"><Setting /></el-icon>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="main-area" :class="{ 'full-width': !shouldShowSidebar }">
      <template v-if="route.name === 'FilePreview' || isFullScreenPage">
        <router-view />
      </template>
      <template v-else>
        <main class="content-area">
          <div class="content-card">
            <router-view />
          </div>
        </main>
      </template>
    </div>
  </div>
</template>

<style scoped>
.mineru-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: #f7f8fa;
  box-sizing: border-box;
}

.mineru-layout.full-screen {
  background: transparent;
}

.sidebar {
  width: 80px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 2px 0 20px rgba(0, 0, 0, 0.1);
  z-index: 10;
  box-sizing: border-box;
  height: 100%;
  border-right: 1px solid rgba(255, 255, 255, 0.2);
}

.logo-area {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.logo {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.nav-menu {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 32px;
  padding: 0 16px;
}

.nav-item {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #6b7280;
  position: relative;
}

.nav-item:hover {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
  transform: translateY(-2px);
}

.nav-item.active {
  background: linear-gradient(45deg, #6366f1, #8b5cf6);
  color: white;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.sidebar-bottom {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
  margin-bottom: 32px;
  padding: 0 16px;
}

.sidebar-icon {
  font-size: 24px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 12px;
  border-radius: 12px;
}

.sidebar-icon:hover {
  color: #6366f1;
  background: rgba(99, 102, 241, 0.1);
  transform: translateY(-2px);
}

.sidebar-icon.active {
  color: #6366f1;
  background: rgba(99, 102, 241, 0.1);
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  box-sizing: border-box;
  height: 100vh;
}

.main-area.full-width {
  width: 100vw;
}

.content-area {
  flex: 1;
  background: #f7f8fa;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 32px;
  box-sizing: border-box;
}

.content-card {
  width: 100%;
  max-width: 1400px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 32px;
  box-sizing: border-box;
}

@media (max-width: 768px) {
  .sidebar {
    width: 60px;
  }
  
  .nav-menu {
    padding: 0 8px;
  }
  
  .nav-item {
    width: 44px;
    height: 44px;
  }
  
  .sidebar-bottom {
    padding: 0 8px;
  }
  
  .content-area {
    padding: 16px;
  }
  
  .content-card {
    padding: 20px;
  }
}

@media (max-width: 480px) {
  .sidebar {
    width: 50px;
  }
  
  .logo-area {
    height: 60px;
  }
  
  .logo {
    width: 32px;
    height: 32px;
  }
  
  .nav-item {
    width: 40px;
    height: 40px;
  }
  
  .content-card {
    padding: 16px;
  }
}
</style>
