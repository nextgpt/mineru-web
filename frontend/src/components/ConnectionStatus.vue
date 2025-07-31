<template>
  <div class="connection-status" v-if="showStatus">
    <div class="status-indicator" :class="statusClass">
      <el-icon class="status-icon">
        <component :is="statusIcon" />
      </el-icon>
      <span class="status-text">{{ statusText }}</span>
      <el-button 
        v-if="!wsService.connected.value && !wsService.connecting.value"
        size="small"
        type="primary"
        plain
        @click="reconnect"
      >
        重连
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { SuccessFilled, WarningFilled, Loading } from '@element-plus/icons-vue'
import { wsService } from '@/services/websocket'

interface Props {
  showWhenConnected?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showWhenConnected: false
})

const showStatus = computed(() => {
  return !wsService.connected.value || props.showWhenConnected
})

const statusClass = computed(() => {
  if (wsService.connected.value) return 'connected'
  if (wsService.connecting.value) return 'connecting'
  return 'disconnected'
})

const statusIcon = computed(() => {
  if (wsService.connected.value) return SuccessFilled
  if (wsService.connecting.value) return Loading
  return WarningFilled
})

const statusText = computed(() => {
  if (wsService.connected.value) return '实时连接已建立'
  if (wsService.connecting.value) return '正在连接...'
  return '连接断开'
})

const reconnect = () => {
  wsService.reconnect()
}
</script>

<style scoped>
.connection-status {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 999;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  font-size: 0.875rem;
  transition: all 0.3s ease;
}

.status-indicator.connected {
  border-color: #67c23a;
  background: #f0f9ff;
}

.status-indicator.connecting {
  border-color: #409eff;
  background: #f0f4ff;
}

.status-indicator.disconnected {
  border-color: #f56c6c;
  background: #fef2f2;
}

.status-icon {
  font-size: 16px;
}

.connected .status-icon {
  color: #67c23a;
}

.connecting .status-icon {
  color: #409eff;
  animation: rotate 1s linear infinite;
}

.disconnected .status-icon {
  color: #f56c6c;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.status-text {
  color: #374151;
  font-weight: 500;
}
</style>