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
        <template #default="{ data }">
          <div class="outline-node">
            <div class="node-content">
              <span class="node-sequence">{{ data.sequence }}</span>
              <span class="node-title">{{ data.title }}</span>
              <span v-if="data.content" class="node-description">{{ data.content }}</span>
            </div>
            <div class="node-actions">
              <el-dropdown @command="handleNodeAction" trigger="click">
                <el-button size="small" type="text">
                  操作 <el-icon><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{action: 'edit', data}">编辑</el-dropdown-item>
                    <el-dropdown-item :command="{action: 'addChild', data}" v-if="data.level < 3">添加子节点</el-dropdown-item>
                    <el-dropdown-item :command="{action: 'copy', data}">复制</el-dropdown-item>
                    <el-dropdown-item :command="{action: 'delete', data}" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
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

    <!-- 添加子节点对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加子节点"
      width="500px"
    >
      <el-form
        ref="addFormRef"
        :model="addForm"
        :rules="addFormRules"
        label-width="80px"
      >
        <el-form-item label="父节点">
          <el-input
            :value="currentParentItem?.title || '根节点'"
            disabled
          />
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input
            v-model="addForm.title"
            placeholder="请输入大纲标题"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述" prop="content">
          <el-input
            v-model="addForm.content"
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
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="handleAddOutline">
            添加
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Loading, Document, ArrowDown } from '@element-plus/icons-vue'
import { outlineApi, type BidOutline } from '@/api/projects'

interface Props {
  projectId: number
}



const props = defineProps<Props>()

const outline = ref<BidOutline[]>([])
const generating = ref(false)
const showEditDialog = ref(false)
const showAddDialog = ref(false)
const editFormRef = ref<FormInstance>()
const addFormRef = ref<FormInstance>()
const currentEditItem = ref<BidOutline | null>(null)
const currentParentItem = ref<BidOutline | null>(null)

const editForm = ref({
  title: '',
  content: ''
})

const addForm = ref({
  title: '',
  content: ''
})

const editFormRules = {
  title: [
    { required: true, message: '请输入大纲标题', trigger: 'blur' },
    { min: 1, max: 200, message: '标题长度在 1 到 200 个字符', trigger: 'blur' }
  ]
}

const addFormRules = {
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
    
    const response = await outlineApi.generateOutline(props.projectId)
    
    if (response.status === 'exists') {
      ElMessage.info('大纲已存在，正在加载...')
      await loadOutline()
    } else if (response.status === 'started') {
      ElMessage.success('大纲生成已开始，请稍后刷新查看结果')
      // 轮询检查生成状态
      pollOutlineGeneration()
    }
  } catch (error: any) {
    console.error('生成大纲失败:', error)
    ElMessage.error(error.response?.data?.detail || '生成大纲失败')
  } finally {
    generating.value = false
  }
}

const pollOutlineGeneration = async () => {
  const maxAttempts = 30 // 最多轮询30次（约5分钟）
  let attempts = 0
  
  const poll = async () => {
    try {
      attempts++
      const response = await loadOutline()
      
      if (outline.value.length > 0) {
        ElMessage.success('标书大纲生成完成')
        return
      }
      
      if (attempts < maxAttempts) {
        setTimeout(poll, 10000) // 每10秒轮询一次
      } else {
        ElMessage.warning('大纲生成时间较长，请稍后手动刷新查看')
      }
    } catch (error) {
      console.error('轮询大纲状态失败:', error)
    }
  }
  
  setTimeout(poll, 10000) // 10秒后开始第一次轮询
}

const loadOutline = async () => {
  try {
    const response = await outlineApi.getOutline(props.projectId)
    
    if (response.status === 'success' && response.outline) {
      // 将树形结构转换为扁平结构
      const flattenOutline = (items: BidOutline[]): BidOutline[] => {
        const result: BidOutline[] = []
        
        const traverse = (nodes: BidOutline[]) => {
          nodes.forEach(node => {
            result.push(node)
            if (node.children && node.children.length > 0) {
              traverse(node.children)
            }
          })
        }
        
        traverse(items)
        return result
      }
      
      outline.value = flattenOutline(response.outline)
    } else {
      outline.value = []
    }
  } catch (error: any) {
    console.error('加载大纲失败:', error)
    if (error.response?.status !== 404) {
      ElMessage.error('加载大纲失败')
    }
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
    
    await outlineApi.updateOutlineNode(props.projectId, currentEditItem.value.id, {
      title: editForm.value.title,
      content: editForm.value.content
    })
    
    // 更新本地数据
    const item = outline.value.find(o => o.id === currentEditItem.value!.id)
    if (item) {
      item.title = editForm.value.title
      item.content = editForm.value.content
    }
    
    ElMessage.success('大纲更新成功')
    showEditDialog.value = false
  } catch (error: any) {
    console.error('更新大纲失败:', error)
    ElMessage.error(error.response?.data?.detail || '更新大纲失败')
  }
}

const handleNodeAction = (command: {action: string, data: BidOutline}) => {
  const { action, data } = command
  
  switch (action) {
    case 'edit':
      editOutline(data)
      break
    case 'addChild':
      addChildNode(data)
      break
    case 'copy':
      copyOutlineNode(data)
      break
    case 'delete':
      deleteOutlineNode(data)
      break
  }
}

const addChildNode = (parentItem: BidOutline) => {
  currentParentItem.value = parentItem
  addForm.value = {
    title: '',
    content: ''
  }
  showAddDialog.value = true
}

const handleAddOutline = async () => {
  if (!addFormRef.value || !currentParentItem.value) return
  
  try {
    const valid = await addFormRef.value.validate()
    if (!valid) return
    
    const newNode = await outlineApi.createOutlineNode(props.projectId, {
      title: addForm.value.title,
      content: addForm.value.content,
      level: currentParentItem.value.level + 1,
      parent_id: currentParentItem.value.id
    })
    
    // 重新加载大纲
    await loadOutline()
    
    ElMessage.success('子节点添加成功')
    showAddDialog.value = false
  } catch (error: any) {
    console.error('添加子节点失败:', error)
    ElMessage.error(error.response?.data?.detail || '添加子节点失败')
  }
}

const copyOutlineNode = async (item: BidOutline) => {
  try {
    await outlineApi.copyOutlineNode(props.projectId, item.id, {
      target_parent_id: item.parent_id
    })
    
    // 重新加载大纲
    await loadOutline()
    
    ElMessage.success('节点复制成功')
  } catch (error: any) {
    console.error('复制节点失败:', error)
    ElMessage.error(error.response?.data?.detail || '复制节点失败')
  }
}

const deleteOutlineNode = async (item: BidOutline) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除"${item.title}"及其所有子节点吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await outlineApi.deleteOutlineNode(props.projectId, item.id)
    
    // 重新加载大纲
    await loadOutline()
    
    ElMessage.success('节点删除成功')
  } catch (error: any) {
    if (error === 'cancel') {
      return
    }
    console.error('删除节点失败:', error)
    ElMessage.error(error.response?.data?.detail || '删除节点失败')
  }
}

const generateContent = (item: BidOutline) => {
  ElMessage.info(`正在为"${item.title}"生成内容...`)
  // 触发父组件切换到文档标签页并生成内容
  emit('generateContent', item)
}

const emit = defineEmits<{
  generateContent: [item: BidOutline]
}>()

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