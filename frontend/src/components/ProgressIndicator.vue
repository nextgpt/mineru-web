<template>
  <div class="progress-indicator" v-if="visible">
    <div class="progress-content">
      <!-- 连接状态指示器 -->
      <div class="connection-status" v-if="showConnectionStatus">
        <el-icon v-if="wsService.connected.value" class="status-icon connected">
          <SuccessFilled />
        </el-icon>
        <el-icon v-else-if="wsService.connecting.value" class="status-icon connecting">
          <Loading />
        </el-icon>
        <el-icon v-else class="status-icon disconnected">
          <WarningFilled />
        </el-icon>
        <span class="status-text">
          {{ getConnectionStatusText() }}
        </span>
      </div>

      <!-- 项目进度显示 -->
      <div class="project-progress" v-if="projectUpdate">
        <div class="progress-header">
          <span class="progress-title">{{ getStatusText(projectUpdate.status) }}</span>
          <el-button 
            v-if="showCancelButton && canCancel" 
            size="small" 
            type="danger" 
            plain
            @click="cancelTask"
          >
            取消
          </el-button>
        </div>

        <!-- 进度条 -->
        <div class="progress-bar-container" v-if="projectUpdate.progress !== undefined">
          <el-progress 
            :percentage="projectUpdate.progress" 
            :stroke-width="8"
            :show-text="false"
            :status="getProgressStatus(projectUpdate.status)"
          />
          <span class="progress-percentage">{{ projectUpdate.progress }}%</span>
        </div>

        <!-- 当前步骤 -->
        <div class="current-step" v-if="projectUpdate.current_step">
          <el-icon class="step-icon"><Clock /></el-icon>
          <span>{{ projectUpdate.current_step }}</span>
        </div>

        <!-- 消息 -->
        <div class="progress-message" v-if="projectUpdate.message">
          {{ projectUpdate.message }}
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="progress-actions" v-if="showActions">
        <el-button 
          v-if="!wsService.connected.value" 
          size="small" 
          @click="reconnect"
          :loading="wsService.connecting.value"
        >
          重新连接
        </el-button>
        <el-button 
          size="small" 
          @click="hide"
          type="text"
        >
          隐藏
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { SuccessFilled, WarningFilled, Loading, Clock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { wsService, type ProjectUpdate } from '@/services/websocket'

interface Props {
  projectId?: string
  showConnectionStatus?: boolean
  showCancelButton?: boolean
  showActions?: boolean
  autoHide?: boolean
  autoHideDelay?: number
}

const props = withDefaults(defineProps<Props>(), {
  showConnectionStatus: true,
  showCancelButton: true,
  showActions: true,
  autoHide: false,
  autoHideDelay: 5000
})

const emit = defineEmits<{
  cancel: []
  hide: []
}>()

const visible = ref(true)
const autoHideTimer = ref<number | null>(null)

const projectUpdate = computed(() => {
  if (!props.projectId) return null
  return wsService.getProjectUpdate(props.projectId)
})

const canCancel = computed(() => {
  if (!projectUpdate.value) return false
  const status = projectUpdate.value.status
  return ['analyzing', 'outlining', 'generating', 'exporting'].includes(status)
})

const getConnectionStatusText = () => {
  if (wsService.connected.value) {
    return '已连接'
  } else if (wsService.connecting.value) {
    return '连接中...'
  } else {
    return '连接断开'
  }
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    analyzing: '分析中',
    analyzed: '分析完成',
    outlining: '生成大纲中',
    outlined: '大纲生成完成',
    generating: '生成内容中',
    generated: '内容生成完成',
    exporting: '导出中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[status] || status
}

const getProgressStatus = (status: string) => {
  if (status === 'failed') return 'exception'
  if (status === 'completed') return 'success'
  return undefined
}

const cancelTask = () => {
  emit('cancel')
}

const hide = () => {
  visible.value = false
  emit('hide')
}

const reconnect = () => {
  wsService.reconnect()
}

const startAutoHide = () => {
  if (props.autoHide && !autoHideTimer.value) {
    autoHideTimer.value = window.setTimeout(() => {
      hide()
    }, props.autoHideDelay)
  }
}

const stopAutoHide = () => {
  if (autoHideTimer.value) {
    clearTimeout(autoHideTimer.value)
    autoHideTimer.value = null
  }
}

// 监听项目更新
watch(projectUpdate, (newUpdate) => {
  if (newUpdate) {
    // 如果任务完成，启动自动隐藏
    if (['completed', 'failed'].includes(newUpdate.status)) {
      startAutoHide()
    } else {
      stopAutoHide()
    }
  }
}, { deep: true })

// 订阅项目更新
onMounted(() => {
  if (props.projectId) {
    wsService.subscribe(props.projectId)
  }
})

onUnmounted(() => {
  if (props.projectId) {
    wsService.unsubscribe(props.projectId)
  }
  stopAutoHide()
})
</script>

<style scoped>
.progress-indicator {
  position: fixed;
  top: 80px;
  right: 24px;
  width: 320px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border: 1px solid #e5e7eb;
  z-index: 1000;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.progress-content {
  padding: 20px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f3f4f6;
}

.status-icon {
  font-size: 16px;
}

.status-icon.connected {
  color: #67c23a;
}

.status-icon.connecting {
  color: #409eff;
  animation: rotate 1s linear infinite;
}

.status-icon.disconnected {
  color: #f56c6c;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.status-text {
  font-size: 0.875rem;
  color: #6b7280;
}

.project-progress {
  margin-bottom: 16px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-title {
  font-weight: 600;
  color: #1f2937;
  font-size: 0.875rem;
}

.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.progress-bar-container :deep(.el-progress) {
  flex: 1;
}

.progress-percentage {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
  min-width: 40px;
  text-align: right;
}

.current-step {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 8px;
}

.step-icon {
  font-size: 14px;
  color: #409eff;
}

.progress-message {
  font-size: 0.875rem;
  color: #374151;
  background: #f9fafb;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.progress-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}

:deep(.el-progress-bar__outer) {
  background-color: #f3f4f6;
}

:deep(.el-progress-bar__inner) {
  background: linear-gradient(90deg, #409eff 0%, #67c23a 100%);
}
</style>