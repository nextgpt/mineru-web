import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ProjectDetail from '@/views/ProjectDetail.vue'
import axios from 'axios'

// Mock project data
const mockProject = {
  id: 'test-project-id',
  project_name: '测试招标项目',
  source_filename: 'test.pdf',
  status: 'analyzed',
  created_at: '2024-01-01T00:00:00',
  updated_at: '2024-01-01T00:00:00'
}

vi.mocked(axios.get).mockResolvedValue({
  data: mockProject
})

describe('ProjectDetail.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders project information correctly', async () => {
    const wrapper = mount(ProjectDetail, {
      global: {
        stubs: {
          'el-button': true,
          'el-icon': true,
          'el-tag': true,
          'el-steps': true,
          'el-step': true,
          'AnalysisStep': true,
          'OutlineStep': true,
          'ContentStep': true,
          'ExportStep': true,
          'ProgressIndicator': true
        }
      }
    })

    await nextTick()

    // 检查项目标题
    expect(wrapper.find('.project-title').text()).toBe('测试招标项目')
    
    // 检查项目元信息
    const metaText = wrapper.find('.project-meta').text()
    expect(metaText).toContain('test.pdf')
    expect(metaText).toContain('2024-01-01')
  })

  it('shows correct step based on project status', async () => {
    const wrapper = mount(ProjectDetail, {
      global: {
        stubs: {
          'el-button': true,
          'el-icon': true,
          'el-tag': true,
          'el-steps': true,
          'el-step': true,
          'AnalysisStep': true,
          'OutlineStep': true,
          'ContentStep': true,
          'ExportStep': true,
          'ProgressIndicator': true
        }
      }
    })

    await nextTick()

    // 测试不同状态对应的步骤
    wrapper.vm.project = { ...mockProject, status: 'analyzing' }
    await nextTick()
    expect(wrapper.vm.currentStep).toBe(0)

    wrapper.vm.project = { ...mockProject, status: 'outlined' }
    await nextTick()
    expect(wrapper.vm.currentStep).toBe(2)

    wrapper.vm.project = { ...mockProject, status: 'completed' }
    await nextTick()
    expect(wrapper.vm.currentStep).toBe(3)
  })

  it('handles project status updates', async () => {
    const wrapper = mount(ProjectDetail, {
      global: {
        stubs: {
          'el-button': true,
          'el-icon': true,
          'el-tag': true,
          'el-steps': true,
          'el-step': true,
          'AnalysisStep': true,
          'OutlineStep': true,
          'ContentStep': true,
          'ExportStep': true,
          'ProgressIndicator': true
        }
      }
    })

    await nextTick()

    // 模拟项目更新
    const updatedProject = { ...mockProject, status: 'generating', progress: 75 }
    wrapper.vm.handleProjectUpdate(updatedProject)

    expect(wrapper.vm.project).toEqual(updatedProject)
    expect(wrapper.vm.showProgressIndicator).toBe(true)
  })

  it('shows progress indicator for active statuses', async () => {
    const wrapper = mount(ProjectDetail, {
      global: {
        stubs: {
          'el-button': true,
          'el-icon': true,
          'el-tag': true,
          'el-steps': true,
          'el-step': true,
          'AnalysisStep': true,
          'OutlineStep': true,
          'ContentStep': true,
          'ExportStep': true,
          'ProgressIndicator': true
        }
      }
    })

    await nextTick()

    // 测试活跃状态显示进度指示器
    const activeStatuses = ['analyzing', 'outlining', 'generating', 'exporting']
    
    for (const status of activeStatuses) {
      const updatedProject = { ...mockProject, status }
      wrapper.vm.handleProjectUpdate(updatedProject)
      expect(wrapper.vm.showProgressIndicator).toBe(true)
    }

    // 测试非活跃状态不显示进度指示器
    const inactiveStatuses = ['analyzed', 'outlined', 'generated', 'completed']
    
    for (const status of inactiveStatuses) {
      const updatedProject = { ...mockProject, status }
      wrapper.vm.handleProjectUpdate(updatedProject)
      expect(wrapper.vm.showProgressIndicator).toBe(false)
    }
  })

  it('handles back navigation', async () => {
    const mockBack = vi.fn()
    const wrapper = mount(ProjectDetail, {
      global: {
        mocks: {
          $router: { back: mockBack }
        },
        stubs: {
          'el-button': { template: '<button @click="$emit(\'click\')"><slot /></button>' },
          'el-icon': true,
          'el-tag': true,
          'el-steps': true,
          'el-step': true,
          'AnalysisStep': true,
          'OutlineStep': true,
          'ContentStep': true,
          'ExportStep': true,
          'ProgressIndicator': true
        }
      }
    })

    await nextTick()

    // 点击返回按钮
    const backButton = wrapper.find('.back-btn')
    await backButton.trigger('click')

    expect(mockBack).toHaveBeenCalled()
  })

  it('formats status text correctly', async () => {
    const wrapper = mount(ProjectDetail, {
      global: {
        stubs: {
          'el-button': true,
          'el-icon': true,
          'el-tag': true,
          'el-steps': true,
          'el-step': true,
          'AnalysisStep': true,
          'OutlineStep': true,
          'ContentStep': true,
          'ExportStep': true,
          'ProgressIndicator': true
        }
      }
    })

    await nextTick()

    // 测试状态文本格式化
    expect(wrapper.vm.getStatusText('analyzing')).toBe('分析中')
    expect(wrapper.vm.getStatusText('analyzed')).toBe('已分析')
    expect(wrapper.vm.getStatusText('outlining')).toBe('大纲生成中')
    expect(wrapper.vm.getStatusText('outlined')).toBe('大纲已生成')
    expect(wrapper.vm.getStatusText('generating')).toBe('内容生成中')
    expect(wrapper.vm.getStatusText('generated')).toBe('内容已生成')
    expect(wrapper.vm.getStatusText('exporting')).toBe('导出中')
    expect(wrapper.vm.getStatusText('completed')).toBe('已完成')
    expect(wrapper.vm.getStatusText('failed')).toBe('失败')
  })

  it('formats status type correctly', async () => {
    const wrapper = mount(ProjectDetail, {
      global: {
        stubs: {
          'el-button': true,
          'el-icon': true,
          'el-tag': true,
          'el-steps': true,
          'el-step': true,
          'AnalysisStep': true,
          'OutlineStep': true,
          'ContentStep': true,
          'ExportStep': true,
          'ProgressIndicator': true
        }
      }
    })

    await nextTick()

    // 测试状态类型格式化
    expect(wrapper.vm.getStatusType('analyzing')).toBe('warning')
    expect(wrapper.vm.getStatusType('analyzed')).toBe('info')
    expect(wrapper.vm.getStatusType('completed')).toBe('success')
    expect(wrapper.vm.getStatusType('failed')).toBe('danger')
  })

  it('handles step navigation', async () => {
    const wrapper = mount(ProjectDetail, {
      global: {
        stubs: {
          'el-button': true,
          'el-icon': true,
          'el-tag': true,
          'el-steps': true,
          'el-step': true,
          'AnalysisStep': true,
          'OutlineStep': true,
          'ContentStep': true,
          'ExportStep': true,
          'ProgressIndicator': true
        }
      }
    })

    await nextTick()

    // 测试步骤前进
    wrapper.vm.handleNext()
    expect(axios.get).toHaveBeenCalledWith(
      '/api/tender/projects/test-id',
      { headers: { 'X-User-Id': 'test-user-id' } }
    )

    // 测试步骤后退
    wrapper.vm.handlePrev()
    expect(axios.get).toHaveBeenCalledWith(
      '/api/tender/projects/test-id',
      { headers: { 'X-User-Id': 'test-user-id' } }
    )
  })
})