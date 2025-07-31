"""
文档模板系统
提供专业的标书文档模板
"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT

from app.models.tender import AnalysisResult, OutlineStructure, ChapterContent


class BaseTemplate:
    """模板基类"""
    
    def __init__(self, template_name: str):
        self.template_name = template_name
        self.colors = self._get_color_scheme()
        self.fonts = self._get_font_scheme()
    
    def _get_color_scheme(self) -> Dict[str, Any]:
        """获取颜色方案"""
        return {
            'primary': colors.HexColor('#1f4e79'),      # 深蓝色
            'secondary': colors.HexColor('#4472c4'),    # 蓝色
            'accent': colors.HexColor('#70ad47'),       # 绿色
            'text': colors.black,
            'light_gray': colors.HexColor('#f2f2f2'),
            'medium_gray': colors.HexColor('#d9d9d9'),
            'dark_gray': colors.HexColor('#595959')
        }
    
    def _get_font_scheme(self) -> Dict[str, str]:
        """获取字体方案"""
        return {
            'title': 'Helvetica-Bold',
            'heading': 'Helvetica-Bold',
            'body': 'Helvetica',
            'caption': 'Helvetica'
        }


class StandardPDFTemplate(BaseTemplate):
    """标准PDF模板"""
    
    def __init__(self):
        super().__init__("standard")
        self.setup_styles()
    
    def setup_styles(self):
        """设置PDF样式"""
        styles = getSampleStyleSheet()
        
        # 文档标题样式
        self.title_style = ParagraphStyle(
            'DocumentTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            spaceBefore=20,
            alignment=TA_CENTER,
            textColor=self.colors['primary'],
            fontName=self.fonts['title']
        )
        
        # 章节标题样式
        self.chapter_title_style = ParagraphStyle(
            'ChapterTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=15,
            spaceBefore=25,
            textColor=self.colors['primary'],
            fontName=self.fonts['heading'],
            borderWidth=1,
            borderColor=self.colors['primary'],
            borderPadding=5
        )
        
        # 子标题样式
        self.subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15,
            textColor=self.colors['secondary'],
            fontName=self.fonts['heading']
        )
        
        # 正文样式
        self.body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            spaceBefore=2,
            alignment=TA_JUSTIFY,
            leftIndent=0,
            rightIndent=0,
            fontName=self.fonts['body'],
            leading=14
        )
        
        # 重点内容样式
        self.emphasis_style = ParagraphStyle(
            'Emphasis',
            parent=self.body_style,
            textColor=self.colors['accent'],
            fontName=self.fonts['heading'],
            backColor=self.colors['light_gray'],
            borderWidth=1,
            borderColor=self.colors['accent'],
            borderPadding=8
        )
        
        # 目录样式
        self.toc_title_style = ParagraphStyle(
            'TOCTitle',
            parent=self.body_style,
            fontSize=12,
            fontName=self.fonts['heading'],
            spaceAfter=4
        )
        
        self.toc_item_style = ParagraphStyle(
            'TOCItem',
            parent=self.body_style,
            fontSize=10,
            leftIndent=20,
            spaceAfter=2
        )
        
        # 表格标题样式
        self.table_title_style = ParagraphStyle(
            'TableTitle',
            parent=self.body_style,
            fontSize=10,
            fontName=self.fonts['heading'],
            alignment=TA_CENTER,
            spaceAfter=5
        )
    
    def get_table_style(self, header_bg: bool = True) -> TableStyle:
        """获取表格样式"""
        style_commands = [
            ('TEXTCOLOR', (0, 0), (-1, -1), self.colors['text']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.fonts['body']),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['medium_gray'])
        ]
        
        if header_bg:
            style_commands.extend([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), self.fonts['heading'])
            ])
        
        return TableStyle(style_commands)


class ProfessionalPDFTemplate(BaseTemplate):
    """专业PDF模板"""
    
    def __init__(self):
        super().__init__("professional")
        self.setup_styles()
    
    def setup_styles(self):
        """设置专业PDF样式"""
        styles = getSampleStyleSheet()
        
        # 更加正式的颜色方案
        self.colors.update({
            'primary': colors.HexColor('#2c3e50'),      # 深灰蓝
            'secondary': colors.HexColor('#34495e'),    # 灰蓝
            'accent': colors.HexColor('#e74c3c'),       # 红色强调
        })
        
        # 文档标题样式 - 更加正式
        self.title_style = ParagraphStyle(
            'DocumentTitle',
            parent=styles['Title'],
            fontSize=22,
            spaceAfter=40,
            spaceBefore=30,
            alignment=TA_CENTER,
            textColor=self.colors['primary'],
            fontName=self.fonts['title'],
            borderWidth=2,
            borderColor=self.colors['primary'],
            borderPadding=15
        )
        
        # 章节标题样式 - 带编号和装饰
        self.chapter_title_style = ParagraphStyle(
            'ChapterTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            spaceBefore=30,
            textColor=self.colors['primary'],
            fontName=self.fonts['heading'],
            backColor=self.colors['light_gray'],
            borderWidth=0,
            borderPadding=10,
            leftIndent=10
        )
        
        # 其他样式继承标准模板
        standard_template = StandardPDFTemplate()
        self.subtitle_style = standard_template.subtitle_style
        self.body_style = standard_template.body_style
        self.emphasis_style = standard_template.emphasis_style
        self.toc_title_style = standard_template.toc_title_style
        self.toc_item_style = standard_template.toc_item_style
        self.table_title_style = standard_template.table_title_style


class StandardWordTemplate(BaseTemplate):
    """标准Word模板"""
    
    def __init__(self):
        super().__init__("standard")
    
    def setup_document_styles(self, doc: Document):
        """设置Word文档样式"""
        styles = doc.styles
        
        # 文档标题样式
        if 'Document Title' not in [s.name for s in styles]:
            title_style = styles.add_style('Document Title', WD_STYLE_TYPE.PARAGRAPH)
            title_font = title_style.font
            title_font.name = 'Arial'
            title_font.size = Pt(24)
            title_font.bold = True
            title_font.color.rgb = RGBColor(31, 78, 121)  # 深蓝色
            title_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            title_style.paragraph_format.space_after = Pt(30)
            title_style.paragraph_format.space_before = Pt(20)
        
        # 章节标题样式
        if 'Chapter Title' not in [s.name for s in styles]:
            chapter_style = styles.add_style('Chapter Title', WD_STYLE_TYPE.PARAGRAPH)
            chapter_font = chapter_style.font
            chapter_font.name = 'Arial'
            chapter_font.size = Pt(16)
            chapter_font.bold = True
            chapter_font.color.rgb = RGBColor(31, 78, 121)
            chapter_style.paragraph_format.space_before = Pt(25)
            chapter_style.paragraph_format.space_after = Pt(15)
        
        # 子标题样式
        if 'Subtitle' not in [s.name for s in styles]:
            subtitle_style = styles.add_style('Subtitle', WD_STYLE_TYPE.PARAGRAPH)
            subtitle_font = subtitle_style.font
            subtitle_font.name = 'Arial'
            subtitle_font.size = Pt(14)
            subtitle_font.bold = True
            subtitle_font.color.rgb = RGBColor(68, 114, 196)  # 蓝色
            subtitle_style.paragraph_format.space_before = Pt(15)
            subtitle_style.paragraph_format.space_after = Pt(10)
        
        # 正文样式
        if 'Body Text' not in [s.name for s in styles]:
            body_style = styles.add_style('Body Text', WD_STYLE_TYPE.PARAGRAPH)
            body_font = body_style.font
            body_font.name = 'Arial'
            body_font.size = Pt(11)
            body_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            body_style.paragraph_format.space_after = Pt(8)
            body_style.paragraph_format.line_spacing = Pt(14)
        
        # 重点内容样式
        if 'Emphasis' not in [s.name for s in styles]:
            emphasis_style = styles.add_style('Emphasis', WD_STYLE_TYPE.PARAGRAPH)
            emphasis_font = emphasis_style.font
            emphasis_font.name = 'Arial'
            emphasis_font.size = Pt(11)
            emphasis_font.bold = True
            emphasis_font.color.rgb = RGBColor(112, 173, 71)  # 绿色
            emphasis_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            emphasis_style.paragraph_format.space_after = Pt(8)
        
        # 目录样式
        if 'TOC Title' not in [s.name for s in styles]:
            toc_title_style = styles.add_style('TOC Title', WD_STYLE_TYPE.PARAGRAPH)
            toc_title_font = toc_title_style.font
            toc_title_font.name = 'Arial'
            toc_title_font.size = Pt(12)
            toc_title_font.bold = True
            toc_title_style.paragraph_format.space_after = Pt(4)
        
        if 'TOC Item' not in [s.name for s in styles]:
            toc_item_style = styles.add_style('TOC Item', WD_STYLE_TYPE.PARAGRAPH)
            toc_item_font = toc_item_style.font
            toc_item_font.name = 'Arial'
            toc_item_font.size = Pt(10)
            toc_item_style.paragraph_format.left_indent = Inches(0.25)
            toc_item_style.paragraph_format.space_after = Pt(2)
    
    def setup_table_style(self, table):
        """设置表格样式"""
        # 设置表格对齐
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # 设置表格样式
        for row in table.rows:
            for cell in row.cells:
                # 设置单元格字体
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.name = 'Arial'
                        run.font.size = Pt(10)
                
                # 设置单元格边距
                cell.vertical_alignment = 1  # 垂直居中
        
        # 设置表头样式
        if len(table.rows) > 0:
            header_row = table.rows[0]
            for cell in header_row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)  # 白色文字


class ProfessionalWordTemplate(BaseTemplate):
    """专业Word模板"""
    
    def __init__(self):
        super().__init__("professional")
    
    def setup_document_styles(self, doc: Document):
        """设置专业Word文档样式"""
        # 先设置标准样式
        standard_template = StandardWordTemplate()
        standard_template.setup_document_styles(doc)
        
        # 修改为更专业的样式
        styles = doc.styles
        
        # 修改文档标题样式
        if 'Document Title' in [s.name for s in styles]:
            title_style = styles['Document Title']
            title_style.font.color.rgb = RGBColor(44, 62, 80)  # 深灰蓝
            title_style.font.size = Pt(22)
        
        # 修改章节标题样式
        if 'Chapter Title' in [s.name for s in styles]:
            chapter_style = styles['Chapter Title']
            chapter_style.font.color.rgb = RGBColor(44, 62, 80)
            chapter_style.font.size = Pt(18)


class TemplateManager:
    """模板管理器"""
    
    def __init__(self):
        self.pdf_templates = {
            'standard': StandardPDFTemplate,
            'professional': ProfessionalPDFTemplate
        }
        self.word_templates = {
            'standard': StandardWordTemplate,
            'professional': ProfessionalWordTemplate
        }
    
    def get_pdf_template(self, template_name: str = 'standard') -> BaseTemplate:
        """获取PDF模板"""
        template_class = self.pdf_templates.get(template_name, StandardPDFTemplate)
        return template_class()
    
    def get_word_template(self, template_name: str = 'standard') -> BaseTemplate:
        """获取Word模板"""
        template_class = self.word_templates.get(template_name, StandardWordTemplate)
        return template_class()
    
    def list_available_templates(self) -> Dict[str, List[str]]:
        """列出可用模板"""
        return {
            'pdf': list(self.pdf_templates.keys()),
            'word': list(self.word_templates.keys())
        }
    
    def validate_template_name(self, template_name: str, format_type: str) -> bool:
        """验证模板名称"""
        if format_type.lower() == 'pdf':
            return template_name in self.pdf_templates
        elif format_type.lower() in ['word', 'docx']:
            return template_name in self.word_templates
        return False


class DocumentFormatter:
    """文档格式化工具"""
    
    @staticmethod
    def format_project_info_table(analysis: AnalysisResult) -> List[List[str]]:
        """格式化项目信息表格"""
        project_info = analysis.project_info
        
        table_data = [
            ['项目信息', '详细内容']
        ]
        
        # 基本信息
        if project_info.get('project_name'):
            table_data.append(['项目名称', project_info['project_name']])
        if project_info.get('budget'):
            table_data.append(['项目预算', project_info['budget']])
        if project_info.get('duration'):
            table_data.append(['项目工期', project_info['duration']])
        if project_info.get('location'):
            table_data.append(['项目地点', project_info['location']])
        if project_info.get('contact_info'):
            table_data.append(['联系方式', project_info['contact_info']])
        if project_info.get('deadline'):
            table_data.append(['投标截止时间', project_info['deadline']])
        
        # 生成时间
        table_data.append(['文档生成时间', datetime.now().strftime('%Y年%m月%d日 %H:%M')])
        
        return table_data
    
    @staticmethod
    def format_technical_requirements_table(analysis: AnalysisResult) -> List[List[str]]:
        """格式化技术要求表格"""
        tech_req = analysis.technical_requirements
        
        table_data = [
            ['技术要求类别', '具体要求']
        ]
        
        if tech_req.get('functional_requirements'):
            reqs = tech_req['functional_requirements']
            if isinstance(reqs, list):
                table_data.append(['功能性要求', '\n'.join(reqs)])
            else:
                table_data.append(['功能性要求', str(reqs)])
        
        if tech_req.get('performance_requirements'):
            table_data.append(['性能要求', str(tech_req['performance_requirements'])])
        
        if tech_req.get('technical_specifications'):
            table_data.append(['技术规格', str(tech_req['technical_specifications'])])
        
        if tech_req.get('compliance_standards'):
            table_data.append(['合规标准', str(tech_req['compliance_standards'])])
        
        return table_data
    
    @staticmethod
    def format_evaluation_criteria_table(analysis: AnalysisResult) -> List[List[str]]:
        """格式化评分标准表格"""
        eval_criteria = analysis.evaluation_criteria
        
        table_data = [
            ['评分项目', '权重/标准', '具体要求']
        ]
        
        if eval_criteria.get('technical_score'):
            tech_score = eval_criteria['technical_score']
            if isinstance(tech_score, dict):
                weight = tech_score.get('weight', '未指定')
                criteria = tech_score.get('criteria', '未指定')
                table_data.append(['技术分', str(weight), str(criteria)])
            else:
                table_data.append(['技术分', '未指定', str(tech_score)])
        
        if eval_criteria.get('commercial_score'):
            comm_score = eval_criteria['commercial_score']
            if isinstance(comm_score, dict):
                weight = comm_score.get('weight', '未指定')
                criteria = comm_score.get('criteria', '未指定')
                table_data.append(['商务分', str(weight), str(criteria)])
            else:
                table_data.append(['商务分', '未指定', str(comm_score)])
        
        if eval_criteria.get('qualification_requirements'):
            table_data.append(['资质要求', '必需', str(eval_criteria['qualification_requirements'])])
        
        if eval_criteria.get('evaluation_method'):
            table_data.append(['评标方法', '说明', str(eval_criteria['evaluation_method'])])
        
        return table_data
    
    @staticmethod
    def split_content_into_paragraphs(content: str, max_length: int = 500) -> List[str]:
        """将长内容分割为段落"""
        if not content:
            return []
        
        # 首先按双换行符分割
        paragraphs = content.split('\n\n')
        
        # 如果段落太长，进一步分割
        result = []
        for para in paragraphs:
            if len(para) <= max_length:
                result.append(para.strip())
            else:
                # 按句号分割长段落
                sentences = para.split('。')
                current_para = ""
                
                for sentence in sentences:
                    if len(current_para + sentence + '。') <= max_length:
                        current_para += sentence + '。'
                    else:
                        if current_para:
                            result.append(current_para.strip())
                        current_para = sentence + '。'
                
                if current_para:
                    result.append(current_para.strip())
        
        return [p for p in result if p.strip()]
    
    @staticmethod
    def extract_key_points(content: str, max_points: int = 5) -> List[str]:
        """从内容中提取关键点"""
        if not content:
            return []
        
        # 简单的关键点提取逻辑
        sentences = content.split('。')
        key_points = []
        
        # 寻找包含关键词的句子
        keywords = ['重要', '关键', '核心', '主要', '首先', '其次', '最后', '特别', '尤其']
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and any(keyword in sentence for keyword in keywords):
                key_points.append(sentence + '。')
                if len(key_points) >= max_points:
                    break
        
        # 如果关键点不够，添加前几个句子
        if len(key_points) < max_points:
            for sentence in sentences[:max_points]:
                sentence = sentence.strip()
                if sentence and sentence + '。' not in key_points:
                    key_points.append(sentence + '。')
                    if len(key_points) >= max_points:
                        break
        
        return key_points


# 全局模板管理器实例
template_manager = TemplateManager()
document_formatter = DocumentFormatter()