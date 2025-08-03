<script setup lang="ts">
import { HomeFilled, Document, Setting } from '@element-plus/icons-vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const menuItems = [
  { icon: HomeFilled, path: '/', tooltip: '首页', label: '首页' },
  { icon: Document, path: '/projects', tooltip: '创建投标方案', label: '项目' }
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
</script>

<template>
  <div class="mineru-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="logo-area">
        <img src="/logo.png" alt="logo" class="logo" />
      </div>
      <nav class="nav-menu">
        <div v-for="item in menuItems" :key="item.path" class="nav-item" :class="{active: activeMenu() === item.path}" @click="router.push(item.path)" :title="item.tooltip">
          <el-icon :size="20"><component :is="item.icon" /></el-icon>
          <span class="nav-label">{{ item.label }}</span>
        </div>
      </nav>
      <div class="sidebar-bottom">
        <div class="nav-item" :class="{active: isSettingsPage()}" @click="router.push('/settings')" title="设置">
          <el-icon :size="20"><Setting /></el-icon>
          <span class="nav-label">设置</span>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="main-area">
      <main class="content-area">
        <div class="content-full">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.mineru-layout {
  display: flex;
  height: 100vh; /* 固定高度，防止被内容撑开出现滚动条 */
  overflow: hidden; /* 禁止自身滚动，让子元素独立滚动 */
  background: #f7f8fa;
  box-sizing: border-box;
}



.sidebar {
  width: 80px;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 2px 0 8px 0 rgba(0,0,0,0.03);
  z-index: 10;
  box-sizing: border-box;
  height: 100%; /* 撑满父容器高度 */
  overflow-y: auto; /* 如果内容可能超出，允许独立滚动 */
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
}
.nav-item {
  width: 64px;
  height: 64px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  color: #8c8c8c;
  gap: 4px;
}

.nav-item.active {
  background: #e6f4ff;
  color: #1890ff;
}

.nav-item:hover {
  background: #f5f5f5;
  color: #1890ff;
}

.nav-label {
  font-size: 10px;
  font-weight: 400;
  line-height: 1;
  text-align: center;
  white-space: nowrap;
}
.sidebar-bottom {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
  margin-bottom: 24px;
}
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  box-sizing: border-box;
  height: 100vh; /* 撑满父容器高度 */
  /* overflow-y: auto; 允许主内容区独立垂直滚动 */
}
.content-area {
  flex: 1;
  background: #f7f8fa;
  display: flex;
  justify-content: center;
  align-items: stretch;
  padding: 0;
  box-sizing: border-box;
}

.content-card {
  width: calc(100vw - 80px - 54px); /* 减去侧边栏宽度和左右边距(27px * 2) */
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 4px 24px 0 rgba(0,0,0,0.04);
  padding: 20px 16px 24px 16px;
  margin: 0 27px; /* 导航栏宽度的1/3 (80px / 3 ≈ 27px) */
  position: relative;
  transition: all 0.2s;
  box-sizing: border-box;
}
/* 非首页全屏内容区样式 */
.content-full {
  width: 100%;
  height: 100%;
  max-width: none;
  min-height: 0;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  padding: 0;
  margin: 0;
  box-sizing: border-box;
}
@media (max-width: 900px) {
  .content-card {
    padding: 8px 2px;
    min-height: 0;
  }
}
</style>
