// API服务测试工具

import { ragflowService, deepseekService } from '@/api'
import { ElMessage } from 'element-plus'

/**
 * 测试RAGFLOW API连接
 */
export async function testRAGFlowConnection(): Promise<boolean> {
  try {
    console.log('Testing RAGFLOW connection...')
    await ragflowService.getDatasets(1, 1)
    ElMessage.success('RAGFLOW API连接成功')
    return true
  } catch (error) {
    console.error('RAGFLOW connection test failed:', error)
    ElMessage.error('RAGFLOW API连接失败，请检查配置')
    return false
  }
}

/**
 * 测试DeepSeek API连接
 */
export async function testDeepSeekConnection(): Promise<boolean> {
  try {
    console.log('Testing DeepSeek connection...')
    
    // 发送一个简单的测试消息
    const response = await deepseekService.createChatCompletion([
      {
        role: 'user',
        content: '你好，请回复"连接成功"'
      }
    ], {
      maxTokens: 10,
      temperature: 0.1
    })
    
    if (response.choices && response.choices.length > 0) {
      ElMessage.success('DeepSeek API连接成功')
      return true
    } else {
      throw new Error('No response from DeepSeek API')
    }
  } catch (error) {
    console.error('DeepSeek connection test failed:', error)
    ElMessage.error('DeepSeek API连接失败，请检查配置')
    return false
  }
}

/**
 * 测试所有API连接
 */
export async function testAllConnections(): Promise<{ ragflow: boolean; deepseek: boolean }> {
  const results = {
    ragflow: false,
    deepseek: false
  }

  try {
    results.ragflow = await testRAGFlowConnection()
  } catch (error) {
    console.error('RAGFLOW test error:', error)
  }

  try {
    results.deepseek = await testDeepSeekConnection()
  } catch (error) {
    console.error('DeepSeek test error:', error)
  }

  return results
}

/**
 * 创建测试数据集
 */
export async function createTestDataset(): Promise<string | null> {
  try {
    const testName = `test_dataset_${Date.now()}`
    const dataset = await ragflowService.createDataset(testName)
    ElMessage.success(`测试数据集创建成功: ${dataset.name}`)
    return dataset.id
  } catch (error) {
    console.error('Failed to create test dataset:', error)
    ElMessage.error('创建测试数据集失败')
    return null
  }
}

/**
 * 清理测试数据
 */
export async function cleanupTestData(): Promise<void> {
  try {
    const { datasets } = await ragflowService.getDatasets()
    const testDatasets = datasets.filter(d => d.name.startsWith('test_dataset_'))
    
    for (const dataset of testDatasets) {
      await ragflowService.deleteDataset(dataset.id)
      console.log(`Deleted test dataset: ${dataset.name}`)
    }
    
    if (testDatasets.length > 0) {
      ElMessage.success(`清理了 ${testDatasets.length} 个测试数据集`)
    }
  } catch (error) {
    console.error('Failed to cleanup test data:', error)
    ElMessage.error('清理测试数据失败')
  }
}