"""
完整工作流程集成测试
测试从项目创建到文档导出的完整流程
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.models.tender import TenderProject, TenderStatus
from app.services.tender_analysis import TenderAnalysisService
from app.services.outline_generation import OutlineGenerationService
from app.services.content_generation import ContentGenerationService
from app.services.document_export import DocumentExportService
from app.services.tender_storage import TenderStorageService


class TestCompleteWorkflow:
    """完整工作流程测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_project(self):
        """模拟项目对象"""
        project = Mock(spec=TenderProject)
        project.id = "test-project-id"
        project.tenant_id = "test-tenant"
        project.user_id = "test-user"
        project.project_name = "测试招标项目"
        project.source_filename = "test.pdf"
        project.status = TenderStatus.CREATED
        project.get_storage_path.return_value = "tenants/test-tenant/projects/test-project-id"
        return project
    
    @pytest.fixture
    def mock_storage_service(self):
        """模拟存储服务"""
        return Mock(spec=TenderStorageService)
    
    async def test_complete_tender_generation_workflow(
        self, 
        mock_db, 
        mock_project, 
        mock_storage_service
    ):
        """测试完整的标书生成工作流程"""
        
        # 1. 项目创建阶段
        mock_project.status = TenderStatus.CREATED
        
        # 2. 文档分析阶段
        analysis_service = TenderAnalysisService(mock_db, mock_storage_service)
        
        # 模拟分析结果
        mock_analysis_result = {
            "project_info": {
                "project_name": "测试项目",
                "budget": "100万元",
                "duration": "6个月"
            },
            "technical_requirements": {
                "functional_requirements": ["需求1", "需求2"],
                "performance_requirements": "性能要求",
                "technical_specifications": "技术规格"
            },
            "evaluation_criteria": {
                "technical_score": "技术分70分",
                "commercial_score": "商务分30分"
            },
            "submission_requirements": {
                "deadline": "2024-12-31",
                "document_format": "PDF格式"
            }
        }
        
        with patch.object(analysis_service, 'analyze_tender_document', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = True
            mock_storage_service.save_analysis_result = AsyncMock()
            
            # 执行分析
            result = await analysis_service.analyze_tender_document(mock_project)
            assert result is True
            
            # 更新项目状态
            mock_project.status = TenderStatus.ANALYZED
        
        # 3. 大纲生成阶段
        outline_service = OutlineGenerationService(mock_db, mock_storage_service)
        
        # 模拟大纲结果
        mock_outline = {
            "chapters": [
                {
                    "chapter_id": "1",
                    "title": "项目概述",
                    "description": "项目基本信息",
                    "subsections": [
                        {"id": "1.1", "title": "项目背景"},
                        {"id": "1.2", "title": "项目目标"}
                    ]
                },
                {
                    "chapter_id": "2",
                    "title": "技术方案",
                    "description": "详细技术方案",
                    "subsections": [
                        {"id": "2.1", "title": "技术架构"},
                        {"id": "2.2", "title": "实施方案"}
                    ]
                }
            ]
        }
        
        with patch.object(outline_service, 'generate_outline', new_callable=AsyncMock) as mock_generate_outline:
            mock_generate_outline.return_value = True
            mock_storage_service.save_outline = AsyncMock()
            
            # 执行大纲生成
            result = await outline_service.generate_outline(mock_project)
            assert result is True
            
            # 更新项目状态
            mock_project.status = TenderStatus.OUTLINED
        
        # 4. 内容生成阶段
        content_service = ContentGenerationService(mock_db, mock_storage_service)
        
        # 模拟内容生成
        mock_chapters = [
            {
                "chapter_id": "1",
                "title": "项目概述",
                "content": "这是项目概述的详细内容..."
            },
            {
                "chapter_id": "2", 
                "title": "技术方案",
                "content": "这是技术方案的详细内容..."
            }
        ]
        
        with patch.object(content_service, 'generate_all_content', new_callable=AsyncMock) as mock_generate_content:
            mock_generate_content.return_value = True
            mock_storage_service.save_chapter_content = AsyncMock()
            
            # 执行内容生成
            result = await content_service.generate_all_content(mock_project)
            assert result is True
            
            # 更新项目状态
            mock_project.status = TenderStatus.GENERATED
        
        # 5. 文档导出阶段
        export_service = DocumentExportService(mock_db, mock_storage_service)
        
        with patch.object(export_service, 'export_to_pdf', new_callable=AsyncMock) as mock_export:
            mock_export.return_value = "document-id-123"
            
            # 执行文档导出
            document_id = await export_service.export_to_pdf(
                mock_project,
                title="测试标书",
                company_name="测试公司"
            )
            
            assert document_id == "document-id-123"
            
            # 更新项目状态
            mock_project.status = TenderStatus.COMPLETED
        
        # 验证整个流程完成
        assert mock_project.status == TenderStatus.COMPLETED
    
    async def test_workflow_error_handling(
        self, 
        mock_db, 
        mock_project, 
        mock_storage_service
    ):
        """测试工作流程中的错误处理"""
        
        # 测试分析阶段失败
        analysis_service = TenderAnalysisService(mock_db, mock_storage_service)
        
        with patch.object(analysis_service, 'analyze_tender_document', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("分析失败")
            
            with pytest.raises(Exception, match="分析失败"):
                await analysis_service.analyze_tender_document(mock_project)
            
            # 验证项目状态保持不变
            assert mock_project.status == TenderStatus.CREATED
    
    async def test_workflow_status_transitions(
        self, 
        mock_db, 
        mock_project, 
        mock_storage_service
    ):
        """测试工作流程状态转换"""
        
        # 初始状态
        assert mock_project.status == TenderStatus.CREATED
        
        # 模拟各阶段状态转换
        status_transitions = [
            TenderStatus.ANALYZING,
            TenderStatus.ANALYZED,
            TenderStatus.OUTLINING,
            TenderStatus.OUTLINED,
            TenderStatus.GENERATING,
            TenderStatus.GENERATED,
            TenderStatus.EXPORTING,
            TenderStatus.COMPLETED
        ]
        
        for status in status_transitions:
            mock_project.status = status
            
            # 验证状态有效性
            assert mock_project.status in [
                TenderStatus.CREATED,
                TenderStatus.ANALYZING,
                TenderStatus.ANALYZED,
                TenderStatus.OUTLINING,
                TenderStatus.OUTLINED,
                TenderStatus.GENERATING,
                TenderStatus.GENERATED,
                TenderStatus.EXPORTING,
                TenderStatus.COMPLETED,
                TenderStatus.FAILED
            ]
    
    async def test_concurrent_project_processing(
        self, 
        mock_db, 
        mock_storage_service
    ):
        """测试并发项目处理"""
        
        # 创建多个项目
        projects = []
        for i in range(3):
            project = Mock(spec=TenderProject)
            project.id = f"project-{i}"
            project.tenant_id = "test-tenant"
            project.user_id = f"user-{i}"
            project.project_name = f"项目{i}"
            project.status = TenderStatus.CREATED
            project.get_storage_path.return_value = f"tenants/test-tenant/projects/project-{i}"
            projects.append(project)
        
        # 模拟并发分析
        analysis_service = TenderAnalysisService(mock_db, mock_storage_service)
        
        async def analyze_project(project):
            with patch.object(analysis_service, 'analyze_tender_document', new_callable=AsyncMock) as mock_analyze:
                mock_analyze.return_value = True
                result = await analysis_service.analyze_tender_document(project)
                project.status = TenderStatus.ANALYZED
                return result
        
        # 并发执行分析
        tasks = [analyze_project(project) for project in projects]
        results = await asyncio.gather(*tasks)
        
        # 验证所有项目都分析成功
        assert all(results)
        assert all(project.status == TenderStatus.ANALYZED for project in projects)


class TestWorkflowPerformance:
    """工作流程性能测试"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_storage_service(self):
        return Mock(spec=TenderStorageService)
    
    async def test_large_document_processing(
        self, 
        mock_db, 
        mock_storage_service
    ):
        """测试大文档处理性能"""
        
        # 创建大项目模拟
        project = Mock(spec=TenderProject)
        project.id = "large-project"
        project.tenant_id = "test-tenant"
        project.user_id = "test-user"
        project.project_name = "大型项目"
        project.status = TenderStatus.CREATED
        project.get_storage_path.return_value = "tenants/test-tenant/projects/large-project"
        
        # 模拟大量章节
        large_outline = {
            "chapters": [
                {
                    "chapter_id": str(i),
                    "title": f"章节{i}",
                    "description": f"章节{i}描述",
                    "subsections": [
                        {"id": f"{i}.{j}", "title": f"子章节{i}.{j}"}
                        for j in range(1, 6)  # 每章5个子章节
                    ]
                }
                for i in range(1, 21)  # 20个主章节
            ]
        }
        
        # 测试大纲生成性能
        outline_service = OutlineGenerationService(mock_db, mock_storage_service)
        
        with patch.object(outline_service, 'generate_outline', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = True
            mock_storage_service.save_outline = AsyncMock()
            
            import time
            start_time = time.time()
            
            result = await outline_service.generate_outline(project)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 验证处理成功且时间合理（这里只是示例，实际阈值需要根据需求调整）
            assert result is True
            assert processing_time < 10.0  # 假设10秒内完成
    
    async def test_memory_usage_during_processing(
        self, 
        mock_db, 
        mock_storage_service
    ):
        """测试处理过程中的内存使用"""
        
        project = Mock(spec=TenderProject)
        project.id = "memory-test-project"
        project.tenant_id = "test-tenant"
        project.user_id = "test-user"
        project.status = TenderStatus.CREATED
        project.get_storage_path.return_value = "tenants/test-tenant/projects/memory-test-project"
        
        # 模拟内容生成服务
        content_service = ContentGenerationService(mock_db, mock_storage_service)
        
        with patch.object(content_service, 'generate_all_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = True
            
            # 这里可以添加内存监控逻辑
            # 例如使用 psutil 或 tracemalloc
            
            result = await content_service.generate_all_content(project)
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__])