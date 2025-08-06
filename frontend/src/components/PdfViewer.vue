<template>
  <div class="pdf-viewer-container">
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>正在加载PDF文档...</span>
    </div>
    
    <div v-else-if="error" class="error-container">
      <el-icon><WarningFilled /></el-icon>
      <span>{{ error }}</span>
      <el-button @click="retry" size="small" type="primary">重试</el-button>
    </div>
    
    <div v-else class="pdf-content">
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
          
          <span class="page-info">
            第 {{ currentPage }} 页，共 {{ totalPages }} 页
          </span>
        </div>
        
        <div class="toolbar-right">
          <el-button-group size="small">
            <el-button @click="zoomOut" :disabled="scale <= 0.5">
              <el-icon><ZoomOut /></el-icon>
            </el-button>
            <el-button @click="resetZoom">
              {{ Math.round(scale * 100) }}%
            </el-button>
            <el-button @click="zoomIn" :disabled="scale >= 3">
              <el-icon><ZoomIn /></el-icon>
            </el-button>
          </el-button-group>
        </div>
      </div>
      
      <!-- PDF页面容器 -->
      <div class="pdf-pages" ref="pagesContainer">
        <div 
          v-for="pageNum in totalPages" 
          :key="pageNum"
          :class="['pdf-page', { active: pageNum === currentPage }]"
          :ref="el => setPageRef(el, pageNum)"
        >
          <canvas 
            :ref="el => setCanvasRef(el, pageNum)"
            class="pdf-canvas"
          ></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Loading, WarningFilled, ArrowLeft, ArrowRight, ZoomOut, ZoomIn } from '@element-plus/icons-vue'
import * as pdfjsLib from 'pdfjs-dist'
import type { PDFDocumentProxy } from 'pdfjs-dist'

// 设置PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@5.2.133/build/pdf.worker.min.mjs'

interface Props {
  url: string
  width?: number
  height?: number
}

const props = withDefaults(defineProps<Props>(), {
  width: 800,
  height: 600
})

// 响应式数据
const loading = ref(true)
const error = ref('')
const currentPage = ref(1)
const totalPages = ref(0)
const scale = ref(1.0)
const pdfDocument = ref<PDFDocumentProxy | null>(null)

// DOM引用
const pagesContainer = ref<HTMLElement>()
const pageRefs = ref<Map<number, HTMLElement>>(new Map())
const canvasRefs = ref<Map<number, HTMLCanvasElement>>(new Map())

// 设置页面和canvas引用
const setPageRef = (el: any, pageNum: number) => {
  if (el && el instanceof HTMLElement) {
    pageRefs.value.set(pageNum, el)
  }
}

const setCanvasRef = (el: any, pageNum: number) => {
  if (el && el instanceof HTMLCanvasElement) {
    canvasRefs.value.set(pageNum, el)
  }
}

// 加载PDF文档
const loadPdf = async () => {
  try {
    loading.value = true
    error.value = ''
    
    console.log('[PDF Viewer] Loading PDF from:', props.url)
    
    // 加载PDF文档
    const loadingTask = pdfjsLib.getDocument({
      url: props.url,
      cMapUrl: 'https://cdn.jsdelivr.net/npm/pdfjs-dist@5.2.133/cmaps/',
      cMapPacked: true,
    })
    
    pdfDocument.value = await loadingTask.promise
    totalPages.value = pdfDocument.value.numPages
    
    console.log('[PDF Viewer] PDF loaded successfully, pages:', totalPages.value)
    
    // 等待DOM更新后渲染页面
    await nextTick()
    await renderAllPages()
    
  } catch (err) {
    console.error('[PDF Viewer] Failed to load PDF:', err)
    error.value = '加载PDF文档失败: ' + (err as Error).message
  } finally {
    loading.value = false
  }
}

// 渲染所有页面
const renderAllPages = async () => {
  if (!pdfDocument.value) return
  
  try {
    // 渲染前几页（可见页面）
    const visiblePages = Math.min(3, totalPages.value)
    for (let pageNum = 1; pageNum <= visiblePages; pageNum++) {
      await renderPage(pageNum)
    }
    
    // 异步渲染剩余页面
    setTimeout(async () => {
      for (let pageNum = visiblePages + 1; pageNum <= totalPages.value; pageNum++) {
        await renderPage(pageNum)
      }
    }, 100)
    
  } catch (err) {
    console.error('[PDF Viewer] Failed to render pages:', err)
    error.value = '渲染PDF页面失败'
  }
}

// 渲染单个页面
const renderPage = async (pageNum: number) => {
  if (!pdfDocument.value) return
  
  try {
    const page = await pdfDocument.value.getPage(pageNum)
    const canvas = canvasRefs.value.get(pageNum)
    
    if (!canvas) {
      console.warn(`[PDF Viewer] Canvas not found for page ${pageNum}`)
      return
    }
    
    const context = canvas.getContext('2d')
    if (!context) return
    
    // 计算缩放比例
    const viewport = page.getViewport({ scale: scale.value })
    
    // 设置canvas尺寸
    canvas.width = viewport.width
    canvas.height = viewport.height
    canvas.style.width = viewport.width + 'px'
    canvas.style.height = viewport.height + 'px'
    
    // 渲染页面
    const renderContext = {
      canvasContext: context,
      viewport: viewport
    }
    
    await page.render(renderContext).promise
    console.log(`[PDF Viewer] Page ${pageNum} rendered successfully`)
    
  } catch (err) {
    console.error(`[PDF Viewer] Failed to render page ${pageNum}:`, err)
  }
}

// 页面导航
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

// 滚动到指定页面
const scrollToPage = (pageNum: number) => {
  const pageElement = pageRefs.value.get(pageNum)
  if (pageElement && pagesContainer.value) {
    pageElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// 缩放控制
const zoomIn = async () => {
  if (scale.value < 3) {
    scale.value = Math.min(3, scale.value + 0.25)
    await renderAllPages()
  }
}

const zoomOut = async () => {
  if (scale.value > 0.5) {
    scale.value = Math.max(0.5, scale.value - 0.25)
    await renderAllPages()
  }
}

const resetZoom = async () => {
  scale.value = 1.0
  await renderAllPages()
}

// 重试加载
const retry = () => {
  loadPdf()
}

// 监听滚动事件，更新当前页面
const handleScroll = () => {
  if (!pagesContainer.value) return
  
  const container = pagesContainer.value
  const containerTop = container.scrollTop
  const containerHeight = container.clientHeight
  
  // 找到当前可见的页面
  for (let pageNum = 1; pageNum <= totalPages.value; pageNum++) {
    const pageElement = pageRefs.value.get(pageNum)
    if (!pageElement) continue
    
    const pageTop = pageElement.offsetTop - container.offsetTop
    const pageBottom = pageTop + pageElement.offsetHeight
    
    // 检查页面是否在可视区域内
    if (pageTop <= containerTop + containerHeight / 2 && pageBottom >= containerTop + containerHeight / 2) {
      currentPage.value = pageNum
      break
    }
  }
}

// 生命周期
onMounted(() => {
  loadPdf()
  
  // 添加滚动监听
  if (pagesContainer.value) {
    pagesContainer.value.addEventListener('scroll', handleScroll)
  }
})

onUnmounted(() => {
  // 清理资源
  if (pagesContainer.value) {
    pagesContainer.value.removeEventListener('scroll', handleScroll)
  }
  
  if (pdfDocument.value) {
    pdfDocument.value.destroy()
  }
})
</script>

<style scoped>
.pdf-viewer-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: #666;
}

.loading-container .el-icon {
  font-size: 32px;
  color: #409eff;
}

.error-container .el-icon {
  font-size: 32px;
  color: #f56c6c;
}

.pdf-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.pdf-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
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
  margin-left: 12px;
}

.pdf-pages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.pdf-page {
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  padding: 10px;
  transition: all 0.3s;
}

.pdf-page.active {
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.3);
  border: 2px solid #409eff;
}

.pdf-canvas {
  display: block;
  max-width: 100%;
  height: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .pdf-toolbar {
    padding: 8px 12px;
    flex-direction: column;
    gap: 8px;
  }
  
  .toolbar-left,
  .toolbar-right {
    width: 100%;
    justify-content: center;
  }
  
  .pdf-pages {
    padding: 10px;
    gap: 10px;
  }
  
  .page-info {
    margin-left: 0;
    text-align: center;
  }
}
</style>