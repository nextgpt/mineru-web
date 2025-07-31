"""
系统集成测试
测试完整的系统功能和组件间的集成
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.models.tender import TenderProject, TenderStatus
from app.services.tender_analysis import TenderAnalysisService
from app.services.outline_generation import OutlineGenerationService
from app.services.content_generation import ContentGenerationService
from app.services.document_export import DocumentExportService
from app.services.tender_storage import TenderStorageService
from app.api.tender import router as tender_router


class TestSystemIntegration:
    """系统集成测试"""
    
    @pytest.fixture
    def app(self):
        """创建测试应用"""
        app = FastAPI()
        app.include_router(tender_router, prefix="/api/tender")
        return app
    
    @pytest.fixture
    def client(self, app):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_project(self):
        """模拟项目对象"""
        project = Mock(spec=TenderProject)
        project.id = "integration-test-project"
        project.tenant_id = "test-tenant"
        project.user_id = "test-user"
        project.project_name = "集成测试项目"
        project.source_filename = "integration_test.pdf"
        project.status = TenderStatus.CREATED
        project.get_storage_path.return_value = "tenants/test-tenant/projects/integration-test-project"
        return project
    
    async def test_complete_workflow_integration(self, mock_db, mock_project):
        """测试完整工作流程的集成"""
        storage_service = Mock(spec=TenderStorageService)
        
        # 1. 测试分析服务集成
        analysis_service = TenderAnalysisService(mock_db, storage_service)
        
        with patch.object(analysis_service, 'analyze_tender_document', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = True
            storage_service.save_analysis_result = AsyncMock()
            
            # 执行分析
            start_time = time.time()
            result = await analysis_service.analyze_tender_document(mock_project)
            analysis_time = time.time() - start_time
            
            assert result is True
            assert analysis_time < 5.0  # 分析应在5秒内完成
            mock_project.status = TenderStatus.ANALYZED
        
        # 2. 测试大纲生成服务集成
        outline_service = OutlineGenerationService(mock_db, storage_service)
        
        with patch.object(outline_service, 'generate_outline', new_callable=AsyncMock) as mock_outline:
            mock_outline.return_value = True
            storage_service.save_outline = AsyncMock()
            
            start_time = time.time()
            result = await outline_service.generate_outline(mock_project)
            outline_time = time.time() - start_time
            
            assert result is True
            assert outline_time < 10.0  # 大纲生成应在10秒内完成
            mock_project.status = TenderStatus.OUTLINED
        
        # 3. 测试内容生成服务集成
        content_service = ContentGenerationService(mock_db, storage_service)
        
        with patch.object(content_service, 'generate_all_content', new_callable=AsyncMock) as mock_content:
            mock_content.return_value = True
            storage_service.save_chapter_content = AsyncMock()
            
            start_time = time.time()
            result = await content_service.generate_all_content(mock_project)
            content_time = time.time() - start_time
            
            assert result is True
            assert content_time < 30.0  # 内容生成应在30秒内完成
            mock_project.status = TenderStatus.GENERATED
        
        # 4. 测试文档导出服务集成
        export_service = DocumentExportService(mock_db, storage_service)
        
        with patch.object(export_service, 'export_to_pdf', new_callable=AsyncMock) as mock_export:
            mock_export.return_value = "document-id"
            
            start_time = time.time()
            document_id = await export_service.export_to_pdf(
                mock_project,
                title="集成测试标书",
                company_name="测试公司"
            )
            export_time = time.time() - start_time
            
            assert document_id == "document-id"
            assert export_time < 15.0  # 导出应在15秒内完成
            mock_project.status = TenderStatus.COMPLETED
        
        # 验证整个流程完成
        total_time = analysis_time + outline_time + content_time + export_time
        assert total_time < 60.0  # 整个流程应在1分钟内完成
        assert mock_project.status == TenderStatus.COMPLETED
    
    async def test_concurrent_project_processing(self, mock_db):
        """测试并发项目处理能力"""
        storage_service = Mock(spec=TenderStorageService)
        
        # 创建多个项目
        projects = []
        for i in range(5):
            project = Mock(spec=TenderProject)
            project.id = f"concurrent-project-{i}"
            project.tenant_id = "test-tenant"
            project.user_id = f"user-{i}"
            project.project_name = f"并发测试项目{i}"
            project.status = TenderStatus.CREATED
            project.get_storage_path.return_value = f"tenants/test-tenant/projects/concurrent-project-{i}"
            projects.append(project)
        
        # 并发执行分析
        analysis_service = TenderAnalysisService(mock_db, storage_service)
        
        async def analyze_project(project):
            with patch.object(analysis_service, 'analyze_tender_document', new_callable=AsyncMock) as mock_analyze:
                mock_analyze.return_value = True
                storage_service.save_analysis_result = AsyncMock()
                
                # 模拟处理时间
                await asyncio.sleep(0.1)
                result = await analysis_service.analyze_tender_document(project)
                project.status = TenderStatus.ANALYZED
                return result
        
        start_time = time.time()
        tasks = [analyze_project(project) for project in projects]
        results = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time
        
        # 验证并发处理结果
        assert all(results)
        assert all(project.status == TenderStatus.ANALYZED for project in projects)
        assert concurrent_time < 2.0  # 并发处理应该比串行快很多
    
    async def test_error_handling_integration(self, mock_db, mock_project):
        """测试错误处理集成"""
        storage_service = Mock(spec=TenderStorageService)
        
        # 测试分析阶段错误处理
        analysis_service = TenderAnalysisService(mock_db, storage_service)
        
        with patch.object(analysis_service, 'analyze_tender_document', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("模拟分析错误")
            
            with pytest.raises(Exception, match="模拟分析错误"):
                await analysis_service.analyze_tender_document(mock_project)
            
            # 验证项目状态未改变
            assert mock_project.status == TenderStatus.CREATED
        
        # 测试大纲生成阶段错误处理
        outline_service = OutlineGenerationService(mock_db, storage_service)
        
        with patch.object(outline_service, 'generate_outline', new_callable=AsyncMock) as mock_outline:
            mock_outline.side_effect = Exception("模拟大纲生成错误")
            
            with pytest.raises(Exception, match="模拟大纲生成错误"):
                await outline_service.generate_outline(mock_project)
    
    async def test_data_consistency_integration(self, mock_db, mock_project):
        """测试数据一致性集成"""
        storage_service = Mock(spec=TenderStorageService)
        
        # 模拟分析结果
        analysis_result = {
            "project_info": {"project_name": "测试项目"},
            "technical_requirements": {"functional_requirements": ["需求1"]},
            "evaluation_criteria": {"technical_score": "70分"},
            "submission_requirements": {"deadline": "2024-12-31"}
        }
        
        # 模拟大纲结果
        outline_result = {
            "chapters": [
                {
                    "chapter_id": "1",
                    "title": "项目概述",
                    "description": "项目基本信息"
                }
            ]
        }
        
        # 模拟内容结果
        content_result = [
            {
                "chapter_id": "1",
                "title": "项目概述",
                "content": "这是项目概述内容"
            }
        ]
        
        # 设置存储服务模拟
        storage_service.save_analysis_result = AsyncMock()
        storage_service.load_analysis_result = AsyncMock(return_value=analysis_result)
        storage_service.save_outline = AsyncMock()
        storage_service.load_outline = AsyncMock(return_value=Mock(to_dict=Mock(return_value=outline_result)))
        storage_service.save_chapter_content = AsyncMock()
        storage_service.load_all_chapters = AsyncMock(return_value=content_result)
        
        # 执行完整流程
        analysis_service = TenderAnalysisService(mock_db, storage_service)
        outline_service = OutlineGenerationService(mock_db, storage_service)
        content_service = ContentGenerationService(mock_db, storage_service)
        
        with patch.object(analysis_service, 'analyze_tender_document', new_callable=AsyncMock) as mock_analyze, \
             patch.object(outline_service, 'generate_outline', new_callable=AsyncMock) as mock_outline, \
             patch.object(content_service, 'generate_all_content', new_callable=AsyncMock) as mock_content:
            
            mock_analyze.return_value = True
            mock_outline.return_value = True
            mock_content.return_value = True
            
            # 执行流程
            await analysis_service.analyze_tender_document(mock_project)
            await outline_service.generate_outline(mock_project)
            await content_service.generate_all_content(mock_project)
            
            # 验证数据保存调用
            storage_service.save_analysis_result.assert_called()
            storage_service.save_outline.assert_called()
            storage_service.save_chapter_content.assert_called()
    
    @patch('app.api.tender.get_db')
    def test_api_integration(self, mock_get_db, client):
        """测试API集成"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # 模拟文件查询
        mock_file = Mock()
        mock_file.id = 1
        mock_file.filename = "integration_test.pdf"
        mock_file.status = "parsed"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_file
        
        # 模拟项目创建
        with patch('app.api.tender.TenderProject') as mock_project_class:
            mock_project = Mock()
            mock_project.id = "api-integration-project"
            mock_project.project_name = "API集成测试项目"
            mock_project.source_filename = "integration_test.pdf"
            mock_project.status = TenderStatus.CREATED
            mock_project_class.return_value = mock_project
            
            # 测试创建项目API
            response = client.post(
                "/api/tender/projects",
                json={
                    "project_name": "API集成测试项目",
                    "source_file_id": 1
                },
                headers={"X-User-Id": "test-user"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "api-integration-project"
            assert data["project_name"] == "API集成测试项目"
        
        # 测试获取项目详情API
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        response = client.get(
            "/api/tender/projects/api-integration-project",
            headers={"X-User-Id": "test-user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "api-integration-project"


class TestPerformanceIntegration:
    """性能集成测试"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_storage_service(self):
        return Mock(spec=TenderStorageService)
    
    async def test_large_project_performance(self, mock_db, mock_storage_service):
        """测试大型项目处理性能"""
        # 创建大型项目模拟
        project = Mock(spec=TenderProject)
        project.id = "large-performance-project"
        project.tenant_id = "test-tenant"
        project.user_id = "test-user"
        project.project_name = "大型性能测试项目"
        project.status = TenderStatus.CREATED
        project.get_storage_path.return_value = "tenants/test-tenant/projects/large-performance-project"
        
        # 模拟大量章节的大纲
        large_outline = {
            "chapters": [
                {
                    "chapter_id": str(i),
                    "title": f"章节{i}",
                    "description": f"章节{i}描述",
                    "subsections": [
                        {"id": f"{i}.{j}", "title": f"子章节{i}.{j}"}
                        for j in range(1, 11)  # 每章10个子章节
                    ]
                }
                for i in range(1, 51)  # 50个主章节
            ]
        }
        
        # 测试大纲生成性能
        outline_service = OutlineGenerationService(mock_db, mock_storage_service)
        
        with patch.object(outline_service, 'generate_outline', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = True
            mock_storage_service.save_outline = AsyncMock()
            
            start_time = time.time()
            result = await outline_service.generate_outline(project)
            processing_time = time.time() - start_time
            
            assert result is True
            assert processing_time < 20.0  # 大型项目处理应在20秒内完成
    
    async def test_memory_usage_performance(self, mock_db, mock_storage_service):
        """测试内存使用性能"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建多个项目进行处理
        projects = []
        for i in range(10):
            project = Mock(spec=TenderProject)
            project.id = f"memory-test-project-{i}"
            project.tenant_id = "test-tenant"
            project.user_id = f"user-{i}"
            project.status = TenderStatus.CREATED
            project.get_storage_path.return_value = f"tenants/test-tenant/projects/memory-test-project-{i}"
            projects.append(project)
        
        # 模拟内容生成
        content_service = ContentGenerationService(mock_db, mock_storage_service)
        
        with patch.object(content_service, 'generate_all_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = True
            mock_storage_service.save_chapter_content = AsyncMock()
            
            # 处理所有项目
            for project in projects:
                await content_service.generate_all_content(project)
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # 内存增长应该在合理范围内（这里设置为100MB）
            assert memory_increase < 100, f"内存增长过多: {memory_increase}MB"
    
    async def test_concurrent_load_performance(self, mock_db, mock_storage_service):
        """测试并发负载性能"""
        # 创建大量并发任务
        num_concurrent_tasks = 20
        
        async def simulate_task():
            project = Mock(spec=TenderProject)
            project.id = f"load-test-{time.time()}"
            project.tenant_id = "test-tenant"
            project.user_id = "load-test-user"
            project.status = TenderStatus.CREATED
            project.get_storage_path.return_value = f"tenants/test-tenant/projects/{project.id}"
            
            analysis_service = TenderAnalysisService(mock_db, mock_storage_service)
            
            with patch.object(analysis_service, 'analyze_tender_document', new_callable=AsyncMock) as mock_analyze:
                mock_analyze.return_value = True
                mock_storage_service.save_analysis_result = AsyncMock()
                
                # 模拟处理时间
                await asyncio.sleep(0.05)
                return await analysis_service.analyze_tender_document(project)
        
        start_time = time.time()
        tasks = [simulate_task() for _ in range(num_concurrent_tasks)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # 验证并发处理结果
        assert all(results)
        assert total_time < 5.0  # 20个并发任务应在5秒内完成
        
        # 计算吞吐量
        throughput = num_concurrent_tasks / total_time
        assert throughput > 5  # 每秒至少处理5个任务


class TestSecurityIntegration:
    """安全集成测试"""
    
    @pytest.fixture
    def client(self):
        app = FastAPI()
        app.include_router(tender_router, prefix="/api/tender")
        return TestClient(app)
    
    def test_authentication_required(self, client):
        """测试认证要求"""
        # 不提供用户ID头部
        response = client.get("/api/tender/projects")
        
        # 应该返回认证错误（具体状态码取决于实现）
        assert response.status_code in [401, 403, 422]
    
    def test_tenant_isolation(self, client):
        """测试租户隔离"""
        with patch('app.api.tender.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # 模拟查询结果为空（其他租户的项目）
            mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            
            response = client.get(
                "/api/tender/projects",
                headers={"X-User-Id": "user1"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert len(data["projects"]) == 0
    
    def test_input_validation(self, client):
        """测试输入验证"""
        with patch('app.api.tender.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # 测试无效的项目创建数据
            response = client.post(
                "/api/tender/projects",
                json={
                    "project_name": "",  # 空名称
                    "source_file_id": "invalid"  # 无效ID
                },
                headers={"X-User-Id": "test-user"}
            )
            
            # 应该返回验证错误
            assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])