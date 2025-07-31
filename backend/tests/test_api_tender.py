"""
招标API接口测试
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.tender import router as tender_router
from app.models.tender import TenderProject, TenderStatus
from app.services.tender_analysis import TenderAnalysisService
from app.services.outline_generation import OutlineGenerationService
from app.services.content_generation import ContentGenerationService
from app.services.document_export import DocumentExportService


@pytest.fixture
def app():
    """创建测试应用"""
    app = FastAPI()
    app.include_router(tender_router, prefix="/api/tender")
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_project():
    """模拟项目对象"""
    project = Mock(spec=TenderProject)
    project.id = "test-project-id"
    project.tenant_id = "test-tenant"
    project.user_id = "test-user"
    project.project_name = "测试招标项目"
    project.source_filename = "test.pdf"
    project.status = TenderStatus.CREATED
    project.created_at = "2024-01-01T00:00:00"
    project.updated_at = "2024-01-01T00:00:00"
    return project


class TestTenderProjectAPI:
    """招标项目API测试"""
    
    @patch('app.api.tender.get_db')
    def test_create_project_success(self, mock_get_db, client):
        """测试创建项目成功"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # 模拟文件查询
        mock_file = Mock()
        mock_file.id = 1
        mock_file.filename = "test.pdf"
        mock_file.status = "parsed"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_file
        
        # 模拟项目创建
        with patch('app.api.tender.TenderProject') as mock_project_class:
            mock_project = Mock()
            mock_project.id = "new-project-id"
            mock_project.project_name = "新项目"
            mock_project.source_filename = "test.pdf"
            mock_project.status = TenderStatus.CREATED
            mock_project_class.return_value = mock_project
            
            # 发送请求
            response = client.post(
                "/api/tender/projects",
                json={
                    "project_name": "新项目",
                    "source_file_id": 1
                },
                headers={"X-User-Id": "test-user"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "new-project-id"
            assert data["project_name"] == "新项目"
    
    @patch('app.api.tender.get_db')
    def test_create_project_file_not_found(self, mock_get_db, client):
        """测试创建项目时文件不存在"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # 模拟文件不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 发送请求
        response = client.post(
            "/api/tender/projects",
            json={
                "project_name": "新项目",
                "source_file_id": 999
            },
            headers={"X-User-Id": "test-user"}
        )
        
        assert response.status_code == 404
        assert "文件不存在" in response.json()["detail"]
    
    @patch('app.api.tender.get_db')
    def test_get_projects_list(self, mock_get_db, client, mock_project):
        """测试获取项目列表"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # 模拟查询结果
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = [mock_project]
        mock_query.count.return_value = 1
        mock_db.query.return_value.filter.return_value = mock_query
        
        # 发送请求
        response = client.get(
            "/api/tender/projects",
            headers={"X-User-Id": "test-user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["projects"]) == 1
        assert data["projects"][0]["id"] == "test-project-id"
    
    @patch('app.api.tender.get_db')
    def test_get_project_detail(self, mock_get_db, client, mock_project):
        """测试获取项目详情"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 发送请求
        response = client.get(
            "/api/tender/projects/test-project-id",
            headers={"X-User-Id": "test-user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-project-id"
        assert data["project_name"] == "测试招标项目"
    
    @patch('app.api.tender.get_db')
    def test_get_project_not_found(self, mock_get_db, client):
        """测试获取不存在的项目"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 发送请求
        response = client.get(
            "/api/tender/projects/nonexistent-id",
            headers={"X-User-Id": "test-user"}
        )
        
        assert response.status_code == 404
        assert "项目不存在" in response.json()["detail"]
    
    @patch('app.api.tender.get_db')
    def test_delete_project_success(self, mock_get_db, client, mock_project):
        """测试删除项目成功"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 发送请求
        response = client.delete(
            "/api/tender/projects/test-project-id",
            headers={"X-User-Id": "test-user"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "项目删除成功"
        
        # 验证删除操作被调用
        mock_db.delete.assert_called_once_with(mock_project)
        mock_db.commit.assert_called_once()


class TestTenderAnalysisAPI:
    """招标分析API测试"""
    
    @patch('app.api.tender.get_db')
    @patch('app.api.tender.TenderAnalysisService')
    def test_start_analysis_success(self, mock_analysis_service, mock_get_db, client, mock_project):
        """测试启动分析成功"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 模拟分析服务
        mock_service = Mock()
        mock_service.analyze_tender_document = AsyncMock(return_value=True)
        mock_analysis_service.return_value = mock_service
        
        # 发送请求
        response = client.post(
            "/api/tender/projects/test-project-id/analyze",
            headers={"X-User-Id": "test-user"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "分析任务已启动"
    
    @patch('app.api.tender.get_db')
    @patch('app.api.tender.TenderStorageService')
    def test_get_analysis_result(self, mock_storage_service, mock_get_db, client, mock_project):
        """测试获取分析结果"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 模拟存储服务
        mock_storage = Mock()
        mock_analysis_result = {
            "project_info": {"project_name": "测试项目"},
            "technical_requirements": {"functional_requirements": ["需求1", "需求2"]},
            "evaluation_criteria": {"technical_score": "技术分评分"},
            "submission_requirements": {"deadline": "2024-12-31"}
        }
        mock_storage.load_analysis_result = AsyncMock(return_value=mock_analysis_result)
        mock_storage_service.return_value = mock_storage
        
        # 发送请求
        response = client.get(
            "/api/tender/projects/test-project-id/analysis",
            headers={"X-User-Id": "test-user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "project_info" in data
        assert "technical_requirements" in data
    
    @patch('app.api.tender.get_db')
    @patch('app.api.tender.TenderStorageService')
    def test_update_analysis_result(self, mock_storage_service, mock_get_db, client, mock_project):
        """测试更新分析结果"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 模拟存储服务
        mock_storage = Mock()
        mock_storage.save_analysis_result = AsyncMock()
        mock_storage_service.return_value = mock_storage
        
        # 发送请求
        update_data = {
            "project_info": {"project_name": "更新的项目"},
            "technical_requirements": {"functional_requirements": ["新需求1"]},
            "evaluation_criteria": {"technical_score": "新的技术分评分"},
            "submission_requirements": {"deadline": "2024-12-31"}
        }
        
        response = client.put(
            "/api/tender/projects/test-project-id/analysis",
            json=update_data,
            headers={"X-User-Id": "test-user"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "分析结果已更新"


class TestOutlineGenerationAPI:
    """大纲生成API测试"""
    
    @patch('app.api.tender.get_db')
    @patch('app.api.tender.OutlineGenerationService')
    def test_generate_outline_success(self, mock_outline_service, mock_get_db, client, mock_project):
        """测试生成大纲成功"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 模拟大纲生成服务
        mock_service = Mock()
        mock_service.generate_outline = AsyncMock(return_value=True)
        mock_outline_service.return_value = mock_service
        
        # 发送请求
        response = client.post(
            "/api/tender/projects/test-project-id/outline/generate",
            headers={"X-User-Id": "test-user"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "大纲生成任务已启动"
    
    @patch('app.api.tender.get_db')
    @patch('app.api.tender.TenderStorageService')
    def test_get_outline(self, mock_storage_service, mock_get_db, client, mock_project):
        """测试获取大纲"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 模拟存储服务
        mock_storage = Mock()
        mock_outline = {
            "chapters": [
                {
                    "chapter_id": "1",
                    "title": "项目概述",
                    "description": "项目基本信息",
                    "subsections": [
                        {"id": "1.1", "title": "项目背景"}
                    ]
                }
            ]
        }
        mock_storage.load_outline = AsyncMock(return_value=Mock(to_dict=Mock(return_value=mock_outline)))
        mock_storage_service.return_value = mock_storage
        
        # 发送请求
        response = client.get(
            "/api/tender/projects/test-project-id/outline",
            headers={"X-User-Id": "test-user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "chapters" in data
        assert len(data["chapters"]) == 1


class TestContentGenerationAPI:
    """内容生成API测试"""
    
    @patch('app.api.tender.get_db')
    @patch('app.api.tender.ContentGenerationService')
    def test_generate_all_content_success(self, mock_content_service, mock_get_db, client, mock_project):
        """测试生成所有内容成功"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 模拟内容生成服务
        mock_service = Mock()
        mock_service.generate_all_content = AsyncMock(return_value=True)
        mock_content_service.return_value = mock_service
        
        # 发送请求
        response = client.post(
            "/api/tender/projects/test-project-id/content/generate-all",
            headers={"X-User-Id": "test-user"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "内容生成任务已启动"
    
    @patch('app.api.tender.get_db')
    @patch('app.api.tender.ContentGenerationService')
    def test_generate_chapter_content(self, mock_content_service, mock_get_db, client, mock_project):
        """测试生成章节内容"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 模拟内容生成服务
        mock_service = Mock()
        mock_service.generate_chapter_content = AsyncMock(return_value=True)
        mock_content_service.return_value = mock_service
        
        # 发送请求
        response = client.post(
            "/api/tender/projects/test-project-id/content/generate-chapter",
            json={"chapter_id": "1"},
            headers={"X-User-Id": "test-user"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "章节内容生成任务已启动"


class TestDocumentExportAPI:
    """文档导出API测试"""
    
    @patch('app.api.tender.get_db')
    @patch('app.api.tender.DocumentExportService')
    def test_export_document_success(self, mock_export_service, mock_get_db, client, mock_project):
        """测试导出文档成功"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 模拟导出服务
        mock_service = Mock()
        mock_service.export_to_pdf = AsyncMock(return_value="document-id")
        mock_export_service.return_value = mock_service
        
        # 发送请求
        response = client.post(
            "/api/tender/projects/test-project-id/export",
            json={
                "format": "pdf",
                "options": {
                    "title": "测试标书",
                    "company_name": "测试公司",
                    "include_cover": True,
                    "include_toc": True
                }
            },
            headers={"X-User-Id": "test-user"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "导出任务已启动"
    
    @patch('app.api.tender.get_db')
    @patch('app.api.tender.DocumentManagementService')
    def test_get_documents_list(self, mock_doc_service, mock_get_db, client, mock_project):
        """测试获取文档列表"""
        # 模拟数据库
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 模拟文档管理服务
        mock_service = Mock()
        mock_documents = [
            {
                "id": "doc-1",
                "filename": "test.pdf",
                "file_size": 1024,
                "created_at": "2024-01-01T00:00:00"
            }
        ]
        mock_service.get_project_documents = AsyncMock(return_value=mock_documents)
        mock_doc_service.return_value = mock_service
        
        # 发送请求
        response = client.get(
            "/api/tender/projects/test-project-id/documents",
            headers={"X-User-Id": "test-user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert len(data["documents"]) == 1


if __name__ == "__main__":
    pytest.main([__file__])