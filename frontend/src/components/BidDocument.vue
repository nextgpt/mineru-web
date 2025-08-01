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
          <el-button size="small" @click="printPreview" v-if="viewMode === 'preview'">
            打印预览
          </el-button>
          <el-button size="small" @click="saveDocument" :loading="saving">
            保存
          </el-button>
        </div>
      </div>

      <!-- 编辑模式 -->
      <div v-if="viewMode === 'edit'" class="document-editor">
        <div class="editor-toolbar">
          <el-button-group size="small">
            <el-button @click="insertText('**', '**')" title="粗体">
              <strong>B</strong>
            </el-button>
            <el-button @click="insertText('*', '*')" title="斜体">
              <em>I</em>
            </el-button>
            <el-button @click="insertText('# ', '')" title="标题">H1</el-button>
            <el-button @click="insertText('## ', '')" title="二级标题">H2</el-button>
            <el-button @click="insertText('### ', '')" title="三级标题">H3</el-button>
          </el-button-group>
          <el-button-group size="small" style="margin-left: 12px;">
            <el-button @click="insertText('- ', '')" title="无序列表">列表</el-button>
            <el-button @click="insertText('1. ', '')" title="有序列表">编号</el-button>
            <el-button @click="insertText('> ', '')" title="引用">引用</el-button>
          </el-button-group>
        </div>
        <el-input
          ref="editorTextarea"
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
      width="500px"
    >
      <div class="export-options">
        <div class="export-section">
          <h4>选择导出格式：</h4>
          <el-radio-group v-model="exportFormat" class="format-options">
            <el-radio label="pdf" class="format-option">
              <div class="format-info">
                <strong>PDF 格式</strong>
                <span>适合打印和正式提交</span>
              </div>
            </el-radio>
            <el-radio label="docx" class="format-option">
              <div class="format-info">
                <strong>Word 格式</strong>
                <span>可进一步编辑和修改</span>
              </div>
            </el-radio>
            <el-radio label="md" class="format-option">
              <div class="format-info">
                <strong>Markdown 格式</strong>
                <span>纯文本格式，便于版本控制</span>
              </div>
            </el-radio>
          </el-radio-group>
        </div>
        
        <div class="export-section">
          <h4>导出选项：</h4>
          <el-checkbox v-model="exportOptions.includeOutline">包含大纲目录</el-checkbox>
          <el-checkbox v-model="exportOptions.includePageNumbers">包含页码</el-checkbox>
          <el-checkbox v-model="exportOptions.includeWatermark">添加水印</el-checkbox>
        </div>
        
        <div class="export-section" v-if="exportOptions.includeWatermark">
          <el-form-item label="水印文字：">
            <el-input 
              v-model="exportOptions.watermarkText" 
              placeholder="请输入水印文字"
              maxlength="50"
            />
          </el-form-item>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showExportDialog = false">取消</el-button>
          <el-button type="primary" @click="handleExport" :loading="exporting">
            <el-icon><Download /></el-icon>
            导出文档
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Document, Upload, Download } from '@element-plus/icons-vue'
import { documentApi, type BidDocument } from '@/api/projects'

interface Props {
  projectId: number
  selectedOutlineId?: number
}

const props = defineProps<Props>()

const document = ref<BidDocument | null>(null)
const documents = ref<BidDocument[]>([])
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
const autoSaveTimer = ref<NodeJS.Timeout | null>(null)
const editorTextarea = ref<any>(null)

const exportOptions = ref({
  includeOutline: true,
  includePageNumbers: true,
  includeWatermark: false,
  watermarkText: '内部文档'
})

// 计算属性
const wordCount = computed(() => {
  return documentContent.value.replace(/\s/g, '').length
})

const formattedContent = computed(() => {
  // 增强的 Markdown 到 HTML 转换
  let html = documentContent.value
  
  // 标题转换
  html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>')
  
  // 粗体和斜体
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>')
  
  // 列表
  html = html.replace(/^- (.*$)/gm, '<li>$1</li>')
  html = html.replace(/^(\d+)\. (.*$)/gm, '<li>$2</li>')
  
  // 引用
  html = html.replace(/^> (.*$)/gm, '<blockquote>$1</blockquote>')
  
  // 换行
  html = html.replace(/\n/g, '<br>')
  
  // 包装列表项
  html = html.replace(/(<li>.*?<\/li>)/gs, '<ul>$1</ul>')
  html = html.replace(/<\/ul><br><ul>/g, '')
  
  // 包装引用
  html = html.replace(/(<blockquote>.*?<\/blockquote>)/gs, '<div class="quote-block">$1</div>')
  html = html.replace(/<\/div><br><div class="quote-block">/g, '<br>')
  
  return html
})

const generateFullDocument = async () => {
  try {
    generating.value = true
    generateProgress.value = 0
    progressText.value = '正在初始化生成任务...'
    
    const response = await documentApi.generateDocument(props.projectId, {
      outline_id: props.selectedOutlineId,
      regenerate: false
    })
    
    if (response.status === 'started') {
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
      
      // 轮询检查生成状态
      await pollDocumentGeneration()
    } else if (response.status === 'exists') {
      ElMessage.info('文档已存在，正在加载...')
      await loadDocuments()
    }
    
    generating.value = false
    ElMessage.success('标书生成完成')
  } catch (error: any) {
    console.error('生成标书失败:', error)
    ElMessage.error(error.response?.data?.detail || '生成标书失败')
    generating.value = false
    progressStatus.value = 'exception'
  }
}

const pollDocumentGeneration = async () => {
  const maxAttempts = 30 // 最多轮询30次
  let attempts = 0
  
  const poll = async () => {
    try {
      attempts++
      await loadDocuments()
      
      if (documents.value.length > 0) {
        // 选择最新的文档
        const latestDoc = documents.value.sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )[0]
        
        document.value = latestDoc
        documentContent.value = latestDoc.content
        return
      }
      
      if (attempts < maxAttempts) {
        setTimeout(poll, 10000) // 每10秒轮询一次
      } else {
        ElMessage.warning('文档生成时间较长，请稍后手动刷新查看')
      }
    } catch (error) {
      console.error('轮询文档状态失败:', error)
    }
  }
  
  setTimeout(poll, 10000) // 10秒后开始第一次轮询
}

const loadDocuments = async () => {
  try {
    const response = await documentApi.getDocuments(props.projectId)
    
    if (response.status === 'success' && response.documents) {
      documents.value = response.documents
      
      // 如果有指定的大纲ID，优先选择对应的文档
      if (props.selectedOutlineId) {
        const targetDoc = documents.value.find(doc => doc.outline_id === props.selectedOutlineId)
        if (targetDoc) {
          document.value = targetDoc
          documentContent.value = targetDoc.content
          return
        }
      }
      
      // 否则选择最新的文档
      if (documents.value.length > 0) {
        const latestDoc = documents.value.sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )[0]
        
        document.value = latestDoc
        documentContent.value = latestDoc.content
      }
    }
  } catch (error: any) {
    console.error('加载文档失败:', error)
    if (error.response?.status !== 404) {
      ElMessage.error('加载文档失败')
    }
  }
}

const handleContentChange = () => {
  // 标记文档已被编辑
  if (document.value && document.value.status === 'generated') {
    document.value.status = 'edited'
  }
  
  // 设置自动保存
  if (autoSaveTimer.value) {
    clearTimeout(autoSaveTimer.value)
  }
  
  autoSaveTimer.value = setTimeout(() => {
    saveDocument(true) // 自动保存
  }, 3000) // 3秒后自动保存
}

const saveDocument = async (isAutoSave = false) => {
  if (!document.value) return
  
  try {
    saving.value = true
    
    const updatedDoc = await documentApi.updateDocument(props.projectId, document.value.id, {
      content: documentContent.value,
      status: document.value.status
    })
    
    document.value = updatedDoc
    
    if (!isAutoSave) {
      ElMessage.success('文档保存成功')
    }
  } catch (error: any) {
    console.error('保存文档失败:', error)
    if (!isAutoSave) {
      ElMessage.error(error.response?.data?.detail || '保存文档失败')
    }
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
    
    // 构建导出参数
    const exportParams = new URLSearchParams({
      format: exportFormat.value,
      include_outline: exportOptions.value.includeOutline.toString(),
      include_page_numbers: exportOptions.value.includePageNumbers.toString(),
      include_watermark: exportOptions.value.includeWatermark.toString(),
    })
    
    if (exportOptions.value.includeWatermark && exportOptions.value.watermarkText) {
      exportParams.append('watermark_text', exportOptions.value.watermarkText)
    }
    
    // 调用导出API
    const response = await fetch(`/api/projects/${props.projectId}/export?${exportParams.toString()}`, {
      method: 'GET',
      headers: {
        'X-User-Id': localStorage.getItem('userId') || 'anonymous'
      }
    })
    
    if (!response.ok) {
      throw new Error('导出失败')
    }
    
    const blob = await response.blob()
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    
    // 根据格式设置文件名
    const formatExtensions = {
      pdf: 'pdf',
      docx: 'docx',
      md: 'md'
    }
    
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
    a.download = `标书文档_${timestamp}.${formatExtensions[exportFormat.value as keyof typeof formatExtensions]}`
    
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success(`文档已导出为 ${exportFormat.value.toUpperCase()} 格式`)
    showExportDialog.value = false
  } catch (error: any) {
    console.error('导出文档失败:', error)
    ElMessage.error(error.response?.data?.detail || '导出文档失败')
  } finally {
    exporting.value = false
  }
}

// 监听选中的大纲ID变化
watch(() => props.selectedOutlineId, async (newOutlineId) => {
  if (newOutlineId) {
    // 如果指定了大纲ID，尝试生成对应的文档内容
    await generateDocumentForOutline(newOutlineId)
  }
})

const generateDocumentForOutline = async (outlineId: number) => {
  try {
    // 检查是否已有对应的文档
    const existingDoc = documents.value.find(doc => doc.outline_id === outlineId)
    if (existingDoc) {
      document.value = existingDoc
      documentContent.value = existingDoc.content
      return
    }
    
    // 生成新的文档内容
    generating.value = true
    progressText.value = '正在为选中的大纲节点生成内容...'
    
    const response = await documentApi.generateDocument(props.projectId, {
      outline_id: outlineId,
      regenerate: false
    })
    
    if (response.status === 'started') {
      await pollDocumentGeneration()
    }
  } catch (error: any) {
    console.error('生成大纲文档失败:', error)
    ElMessage.error(error.response?.data?.detail || '生成文档失败')
  } finally {
    generating.value = false
  }
}

const insertText = (before: string, after: string) => {
  if (!editorTextarea.value) return
  
  const textarea = editorTextarea.value.textarea || editorTextarea.value.$refs.textarea
  if (!textarea) return
  
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selectedText = documentContent.value.substring(start, end)
  
  const newText = before + selectedText + after
  const newContent = documentContent.value.substring(0, start) + newText + documentContent.value.substring(end)
  
  documentContent.value = newContent
  
  // 设置新的光标位置
  setTimeout(() => {
    const newCursorPos = start + before.length + selectedText.length + after.length
    textarea.setSelectionRange(newCursorPos, newCursorPos)
    textarea.focus()
  }, 0)
  
  handleContentChange()
}

const printPreview = () => {
  const printWindow = window.open('', '_blank')
  if (!printWindow) return
  
  const printContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>标书文档 - 打印预览</title>
      <style>
        body {
          font-family: 'Microsoft YaHei', Arial, sans-serif;
          line-height: 1.6;
          color: #333;
          max-width: 800px;
          margin: 0 auto;
          padding: 40px 20px;
        }
        h1 {
          font-size: 24px;
          font-weight: 600;
          margin: 24px 0 16px 0;
          color: #1f2937;
          border-bottom: 2px solid #3b82f6;
          padding-bottom: 8px;
        }
        h2 {
          font-size: 20px;
          font-weight: 600;
          margin: 20px 0 12px 0;
          color: #374151;
        }
        h3 {
          font-size: 16px;
          font-weight: 600;
          margin: 16px 0 8px 0;
          color: #4b5563;
        }
        p {
          margin: 8px 0;
        }
        ul {
          margin: 8px 0;
          padding-left: 20px;
        }
        li {
          margin: 4px 0;
        }
        .quote-block {
          border-left: 4px solid #3b82f6;
          padding: 12px 16px;
          margin: 16px 0;
          background-color: #f8faff;
          border-radius: 0 4px 4px 0;
        }
        .quote-block blockquote {
          margin: 0;
          font-style: italic;
          color: #4b5563;
        }
        @media print {
          body {
            padding: 20px;
          }
        }
      </style>
    </head>
    <body>
      ${formattedContent.value}
    </body>
    </html>
  `
  
  printWindow.document.write(printContent)
  printWindow.document.close()
  
  // 等待内容加载完成后打开打印对话框
  setTimeout(() => {
    printWindow.print()
  }, 500)
}

onMounted(() => {
  loadDocuments()
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

.editor-toolbar {
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 8px;
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

.export-section {
  margin-bottom: 24px;
}

.export-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #1f2937;
  font-weight: 600;
}

.format-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.format-option {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.2s;
}

.format-option:hover {
  border-color: #3b82f6;
  background-color: #f8faff;
}

.format-option.is-checked {
  border-color: #3b82f6;
  background-color: #eff6ff;
}

.format-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-left: 8px;
}

.format-info strong {
  font-size: 14px;
  color: #1f2937;
}

.format-info span {
  font-size: 12px;
  color: #6b7280;
}

.export-section .el-checkbox {
  display: block;
  margin-bottom: 8px;
}

.quote-block {
  border-left: 4px solid #3b82f6;
  padding-left: 16px;
  margin: 16px 0;
  background-color: #f8faff;
  padding: 12px 16px;
  border-radius: 0 4px 4px 0;
}

.quote-block blockquote {
  margin: 0;
  font-style: italic;
  color: #4b5563;
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