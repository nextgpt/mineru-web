<template>
  <div class="bid-document-component">
    <div class="document-header">
      <h3 class="section-title">标书内容</h3>
      <div class="document-actions">
        <el-button 
          v-if="!document && !generating" 
          type="primary" 
          @click="generateFullDocument"
        >
          生成完整标书
        </el-button>
        <el-button 
          v-if="document" 
          @click="exportDocument"
        >
          <el-icon><Upload /></el-icon>
          导出文档
        </el-button>
      </div>
    </div>

    <!-- 生成中状态 -->
    <div v-if="generating" class="generating-state">
      <div class="generating-content">
        <el-icon class="generating-icon" size="48"><Loading /></el-icon>
        <h4 class="generating-title">正在生成标书内容...</h4>
        <p class="generating-text">AI正在基于大纲结构生成完整的标书内容，这可能需要几分钟时间。</p>
        <div class="progress-info">
          <el-progress :percentage="generateProgress" :status="progressStatus" />
          <p class="progress-text">{{ progressText }}</p>
        </div>
      </div>
    </div>

    <!-- 文档内容 -->
    <div v-else-if="document" class="document-content">
      <div class="document-toolbar">
        <div class="toolbar-left">
          <el-button-group>
            <el-button 
              :type="viewMode === 'edit' ? 'primary' : ''" 
              @click="viewMode = 'edit'"
              size="small"
            >
              编辑模式
            </el-button>
            <el-button 
              :type="viewMode === 'preview' ? 'primary' : ''" 
              @click="viewMode = 'preview'"
              size="small"
            >
              预览模式
            </el-button>
          </el-button-group>
        </div>
        <div class="toolbar-right">
          <span class="word-count">字数: {{ wordCount }}</span>
          <el-button size="small" @click="saveDocument" :loading="saving">
            保存
          </el-button>
        </div>
      </div>

      <!-- 编辑模式 -->
      <div v-if="viewMode === 'edit'" class="document-editor">
        <el-input
          v-model="documentContent"
          type="textarea"
          :rows="25"
          placeholder="标书内容将在这里显示..."
          @input="handleContentChange"
          class="editor-textarea"
        />
      </div>

      <!-- 预览模式 -->
      <div v-else class="document-preview">
        <div class="preview-content" v-html="formattedContent"></div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-icon size="48" color="#d1d5db"><Document /></el-icon>
      <h4 class="empty-title">尚未生成标书内容</h4>
      <p class="empty-text">基于标书大纲，AI将为您生成完整的标书内容。</p>
    </div>

    <!-- 导出选项对话框 -->
    <el-dialog
      v-model="showExportDialog"
      title="导出标书文档"
      width="400px"
    >
      <div class="export-options">
        <h4>选择导出格式：</h4>
        <el-radio-group v-model="exportFormat">
          <el-radio label="pdf">PDF 格式</el-radio>
          <el-radio label="docx">Word 格式</el-radio>
          <el-radio label="md">Markdown 格式</el-radio>
        </el-radio-group>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showExportDialog = false">取消</el-button>
          <el-button type="primary" @click="handleExport" :loading="exporting">
            导出
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Document, Upload } from '@element-plus/icons-vue'

interface Props {
  projectId: number
}

interface BidDocument {
  id: number
  project_id: number
  user_id: string
  title: string
  content: string
  outline_id?: number
  status: 'draft' | 'generated' | 'edited' | 'finalized'
  version: number
  created_at: string
  updated_at: string
}

const props = defineProps<Props>()

const document = ref<BidDocument | null>(null)
const generating = ref(false)
const saving = ref(false)
const exporting = ref(false)
const viewMode = ref<'edit' | 'preview'>('edit')
const documentContent = ref('')
const generateProgress = ref(0)
const progressStatus = ref<'success' | 'exception' | undefined>()
const progressText = ref('')
const showExportDialog = ref(false)
const exportFormat = ref('pdf')

// 计算属性
const wordCount = computed(() => {
  return documentContent.value.replace(/\s/g, '').length
})

const formattedContent = computed(() => {
  // 简单的 Markdown 到 HTML 转换
  return documentContent.value
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
})

const generateFullDocument = async () => {
  try {
    generating.value = true
    generateProgress.value = 0
    progressText.value = '正在初始化生成任务...'
    
    // 模拟生成进度
    const progressSteps = [
      { progress: 20, text: '正在分析大纲结构...' },
      { progress: 40, text: '正在生成项目概述...' },
      { progress: 60, text: '正在生成技术方案...' },
      { progress: 80, text: '正在生成实施计划...' },
      { progress: 100, text: '标书生成完成！' }
    ]
    
    for (const step of progressSteps) {
      await new Promise(resolve => setTimeout(resolve, 1000))
      generateProgress.value = step.progress
      progressText.value = step.text
    }
    
    // TODO: 调用后端API生成文档
    // document.value = await documentApi.generateDocument(props.projectId)
    
    // 模拟生成的文档内容
    documentContent.value = `# 智能办公系统建设项目技术方案

## 1. 项目概述

### 1.1 项目背景

随着信息技术的快速发展和数字化转型的深入推进，传统的办公模式已经无法满足现代企业高效、协同、智能化的办公需求。本项目旨在构建一套完整的智能办公系统，通过先进的技术手段提升办公效率，优化工作流程，实现办公环境的数字化升级。

### 1.2 项目目标

本项目的主要目标包括：
- 建设统一的智能办公平台，整合各类办公应用
- 实现办公流程的数字化和自动化
- 提供便捷的移动办公解决方案
- 建立完善的数据安全保障体系
- 提升整体办公效率30%以上

## 2. 技术方案

### 2.1 系统架构设计

本系统采用微服务架构设计，具备高可用、高并发、易扩展的特点。整体架构分为以下几个层次：

**前端展示层**
- Web端：基于Vue.js 3.0框架开发
- 移动端：采用React Native跨平台开发
- 桌面端：使用Electron技术栈

**API网关层**
- 统一的API入口管理
- 请求路由和负载均衡
- 安全认证和权限控制

**业务服务层**
- 用户管理服务
- 文档管理服务
- 流程审批服务
- 即时通讯服务
- 视频会议服务

**数据存储层**
- 关系型数据库：PostgreSQL
- 缓存数据库：Redis
- 文件存储：MinIO对象存储
- 搜索引擎：Elasticsearch

### 2.2 核心功能模块

**文档管理模块**
- 支持多种文档格式的在线预览和编辑
- 版本控制和协同编辑功能
- 智能分类和全文检索
- 文档安全权限管理

**流程审批模块**
- 可视化流程设计器
- 灵活的审批规则配置
- 移动端审批支持
- 审批过程全程跟踪

**即时通讯模块**
- 实时消息推送
- 群组聊天和文件共享
- 消息加密传输
- 离线消息存储

**视频会议模块**
- 高清音视频通话
- 屏幕共享和白板功能
- 会议录制和回放
- 多终端同步接入

## 3. 技术特色

### 3.1 人工智能集成

系统集成了多项AI技术，包括：
- 智能文档分析和摘要生成
- 语音转文字和智能会议纪要
- 智能日程安排和提醒
- 基于机器学习的个性化推荐

### 3.2 安全保障

采用多层次的安全防护措施：
- 数据传输加密（TLS 1.3）
- 数据存储加密（AES-256）
- 多因子身份认证
- 细粒度权限控制
- 安全审计日志

### 3.3 性能优化

通过多种技术手段保障系统性能：
- 分布式缓存策略
- 数据库读写分离
- CDN内容分发
- 异步任务处理
- 智能负载均衡

## 4. 实施计划

### 4.1 项目阶段划分

**第一阶段（1-2个月）：基础平台建设**
- 系统架构搭建
- 基础服务开发
- 数据库设计和部署

**第二阶段（3-4个月）：核心功能开发**
- 文档管理模块开发
- 流程审批模块开发
- 用户权限系统开发

**第三阶段（5-6个月）：高级功能开发**
- 即时通讯模块开发
- 视频会议模块开发
- AI功能集成

**第四阶段（7-8个月）：系统集成和测试**
- 系统集成测试
- 性能优化调试
- 安全测试验证

**第五阶段（9个月）：部署上线**
- 生产环境部署
- 用户培训和支持
- 系统稳定性监控

### 4.2 质量保证

- 建立完善的代码审查机制
- 实施自动化测试流程
- 定期进行安全漏洞扫描
- 建立持续集成和部署流程

## 5. 预期效果

通过本项目的实施，预期将达到以下效果：

- **效率提升**：整体办公效率提升30%以上
- **成本节约**：减少纸质文档使用，降低办公成本20%
- **协同增强**：跨部门协作效率提升50%
- **安全保障**：建立企业级安全防护体系
- **用户体验**：提供统一、便捷的办公体验

## 6. 总结

本技术方案基于先进的技术架构和丰富的行业经验，能够为客户提供一套完整、高效、安全的智能办公解决方案。我们承诺严格按照项目计划执行，确保项目按时、按质完成，为客户创造最大价值。`

    document.value = {
      id: 1,
      project_id: props.projectId,
      user_id: 'user123',
      title: '智能办公系统建设项目技术方案',
      content: documentContent.value,
      status: 'generated',
      version: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    
    generating.value = false
    ElMessage.success('标书生成完成')
  } catch (error) {
    console.error('生成标书失败:', error)
    ElMessage.error('生成标书失败')
    generating.value = false
    progressStatus.value = 'exception'
  }
}

const loadDocument = async () => {
  try {
    // TODO: 调用后端API获取文档
    // const doc = await documentApi.getDocument(props.projectId)
    // if (doc) {
    //   document.value = doc
    //   documentContent.value = doc.content
    // }
  } catch (error) {
    console.error('加载文档失败:', error)
  }
}

const handleContentChange = () => {
  // 标记文档已被编辑
  if (document.value && document.value.status === 'generated') {
    document.value.status = 'edited'
  }
}

const saveDocument = async () => {
  if (!document.value) return
  
  try {
    saving.value = true
    
    // TODO: 调用后端API保存文档
    // await documentApi.updateDocument(document.value.id, {
    //   content: documentContent.value
    // })
    
    document.value.content = documentContent.value
    document.value.updated_at = new Date().toISOString()
    
    ElMessage.success('文档保存成功')
  } catch (error) {
    console.error('保存文档失败:', error)
    ElMessage.error('保存文档失败')
  } finally {
    saving.value = false
  }
}

const exportDocument = () => {
  showExportDialog.value = true
}

const handleExport = async () => {
  try {
    exporting.value = true
    
    // TODO: 调用后端API导出文档
    // const blob = await documentApi.exportDocument(props.projectId, exportFormat.value)
    // const url = window.URL.createObjectURL(blob)
    // const a = document.createElement('a')
    // a.href = url
    // a.download = `标书文档.${exportFormat.value}`
    // a.click()
    // window.URL.revokeObjectURL(url)
    
    // 模拟导出
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessage.success(`文档已导出为 ${exportFormat.value.toUpperCase()} 格式`)
    showExportDialog.value = false
  } catch (error) {
    console.error('导出文档失败:', error)
    ElMessage.error('导出文档失败')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  loadDocument()
})
</script>

<style scoped>
.bid-document-component {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.document-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.document-actions {
  display: flex;
  gap: 12px;
}

.generating-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.generating-content {
  text-align: center;
  max-width: 500px;
}

.generating-icon {
  color: #3b82f6;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.generating-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 16px 0 8px 0;
}

.generating-text {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.5;
  margin: 0 0 24px 0;
}

.progress-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-text {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

.document-content {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.document-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.word-count {
  font-size: 13px;
  color: #6b7280;
}

.document-editor {
  padding: 0;
}

.editor-textarea {
  border: none;
  border-radius: 0;
}

.editor-textarea :deep(.el-textarea__inner) {
  border: none;
  border-radius: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  padding: 20px;
  resize: none;
}

.document-preview {
  padding: 20px;
  min-height: 600px;
}

.preview-content {
  font-size: 14px;
  line-height: 1.8;
  color: #1f2937;
}

.preview-content :deep(h1) {
  font-size: 24px;
  font-weight: 600;
  margin: 24px 0 16px 0;
  color: #1f2937;
}

.preview-content :deep(h2) {
  font-size: 20px;
  font-weight: 600;
  margin: 20px 0 12px 0;
  color: #374151;
}

.preview-content :deep(h3) {
  font-size: 16px;
  font-weight: 600;
  margin: 16px 0 8px 0;
  color: #4b5563;
}

.preview-content :deep(p) {
  margin: 8px 0;
}

.preview-content :deep(ul) {
  margin: 8px 0;
  padding-left: 20px;
}

.preview-content :deep(li) {
  margin: 4px 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  text-align: center;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #6b7280;
  margin: 16px 0 8px 0;
}

.empty-text {
  font-size: 14px;
  color: #9ca3af;
  line-height: 1.5;
  max-width: 400px;
  margin: 0;
}

.export-options {
  padding: 20px 0;
}

.export-options h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #1f2937;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .document-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .document-toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .toolbar-right {
    justify-content: space-between;
  }
}
</style>