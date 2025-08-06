/**
 * RAGFLOW API 服务测试工具
 * 用于验证 RAGFLOW API 集成的功能
 */

import { ragflowService } from '@/api/ragflow'
import type { OutlineStage } from '@/types/tender'

export class RAGFlowTestUtils {
  /**
   * 测试基础API功能
   */
  static async testBasicAPI(): Promise<void> {
    console.log('=== RAGFLOW API 基础功能测试 ===')
    
    try {
      // 测试获取数据集列表
      console.log('1. 测试获取数据集列表...')
      const datasets = await ragflowService.getDatasets(1, 10)
      console.log(`✓ 成功获取 ${datasets.datasets.length} 个数据集`)
      
      if (datasets.datasets.length > 0) {
        const testDataset = datasets.datasets[0]
        console.log(`使用测试数据集: ${testDataset.name} (${testDataset.id})`)
        
        // 测试获取文档列表
        console.log('2. 测试获取文档列表...')
        const documentsResult = await ragflowService.getDocuments(1, 10)
        console.log(`✓ 成功获取 ${documentsResult.data?.documents.length || 0} 个文档`)
        
        if (documentsResult.data?.documents.length && documentsResult.data.documents.length > 0) {
          // 测试检索功能
          console.log('3. 测试内容检索...')
          const retrievalResult = await ragflowService.retrieveContent(
            testDataset.id,
            '项目需求概况'
          )
          console.log(`✓ 成功检索到 ${retrievalResult.chunks.length} 个相关片段`)
        }
      }
      
      console.log('✓ 基础API测试完成')
      
    } catch (error) {
      console.error('✗ 基础API测试失败:', error)
      throw error
    }
  }

  /**
   * 测试五阶段大纲生成
   */
  static async testOutlineGeneration(datasetId: string): Promise<OutlineStage[]> {
    console.log('=== 五阶段大纲生成测试 ===')
    
    const stages: OutlineStage[] = []
    
    try {
      const result = await ragflowService.generateOutlineStages(
        datasetId,
        (stage) => {
          console.log(`阶段 ${stage.id}: ${stage.title} - ${stage.status}`)
          if (stage.status === 'completed') {
            console.log(`结果预览: ${stage.result.substring(0, 100)}...`)
          }
          stages.push({ ...stage })
        }
      )
      
      console.log('✓ 五阶段大纲生成测试完成')
      return result
      
    } catch (error) {
      console.error('✗ 五阶段大纲生成测试失败:', error)
      throw error
    }
  }

  /**
   * 测试缓存机制
   */
  static async testCacheMechanism(datasetId: string): Promise<void> {
    console.log('=== 缓存机制测试 ===')
    
    try {
      const testQuestion = '测试缓存问题'
      
      // 清除缓存
      ragflowService.clearRetrievalCache()
      console.log('1. 缓存已清除')
      
      // 第一次检索（应该调用API）
      console.log('2. 第一次检索（调用API）...')
      const start1 = Date.now()
      await ragflowService.retrieveContent(datasetId, testQuestion)
      const time1 = Date.now() - start1
      console.log(`✓ 第一次检索耗时: ${time1}ms`)
      
      // 第二次检索（应该使用缓存）
      console.log('3. 第二次检索（使用缓存）...')
      const start2 = Date.now()
      await ragflowService.retrieveContent(datasetId, testQuestion)
      const time2 = Date.now() - start2
      console.log(`✓ 第二次检索耗时: ${time2}ms`)
      
      // 验证缓存效果
      if (time2 < time1 / 2) {
        console.log('✓ 缓存机制工作正常')
      } else {
        console.warn('⚠ 缓存效果不明显')
      }
      
      // 显示缓存统计
      const stats = ragflowService.getCacheStats()
      console.log(`缓存统计: ${stats.size} 个条目`)
      
    } catch (error) {
      console.error('✗ 缓存机制测试失败:', error)
      throw error
    }
  }

  /**
   * 测试错误处理和重试机制
   */
  static async testErrorHandling(): Promise<void> {
    console.log('=== 错误处理和重试机制测试 ===')
    
    try {
      // 测试无效数据集ID
      console.log('1. 测试无效数据集ID...')
      try {
        await ragflowService.retrieveContent('invalid-dataset-id', '测试问题')
        console.warn('⚠ 预期应该抛出错误')
      } catch (error) {
        console.log('✓ 正确处理无效数据集ID错误')
      }
      
      // 测试空问题
      console.log('2. 测试空问题...')
      try {
        await ragflowService.retrieveContent('valid-dataset-id', '')
        console.warn('⚠ 预期应该抛出错误')
      } catch (error) {
        console.log('✓ 正确处理空问题错误')
      }
      
      console.log('✓ 错误处理测试完成')
      
    } catch (error) {
      console.error('✗ 错误处理测试失败:', error)
      throw error
    }
  }

  /**
   * 运行完整测试套件
   */
  static async runFullTestSuite(): Promise<void> {
    console.log('=== RAGFLOW API 完整测试套件 ===')
    
    try {
      // 基础API测试
      await this.testBasicAPI()
      
      // 获取第一个数据集用于后续测试
      const datasets = await ragflowService.getDatasets(1, 1)
      if (datasets.datasets.length === 0) {
        console.warn('⚠ 没有可用的数据集，跳过高级测试')
        return
      }
      
      const testDatasetId = datasets.datasets[0].id
      
      // 缓存机制测试
      await this.testCacheMechanism(testDatasetId)
      
      // 五阶段大纲生成测试
      await this.testOutlineGeneration(testDatasetId)
      
      // 错误处理测试
      await this.testErrorHandling()
      
      console.log('🎉 所有测试通过！')
      
    } catch (error) {
      console.error('❌ 测试套件执行失败:', error)
      throw error
    }
  }
}

// 导出便捷的测试函数
export const testRAGFlowAPI = RAGFlowTestUtils.runFullTestSuite
export const testBasicAPI = RAGFlowTestUtils.testBasicAPI
export const testOutlineGeneration = RAGFlowTestUtils.testOutlineGeneration
export const testCacheMechanism = RAGFlowTestUtils.testCacheMechanism
export const testErrorHandling = RAGFlowTestUtils.testErrorHandling