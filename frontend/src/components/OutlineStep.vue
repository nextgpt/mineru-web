<template>
  <div class="outline-step">
    <div class="step-header">
      <h2 class="step-title">方案大纲生成</h2>
      <p class="step-description">基于分析结果生成标书大纲结构</p>
    </div>

    <div class="step-body">
      <!-- 大纲生成中 -->
      <div v-if="project?.status === 'outlining'" class="generating-state">
        <div class="loading-container">
          <el-icon class="loading-icon" size="48"><Loading /></el-icon>
          <h3>正在生成方案大纲...</h3>
          <p>请稍候，系统正在基于分析结果生成标书框架</p>
        </div>
      </div>

      <!-- 大纲结果 -->
      <div v-else-if="outlineData" class="outline-result">
        <div class="outline-toolbar">
          <el-button @click="showEditDialog = true" type="primary" plain>
            <el-icon><Edit /></el-icon> 编辑大纲
          </el-button>
          <el-button @click="regenerateOutline" type="warning" plain :loading="regenerating">
            <el-icon><Refresh /></el-icon> 重新生成
          </el-button>
        </div>

        <div class="outline-content">
          <div class="outline-tree">
            <div v-for="(chapter, index) in outlineData.chapters" :key="index" class="chapter-item">
              <div class="chapter-header">
                <span class="chapter-number">{{ chapter.chapter_id }}</span>
                <span class="chapter-title">{{ chapter.title }}</span>
              </div>
              <div class="chapter-description" v-if="chapter.description">
                {{ chapter.description }}
              </div>
              <div v-if="chapter.subsections" class="subsections">
                <div v-for="subsection in chapter.subsections" :key="subsection.id" class="subsection-item">
                  <span class="subsection-number">{{ subsection.id }}</span>
                  <span class="subsection-title">{{ subsection.title }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 未开始生成 -->
      <div v-else class="not-started-state">
        <el-result icon="info" title="等待生成大纲" sub-title="点击下方按钮开始生成方案大纲">
          <template #extra>
            <el-button type="primary" @click="generateOutline" :loading="generating">生成大纲</el-button>
          </template>
        </el-result>
      </div>
    </div>

    <!-- 步骤操作 -->
    <div class="step-actions" v-if="project?.status === 'outlined'">
      <el-button @click="$emit('prev')" size="large">
        <el-icon><ArrowLeft /></el-icon> 上一步
      </el-button>
      <el-button type="primary" @click="proceedToNext" size="large">
        下一步：生成内容 <el-icon><ArrowRight /></el-icon>
      </el-button>
    </div>
  </div>
</template>
<scri
pt setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { Loading, Edit, Refresh, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
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

interface OutlineChapter {
  chapter_id: string
  title: string
  description?: string
  subsections?: Array<{
    id: string
    title: string
  }>
}

interface OutlineData {
  chapters: OutlineChapter[]
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
const regenerating = ref(false)
const saving = ref(false)
const outlineData = ref<OutlineData | null>(null)

const editForm = reactive({
  chapters: [] as OutlineChapter[]
})

const fetchOutline = async () => {
  if (!props.project) return
  
  try {
    const res = await axios.get(`/api/tender/projects/${props.project.id}/outline`, {
      headers: { 'X-User-Id': getUserId() }
    })
    outlineData.value = res.data
    
    // 初始化编辑表单
    if (res.data?.chapters) {
      editForm.chapters = JSON.parse(JSON.stringify(res.data.chapters))
    }
  } catch (e: any) {
    if (e.response?.status !== 404) {
      ElMessage.error('获取大纲失败')
    }
  }
}

const generateOutline = async () => {
  if (!props.project) return
  
  generating.value = true
  try {
    await axios.post(`/api/tender/projects/${props.project.id}/outline/generate`, {}, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    ElMessage.success('大纲生成任务已启动')
    
    // 更新项目状态
    emit('update', { ...props.project, status: 'outlining' })
    
    // 开始轮询检查状态
    pollOutlineStatus()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '启动大纲生成失败')
  } finally {
    generating.value = false
  }
}

const regenerateOutline = async () => {
  if (!props.project) return
  
  regenerating.value = true
  try {
    await axios.post(`/api/tender/projects/${props.project.id}/outline/generate`, {
      regenerate: true
    }, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    ElMessage.success('大纲重新生成任务已启动')
    
    // 更新项目状态
    emit('update', { ...props.project, status: 'outlining' })
    
    // 开始轮询检查状态
    pollOutlineStatus()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '重新生成大纲失败')
  } finally {
    regenerating.value = false
  }
}

const pollOutlineStatus = () => {
  const timer = setInterval(async () => {
    if (!props.project) {
      clearInterval(timer)
      return
    }
    
    try {
      const res = await axios.get(`/api/tender/projects/${props.project.id}`, {
        headers: { 'X-User-Id': getUserId() }
      })
      
      emit('update', res.data)
      
      if (res.data.status === 'outlined') {
        clearInterval(timer)
        await fetchOutline()
      } else if (res.data.status === 'failed') {
        clearInterval(timer)
      }
    } catch (e) {
      clearInterval(timer)
    }
  }, 3000)
}

const saveOutline = async () => {
  if (!props.project) return
  
  saving.value = true
  try {
    await axios.put(`/api/tender/projects/${props.project.id}/outline`, {
      chapters: editForm.chapters
    }, {
      headers: { 'X-User-Id': getUserId() }
    })
    
    ElMessage.success('大纲已保存')
    showEditDialog.value = false
    await fetchOutline()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存大纲失败')
  } finally {
    saving.value = false
  }
}

const proceedToNext = () => {
  emit('next')
}

// 监听项目变化
watch(() => props.project, (newProject) => {
  if (newProject && (newProject.status === 'outlined' || newProject.status === 'generating')) {
    fetchOutline()
  }
}, { immediate: true })

onMounted(() => {
  if (props.project?.status === 'outlining') {
    pollOutlineStatus()
  }
})
</script>

<style scoped>
.outline-step {
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

.loading-container h3 {
  font-size: 1.25rem;
  color: #1f2937;
  margin: 16px 0 8px 0;
}

.loading-container p {
  color: #6b7280;
  margin: 0;
}

.loading-icon {
  color: #409eff;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.outline-result {
  margin-bottom: 24px;
}

.outline-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  justify-content: center;
}

.outline-content {
  background: #f9fafb;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
}

.outline-tree {
  max-width: 800px;
  margin: 0 auto;
}

.chapter-item {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chapter-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.chapter-number {
  background: #409eff;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.875rem;
  min-width: 40px;
  text-align: center;
}

.chapter-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

.chapter-description {
  color: #6b7280;
  font-size: 0.875rem;
  line-height: 1.5;
  margin-bottom: 12px;
  padding-left: 52px;
}

.subsections {
  padding-left: 52px;
}

.subsection-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #f3f4f6;
}

.subsection-item:last-child {
  border-bottom: none;
}

.subsection-number {
  background: #f3f4f6;
  color: #6b7280;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: 500;
  min-width: 32px;
  text-align: center;
}

.subsection-title {
  color: #374151;
  font-size: 0.875rem;
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

:deep(.el-result) {
  padding: 32px;
}
</style>