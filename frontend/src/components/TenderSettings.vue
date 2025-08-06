<template>
  <div class="tender-settings">
    <div class="settings-header">
      <h3 class="settings-title">标书生成设置</h3>
      <p class="settings-description">请选择标书的篇幅和写作质量，系统将根据您的选择生成相应的技术方案大纲。</p>
    </div>

    <div class="settings-content">
      <!-- 篇幅选择 -->
      <div class="setting-group">
        <label class="setting-label">
          <el-icon><Document /></el-icon>
          篇幅选择
        </label>
        <div class="setting-options">
          <div class="length-grid">
            <div 
              v-for="option in lengthOptions" 
              :key="option.value"
              :class="['length-card', { active: localSettings.length === option.value }]"
              @click="localSettings.length = option.value"
            >
              <div class="length-title">{{ option.label }}</div>
              <div class="length-range">{{ option.range }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 写作质量选择 -->
      <div class="setting-group">
        <label class="setting-label">
          <el-icon><Star /></el-icon>
          写作质量
        </label>
        <div class="setting-options">
          <div class="quality-grid">
            <div 
              :class="['quality-card', { active: localSettings.quality === 'standard' }]"
              @click="localSettings.quality = 'standard'"
            >
              <div class="quality-icon">
                <el-icon><User /></el-icon>
              </div>
              <div class="quality-content">
                <div class="quality-title">标准写作</div>
                <div class="quality-desc">语言规范，逻辑清晰</div>
              </div>
            </div>
            <div 
              :class="['quality-card', { active: localSettings.quality === 'expert' }]"
              @click="localSettings.quality = 'expert'"
            >
              <div class="quality-icon">
                <el-icon><Medal /></el-icon>
              </div>
              <div class="quality-content">
                <div class="quality-title">专家写作</div>
                <div class="quality-desc">专业术语丰富，分析深入</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 图片设置 -->
      <div class="setting-group">
        <label class="setting-label">
          <el-icon><Picture /></el-icon>
          图片设置
        </label>
        <div class="setting-options">
          <div class="image-settings">
            <div class="setting-row">
              <span class="setting-item-label">包含图片：</span>
              <el-switch v-model="localSettings.includeImages" />
            </div>
            <div v-if="localSettings.includeImages" class="setting-row">
              <span class="setting-item-label">图片质量：</span>
              <el-select v-model="localSettings.imageQuality" style="width: 120px">
                <el-option label="标准" value="standard" />
                <el-option label="高清" value="high" />
              </el-select>
            </div>
          </div>
        </div>
      </div>

      <!-- 表格设置 -->
      <div class="setting-group">
        <label class="setting-label">
          <el-icon><Grid /></el-icon>
          表格设置
        </label>
        <div class="setting-options">
          <div class="table-settings">
            <div class="setting-row">
              <span class="setting-item-label">包含表格：</span>
              <el-switch v-model="localSettings.includeTables" />
            </div>
            <div v-if="localSettings.includeTables" class="setting-row">
              <span class="setting-item-label">表格样式：</span>
              <el-select v-model="localSettings.tableStyle" style="width: 120px">
                <el-option label="简洁" value="simple" />
                <el-option label="专业" value="professional" />
              </el-select>
            </div>
          </div>
        </div>
      </div>

      <!-- 预估信息 -->
      <div class="estimate-info">
        <div class="estimate-card">
          <div class="estimate-item">
            <span class="estimate-label">预估页数：</span>
            <span class="estimate-value">{{ estimatedPages }}</span>
          </div>
          <div class="estimate-item">
            <span class="estimate-label">生成时间：</span>
            <span class="estimate-value">{{ estimatedTime }}</span>
          </div>
          <div class="estimate-item">
            <span class="estimate-label">内容质量：</span>
            <span class="estimate-value">{{ qualityLevel }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="settings-footer">
      <el-button 
        type="primary" 
        size="large" 
        :loading="loading"
        :disabled="!canStartGeneration"
        @click="handleStartGeneration"
        class="start-button"
      >
        <el-icon v-if="!loading"><EditPen /></el-icon>
        {{ loading ? '正在准备...' : '开始生成大纲' }}
      </el-button>
      
      <div class="footer-tips">
        <el-icon><Warning /></el-icon>
        <span>生成过程需要几分钟时间，请耐心等待</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Document, Star, EditPen, Warning, Picture, Grid, User, Medal } from '@element-plus/icons-vue'
import type { GenerationSettings } from '@/types/tender'

// Props
interface Props {
  settings: GenerationSettings
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
interface Emits {
  (e: 'update:settings', settings: GenerationSettings): void
  (e: 'start-generation'): void
}

const emit = defineEmits<Emits>()

// 篇幅选项
const lengthOptions = [
  { value: 'short' as const, label: '短篇', range: '100-200页' },
  { value: 'medium' as const, label: '中篇', range: '200-600页' },
  { value: 'medium-long' as const, label: '中长篇', range: '500-800页' },
  { value: 'long' as const, label: '长篇', range: '800-1200页' },
  { value: 'extra-long' as const, label: '超长篇', range: '1200-1500页' }
]

// 本地设置状态
const localSettings = ref<GenerationSettings>({ 
  ...{
    length: 'medium',
    quality: 'standard',
    includeImages: true,
    imageQuality: 'standard',
    includeTables: true,
    tableStyle: 'simple'
  },
  ...props.settings 
})

// 监听props变化
watch(() => props.settings, (newSettings) => {
  localSettings.value = { ...newSettings }
}, { deep: true })

// 监听本地设置变化，同步到父组件
watch(localSettings, (newSettings) => {
  emit('update:settings', { ...newSettings })
}, { deep: true })

// 计算属性
const estimatedPages = computed(() => {
  const option = lengthOptions.find(opt => opt.value === localSettings.value.length)
  return option?.range || '未知'
})

const estimatedTime = computed(() => {
  const baseTimes = {
    short: '3-5分钟',
    medium: '5-8分钟',
    'medium-long': '8-12分钟',
    long: '12-15分钟',
    'extra-long': '15-20分钟'
  }
  return baseTimes[localSettings.value.length] || '未知'
})

const qualityLevel = computed(() => {
  return localSettings.value.quality === 'expert' ? '专业级' : '标准级'
})

const canStartGeneration = computed(() => {
  return localSettings.value.length && localSettings.value.quality && !props.loading
})

// 方法
const handleStartGeneration = () => {
  if (canStartGeneration.value) {
    emit('start-generation')
  }
}
</script>

<style scoped>
.tender-settings {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px;
  background: #fff;
}

.settings-header {
  margin-bottom: 32px;
}

.settings-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
}

.settings-description {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

.settings-content {
  flex: 1;
  overflow-y: auto;
}

.setting-group {
  margin-bottom: 32px;
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafbfc;
}

.setting-label {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.setting-label .el-icon {
  margin-right: 8px;
  color: #409eff;
  font-size: 18px;
}

.setting-options {
  margin-bottom: 12px;
}

.length-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.length-card {
  padding: 16px 12px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #fff;
}

.length-card:hover {
  border-color: #409eff;
  background: #f0f4ff;
}

.length-card.active {
  border-color: #409eff;
  background: #409eff;
  color: #fff;
}

.length-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
}

.length-range {
  font-size: 12px;
  opacity: 0.8;
}

.quality-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.quality-card {
  padding: 16px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background: #fff;
  display: flex;
  align-items: center;
  gap: 12px;
}

.quality-card:hover {
  border-color: #409eff;
  background: #f0f4ff;
}

.quality-card.active {
  border-color: #409eff;
  background: #409eff;
  color: #fff;
}

.quality-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.quality-content {
  flex: 1;
}

.quality-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
}

.quality-desc {
  font-size: 12px;
  opacity: 0.8;
}

.image-settings,
.table-settings {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.setting-item-label {
  font-size: 14px;
  color: #606266;
}

.estimate-info {
  margin-top: 24px;
}

.estimate-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  color: #fff;
}

.estimate-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.estimate-item:last-child {
  margin-bottom: 0;
}

.estimate-label {
  font-size: 14px;
  opacity: 0.9;
}

.estimate-value {
  font-size: 14px;
  font-weight: 600;
}

.settings-footer {
  margin-top: 32px;
  text-align: center;
}

.start-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  margin-bottom: 16px;
}

.start-button .el-icon {
  margin-right: 8px;
  font-size: 18px;
}

.footer-tips {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #909399;
}

.footer-tips .el-icon {
  margin-right: 6px;
  color: #e6a23c;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .tender-settings {
    padding: 16px;
  }
  
  .setting-group {
    padding: 16px;
    margin-bottom: 24px;
  }
  
  .length-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .quality-grid {
    grid-template-columns: 1fr;
  }
  
  .estimate-card {
    padding: 16px;
  }
}
</style>