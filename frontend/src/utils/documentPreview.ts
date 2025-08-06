// 文档预览工具类
import mammoth from 'mammoth'
import * as XLSX from 'xlsx'

export class DocumentPreviewService {
  /**
   * 获取文件预览URL
   */
  static getPreviewUrl(projectId: string, fileName: string): string {
    // 这里应该根据实际的文件存储方式来构建URL
    // 暂时使用模拟的URL
    return `/api/files/${projectId}/preview?filename=${encodeURIComponent(fileName)}`
  }

  /**
   * 获取文件下载URL
   */
  static getDownloadUrl(projectId: string, fileName: string): string {
    // 对于PDF文件，如果是演示模式，使用测试PDF
    if (this.isPdf(fileName)) {
      // 使用一个可以在iframe中显示的PDF
      return 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'
    }
    return `/api/files/${projectId}/download?filename=${encodeURIComponent(fileName)}`
  }

  /**
   * 检查是否为PDF文件
   */
  static isPdf(fileName: string): boolean {
    return /\.pdf$/i.test(fileName)
  }

  /**
   * 检查是否为Word文档
   */
  static isWord(fileName: string): boolean {
    return /\.(doc|docx)$/i.test(fileName)
  }

  /**
   * 检查是否为Excel文档
   */
  static isExcel(fileName: string): boolean {
    return /\.(xls|xlsx)$/i.test(fileName)
  }

  /**
   * 检查是否为图片文件
   */
  static isImage(fileName: string): boolean {
    return /\.(png|jpe?g|gif|bmp|webp|svg)$/i.test(fileName)
  }

  /**
   * 检查是否为文本文件
   */
  static isText(fileName: string): boolean {
    return /\.(txt|md|json|log|csv)$/i.test(fileName)
  }

  /**
   * 检查是否为Office文档
   */
  static isOffice(fileName: string): boolean {
    return this.isWord(fileName) || this.isExcel(fileName)
  }

  /**
   * 预览Word文档
   */
  static async previewWord(file: File | ArrayBuffer): Promise<string> {
    try {
      const arrayBuffer = file instanceof File ? await file.arrayBuffer() : file
      const result = await mammoth.convertToHtml({ arrayBuffer })
      return result.value
    } catch (error) {
      console.error('Word文档预览失败:', error)
      throw new Error('Word文档预览失败')
    }
  }

  /**
   * 预览Excel文档
   */
  static async previewExcel(file: File | ArrayBuffer): Promise<string> {
    try {
      const arrayBuffer = file instanceof File ? await file.arrayBuffer() : file
      const workbook = XLSX.read(arrayBuffer, { type: 'array' })
      
      let html = '<div class="excel-preview">'
      
      // 遍历所有工作表
      workbook.SheetNames.forEach((sheetName, index) => {
        const worksheet = workbook.Sheets[sheetName]
        html += `<div class="sheet-container">`
        html += `<h3 class="sheet-title">工作表: ${sheetName}</h3>`
        html += XLSX.utils.sheet_to_html(worksheet, { 
          id: `sheet-${index}`,
          editable: false 
        })
        html += '</div>'
      })
      
      html += '</div>'
      return html
    } catch (error) {
      console.error('Excel文档预览失败:', error)
      throw new Error('Excel文档预览失败')
    }
  }

  /**
   * 预览文本文件
   */
  static async previewText(file: File | string): Promise<string> {
    try {
      if (typeof file === 'string') {
        return file
      }
      return await file.text()
    } catch (error) {
      console.error('文本文件预览失败:', error)
      throw new Error('文本文件预览失败')
    }
  }

  /**
   * 从URL获取文件内容
   */
  static async fetchFileContent(url: string): Promise<ArrayBuffer> {
    try {
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      return await response.arrayBuffer()
    } catch (error) {
      console.error('获取文件内容失败:', error)
      throw new Error('获取文件内容失败')
    }
  }

  /**
   * 从URL获取文本内容
   */
  static async fetchTextContent(url: string): Promise<string> {
    try {
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      return await response.text()
    } catch (error) {
      console.error('获取文本内容失败:', error)
      throw new Error('获取文本内容失败')
    }
  }

  /**
   * 生成PDF预览URL（使用PDF.js或浏览器内置预览）
   */
  static getPdfViewerUrl(fileUrl: string): string {
    // 可以使用PDF.js viewer
    // return `/pdfjs/web/viewer.html?file=${encodeURIComponent(fileUrl)}`
    
    // 或者直接使用浏览器内置预览
    return fileUrl
  }

  /**
   * 创建模拟文件内容（用于演示）
   */
  static createMockContent(fileName: string): string {
    const fileType = this.getFileType(fileName)
    
    switch (fileType) {
      case 'pdf':
        return '这是一个PDF文档的模拟内容。实际应用中，这里会显示PDF的预览。'
      case 'word':
        return `
          <div class="word-preview">
            <h1>招标文件</h1>
            <h2>项目概述</h2>
            <p>本项目是关于某某系统的建设项目，旨在提升业务处理效率和用户体验。</p>
            <h2>技术要求</h2>
            <ul>
              <li>系统架构：采用微服务架构</li>
              <li>开发语言：Java、JavaScript</li>
              <li>数据库：MySQL、Redis</li>
              <li>部署方式：Docker容器化部署</li>
            </ul>
            <h2>项目时间</h2>
            <p>项目开发周期为6个月，分为需求分析、系统设计、开发实施、测试验收四个阶段。</p>
          </div>
        `
      case 'excel':
        return `
          <div class="excel-preview">
            <h3>工作表: 项目预算</h3>
            <table border="1" style="border-collapse: collapse; width: 100%;">
              <tr style="background-color: #f0f0f0;">
                <th>项目</th>
                <th>数量</th>
                <th>单价</th>
                <th>总价</th>
              </tr>
              <tr>
                <td>系统开发</td>
                <td>1</td>
                <td>500,000</td>
                <td>500,000</td>
              </tr>
              <tr>
                <td>系统测试</td>
                <td>1</td>
                <td>100,000</td>
                <td>100,000</td>
              </tr>
              <tr>
                <td>项目管理</td>
                <td>1</td>
                <td>50,000</td>
                <td>50,000</td>
              </tr>
              <tr style="background-color: #f0f0f0; font-weight: bold;">
                <td>总计</td>
                <td>-</td>
                <td>-</td>
                <td>650,000</td>
              </tr>
            </table>
          </div>
        `
      case 'text':
        return `项目名称：某某信息系统建设项目
项目编号：2024-001
发布时间：2024年1月15日

一、项目概述
本项目旨在建设一套完整的信息管理系统，提升业务处理效率。

二、技术要求
1. 系统架构：B/S架构
2. 开发技术：Java + Vue.js
3. 数据库：MySQL 8.0+
4. 服务器：Linux CentOS 7+

三、项目周期
总工期：6个月
- 需求分析：1个月
- 系统设计：1个月  
- 开发实施：3个月
- 测试验收：1个月

四、投标要求
1. 具有软件开发资质
2. 有类似项目经验
3. 技术团队不少于10人`
      default:
        return '暂不支持该文件格式的预览'
    }
  }

  /**
   * 获取文件类型
   */
  private static getFileType(fileName: string): string {
    if (this.isPdf(fileName)) return 'pdf'
    if (this.isWord(fileName)) return 'word'
    if (this.isExcel(fileName)) return 'excel'
    if (this.isImage(fileName)) return 'image'
    if (this.isText(fileName)) return 'text'
    return 'unknown'
  }
}