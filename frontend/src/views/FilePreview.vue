<template>
  <div class="tender-preview-wrapper">
    <!-- 左侧固定原文预览 -->
    <div class="preview-left-panel">
      <div class="left-panel-header">
        <el-icon><Document /></el-icon>
        <span class="panel-title">原文预览</span>
        <div class="file-info">
          <span class="file-name">{{ currentProject?.fileName || '未选择文件' }}</span>
        </div>
      </div>
      <div class="left-panel-content">
        <div v-if="loading" class="loading-container">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>正在加载文档...</span>
        </div>
        <div v-else-if="currentProject" class="document-preview">
          <template v-if="isPdf(currentProject.fileName)">
            <div v-if="fileUrl" class="pdf-preview-container">
              <!-- PDF工具栏 -->
              <div class="pdf-toolbar">
                <div class="toolbar-left">
                  <el-button-group size="small">
                    <el-button @click="previousPage" :disabled="currentPage <= 1">
                      <el-icon><ArrowLeft /></el-icon>
                    </el-button>
                    <el-button @click="nextPage" :disabled="currentPage >= totalPages">
                      <el-icon><ArrowRight /></el-icon>
                    </el-button>
                  </el-button-group>
                  <span class="page-info">第 {{ currentPage }} 页，共 {{ totalPages }} 页</span>
                </div>
                <div class="toolbar-right">
                  <el-button-group size="small">
                    <el-button @click="zoomOut" :disabled="scale <= 0.5">
                      <el-icon><ZoomOut /></el-icon>
                    </el-button>
                    <el-button @click="resetZoom">{{ Math.round(scale * 100) }}%</el-button>
                    <el-button @click="zoomIn" :disabled="scale >= 2">
                      <el-icon><ZoomIn /></el-icon>
                    </el-button>
                  </el-button-group>
                </div>
              </div>
              
              <!-- PDF内容区域 -->
              <div class="pdf-content-area">
                <div v-if="pdfLoading" class="pdf-loading">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  <span>正在加载PDF文档...</span>
                </div>
                
                <div v-else-if="pdfError" class="pdf-error">
                  <el-icon class="error-icon"><WarningFilled /></el-icon>
                  <p>PDF加载失败</p>
                  <el-button @click="retryLoadPdf" size="small">重试</el-button>
                </div>
                
                <div v-else class="pdf-pages-container" ref="pdfContainer">
                  <canvas 
                    v-for="pageNum in totalPages" 
                    :key="pageNum"
                    :ref="el => setCanvasRef(el, pageNum)"
                    :class="['pdf-page-canvas', { active: pageNum === currentPage }]"
                    :style="{ transform: `scale(${scale})` }"
                  ></canvas>
                </div>
              </div>
            </div>
          </template>
          <template v-else-if="isOffice(currentProject.fileName)">
            <div v-if="loadingOffice" class="loading-office">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>正在加载预览...</span>
            </div>
            <div v-else class="office-preview" v-html="officeContent"></div>
          </template>
          <template v-else-if="isImage(currentProject.fileName)">
            <img :src="fileUrl" class="image-preview" />
          </template>
          <template v-else-if="isText(currentProject.fileName)">
            <el-scrollbar class="text-preview">
              <pre>{{ textContent }}</pre>
            </el-scrollbar>
          </template>
          <template v-else>
            <el-empty description="暂不支持该类型文件预览" :image-size="80" />
          </template>
        </div>
        <div v-else class="no-project">
          <el-empty description="请选择一个项目进行预览" :image-size="80" />
        </div>
      </div>
    </div>

    <!-- 右侧内容区域 -->
    <div class="preview-right-panel">
      <div class="right-panel-header">
        <div class="panel-tabs">
          <div 
            v-for="tab in rightPanelTabs" 
            :key="tab.key"
            :class="['tab-item', { active: rightPanelMode === tab.key }]"
            @click="setRightPanelMode(tab.key)"
          >
            <el-icon><component :is="tab.icon" /></el-icon>
            <span>{{ tab.label }}</span>
          </div>
        </div>
      </div>
      <div class="right-panel-content">
        <!-- 标书设置界面 -->
        <div v-if="rightPanelMode === 'settings'" class="settings-panel">
          <TenderSettings 
            v-model:settings="previewSettings"
            :loading="settingsLoading"
            @start-generation="handleStartGeneration"
          />
        </div>
        
        <!-- 大纲生成界面 -->
        <div v-else-if="rightPanelMode === 'outline'" class="outline-panel">
          <div class="outline-content">
            <div v-if="outlineLoading" class="loading-container">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>正在生成大纲...</span>
            </div>
            <div v-else-if="outlineContent" class="outline-result">
              <div class="markdown-content" v-html="renderedOutline"></div>
            </div>
            <div v-else class="no-outline">
              <el-empty description="暂无大纲内容" :image-size="60" />
            </div>
          </div>
        </div>
        
        <!-- 标书内容界面 -->
        <div v-else-if="rightPanelMode === 'content'" class="content-panel">
          <div class="content-wrapper">
            <div v-if="contentLoading" class="loading-container">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>正在生成标书内容...</span>
            </div>
            <div v-else-if="proposalContent" class="content-result">
              <div class="markdown-content" v-html="renderedContent"></div>
            </div>
            <div v-else class="no-content">
              <el-empty description="暂无标书内容" :image-size="60" />
            </div>
          </div>
          <div v-if="proposalContent" class="content-actions">
            <el-button type="primary" @click="handleSaveContent">保存</el-button>
            <el-button @click="handleDownloadContent">下载</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, Setting, List, Edit, Loading, Download, ArrowLeft, ArrowRight, ZoomOut, ZoomIn, WarningFilled } from '@element-plus/icons-vue'
import * as pdfjsLib from 'pdfjs-dist'
import MarkdownIt from 'markdown-it'
import mk from 'markdown-it-katex'
import 'katex/dist/katex.min.css'
import { useProjectStore } from '@/store/project'
import { DocumentPreviewService } from '@/utils/documentPreview'
import type { TenderProject, GenerationSettings, RightPanelMode } from '@/types/tender'
import TenderSettings from '@/components/TenderSettings.vue'

// 创建带公式支持的 Markdown 渲染器
const md = MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
}).use(mk)

// 路由和状态管理
const route = useRoute()
const projectStore = useProjectStore()

// 右侧面板标签配置
const rightPanelTabs = [
  { key: 'settings', label: '标书设置', icon: Setting },
  { key: 'outline', label: '大纲预览', icon: List },
  { key: 'content', label: '标书内容', icon: Edit }
] as const


// 当前项目和状态
const currentProject = ref<TenderProject | null>(null)
const loading = ref(false)
const rightPanelMode = ref<RightPanelMode>('settings')

// 预览设置
const previewSettings = ref<GenerationSettings>({
  length: 'medium',
  quality: 'standard',
  includeImages: true,
  imageQuality: 'standard',
  includeTables: true,
  tableStyle: 'simple'
})

// 各种加载状态
const settingsLoading = ref(false)
const outlineLoading = ref(false)
const contentLoading = ref(false)

// 内容缓存
const contentCache = ref<Map<string, string>>(new Map())
const outlineContent = ref('')
const proposalContent = ref('')

// 设置右侧面板模式
const setRightPanelMode = (mode: RightPanelMode) => {
  rightPanelMode.value = mode
}


// 文件类型检测 - 使用DocumentPreviewService
const isImage = (name?: string) => name ? DocumentPreviewService.isImage(name) : false
const isText = (name?: string) => name ? DocumentPreviewService.isText(name) : false
const isWord = (name?: string) => name ? DocumentPreviewService.isWord(name) : false
const isExcel = (name?: string) => name ? DocumentPreviewService.isExcel(name) : false
const isOffice = (name?: string) => name ? DocumentPreviewService.isOffice(name) : false
const isPdf = (name?: string) => name ? DocumentPreviewService.isPdf(name) : false

// 加载项目数据
const loadProject = async () => {
  const projectId = route.params.id as string
  if (!projectId) {
    ElMessage.error('无效的项目ID')
    return
  }

  loading.value = true
  try {
    // 从项目store中获取项目数据
    await projectStore.loadProjects()
    const project = projectStore.projects.find(p => p.id === projectId)
    
    if (!project) {
      ElMessage.error('项目不存在')
      return
    }

    currentProject.value = project
    projectStore.selectProject(project)

    // 加载文件预览内容
    await loadFilePreview()
    
    // 根据项目状态设置右侧面板模式
    if (project.outline) {
      outlineContent.value = project.outline
      if (project.content) {
        proposalContent.value = project.content
        rightPanelMode.value = 'content'
      } else {
        rightPanelMode.value = 'outline'
      }
    } else {
      rightPanelMode.value = 'settings'
    }

    // 如果有保存的设置，加载它们
    if (project.settings) {
      previewSettings.value = project.settings
    }

  } catch (error) {
    console.error('Failed to load project:', error)
    ElMessage.error('加载项目失败')
  } finally {
    loading.value = false
  }
}

// 文件预览相关
const fileUrl = ref('')
const textContent = ref('')
const officeContent = ref('')
const loadingOffice = ref(false)

// 加载文件预览内容
const loadFilePreview = async () => {
  if (!currentProject.value) return

  try {
    // 检查缓存
    const cacheKey = `preview_${currentProject.value.id}`
    if (contentCache.value.has(cacheKey)) {
      const cachedData = JSON.parse(contentCache.value.get(cacheKey)!)
      fileUrl.value = cachedData.fileUrl || ''
      textContent.value = cachedData.textContent || ''
      officeContent.value = cachedData.officeContent || ''
      return
    }

    // 获取文件URL
    fileUrl.value = DocumentPreviewService.getDownloadUrl(currentProject.value.id, currentProject.value.fileName)
    
    // 根据文件类型加载相应内容
    if (isPdf(currentProject.value.fileName)) {
      // PDF文件加载文档
      await loadPdfDocument()
    } else if (isText(currentProject.value.fileName)) {
      await fetchTextContent()
    } else if (isOffice(currentProject.value.fileName)) {
      await previewOfficeFile()
    } else if (isImage(currentProject.value.fileName)) {
      // 图片文件直接使用URL
      // fileUrl.value 已经设置好了
    } else {
      // 不支持的文件类型，使用模拟内容
      if (isOffice(currentProject.value.fileName)) {
        officeContent.value = DocumentPreviewService.createMockContent(currentProject.value.fileName)
      } else if (isText(currentProject.value.fileName)) {
        textContent.value = DocumentPreviewService.createMockContent(currentProject.value.fileName)
      }
    }

    // 缓存预览内容
    const cacheData = {
      fileUrl: fileUrl.value,
      textContent: textContent.value,
      officeContent: officeContent.value
    }
    contentCache.value.set(cacheKey, JSON.stringify(cacheData))

  } catch (error) {
    console.error('Failed to load file preview:', error)
    ElMessage.error('加载文件预览失败')
    
    // 加载失败时使用模拟内容
    if (currentProject.value) {
      if (isOffice(currentProject.value.fileName)) {
        officeContent.value = DocumentPreviewService.createMockContent(currentProject.value.fileName)
      } else if (isText(currentProject.value.fileName)) {
        textContent.value = DocumentPreviewService.createMockContent(currentProject.value.fileName)
      }
    }
  }
}

// 处理开始生成大纲
const handleStartGeneration = async () => {
  if (!currentProject.value) return

  try {
    settingsLoading.value = true
    
    // 保存设置到项目
    projectStore.updateProject(currentProject.value.id, {
      settings: previewSettings.value
    })

    // 切换到大纲面板
    rightPanelMode.value = 'outline'
    outlineLoading.value = true

    // 这里应该调用大纲生成API
    // 暂时使用模拟数据
    setTimeout(() => {
      outlineContent.value = '# 技术方案大纲\n\n## 1. 项目概述\n\n## 2. 技术方案\n\n## 3. 实施计划'
      outlineLoading.value = false
      
      // 保存大纲到项目
      projectStore.updateProject(currentProject.value!.id, {
        outline: outlineContent.value,
        status: 'generating'
      })
    }, 2000)

  } catch (error) {
    console.error('Failed to start generation:', error)
    ElMessage.error('开始生成失败')
  } finally {
    settingsLoading.value = false
  }
}

// 保存内容
const handleSaveContent = async () => {
  if (!currentProject.value || !proposalContent.value) return

  try {
    projectStore.updateProject(currentProject.value.id, {
      content: proposalContent.value,
      status: 'completed'
    })
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('Failed to save content:', error)
    ElMessage.error('保存失败')
  }
}

// 下载内容
const handleDownloadContent = async () => {
  if (!proposalContent.value) return

  try {
    // 创建下载链接
    const blob = new Blob([proposalContent.value], { type: 'text/markdown' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${currentProject.value?.name || '标书'}.md`
    document.body.appendChild(link)
    link.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(link)
    
    ElMessage.success('下载成功')
  } catch (error) {
    console.error('Failed to download content:', error)
    ElMessage.error('下载失败')
  }
}



// Office文件预览
const previewOfficeFile = async () => {
  if (!currentProject.value || !fileUrl.value) return
  loadingOffice.value = true
  try {
    // 尝试从服务器获取文件内容
    const arrayBuffer = await DocumentPreviewService.fetchFileContent(fileUrl.value)
    
    if (isWord(currentProject.value.fileName)) {
      officeContent.value = await DocumentPreviewService.previewWord(arrayBuffer)
    } else if (isExcel(currentProject.value.fileName)) {
      officeContent.value = await DocumentPreviewService.previewExcel(arrayBuffer)
    }
  } catch (e) {
    console.error('预览 Office 文件失败:', e)
    ElMessage.warning('无法连接到服务器，显示模拟内容')
    // 使用模拟内容
    officeContent.value = DocumentPreviewService.createMockContent(currentProject.value.fileName)
  } finally {
    loadingOffice.value = false
  }
}

// 文本文件预览
const fetchTextContent = async () => {
  if (!fileUrl.value || !currentProject.value) return
  try {
    textContent.value = await DocumentPreviewService.fetchTextContent(fileUrl.value)
  } catch (e) {
    console.error('获取文本内容失败:', e)
    ElMessage.warning('无法连接到服务器，显示模拟内容')
    // 使用模拟内容
    textContent.value = DocumentPreviewService.createMockContent(currentProject.value.fileName)
  }
}

// PDF相关
const pdfError = ref(false)
const pdfLoading = ref(false)
const currentPage = ref(1)
const totalPages = ref(0)
const scale = ref(1.0)
const pdfDocument = ref<any>(null)
const pdfContainer = ref<HTMLElement>()
const canvasRefs = ref<Map<number, HTMLCanvasElement>>(new Map())

// 设置PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@5.2.133/build/pdf.worker.min.mjs'

const setCanvasRef = (el: any, pageNum: number) => {
  if (el && el instanceof HTMLCanvasElement) {
    canvasRefs.value.set(pageNum, el)
  }
}

const loadPdfDocument = async () => {
  if (!fileUrl.value) return
  
  try {
    pdfLoading.value = true
    pdfError.value = false
    
    const loadingTask = pdfjsLib.getDocument({
      url: fileUrl.value,
      cMapUrl: 'https://cdn.jsdelivr.net/npm/pdfjs-dist@5.2.133/cmaps/',
      cMapPacked: true,
    })
    
    pdfDocument.value = await loadingTask.promise
    totalPages.value = pdfDocument.value.numPages
    currentPage.value = 1
    
    // 等待DOM更新后渲染页面
    await nextTick()
    await renderAllPages()
    
  } catch (error) {
    console.error('PDF load failed:', error)
    pdfError.value = true
  } finally {
    pdfLoading.value = false
  }
}

const renderAllPages = async () => {
  if (!pdfDocument.value) return
  
  for (let pageNum = 1; pageNum <= totalPages.value; pageNum++) {
    await renderPage(pageNum)
  }
}

const renderPage = async (pageNum: number) => {
  if (!pdfDocument.value) return
  
  try {
    const page = await pdfDocument.value.getPage(pageNum)
    const canvas = canvasRefs.value.get(pageNum)
    
    if (!canvas) return
    
    const context = canvas.getContext('2d')
    if (!context) return
    
    const viewport = page.getViewport({ scale: 1.5 }) // 基础缩放
    
    canvas.width = viewport.width
    canvas.height = viewport.height
    canvas.style.width = viewport.width + 'px'
    canvas.style.height = viewport.height + 'px'
    
    const renderContext = {
      canvasContext: context,
      viewport: viewport
    }
    
    await page.render(renderContext).promise
    
  } catch (error) {
    console.error(`Failed to render page ${pageNum}:`, error)
  }
}

const previousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    scrollToPage(currentPage.value)
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    scrollToPage(currentPage.value)
  }
}

const scrollToPage = (pageNum: number) => {
  const canvas = canvasRefs.value.get(pageNum)
  if (canvas && pdfContainer.value) {
    canvas.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

const zoomIn = () => {
  if (scale.value < 2) {
    scale.value = Math.min(2, scale.value + 0.25)
  }
}

const zoomOut = () => {
  if (scale.value > 0.5) {
    scale.value = Math.max(0.5, scale.value - 0.25)
  }
}

const resetZoom = () => {
  scale.value = 1.0
}

const retryLoadPdf = () => {
  loadPdfDocument()
}

// 计算属性
const renderedContent = computed(() => {
  return md.render(proposalContent.value || '')
})

const renderedOutline = computed(() => {
  return md.render(outlineContent.value || '')
})

// 生命周期
onMounted(() => {
  loadProject()
})

// 监听路由变化
watch(() => route.params.id, () => {
  if (route.params.id) {
    loadProject()
  }
})
</script>

<style scoped>
.tender-preview-wrapper {
  height: 100vh;
  display: flex;
  background: #f5f7fa;
}

/* 左侧面板 */
.preview-left-panel {
  width: 50%;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.left-panel-header {
  height: 60px;
  padding: 0 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  background: #fafbfc;
}

.left-panel-header .el-icon {
  margin-right: 8px;
  color: #409eff;
  font-size: 18px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-right: 16px;
}

.file-info {
  flex: 1;
  display: flex;
  align-items: center;
}

.file-name {
  font-size: 14px;
  color: #606266;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.left-panel-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.loading-container .el-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.document-preview {
  height: 100%;
  overflow: auto;
}

.pdf-viewer {
  width: 100%;
  height: 100%;
  border: none;
}

.office-preview {
  padding: 20px;
  height: calc(100% - 40px);
  overflow: auto;
}

.loading-office {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.image-preview {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 20px auto;
}

.text-preview {
  height: 100%;
  padding: 20px;
}

.text-preview pre {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.5;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-word;
}

.no-project {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

/* 右侧面板 */
.preview-right-panel {
  width: 50%;
  background: #fff;
  display: flex;
  flex-direction: column;
}

.right-panel-header {
  height: 60px;
  border-bottom: 1px solid #e4e7ed;
  background: #fafbfc;
  display: flex;
  align-items: center;
}

.panel-tabs {
  display: flex;
  width: 100%;
}

.tab-item {
  flex: 1;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  border-bottom: 3px solid transparent;
  color: #606266;
}

.tab-item:hover {
  background: #f0f2f5;
  color: #409eff;
}

.tab-item.active {
  color: #409eff;
  border-bottom-color: #409eff;
  background: #fff;
}

.tab-item .el-icon {
  margin-right: 6px;
  font-size: 16px;
}

.right-panel-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}

/* 各个面板样式 */
.settings-panel,
.outline-panel,
.content-panel {
  height: 100%;
  overflow: auto;
}

.outline-content,
.content-wrapper {
  height: calc(100% - 60px);
  overflow: auto;
  padding: 20px;
}

.content-panel {
  display: flex;
  flex-direction: column;
}

.content-actions {
  height: 60px;
  padding: 0 20px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  background: #fafbfc;
}

.outline-result,
.content-result {
  background: #fff;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
  padding: 20px;
}

.no-outline,
.no-content {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

/* Markdown内容样式 */
.markdown-content {
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  max-width: 100%;
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
}

.markdown-content :deep(h1) {
  font-size: 24px;
  margin: 20px 0 16px 0;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
  color: #303133;
  font-weight: 600;
}

.markdown-content :deep(h2) {
  font-size: 20px;
  margin: 18px 0 14px 0;
  color: #303133;
  font-weight: 600;
}

.markdown-content :deep(h3) {
  font-size: 16px;
  margin: 16px 0 12px 0;
  color: #303133;
  font-weight: 600;
}

.markdown-content :deep(p) {
  margin: 12px 0;
  line-height: 1.6;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 24px;
  margin: 12px 0;
}

.markdown-content :deep(li) {
  margin: 6px 0;
  line-height: 1.6;
}

.markdown-content :deep(code) {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  color: #e6a23c;
}

.markdown-content :deep(pre) {
  background-color: #f5f7fa;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 16px 0;
  border: 1px solid #e4e7ed;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
  color: #303133;
}

.markdown-content :deep(blockquote) {
  margin: 16px 0;
  padding: 0 16px;
  color: #909399;
  border-left: 4px solid #e4e7ed;
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
  border: 1px solid #e4e7ed;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #e4e7ed;
  padding: 8px 12px;
  text-align: left;
}

.markdown-content :deep(th) {
  background-color: #f5f7fa;
  font-weight: 600;
}

.markdown-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  margin: 8px 0;
}

/* 文档预览样式增强 */
.office-preview :deep(.word-preview) {
  font-family: 'Microsoft YaHei', Arial, sans-serif;
  line-height: 1.6;
  color: #333;
}

.office-preview :deep(.word-preview h1) {
  font-size: 24px;
  color: #2c3e50;
  border-bottom: 2px solid #3498db;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

.office-preview :deep(.word-preview h2) {
  font-size: 20px;
  color: #34495e;
  margin-top: 25px;
  margin-bottom: 15px;
}

.office-preview :deep(.word-preview p) {
  margin-bottom: 12px;
  text-align: justify;
}

.office-preview :deep(.word-preview ul) {
  margin: 15px 0;
  padding-left: 25px;
}

.office-preview :deep(.word-preview li) {
  margin-bottom: 8px;
}

.office-preview :deep(.excel-preview) {
  font-family: 'Microsoft YaHei', Arial, sans-serif;
}

.office-preview :deep(.excel-preview .sheet-container) {
  margin-bottom: 30px;
}

.office-preview :deep(.excel-preview .sheet-title) {
  font-size: 18px;
  color: #2c3e50;
  margin-bottom: 15px;
  padding: 10px;
  background: #ecf0f1;
  border-left: 4px solid #3498db;
}

.office-preview :deep(.excel-preview table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
  font-size: 14px;
}

.office-preview :deep(.excel-preview th) {
  background-color: #34495e;
  color: white;
  padding: 12px 8px;
  text-align: left;
  font-weight: 600;
}

.office-preview :deep(.excel-preview td) {
  padding: 10px 8px;
  border-bottom: 1px solid #bdc3c7;
}

.office-preview :deep(.excel-preview tr:nth-child(even)) {
  background-color: #f8f9fa;
}

.office-preview :deep(.excel-preview tr:hover) {
  background-color: #e8f4f8;
}

/* PDF预览样式 */
.pdf-preview-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.pdf-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-info {
  font-size: 14px;
  color: #606266;
  margin-left: 8px;
}

.pdf-content-area {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.pdf-loading,
.pdf-error {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  background: #f8f9fa;
}

.pdf-loading .el-icon {
  font-size: 32px;
  color: #409eff;
}

.pdf-error .error-icon {
  font-size: 32px;
  color: #f56c6c;
}

.pdf-pages-container {
  height: 100%;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.pdf-page-canvas {
  display: block;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  transition: all 0.3s;
  transform-origin: center top;
}

.pdf-page-canvas.active {
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.3);
  border: 2px solid #409eff;
}

.pdf-page-canvas:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

/* 图片预览样式 */
.image-preview {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 20px auto;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 文本预览样式 */
.text-preview pre {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #2c3e50;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 6px;
  border-left: 4px solid #3498db;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: auto;
}

/* 加载状态样式 */
.loading-office {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #7f8c8d;
  background: #f8f9fa;
  border-radius: 8px;
  margin: 20px;
}

.loading-office .el-icon {
  font-size: 32px;
  margin-bottom: 12px;
  color: #3498db;
}

/* 空状态样式 */
.no-project,
.no-outline,
.no-content {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #7f8c8d;
  background: #f8f9fa;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .preview-left-panel,
  .preview-right-panel {
    width: 50%;
  }
}

@media (max-width: 768px) {
  .tender-preview-wrapper {
    flex-direction: column;
  }
  
  .preview-left-panel,
  .preview-right-panel {
    width: 100%;
    height: 50vh;
  }
  
  .tab-item span {
    display: none;
  }
}
</style> 