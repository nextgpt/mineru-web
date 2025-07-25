<template>
  <div class="preview-wrapper">
    <div class="preview-sidebar" v-show="!sidebarCollapsed">
      <div class="sidebar-title">
        <el-icon style="margin-right: 6px;"><FolderOpened /></el-icon> 文件列表
      </div>
      <el-input v-model="fileSearch" placeholder="搜索文件" size="small" class="sidebar-search" clearable />
      <el-scrollbar class="sidebar-list">
        <div v-for="file in filteredFiles" :key="file.id" :class="['sidebar-file', currentFile && file.id === currentFile.id ? 'active' : '']" @click="selectFile(file)">
          <el-icon class="sidebar-file-icon"><i class="el-icon-document" /></el-icon>
          <span class="sidebar-file-name">{{ file.filename }}</span>
        </div>
      </el-scrollbar>
      <div class="sidebar-pagination-container">
        <el-pagination
          v-model:current-page="sidebarPage"
          v-model:page-size="sidebarPageSize"
          :total="sidebarTotal"
          :page-sizes="[1, 10, 20, 50]"
          layout="sizes, prev, pager, next"
          size="small"
          class="sidebar-pagination"
        />
      </div>
    </div>
    <div class="preview-main-area">
      <div class="preview-header">
        <el-icon class="sidebar-toggle-btn" @click="sidebarCollapsed = !sidebarCollapsed" :title="sidebarCollapsed ? '展开文件列表' : '收起文件列表'">
          <component :is="sidebarCollapsed ? Menu : Back" />
        </el-icon>
        <span class="file-title">{{ currentFile?.filename }}</span>
        <div class="view-toggle-group">
          <el-button :type="viewMode === 'origin' ? 'primary' : 'default'" size="small" @click="handleViewMode('origin')">原文件</el-button>
          <el-button :type="viewMode === 'markdown' ? 'primary' : 'default'" size="small" @click="handleViewMode('markdown')">Markdown</el-button>
        </div>
        <el-dropdown class="download-btn" @command="handleExport">
          <el-button type="primary" size="small">
            <el-icon><i class="el-icon-download" /></el-icon> 下载 <el-icon><i class="el-icon-arrow-down" /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-for="(name, format) in ExportFormatNames" 
                              :key="format" 
                              :command="format">
                {{ name }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      <div class="preview-content">
        <div v-if="viewMode !== 'markdown'" class="preview-left" :class="{ 'full-width': viewMode === 'origin' }">
          <div class="left-content">
            <template v-if="showOrigin && currentFile">
              <template v-if="isPdf(currentFile.filename)">
                <div style="text-align:center;">
                  <iframe 
                    v-if="fileUrl" 
                    :src="fileUrl" 
                    style="width: 100%; height: calc(100vh - 20px); border: none;"
                    ref="pdfFrame"
                    @load="handlePdfLoad"
                  ></iframe>
                </div>
              </template>
              <template v-else-if="isOffice(currentFile.filename)">
                <div v-if="loadingOffice" class="loading-office">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  <span>正在加载预览...</span>
                </div>
                <div v-else class="office-preview" v-html="officeContent"></div>
              </template>
              <template v-else-if="isImage(currentFile.filename)">
                <img :src="fileUrl" style="max-width:100%;" />
              </template>
              <template v-else-if="isText(currentFile.filename)">
                <el-scrollbar><pre>{{ textContent }}</pre></el-scrollbar>
              </template>
              <template v-else>
                <el-empty description="暂不支持该类型文件预览" :image-size="80" />
              </template>
            </template>
          </div>
        </div>
        <div v-if="viewMode !== 'origin'" class="preview-right" :class="{ 'full-width': viewMode === 'markdown' }">
          <div class="right-content">
            <div class="parsed-content-wrapper">
              <div class="markdown-content" v-html="renderedContent"></div>
              <div v-if="loading" class="loading-more">加载中...</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { FolderOpened, Menu, Back, Loading } from '@element-plus/icons-vue'
import axios from 'axios'
// import { marked } from 'marked'
import MarkdownIt from 'markdown-it'
import mk from 'markdown-it-katex'
import 'katex/dist/katex.min.css'
import mammoth from 'mammoth'
import * as XLSX from 'xlsx'
import { getUserId } from '@/utils/user'


// 创建带公式支持的 Markdown 渲染器
const md = MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
}).use(mk)

interface FileItem {
  id: string
  filename: string
  size: number
  uploadTime: string
  status: string
}


// 折叠侧边栏
const sidebarCollapsed = ref(false)

// 模拟所有文件
const allFiles = ref<FileItem[]>([])
const sidebarPage = ref(1)
const sidebarPageSize = ref(10)
const sidebarTotal = ref(0)
const fileSearch = ref('')

const fetchSidebarFiles = async () => {
  try {
    const res = await axios.get('/api/files', {
      params: {
        page: sidebarPage.value,
        page_size: sidebarPageSize.value,
        search: fileSearch.value
      },
      headers: { 'X-User-Id': getUserId() }
    })
    allFiles.value = res.data.files
    sidebarTotal.value = res.data.total
    // 自动选中第一个文件
    if (allFiles.value.length > 0 && (!currentFile.value || !allFiles.value.find(f => f.id === currentFile.value.id))) {
      selectFile(allFiles.value[0])
    }
  } catch (e) {
    ElMessage.error('获取文件列表失败')
    allFiles.value = []
    sidebarTotal.value = 0
  }
}

watch([sidebarPage, sidebarPageSize, fileSearch], fetchSidebarFiles)
onMounted(() => {
  fetchSidebarFiles()
})

const filteredFiles = computed(() => allFiles.value)

const currentFile = ref<FileItem>(allFiles.value[0])
const selectFile = (file: FileItem) => {
  currentFile.value = file
  // 重置页码
  page.value = 1
  // 重新获取解析内容
  if (viewMode.value !== 'origin') {
    fetchParsedContent()
  }
}

// 内容区切换
const showOrigin = ref(true)


const isImage = (name?: string) => name ? /\.(png|jpe?g|gif|bmp|webp)$/i.test(name) : false
const isText = (name?: string) => name ? /\.(txt|md|json|log)$/i.test(name) : false
const isWord = (name?: string) => name ? /\.(doc|docx)$/i.test(name) : false
const isExcel = (name?: string) => name ? /\.(xls|xlsx)$/i.test(name) : false
const isOffice = (name?: string) => name ? /\.(doc|docx|xls|xlsx)$/i.test(name) : false



const page = ref(1)
const parsedContent = ref('')

const loading = ref(false)

const hasMore = ref(true)

const fetchParsedContent = async () => {
  if (!currentFile.value) return
  loading.value = true
  try {
    const res = await axios.get(`/api/files/${currentFile.value.id}/parsed_content`, {
      headers: { 'X-User-Id': getUserId() }
    })
    // 直接使用返回的内容
    parsedContent.value = res.data || ''
  } catch (e) {
    console.error('Failed to fetch content:', e)
    ElMessage.error('获取解析内容失败')
    parsedContent.value = ''
  } finally {
    loading.value = false
  }
}

const viewMode = ref<'both' | 'origin' | 'markdown'>('both')

const handleViewMode = (mode: 'origin' | 'markdown') => {
  if (viewMode.value === mode) {
    viewMode.value = 'both'
  } else {
    viewMode.value = mode
  }
}

watch(viewMode, (newMode) => {
  if (newMode !== 'origin') {
    fetchParsedContent()
  }
})

// 导出格式类型
const ExportFormats = {
  MARKDOWN: 'markdown',
  MARKDOWN_PAGE: 'markdown_page'
} as const

type ExportFormat = typeof ExportFormats[keyof typeof ExportFormats]

// 导出格式显示名称
const ExportFormatNames: Record<ExportFormat, string> = {
  [ExportFormats.MARKDOWN]: 'Markdown',
  [ExportFormats.MARKDOWN_PAGE]: 'Markdown带页码'
}

const handleExport = async (format: ExportFormat) => {
  if (!currentFile.value) return
  
  try {
    // 发起导出请求
    const res = await axios.get(`/api/files/${currentFile.value.id}/export`, {
      params: { format },
      headers: { 'X-User-Id': getUserId() }
    })
    
    if (res.data.status === 'success') {
      // 使用 fetch 下载文件
      const response = await fetch(res.data.download_url)
      const blob = await response.blob()
      
      // 创建一个 Blob URL
      const url = window.URL.createObjectURL(blob)
      
      // 创建一个隐藏的 a 标签来下载文件
      const link = document.createElement('a')
      link.href = url
      link.download = res.data.filename  // 使用后端返回的文件名
      document.body.appendChild(link)
      link.click()
      
      // 清理
      window.URL.revokeObjectURL(url)
      document.body.removeChild(link)
      
      ElMessage.success(`导出${ExportFormatNames[format]}成功`)
    } else {
      ElMessage.error(`导出${ExportFormatNames[format]}失败`)
    }
  } catch (e) {
    console.error('导出失败:', e)
    ElMessage.error(`导出${ExportFormatNames[format]}失败`)
  }
}



const fileUrl = ref('')
const textContent = ref('')
const officeContent = ref('')
const loadingOffice = ref(false)
const fetchFileUrl = async () => {
  if (!currentFile.value) return
  try {
    const res = await axios.get(`/api/files/${currentFile.value.id}/download_url`, {
      headers: { 'X-User-Id': getUserId() }
    })
    fileUrl.value = res.data.url
  } catch (e) {
    fileUrl.value = ''
    textContent.value = ''
    officeContent.value = ''
  }
}

const previewOfficeFile = async () => {
  if (!currentFile.value || !fileUrl.value) return
  loadingOffice.value = true
  try {
    const response = await fetch(fileUrl.value)
    const blob = await response.blob()
    
    if (isWord(currentFile.value.filename)) {
      const arrayBuffer = await blob.arrayBuffer()
      const result = await mammoth.convertToHtml({ arrayBuffer })
      officeContent.value = result.value
    } else if (isExcel(currentFile.value.filename)) {
      const arrayBuffer = await blob.arrayBuffer()
      const workbook = XLSX.read(arrayBuffer, { type: 'array' })
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
      const html = XLSX.utils.sheet_to_html(firstSheet)
      officeContent.value = html
    }
  } catch (e) {
    console.error('预览 Office 文件失败:', e)
    ElMessage.error('预览 Office 文件失败')
    officeContent.value = ''
  } finally {
    loadingOffice.value = false
  }
}

const fetchTextContent = async () => {
  if (!fileUrl.value) return
  try {
    const res = await axios.get(fileUrl.value)
    textContent.value = res.data
  } catch (e) {
    textContent.value = ''
  }
}

// 监听文件变化
watch(currentFile, async (newFile) => {
  if (!newFile) return
  
  // 清除之前的内容
  fileUrl.value = ''
  textContent.value = ''
  officeContent.value = ''
  
  // 获取新的文件URL
  await fetchFileUrl()
  
  // 根据文件类型触发相应的预览
  if (isText(newFile.filename)) {
    await fetchTextContent()
  } else if (isOffice(newFile.filename)) {
    await previewOfficeFile()
  }
})

const isPdf = (name?: string) => name ? /\.pdf$/i.test(name) : false

const pdfFrame = ref<HTMLIFrameElement | null>(null)
const currentPdfPage = ref(1)

const handlePdfLoad = () => {
  if (!pdfFrame.value) return
  pdfFrame.value.contentWindow?.addEventListener('scroll', handlePdfScroll)
}

const handlePdfScroll = async () => {
  if (!pdfFrame.value) return
  
  const iframe = pdfFrame.value
  const scrollTop = iframe.contentWindow?.scrollY || 0
  const pageHeight = iframe.contentWindow?.innerHeight || 0
  
  const newPage = Math.floor(scrollTop / pageHeight) + 1
  
  if (newPage !== currentPdfPage.value) {
    currentPdfPage.value = newPage
    await loadMarkdownByPage()
  }
}

const loadMarkdownByPage = async () => {
  if (!currentFile.value || loading.value) return
  
  loading.value = true
  try {
    const res = await axios.get(`/api/files/${currentFile.value.id}/parsed_content`, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    // 直接使用返回的内容
    parsedContent.value = res.data || ''
    hasMore.value = false // 由于现在是一次性返回所有内容，不需要分页加载
  } catch (e) {
    console.error('Failed to load markdown content:', e)
    ElMessage.error('加载内容失败')
  } finally {
    loading.value = false
  }
}

// const renderedContent = computed(() => {
//   return marked(parsedContent.value || '')
// })
const renderedContent = computed(() => {
  return md.render(parsedContent.value || '')
})
</script>

<style scoped>
.preview-wrapper {
  height: 100vh;
  padding: 0 0;
  box-sizing: border-box;
  background: #f7f8fa;
  display: flex;
  flex-direction: row;
}
.preview-sidebar {
  width: 220px;
  background: #fff;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  padding: 12px 0 0 0;
  box-sizing: border-box;
  height: 100vh;
}
.sidebar-title {
  font-size: 1.05rem;
  font-weight: 600;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  padding-left: 16px;
}
.sidebar-search {
  margin: 0 12px 6px 12px;
  width: calc(100% - 24px);
  box-sizing: border-box;
}
.sidebar-list {
  flex: 1 1 0;
  max-height: unset;
  min-height: 40px;
  overflow-y: auto;
  margin: 0 12px 6px 12px;
}
.sidebar-file {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}
.sidebar-file.active, .sidebar-file:hover {
  background: #e6f0ff;
}
.sidebar-file-icon {
  margin-right: 6px;
  color: #409eff;
}
.sidebar-file-name {
  font-size: 0.98rem;
}
.sidebar-pagination-container {
  width: 100%;
  padding: 8px 0 10px 0;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  margin-top: auto;
}
.sidebar-pagination {
  text-align: center;
}
.preview-main-area {
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100vh;
}
.preview-header {
  display: flex;
  align-items: center;
  position: relative;
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  padding: 0 0;
}
.file-title {
  margin-left: 0;
  margin-right: 18px;
  font-size: 1.08rem;
  font-weight: 600;
}
.view-toggle-group {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  gap: 8px;
}
.download-btn {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
}
.preview-content {
  height: calc(100% - 65px);
  display: flex;
  padding: 5px 0;
  box-sizing: border-box;
  gap: 3px;
}
.preview-left, .preview-right {
  height: 100%;
  border: 1px solid #4caf50;
  display: flex;
  flex-direction: column;
  background: #fff;
  transition: width 0.3s ease;
}
.preview-left {
  width: 50%;
}
.preview-right {
  width: 50%;
  margin-left: 3px;
  border: 1px solid #ffeb3b;
}
.full-width {
  width: 100% !important;
  margin-left: 0 !important;
}
.left-content {
  flex: 1 1 0;
  overflow: auto;
  padding: 8px;
}
.right-content {
  flex: 1;
  height: 100%;
  position: relative;
  overflow: auto;
}
.origin-img {
  max-width: 100%;
  max-height: 70vh;
  border-radius: 0;
  box-shadow: none;
  transition: transform 0.2s;
}
.origin-text-scroll, .parsed-content-scroll {
  max-height: 70vh;
  width: 100%;
  overflow-x: auto;
}
.origin-text, .parsed-content {
  font-size: 1rem;
  color: #333;
  white-space: pre-wrap;
  padding: 0;
  background: transparent;
  border-radius: 0;
}
.sidebar-toggle-btn {
  cursor: pointer;
  font-size: 1.2em;
  margin-right: 10px;
  color: #b1b3b8;
  transition: color 0.2s;
  vertical-align: middle;
}
.sidebar-toggle-btn:hover {
  color: #409eff;
}
.compare-content {
  display: flex;
  gap: 10px;
}
.compare-origin, .compare-parsed {
  flex: 1;
}
.compare-title {
  font-size: 1.05rem;
  font-weight: 600;
  margin-bottom: 6px;
}
.loading-more, .no-more {
  text-align: center;
  padding: 10px;
  color: #909399;
  font-size: 14px;
}
.parsed-content-scroll {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: #909399 #f4f4f5;
}
.parsed-content-scroll::-webkit-scrollbar {
  width: 6px;
}
.parsed-content-scroll::-webkit-scrollbar-track {
  background: #f4f4f5;
}
.parsed-content-scroll::-webkit-scrollbar-thumb {
  background-color: #909399;
  border-radius: 3px;
}
.parsed-content-wrapper {
  padding: 16px;
  max-width: 100%;
  box-sizing: border-box;
}
.markdown-content {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
  max-width: 100%;
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
}
.markdown-content :deep(h1) {
  font-size: 2em;
  margin: 0.67em 0;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
  word-break: break-word;
}
.markdown-content :deep(h2) {
  font-size: 1.5em;
  margin: 0.83em 0;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
  word-break: break-word;
}
.markdown-content :deep(h3) {
  font-size: 1.25em;
  margin: 1em 0;
  word-break: break-word;
}
.markdown-content :deep(p) {
  margin: 1em 0;
  word-break: break-word;
}
.markdown-content :deep(ul), 
.markdown-content :deep(ol) {
  padding-left: 2em;
  margin: 1em 0;
}
.markdown-content :deep(li) {
  margin: 0.5em 0;
  word-break: break-word;
}
.markdown-content :deep(code) {
  background-color: #f6f8fa;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: monospace;
  word-break: break-all;
}
.markdown-content :deep(pre) {
  background-color: #f6f8fa;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  max-width: 100%;
}
.markdown-content :deep(pre code) {
  white-space: pre;
  word-break: normal;
  overflow-wrap: normal;
}
.markdown-content :deep(blockquote) {
  margin: 1em 0;
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
}
.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
  max-width: 100%;
  overflow-x: auto;
  display: block;
}
.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #dfe2e5;
  padding: 6px 13px;
  word-break: break-word;
}
.markdown-content :deep(th) {
  background-color: #f6f8fa;
}
.markdown-content :deep(img) {
  max-width: 100%;
  height: auto;
}
</style>

<style>
.preview-root .content-card {
  padding: 0 !important;
}
</style> 