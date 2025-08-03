<template>
  <div class="settings-page">
    <!-- 页面标题区域 - 与系统logo平行对齐 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">系统设置</h1>
        <p class="page-subtitle">配置您的应用偏好设置</p>
      </div>
    </div>

    <div class="settings-content">
      <div class="settings-section">
        <h3 class="section-title">用户信息</h3>
        <div class="setting-item">
          <label class="setting-label">用户名</label>
          <el-input
            v-model="userSettings.name"
            placeholder="请输入用户名"
            style="width: 300px"
          />
        </div>
        <div class="setting-item">
          <label class="setting-label">用户ID</label>
          <el-input
            :value="userSettings.id"
            disabled
            style="width: 300px"
          />
        </div>
      </div>

      <div class="settings-section">
        <h3 class="section-title">应用设置</h3>
        <div class="setting-item">
          <label class="setting-label">主题模式</label>
          <el-select v-model="appSettings.theme" style="width: 300px">
            <el-option label="浅色模式" value="light" />
            <el-option label="深色模式" value="dark" />
            <el-option label="跟随系统" value="auto" />
          </el-select>
        </div>
        <div class="setting-item">
          <label class="setting-label">语言设置</label>
          <el-select v-model="appSettings.language" style="width: 300px">
            <el-option label="简体中文" value="zh-CN" />
            <el-option label="English" value="en-US" />
          </el-select>
        </div>
      </div>

      <div class="settings-section">
        <h3 class="section-title">AI 设置</h3>
        <div class="setting-item">
          <label class="setting-label">AI 模型</label>
          <el-select v-model="aiSettings.model" style="width: 300px">
            <el-option label="GPT-4" value="gpt-4" />
            <el-option label="GPT-3.5 Turbo" value="gpt-3.5-turbo" />
            <el-option label="Claude-3" value="claude-3" />
          </el-select>
        </div>
        <div class="setting-item">
          <label class="setting-label">生成质量</label>
          <el-select v-model="aiSettings.quality" style="width: 300px">
            <el-option label="高质量（较慢）" value="high" />
            <el-option label="标准质量" value="standard" />
            <el-option label="快速生成" value="fast" />
          </el-select>
        </div>
      </div>

      <div class="settings-actions">
        <el-button @click="resetSettings">重置设置</el-button>
        <el-button type="primary" @click="saveSettings" :loading="saving">
          保存设置
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getUserInfo, setUserInfo } from '@/utils/user'

// 响应式数据
const saving = ref(false)

const userSettings = reactive({
  id: '',
  name: ''
})

const appSettings = reactive({
  theme: 'light',
  language: 'zh-CN'
})

const aiSettings = reactive({
  model: 'gpt-4',
  quality: 'standard'
})

// 方法
const loadSettings = () => {
  // 加载用户信息
  const userInfo = getUserInfo()
  userSettings.id = userInfo.id
  userSettings.name = userInfo.name

  // 加载应用设置
  const savedAppSettings = localStorage.getItem('appSettings')
  if (savedAppSettings) {
    const parsed = JSON.parse(savedAppSettings)
    Object.assign(appSettings, parsed)
  }

  // 加载AI设置
  const savedAiSettings = localStorage.getItem('aiSettings')
  if (savedAiSettings) {
    const parsed = JSON.parse(savedAiSettings)
    Object.assign(aiSettings, parsed)
  }
}

const saveSettings = async () => {
  try {
    saving.value = true

    // 保存用户信息
    setUserInfo({ name: userSettings.name })

    // 保存应用设置
    localStorage.setItem('appSettings', JSON.stringify(appSettings))

    // 保存AI设置
    localStorage.setItem('aiSettings', JSON.stringify(aiSettings))

    ElMessage.success('设置保存成功')
  } catch (error) {
    console.error('保存设置失败:', error)
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

const resetSettings = () => {
  // 重置应用设置
  appSettings.theme = 'light'
  appSettings.language = 'zh-CN'

  // 重置AI设置
  aiSettings.model = 'gpt-4'
  aiSettings.quality = 'standard'

  ElMessage.info('设置已重置')
}

// 生命周期
onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-page {
  padding: 0 27px; /* 与导航栏间距保持一致 */
  background: #f7f8fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 40px;
  padding: 0;
  height: 64px; /* 与系统logo区域高度一致 */
  border-bottom: 1px solid #e5e7eb;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.page-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.settings-section {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 24px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid #f3f4f6;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.setting-item:last-child {
  margin-bottom: 0;
}

.setting-label {
  font-size: 15px;
  font-weight: 500;
  color: #374151;
  min-width: 120px;
}

.settings-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 24px;
  background: #f9fafb;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
}

.settings-actions .el-button {
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.settings-actions .el-button--primary {
  background: linear-gradient(45deg, #6366f1, #8b5cf6);
  border: none;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.settings-actions .el-button--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
}

.settings-actions .el-button:not(.el-button--primary) {
  background: #fff;
  border: 1px solid #d1d5db;
  color: #374151;
}

.settings-actions .el-button:not(.el-button--primary):hover {
  background: #f9fafb;
  border-color: #9ca3af;
  transform: translateY(-2px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .settings-page {
    padding: 20px;
  }
  
  .page-title {
    font-size: 28px;
  }
  
  .settings-section {
    padding: 20px;
  }
  
  .setting-item {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .setting-label {
    min-width: auto;
    margin-bottom: 8px;
  }
  
  .setting-item .el-input,
  .setting-item .el-select {
    width: 100% !important;
  }
  
  .settings-actions {
    flex-direction: column;
  }
  
  .settings-actions .el-button {
    width: 100%;
  }
}
</style>