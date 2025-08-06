<!--
  RAGFLOW API 使用示例组件
  展示如何在Vue组件中使用RAGFLOW服务
-->
<template>
  <div class="ragflow-example">
    <h2>RAGFLOW API 使用示例</h2>
    
    <!-- 基础操作 -->
    <el-card class="mb-4">
      <template #header>
        <span>基础操作</span>
      </template>
      
      <el-space direction="vertical" style="width: 100%">
        <!-- 创建数据集 -->
        <div>
          <el-input 
            v-model="newDatasetName" 
            placeholder="输入数据集名称"
            style="width: 300px"
          />
          <el-button 
            @click="createDataset" 
            :loading="loading.createDataset"
            type="primary"
          >
            创建数据集
          </el-button>
        </div>
        
        <!-- 上传文档 -->
        <div>
          <el-select v-model="selectedDatasetId" placeholder="选择数据集">
            <el-option
              v-for="dataset in datasets"
              :key="dataset.id"
              :label="dataset.name"
              :value="dataset.id"
            />
          </el-select>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :show-file-list="false"
          >
            <el-button>选择文件</el-button>
          </el-upload>
          <el-button 
            @click="uploadDocument" 
            :loading="loading.uploadDocument"
            :disabled="!selectedFile || !selectedDatasetId"
            type="success"
          >
            上传文档
          </el-button>
        </div>
      </el-space>
    </el-card>

    <!-- 五阶段大纲生成 -->
    <el-card class="mb-4">
      <template #header>
        <span>五阶段大纲生成</span>
      </template>
      
      <div>
        <el-select v-model="outlineDatasetId" placeholder="选择数据集">
          <el-option
            v-for="dataset in datasets"
            :key="dataset.id"
            :label="dataset.name"
            :value="dataset.id"
          />
        </el-select>
        <el-button 
          @click="generateOutline" 
          :loading="loading.generateOutline"
          :disabled="!outlineDatasetId"
          type="primary"
        >
          生成大纲
        </el-button>
      </div>
      
      <!-- 阶段进度显示 -->
      <div v-if="outlineStages.length > 0" class="mt-4">
        <h4>生成进度</h4>
        <el-timeline>
          <el-timeline-item
            v-for="stage in outlineStages"
            :key="stage.id"
            :type="getStageType(stage.status)"
            :timestamp="getStageTimestamp(stage)"
          >
            <h5>{{ stage.title }}</h5>
            <p class="text-sm text-gray-600">{{ stage.prompt }}</p>
            <div v-if="stage.status === 'completed' && stage.result" class="mt-2">
              <el-collapse>
                <el-collapse-item :title="`查看结果 (${stage.result.length} 字符)`">
                  <pre class="whitespace-pre-wrap text-sm">{{ stage.result }}</pre>
                </el-collapse-item>
              </el-collapse>
            </div>
            <div v-if="stage.status === 'error'" class="text-red-500">
              错误: {{ stage.error }}
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-card>

    <!-- 内容检索测试 -->
    <el-card class="mb-4">
      <template #header>
        <span>内容检索测试</span>
      </template>
      
      <div>
        <el-select v-model="retrievalDatasetId" placeholder="选择数据集">
          <el-option
            v-for="dataset in datasets"
            :key="dataset.id"
            :label="dataset.name"
            :value="dataset.id"
          />
        </el-select>
        <el-input 
          v-model="retrievalQuestion" 
          placeholder="输入检索问题"
          style="width: 300px"
        />
        <el-button 
          @click="testRetrieval" 
          :loading="loading.testRetrieval"
          :disabled="!retrievalDatasetId || !retrievalQuestion"
          type="primary"
        >
          检索内容
        </el-button>
      </div>
      
      <!-- 检索结果显示 -->
      <div v-if="retrievalResults.length > 0" class="mt-4">
        <h4>检索结果 ({{ retrievalResults.length }} 个片段)</h4>
        <el-collapse>
          <el-collapse-item
            v-for="(chunk, index) in retrievalResults"
            :key="index"
            :title="`片段 ${index + 1} (相似度: ${(chunk.similarity * 100).toFixed(1)}%)`"
          >
            <pre class="whitespace-pre-wrap text-sm">{{ chunk.content }}</pre>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-card>

    <!-- 缓存统计 -->
    <el-card>
      <template #header>
        <span>缓存统计</span>
      </template>
      
      <div>
        <p>缓存条目数: {{ cacheStats.size }}</p>
        <el-button @click="clearCache" size="small">清除缓存</el-button>
        <el-button @click="refreshCacheStats" size="small">刷新统计</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ragflowService } from '@/api/ragflow'
import type { 
  RAGFlowDataset, 
  OutlineStage, 
  RAGFlowChunk 
} from '@/types/tender'

// 响应式数据
const datasets = ref<RAGFlowDataset[]>([])
const newDatasetName = ref('')
const selectedDatasetId = ref('')
const selectedFile = ref<File | null>(null)
const outlineDatasetId = ref('')
const outlineStages = ref<OutlineStage[]>([])
const retrievalDatasetId = ref('')
const retrievalQuestion = ref('')
const retrievalResults = ref<RAGFlowChunk[]>([])
const cacheStats = ref<{ size: number; keys: string[] }>({ size: 0, keys: [] })

// 加载状态
const loading = ref({
  createDataset: false,
  uploadDocument: false,
  generateOutline: false,
  testRetrieval: false
})

// 组件挂载时加载数据集
onMounted(async () => {
  await loadDatasets()
  refreshCacheStats()
})

// 加载数据集列表
const loadDatasets = async () => {
  try {
    const result = await ragflowService.getDatasets()
    datasets.value = result.datasets
  } catch (error) {
    ElMessage.error('加载数据集失败: ' + (error as Error).message)
  }
}

// 创建数据集
const createDataset = async () => {
  if (!newDatasetName.value.trim()) {
    ElMessage.warning('请输入数据集名称')
    return
  }

  loading.value.createDataset = true
  try {
    const dataset = await ragflowService.createDataset(newDatasetName.value)
    datasets.value.unshift(dataset)
    newDatasetName.value = ''
    ElMessage.success('数据集创建成功')
  } catch (error) {
    ElMessage.error('创建数据集失败: ' + (error as Error).message)
  } finally {
    loading.value.createDataset = false
  }
}

// 处理文件选择
const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
}

// 上传文档
const uploadDocument = async () => {
  if (!selectedFile.value || !selectedDatasetId.value) {
    ElMessage.warning('请选择文件和数据集')
    return
  }

  loading.value.uploadDocument = true
  try {
    const document = await ragflowService.uploadDocument(
      selectedDatasetId.value, 
      selectedFile.value
    )
    
    ElMessage.success('文档上传成功')
    
    // 开始解析文档
    await ragflowService.parseDocument(selectedDatasetId.value, [document.id])
    
    // 等待解析完成
    await ragflowService.waitForDocumentParsing(
      selectedDatasetId.value,
      document.id,
      (progress) => {
        console.log(`解析进度: ${progress}%`)
      }
    )
    
    ElMessage.success('文档解析完成')
    selectedFile.value = null
    
  } catch (error) {
    ElMessage.error('上传文档失败: ' + (error as Error).message)
  } finally {
    loading.value.uploadDocument = false
  }
}

// 生成大纲
const generateOutline = async () => {
  if (!outlineDatasetId.value) {
    ElMessage.warning('请选择数据集')
    return
  }

  loading.value.generateOutline = true
  outlineStages.value = []
  
  try {
    await ragflowService.generateOutlineStages(
      outlineDatasetId.value,
      (stage) => {
        // 更新阶段状态
        const index = outlineStages.value.findIndex(s => s.id === stage.id)
        if (index >= 0) {
          outlineStages.value[index] = { ...stage }
        } else {
          outlineStages.value.push({ ...stage })
        }
      }
    )
    
    ElMessage.success('大纲生成完成')
    
  } catch (error) {
    ElMessage.error('生成大纲失败: ' + (error as Error).message)
  } finally {
    loading.value.generateOutline = false
  }
}

// 测试检索
const testRetrieval = async () => {
  if (!retrievalDatasetId.value || !retrievalQuestion.value.trim()) {
    ElMessage.warning('请选择数据集并输入检索问题')
    return
  }

  loading.value.testRetrieval = true
  try {
    const result = await ragflowService.retrieveContent(
      retrievalDatasetId.value,
      retrievalQuestion.value
    )
    
    retrievalResults.value = result.chunks
    ElMessage.success(`检索完成，找到 ${result.chunks.length} 个相关片段`)
    
  } catch (error) {
    ElMessage.error('检索失败: ' + (error as Error).message)
  } finally {
    loading.value.testRetrieval = false
  }
}

// 清除缓存
const clearCache = () => {
  ragflowService.clearRetrievalCache()
  refreshCacheStats()
  ElMessage.success('缓存已清除')
}

// 刷新缓存统计
const refreshCacheStats = () => {
  cacheStats.value = ragflowService.getCacheStats()
}

// 获取阶段状态类型
const getStageType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'processing': return 'primary'
    case 'error': return 'danger'
    default: return 'info'
  }
}

// 获取阶段时间戳
const getStageTimestamp = (stage: OutlineStage) => {
  if (stage.endTime) {
    return new Date(stage.endTime).toLocaleTimeString()
  } else if (stage.startTime) {
    return new Date(stage.startTime).toLocaleTimeString()
  }
  return ''
}
</script>

<style scoped>
.ragflow-example {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.mb-4 {
  margin-bottom: 16px;
}

.mt-4 {
  margin-top: 16px;
}

.mt-2 {
  margin-top: 8px;
}

.text-sm {
  font-size: 14px;
}

.text-gray-600 {
  color: #6b7280;
}

.text-red-500 {
  color: #ef4444;
}

.whitespace-pre-wrap {
  white-space: pre-wrap;
}

pre {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}
</style>