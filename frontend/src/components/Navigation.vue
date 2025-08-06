<template>
  <aside class="sidebar">
    <div class="logo-area">
      <img src="/logo.png" alt="logo" class="logo" />
    </div>
    <nav class="nav-menu">
      <div 
        v-for="item in menuItems" 
        :key="item.path" 
        class="nav-item" 
        :class="{ active: isActiveRoute(item.path) }" 
        @click="navigateTo(item.path)" 
        :title="item.tooltip"
      >
        <el-icon :size="24">
          <component :is="item.icon" />
        </el-icon>
      </div>
    </nav>
    <div class="sidebar-bottom">
      <el-icon 
        class="sidebar-icon" 
        :class="{ active: isActiveRoute('/settings') }" 
        @click="navigateTo('/settings')" 
        title="设置"
      >
        <Setting />
      </el-icon>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { HomeFilled, Document, Setting } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const menuItems = [
  { icon: HomeFilled, path: '/', tooltip: '首页' },
  { icon: Document, path: '/projects', tooltip: '项目' }
]

const isActiveRoute = (path: string) => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}

const navigateTo = (path: string) => {
  if (route.path !== path) {
    router.push(path)
  }
}
</script>

<style scoped>
.sidebar {
  width: 80px;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 2px 0 8px 0 rgba(0,0,0,0.03);
  z-index: 10;
  box-sizing: border-box;
  height: 100vh;
  overflow-y: auto;
}

.logo-area {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.logo {
  width: 36px;
  height: 36px;
}

.nav-menu {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 24px;
  width: 100%;
}

.nav-item {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  margin: 0 auto;
}

.nav-item::after {
  content: attr(title);
  position: absolute;
  left: 60px;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s;
  z-index: 1000;
}

.nav-item:hover::after {
  opacity: 1;
}

.nav-item {
  color: #606266;
}

.nav-item.active, .nav-item:hover {
  background: #f0f4ff;
  color: #409eff;
}

.sidebar-bottom {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
  margin-bottom: 24px;
  width: 100%;
}

.sidebar-icon {
  font-size: 22px;
  color: #606266;
  cursor: pointer;
  transition: color 0.2s;
}

.sidebar-icon:hover, .sidebar-icon.active {
  color: #409eff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    width: 60px;
  }
  
  .nav-item {
    width: 44px;
    height: 44px;
  }
}

@media (max-width: 480px) {
  .sidebar {
    width: 50px;
  }
  
  .nav-item {
    width: 40px;
    height: 40px;
  }
}
</style>