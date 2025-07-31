<template>
  <div class="content-step">
    <div class="step-header">
      <h2 class="step-title">内容生成</h2>
      <p class="step-description">AI智能生成标书内容</p>
    </div>

    <div class="step-body">
      <!-- 内容生成中 -->
      <div v-if="project?.status === 'generating'" class="generating-state">
        <div class="progress-container">
          <el-icon class="loading-icon" size="48"><Loading /></el-icon>
          <h3>正在生成标书内容...</h3>
          <p>请稍候，AI正在根据大纲逐章节生成内容</p>
          
          <div class="progress-details" v-if="generationProgress">
            <el-progress 
              :percentage="generationProgress.percentage" 
              :stroke-width="8"
              status="success"
            />
            <div class="progress-info">
              <span>{{ generationProgress.current_chapter || '准备中' }}</span>
              <span class="progress-text">
                {{ generationProgress.completed_chapters || 0 }} / {{ generationProgress.total_chapters || 0 }} 章节已完成
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 内容生成结果 -->
      <div v-else-if="contentData && contentData.chapters" class="content-result">
        <div class="content-toolbar">
          <el-button @click="regenerateAllContent" type="warning" plain :loading="regeneratingAll">
            <el-icon><Refresh /></el-icon> 重新生成全部
          </el-button>
        </div>

        <div class="content-chapters">
          <div v-for="chapter in contentData.chapters" :key="chapter.chapter_id" class="chapter-card">
            <div class="chapter-header">
              <div class="chapter-info">
                <span class="chapter-number">{{ chapter.chapter_id }}</span>
                <span class="chapter-title">{{ chapter.title }}</span>
              </div>
              <div class="chapter-actions">
                <el-button 
                  size="small" 
                  @click="editChapter(chapter)"
                  type="primary" 
                  plain
                >
                  编辑
                </el-button>
                <el-button 
                  size="small" 
                  @click="regenerateChapter(chapter.chapter_id)"
                  type="warning" 
                  plain
                  :loading="regeneratingChapters.includes(chapter.chapter_id)"
                >
                  重新生成
                </el-button>
              </div>
            </div>
            
            <div class="chapter-content">
              <div class="content-preview" v-html="formatContent(chapter.content)"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 未开始生成 -->
      <div v-else class="not-started-state">
        <el-result icon="info" title="等待生成内容" sub-title="点击下方按钮开始生成标书内容">
          <template #extra>
            <el-button type="primary" @click="generateContent" :loading="generating">开始生成</el-button>
          </template>
        </el-result>
      </div>
    </div>

    <!-- 步骤操作 -->
    <div class="step-actions" v-if="project?.status === 'generated'">
      <el-button @click="$emit('prev')" size="large">
        <el-icon><ArrowLeft /></el-icon> 上一步
      </el-button>
      <el-button type="primary" @click="proceedToNext" size="large">
        下一步：导出文档 <el-icon><ArrowRight /></el-icon>
      </el-button>
    </div>

    <!-- 章节编辑对话框 -->
    <el-dialog v-model="showEditDialog" :title="`编辑 ${editingChapter?.title}`" width="900px" :close-on-click-modal="false">
      <div class="edit-form">
        <el-input 
          v-model="editForm.content" 
          type="textarea" 
          :rows="20"
          placeholder="请输入章节内容..."
        />
      </div>
      
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveChapter" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template><script
 setup lang="ts">
import { ref, reactive, watch, onMounted, onUnmounted } from 'vue'
import { Loading, Refresh, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { getUserId } from '@/utils/user'

interface ProjectItem {
  id: string
  project_name: string
  source_filename: string
  status: string
  progress?: number
  created_at: string
  updated_at: string
}

interface ContentChapter {
  chapter_id: string
  title: string
  content: string
}

interface ContentData {
  chapters: ContentChapter[]
}

interface GenerationProgress {
  percentage: number
  current_chapter?: string
  completed_chapters?: number
  total_chapters?: number
}

const props = defineProps<{
  project: ProjectItem | null
}>()

const emit = defineEmits<{
  next: []
  prev: []
  update: [project: ProjectItem]
}>()

const showEditDialog = ref(false)
const generating = ref(false)
const regeneratingAll = ref(false)
const saving = ref(false)
const contentData = ref<ContentData | null>(null)
const generationProgress = ref<GenerationProgress | null>(null)
const regeneratingChapters = ref<string[]>([])
const editingChapter = ref<ContentChapter | null>(null)
const progressTimer = ref<number | null>(null)

const editForm = reactive({
  content: ''
})

const fetchContent = async () => {
  if (!props.project) return
  
  try {
    const res = await axios.get(`/api/tender/projects/${props.project.id}/content`, {
      headers: { 'X-User-Id': getUserId() }
    })
    contentData.value = res.data
  } catch (e: any) {
    if (e.response?.status !== 404) {
      ElMessage.error('获取内容失败')
    }
  }
}

const fetchProgress = async () => {
  if (!props.project) return
  
  try {
    const res = await axios.get(`/api/tender/projects/${props.project.id}/content/progress`, {
      headers: { 'X-User-Id': getUserId() }
    })
    generationProgress.value = res.data
  } catch (e) {
    // 忽略进度获取错误
  }
}

const generateContent = async () => {
  if (!props.project) return
  
  generating.value = true
  try {
    await axios.post(`/api/tender/projects/${props.project.id}/content/generate-all`, {}, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    ElMessage.success('内容生成任务已启动')
    
    // 更新项目状态
    emit('update', { ...props.project, status: 'generating' })
    
    // 开始轮询检查状态和进度
    startProgressPolling()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '启动内容生成失败')
  } finally {
    generating.value = false
  }
}

const regenerateAllContent = async () => {
  if (!props.project) return
  
  regeneratingAll.value = true
  try {
    await axios.post(`/api/tender/projects/${props.project.id}/content/generate-all`, {
      regenerate: true
    }, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    ElMessage.success('内容重新生成任务已启动')
    
    // 更新项目状态
    emit('update', { ...props.project, status: 'generating' })
    
    // 开始轮询检查状态和进度
    startProgressPolling()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '重新生成内容失败')
  } finally {
    regeneratingAll.value = false
  }
}

const regenerateChapter = async (chapterId: string) => {
  if (!props.project) return
  
  regeneratingChapters.value.push(chapterId)
  try {
    await axios.post(`/api/tender/projects/${props.project.id}/content/generate-chapter`, {
      chapter_id: chapterId
    }, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    ElMessage.success('章节重新生成任务已启动')
    
    // 等待一段时间后刷新内容
    setTimeout(() => {
      fetchContent()
    }, 3000)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '重新生成章节失败')
  } finally {
    regeneratingChapters.value = regeneratingChapters.value.filter(id => id !== chapterId)
  }
}

const editChapter = (chapter: ContentChapter) => {
  editingChapter.value = chapter
  editForm.content = chapter.content
  showEditDialog.value = true
}

const saveChapter = async () => {
  if (!props.project || !editingChapter.value) return
  
  saving.value = true
  try {
    await axios.put(`/api/tender/projects/${props.project.id}/content/${editingChapter.value.chapter_id}`, {
      content: editForm.content
    }, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    ElMessage.success('章节内容已保存')
    showEditDialog.value = false
    await fetchContent()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存章节失败')
  } finally {
    saving.value = false
  }
}

const formatContent = (content: string) => {
  if (!content) return ''
  
  // 简单的内容格式化，将换行转换为HTML
  return content
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>')
}

const startProgressPolling = () => {
  stopProgressPolling()
  
  progressTimer.value = window.setInterval(async () => {
    if (!props.project) {
      stopProgressPolling()
      return
    }
    
    try {
      // 获取项目状态
      const projectRes = await axios.get(`/api/tender/projects/${props.project.id}`, {
        headers: { 'X-User-Id': getUserId() }
      })
      
      emit('update', projectRes.data)
      
      if (projectRes.data.status === 'generated') {
        stopProgressPolling()
        await fetchContent()
      } else if (projectRes.data.status === 'failed') {
        stopProgressPolling()
      } else if (projectRes.data.status === 'generating') {
        // 获取进度信息
        await fetchProgress()
      }
    } catch (e) {
      stopProgressPolling()
    }
  }, 3000)
}

const stopProgressPolling = () => {
  if (progressTimer.value) {
    clearInterval(progressTimer.value)
    progressTimer.value = null
  }
}

const proceedToNext = () => {
  emit('next')
}

// 监听项目变化
watch(() => props.project, (newProject) => {
  if (newProject && (newProject.status === 'generated' || newProject.status === 'exporting')) {
    fetchContent()
  }
}, { immediate: true })

onMounted(() => {
  if (props.project?.status === 'generating') {
    startProgressPolling()
  }
})

onUnmounted(() => {
  stopProgressPolling()
})
</script>

<style scoped>
.content-step {
  padding: 32px;
}

.step-header {
  text-align: center;
  margin-bottom: 32px;
}

.step-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.step-description {
  color: #6b7280;
  font-size: 1rem;
  margin: 0;
}

.step-body {
  margin-bottom: 32px;
}

.generating-state {
  text-align: center;
  padding: 64px 32px;
}

.progress-container h3 {
  font-size: 1.25rem;
  color: #1f2937;
  margin: 16px 0 8px 0;
}

.progress-container p {
  color: #6b7280;
  margin: 0 0 32px 0;
}

.loading-icon {
  color: #409eff;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.progress-details {
  max-width: 400px;
  margin: 0 auto;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  font-size: 0.875rem;
  color: #6b7280;
}

.progress-text {
  font-weight: 500;
}

.content-result {
  margin-bottom: 24px;
}

.content-toolbar {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.content-chapters {
  max-width: 1000px;
  margin: 0 auto;
}

.chapter-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.chapter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f3f4f6;
}

.chapter-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chapter-number {
  background: #409eff;
  color: white;
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.875rem;
  min-width: 50px;
  text-align: center;
}

.chapter-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

.chapter-actions {
  display: flex;
  gap: 8px;
}

.chapter-content {
  background: #f9fafb;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #e5e7eb;
}

.content-preview {
  color: #374151;
  line-height: 1.6;
  font-size: 0.875rem;
  max-height: 200px;
  overflow-y: auto;
}

.content-preview :deep(p) {
  margin: 0 0 12px 0;
}

.content-preview :deep(p:last-child) {
  margin-bottom: 0;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-top: 1px solid #e5e7eb;
}

.not-started-state {
  padding: 32px;
}

.edit-form {
  margin: 16px 0;
}

:deep(.el-result) {
  padding: 32px;
}

:deep(.el-progress-bar__outer) {
  background-color: #f3f4f6;
}

:deep(.el-progress-bar__inner) {
  background: linear-gradient(90deg, #409eff 0%, #67c23a 100%);
}

:deep(.el-textarea__inner) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
}
</style>