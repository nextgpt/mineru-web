<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { Document } from '@element-plus/icons-vue'
import Navigation from './components/Navigation.vue'

const route = useRoute()

// 当前时间
const currentTime = ref('')
const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', { 
    hour12: false,
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 定时更新时间
let timeInterval: number
onMounted(() => {
  updateTime()
  timeInterval = window.setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<template>
  <div class="mineru-layout">
    <!-- 导航组件 -->
    <Navigation />

    <!-- 主内容区 -->
    <div class="main-area">
      <template v-if="route.name === 'FilePreview'">
        <router-view />
      </template>
      <template v-else>
        <!-- 顶部状态栏 -->
        <div class="top-status-bar">
          <div class="system-logo">
            <el-icon class="logo-icon"><Document /></el-icon>
            <span class="logo-text">智能标书生成</span>
          </div>
          <div class="status-info">
            <span class="user-info">用户: 管理员</span>
            <span class="time-info">{{ currentTime }}</span>
          </div>
        </div>

        <!-- 主内容面板 -->
        <div class="main-content-panel">
          <!-- 网格背景 -->
          <div class="grid-background"></div>
          
          <!-- 内容区域 -->
          <div class="content-wrapper">
            <router-view />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.mineru-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: #f5f7fa;
  box-sizing: border-box;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  box-sizing: border-box;
  height: 100vh;
}

/* 顶部状态栏 */
.top-status-bar {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

.system-logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon {
  font-size: 24px;
  color: #409eff;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 24px;
  font-size: 14px;
  color: #606266;
}

.user-info, .time-info {
  padding: 4px 12px;
  background: #f0f2f5;
  border-radius: 16px;
}

/* 主内容面板 */
.main-content-panel {
  flex: 1;
  position: relative;
  overflow: hidden;
}

/* 网格背景 */
.grid-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(64, 158, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(64, 158, 255, 0.05) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
}

/* 内容包装器 */
.content-wrapper {
  position: relative;
  z-index: 1;
  height: 100%;
  overflow-y: auto;
  padding: 0;
  box-sizing: border-box;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .top-status-bar {
    padding: 0 16px;
  }
  
  .system-logo .logo-text {
    display: none;
  }
  
  .status-info {
    gap: 12px;
    font-size: 12px;
  }
  
  .projects-content {
    padding-left: 16px;
    padding-right: 16px;
  }
}
</style>
