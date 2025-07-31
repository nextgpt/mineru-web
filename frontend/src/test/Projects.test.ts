import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import Projects from '@/views/Projects.vue'
import axios from 'axios'

// Mock axios
vi.mocked(axios.get).mockResolvedValue({
  data: {
    projects: [
      {
        id: 'project-1',
        project_name: '测试项目1',
        source_filename: 'test1.pdf',
        status: 'completed',
        created_at: '2024-01-01T00:00:00',
        updated_at: '2024-01-01T00:00:00'
      },
      {
        id: 'project-2',
        project_name: '测试项目2',
        source_filename: 'test2.pdf',
        status: 'analyzing',
        progress: 50,
        created_at: '2024-01-02T00:00:00',
        updated_at: '2024-01-02T00:00:00'
      }
    ],
    total: 2
  }
})

describe('Projects.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders project list correctly', async () => {
    const wrapper = mount(Projects, {
      global: {
        stubs: {
          'el-button': true,
          'el-input': true,
          'el-select': true,
          'el-option': true,
          'el-tag': true,
          'el-icon': true,
          'el-progress': true,
          'el-dropdown': true,
          'el-dropdown-menu': true,
          'el-dropdown-item': true,
          'el-pagination': true,
          'el-empty': true,
          'el-skeleton': true,
          'el-dialog': true,
          'el-form': true,
          'el-form-item': true,
          'router-link': true
        }
      }
    })

    await nextTick()

    // 检查页面标题
    expect(wrapper.find('.projects-title').text()).toBe('项目管理')
    expect(wrapper.find('.projects-subtitle').text()).toBe('管理您的招标项目')

    // 检查项目卡片
    const projectCards = wrapper.findAll('.project-card')
    expect(projectCards).toHaveLength(2)

    // 检查第一个项目
    const firstCard = projectCards[0]
    expect(firstCard.find('.project-title').text()).toBe('测试项目1')
    expect(firstCard.find('.project-info').text()).toContain('test1.pdf')
  })

  it('handles search functionality', async () => {
    const wrapper = mount(Projects, {
      global: {
        stubs: {
          'el-button': true,
          'el-input': { template: '<input v-model="modelValue" @input="$emit(\'input\')" />' },
          'el-select': true,
          'el-option': true,
          'el-tag': true,
          'el-icon': true,
          'el-progress': true,
          'el-dropdown': true,
          'el-dropdown-menu': true,
          'el-dropdown-item': true,
          'el-pagination': true,
          'el-empty': true,
          'el-skeleton': true,
          'el-dialog': true,
          'el-form': true,
          'el-form-item': true,
          'router-link': true
        }
      }
    })

    await nextTick()

    // 模拟搜索输入
    const searchInput = wrapper.find('.search-input input')
    await searchInput.setValue('测试项目1')
    await searchInput.trigger('input')

    // 验证API调用
    expect(axios.get).toHaveBeenCalledWith('/api/tender/projects', {
      params: expect.objectContaining({
        search: '测试项目1'
      }),
      headers: { 'X-User-Id': 'test-user-id' }
    })
  })

  it('opens project detail when card is clicked', async () => {
    const mockPush = vi.fn()
    const wrapper = mount(Projects, {
      global: {
        mocks: {
          $router: { push: mockPush }
        },
        stubs: {
          'el-button': true,
          'el-input': true,
          'el-select': true,
          'el-option': true,
          'el-tag': true,
          'el-icon': true,
          'el-progress': true,
          'el-dropdown': true,
          'el-dropdown-menu': true,
          'el-dropdown-item': true,
          'el-pagination': true,
          'el-empty': true,
          'el-skeleton': true,
          'el-dialog': true,
          'el-form': true,
          'el-form-item': true,
          'router-link': true
        }
      }
    })

    await nextTick()

    // 点击项目卡片
    const projectCard = wrapper.find('.project-card')
    await projectCard.trigger('click')

    // 验证路由跳转
    expect(mockPush).toHaveBeenCalledWith('/projects/project-1')
  })

  it('shows create project dialog', async () => {
    const wrapper = mount(Projects, {
      global: {
        stubs: {
          'el-button': { template: '<button @click="$emit(\'click\')"><slot /></button>' },
          'el-input': true,
          'el-select': true,
          'el-option': true,
          'el-tag': true,
          'el-icon': true,
          'el-progress': true,
          'el-dropdown': true,
          'el-dropdown-menu': true,
          'el-dropdown-item': true,
          'el-pagination': true,
          'el-empty': true,
          'el-skeleton': true,
          'el-dialog': true,
          'el-form': true,
          'el-form-item': true,
          'router-link': true
        }
      }
    })

    await nextTick()

    // 点击新建项目按钮
    const createButton = wrapper.find('.create-btn')
    await createButton.trigger('click')

    // 验证对话框显示状态
    expect(wrapper.vm.showCreateDialog).toBe(true)
  })

  it('handles project status correctly', async () => {
    const wrapper = mount(Projects, {
      global: {
        stubs: {
          'el-button': true,
          'el-input': true,
          'el-select': true,
          'el-option': true,
          'el-tag': true,
          'el-icon': true,
          'el-progress': true,
          'el-dropdown': true,
          'el-dropdown-menu': true,
          'el-dropdown-item': true,
          'el-pagination': true,
          'el-empty': true,
          'el-skeleton': true,
          'el-dialog': true,
          'el-form': true,
          'el-form-item': true,
          'router-link': true
        }
      }
    })

    await nextTick()

    // 测试状态文本转换
    expect(wrapper.vm.getStatusText('analyzing')).toBe('分析中')
    expect(wrapper.vm.getStatusText('completed')).toBe('已完成')
    expect(wrapper.vm.getStatusText('failed')).toBe('失败')

    // 测试状态类型转换
    expect(wrapper.vm.getStatusType('analyzing')).toBe('warning')
    expect(wrapper.vm.getStatusType('completed')).toBe('success')
    expect(wrapper.vm.getStatusType('failed')).toBe('danger')
  })

  it('handles pagination correctly', async () => {
    const wrapper = mount(Projects, {
      global: {
        stubs: {
          'el-button': true,
          'el-input': true,
          'el-select': true,
          'el-option': true,
          'el-tag': true,
          'el-icon': true,
          'el-progress': true,
          'el-dropdown': true,
          'el-dropdown-menu': true,
          'el-dropdown-item': true,
          'el-pagination': { 
            template: '<div @current-change="$emit(\'current-change\', 2)" @size-change="$emit(\'size-change\', 24)"></div>' 
          },
          'el-empty': true,
          'el-skeleton': true,
          'el-dialog': true,
          'el-form': true,
          'el-form-item': true,
          'router-link': true
        }
      }
    })

    await nextTick()

    // 模拟分页变化
    const pagination = wrapper.find('.pagination-container')
    await pagination.trigger('current-change')
    await pagination.trigger('size-change')

    // 验证参数更新
    expect(wrapper.vm.params.page).toBe(2)
    expect(wrapper.vm.params.pageSize).toBe(24)
  })
})