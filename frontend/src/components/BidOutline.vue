<template>
  <div class="bid-outline-component">
    <div class="outline-header">
      <h3 class="section-title">标书大纲</h3>
      <el-button 
        v-if="!outline.length && !generating" 
        type="primary" 
        @click="generateOutline"
      >
        生成大纲
      </el-button>
    </div>

    <!-- 生成中状态 -->
    <div v-if="generating" class="generating-state">
      <div class="generating-content">
        <el-icon class="generating-icon" size="48"><Loading /></el-icon>
        <h4 class="generating-title">正在生成标书大纲...</h4>
        <p class="generating-text">AI正在基于需求分析结果生成结构化的标书大纲，请稍候。</p>
      </div>
    </div>

    <!-- 大纲树形结构 -->
    <div v-else-if="outline.length" class="outline-tree">
      <el-tree
        :data="outlineTree"
        :props="{ children: 'children', label: 'title' }"
        node-key="id"
        default-expand-all
        class="outline-tree-component"
      >
        <template #default="{ node, data }">
          <div class="outline-node">
            <div class="node-content">
              <span class="node-sequence">{{ data.sequence }}</span>
              <span class="node-title">{{ data.title }}</span>
              <span v-if="data.content" class="node-description">{{ data.content }}</span>
            </div>
            <div class="node-actions">
              <el-button size="small" @click.stop="editOutline(data)">
                编辑
              </el-button>
              <el-button size="small" type="primary" @click.stop="generateContent(data)">
                生成内容
              </el-button>
            </div>
          </div>
        </template>
      </el-tree>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-icon size="48" color="#d1d5db"><Document /></el-icon>
      <h4 class="empty-title">尚未生成标书大纲</h4>
      <p class="empty-text">基于需求分析结果，AI将为您生成结构化的标书大纲。</p>
    </div>

    <!-- 编辑大纲对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑大纲项"
      width="500px"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editFormRules"
        label-width="80px"
      >
        <el-form-item label="标题" prop="title">
          <el-input
            v-model="editForm.title"
            placeholder="请输入大纲标题"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述" prop="content">
          <el-input
            v-model="editForm.content"
            type="textarea"
            :rows="3"
            placeholder="请输入大纲描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="handleEditOutline">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { Loading, Document } from '@element-plus/icons-vue'

interface Props {
  projectId: number
}

interface BidOutline {
  id: number
  project_id: number
  user_id: string
  title: string
  level: number
  sequence: string
  parent_id?: number
  order_index: number
  content?: string
  created_at: string
  children?: BidOutline[]
}

const props = defineProps<Props>()

const outline = ref<BidOutline[]>([])
const generating = ref(false)
const showEditDialog = ref(false)
const editFormRef = ref<FormInstance>()
const currentEditItem = ref<BidOutline | null>(null)

const editForm = ref({
  title: '',
  content: ''
})

const editFormRules = {
  title: [
    { required: true, message: '请输入大纲标题', trigger: 'blur' },
    { min: 1, max: 200, message: '标题长度在 1 到 200 个字符', trigger: 'blur' }
  ]
}

// 将扁平的大纲数据转换为树形结构
const outlineTree = computed(() => {
  const buildTree = (items: BidOutline[], parentId?: number): BidOutline[] => {
    return items
      .filter(item => item.parent_id === parentId)
      .sort((a, b) => a.order_index - b.order_index)
      .map(item => ({
        ...item,
        children: buildTree(items, item.id)
      }))
  }
  
  return buildTree(outline.value)
})

const generateOutline = async () => {
  try {
    generating.value = true
    ElMessage.info('开始生成标书大纲，请稍候...')
    
    // TODO: 调用后端API生成大纲
    // await outlineApi.generateOutline(props.projectId)
    
    // 模拟生成过程
    setTimeout(() => {
      generating.value = false
      ElMessage.success('标书大纲生成完成')
      loadOutline()
    }, 3000)
  } catch (error) {
    console.error('生成大纲失败:', error)
    ElMessage.error('生成大纲失败')
    generating.value = false
  }
}

const loadOutline = async () => {
  try {
    // TODO: 调用后端API获取大纲
    // outline.value = await outlineApi.getOutline(props.projectId)
    
    // 模拟数据
    outline.value = [
      {
        id: 1,
        project_id: props.projectId,
        user_id: 'user123',
        title: '项目概述',
        level: 1,
        sequence: '1',
        order_index: 1,
        content: '项目背景、目标和范围说明',
        created_at: new Date().toISOString()
      },
      {
        id: 2,
        project_id: props.projectId,
        user_id: 'user123',
        title: '项目背景',
        level: 2,
        sequence: '1.1',
        parent_id: 1,
        order_index: 1,
        content: '详细描述项目产生的背景和必要性',
        created_at: new Date().toISOString()
      },
      {
        id: 3,
        project_id: props.projectId,
        user_id: 'user123',
        title: '项目目标',
        level: 2,
        sequence: '1.2',
        parent_id: 1,
        order_index: 2,
        content: '明确项目要达到的具体目标',
        created_at: new Date().toISOString()
      },
      {
        id: 4,
        project_id: props.projectId,
        user_id: 'user123',
        title: '技术方案',
        level: 1,
        sequence: '2',
        order_index: 2,
        content: '详细的技术实现方案',
        created_at: new Date().toISOString()
      },
      {
        id: 5,
        project_id: props.projectId,
        user_id: 'user123',
        title: '系统架构设计',
        level: 2,
        sequence: '2.1',
        parent_id: 4,
        order_index: 1,
        content: '系统整体架构和技术选型',
        created_at: new Date().toISOString()
      },
      {
        id: 6,
        project_id: props.projectId,
        user_id: 'user123',
        title: '功能模块设计',
        level: 2,
        sequence: '2.2',
        parent_id: 4,
        order_index: 2,
        content: '各功能模块的详细设计',
        created_at: new Date().toISOString()
      }
    ]
  } catch (error) {
    console.error('加载大纲失败:', error)
  }
}

const editOutline = (item: BidOutline) => {
  currentEditItem.value = item
  editForm.value = {
    title: item.title,
    content: item.content || ''
  }
  showEditDialog.value = true
}

const handleEditOutline = async () => {
  if (!editFormRef.value || !currentEditItem.value) return
  
  try {
    const valid = await editFormRef.value.validate()
    if (!valid) return
    
    // TODO: 调用后端API更新大纲
    // await outlineApi.updateOutline(currentEditItem.value.id, editForm.value)
    
    // 更新本地数据
    const item = outline.value.find(o => o.id === currentEditItem.value!.id)
    if (item) {
      item.title = editForm.value.title
      item.content = editForm.value.content
    }
    
    ElMessage.success('大纲更新成功')
    showEditDialog.value = false
  } catch (error) {
    console.error('更新大纲失败:', error)
    ElMessage.error('更新大纲失败')
  }
}

const generateContent = (item: BidOutline) => {
  ElMessage.info(`正在为"${item.title}"生成内容...`)
  // TODO: 实现内容生成功能
}

onMounted(() => {
  loadOutline()
})
</script>

<style scoped>
.bid-outline-component {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.outline-header {
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

.generating-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.generating-content {
  text-align: center;
  max-width: 400px;
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
  margin: 0;
}

.outline-tree {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
}

.outline-tree-component :deep(.el-tree-node__content) {
  height: auto;
  padding: 8px 0;
}

.outline-tree-component :deep(.el-tree-node__expand-icon) {
  padding: 6px;
}

.outline-node {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  width: 100%;
  padding: 8px 0;
  gap: 16px;
}

.node-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.node-sequence {
  font-weight: 600;
  color: #3b82f6;
  font-size: 14px;
}

.node-title {
  font-weight: 500;
  color: #1f2937;
  font-size: 15px;
}

.node-description {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.4;
}

.node-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
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

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .outline-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .outline-node {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .node-actions {
    justify-content: flex-end;
  }
}
</style>