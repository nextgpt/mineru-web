"""
招标项目相关API接口
支持项目管理、内容生成、任务管理等功能
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Body, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.tender import TenderProject, TenderStatus
from app.models.file import FileModel
from app.services.content_generation import ContentGenerationService
from app.services.content_management import ContentManagementService
from app.services.task_manager import get_task_manager, TaskType
from app.services.tender_storage import TenderStorageService
from app.utils.user_dep import get_user_id
from app.utils.tenant_manager import TenantManager
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 请求/响应模型 ====================

class ProjectCreateRequest(BaseModel):
    """创建项目请求模型"""
    project_name: str
    source_file_id: int


class ProjectResponse(BaseModel):
    """项目响应模型"""
    id: str
    project_name: str
    source_file_id: int
    source_filename: str
    status: str
    tenant_id: str
    user_id: str
    created_at: str
    updated_at: Optional[str] = None
    progress: int = 0


class ProjectListResponse(BaseModel):
    """项目列表响应模型"""
    total: int
    page: int
    page_size: int
    projects: List[ProjectResponse]


class AnalysisRequest(BaseModel):
    """分析请求模型"""
    force_reanalyze: bool = False


class OutlineGenerateRequest(BaseModel):
    """大纲生成请求模型"""
    custom_requirements: Optional[str] = None


class ContentGenerationRequest(BaseModel):
    """内容生成请求模型"""
    regenerate_existing: bool = False


class ChapterGenerationRequest(BaseModel):
    """章节生成请求模型"""
    chapter_id: str


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    status: str
    message: str


class ExportRequest(BaseModel):
    """导出请求模型"""
    format: str = "pdf"  # pdf, docx
    template: str = "standard"


def get_tenant_id_dep(user_id: str = Depends(get_user_id)) -> str:
    """获取租户ID的依赖函数"""
    return TenantManager.get_tenant_id_from_user(user_id)


# ==================== 项目管理接口 ====================

@router.post("/tender/projects", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreateRequest,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep),
    db: Session = Depends(get_db)
):
    """
    创建招标项目
    
    Args:
        request: 创建项目请求
        user_id: 用户ID
        tenant_id: 租户ID
        db: 数据库会话
        
    Returns:
        ProjectResponse: 创建的项目信息
    """
    try:
        # 验证源文件存在且属于当前用户
        source_file = db.query(FileModel).filter(
            FileModel.id == request.source_file_id,
            FileModel.user_id == user_id
        ).first()
        
        if not source_file:
            raise HTTPException(status_code=404, detail="源文件不存在或无权限访问")
        
        # 创建项目
        project = TenderProject(
            project_name=request.project_name,
            source_file_id=request.source_file_id,
            tenant_id=tenant_id,
            user_id=user_id,
            status=TenderStatus.ANALYZING
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # 初始化项目存储结构
        storage_service = TenderStorageService()
        await storage_service.initialize_project_storage(project)
        
        return ProjectResponse(
            id=project.id,
            project_name=project.project_name,
            source_file_id=project.source_file_id,
            source_filename=source_file.filename,
            status=project.status.value,
            tenant_id=project.tenant_id,
            user_id=project.user_id,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat() if project.updated_at else None,
            progress=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")


@router.get("/tender/projects", response_model=ProjectListResponse)
async def get_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep),
    db: Session = Depends(get_db)
):
    """
    获取项目列表
    
    Args:
        page: 页码
        page_size: 每页数量
        status: 状态筛选
        search: 搜索关键词
        user_id: 用户ID
        tenant_id: 租户ID
        db: 数据库会话
        
    Returns:
        ProjectListResponse: 项目列表
    """
    try:
        # 构建查询
        query = db.query(TenderProject).filter(
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        )
        
        # 状态筛选
        if status:
            try:
                status_enum = TenderStatus(status)
                query = query.filter(TenderProject.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的状态值: {status}")
        
        # 搜索筛选
        if search:
            query = query.filter(TenderProject.project_name.contains(search))
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        projects = query.order_by(TenderProject.created_at.desc()).offset(offset).limit(page_size).all()
        
        # 获取源文件信息
        file_ids = [p.source_file_id for p in projects]
        files = db.query(FileModel).filter(FileModel.id.in_(file_ids)).all()
        file_map = {f.id: f for f in files}
        
        # 构建响应
        project_responses = []
        for project in projects:
            source_file = file_map.get(project.source_file_id)
            project_responses.append(ProjectResponse(
                id=project.id,
                project_name=project.project_name,
                source_file_id=project.source_file_id,
                source_filename=source_file.filename if source_file else "未知文件",
                status=project.status.value,
                tenant_id=project.tenant_id,
                user_id=project.user_id,
                created_at=project.created_at.isoformat(),
                updated_at=project.updated_at.isoformat() if project.updated_at else None,
                progress=0  # TODO: 从存储中获取实际进度
            ))
        
        return ProjectListResponse(
            total=total,
            page=page,
            page_size=page_size,
            projects=project_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")


@router.get("/tender/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep),
    db: Session = Depends(get_db)
):
    """
    获取项目详情
    
    Args:
        project_id: 项目ID
        user_id: 用户ID
        tenant_id: 租户ID
        db: 数据库会话
        
    Returns:
        ProjectResponse: 项目详情
    """
    try:
        # 查询项目
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 获取源文件信息
        source_file = db.query(FileModel).filter(FileModel.id == project.source_file_id).first()
        
        return ProjectResponse(
            id=project.id,
            project_name=project.project_name,
            source_file_id=project.source_file_id,
            source_filename=source_file.filename if source_file else "未知文件",
            status=project.status.value,
            tenant_id=project.tenant_id,
            user_id=project.user_id,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat() if project.updated_at else None,
            progress=0  # TODO: 从存储中获取实际进度
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {str(e)}")


@router.delete("/tender/projects/{project_id}")
async def delete_project(
    project_id: str,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep),
    db: Session = Depends(get_db)
):
    """
    删除项目
    
    Args:
        project_id: 项目ID
        user_id: 用户ID
        tenant_id: 租户ID
        db: 数据库会话
        
    Returns:
        Dict: 删除结果
    """
    try:
        # 查询项目
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 删除存储中的项目数据
        storage_service = TenderStorageService()
        await storage_service.delete_project_storage(project)
        
        # 删除数据库记录
        db.delete(project)
        db.commit()
        
        return {
            "project_id": project_id,
            "deleted": True,
            "message": "项目删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")


# ==================== 招标分析接口 ====================

@router.post("/tender/projects/{project_id}/analyze", response_model=TaskResponse)
async def analyze_tender(
    project_id: str,
    request: AnalysisRequest,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep),
    db: Session = Depends(get_db)
):
    """
    分析招标文件
    
    Args:
        project_id: 项目ID
        request: 分析请求参数
        user_id: 用户ID
        tenant_id: 租户ID
        db: 数据库会话
        
    Returns:
        TaskResponse: 任务信息
    """
    try:
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 检查项目状态
        if not request.force_reanalyze and project.status not in [TenderStatus.ANALYZING, TenderStatus.FAILED]:
            if project.status == TenderStatus.ANALYZED:
                raise HTTPException(status_code=400, detail="项目已分析完成，如需重新分析请设置 force_reanalyze=true")
        
        # 创建分析服务并启动异步任务
        from app.services.tender_analysis import TenderAnalysisService
        analysis_service = TenderAnalysisService(db)
        
        task_id = await analysis_service.analyze_tender_document_async(
            project_id=project_id,
            tenant_id=tenant_id,
            user_id=user_id,
            force_reanalyze=request.force_reanalyze
        )
        
        return TaskResponse(
            task_id=task_id,
            status="created",
            message="招标文件分析任务已创建，正在处理中..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建分析任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建分析任务失败: {str(e)}")


@router.get("/tender/projects/{project_id}/analysis")
async def get_analysis_result(
    project_id: str,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep),
    db: Session = Depends(get_db)
):
    """
    获取分析结果
    
    Args:
        project_id: 项目ID
        user_id: 用户ID
        tenant_id: 租户ID
        db: 数据库会话
        
    Returns:
        Dict: 分析结果
    """
    try:
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 检查项目状态
        if project.status == TenderStatus.ANALYZING:
            raise HTTPException(status_code=400, detail="项目正在分析中，请稍后再试")
        elif project.status in [TenderStatus.FAILED]:
            raise HTTPException(status_code=400, detail="项目分析失败，请重新分析")
        
        # 从存储中获取分析结果
        storage_service = TenderStorageService()
        analysis_result = await storage_service.load_analysis_result(project)
        
        return {
            "project_id": project_id,
            "project_name": project.project_name,
            "status": project.status.value,
            "analysis_result": analysis_result.dict(),
            "analyzed_at": analysis_result.extracted_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分析结果失败: {str(e)}")


@router.put("/tender/projects/{project_id}/analysis")
async def update_analysis_result(
    project_id: str,
    analysis_data: Dict[str, Any] = Body(...),
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep),
    db: Session = Depends(get_db)
):
    """
    更新分析结果
    
    Args:
        project_id: 项目ID
        analysis_data: 分析数据
        user_id: 用户ID
        tenant_id: 租户ID
        db: 数据库会话
        
    Returns:
        Dict: 更新后的分析结果
    """
    try:
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 更新分析结果
        from app.services.tender_analysis import AnalysisResult
        updated_analysis = AnalysisResult(
            project_info=analysis_data.get("project_info", {}),
            technical_requirements=analysis_data.get("technical_requirements", {}),
            evaluation_criteria=analysis_data.get("evaluation_criteria", {}),
            submission_requirements=analysis_data.get("submission_requirements", {}),
            extracted_at=datetime.utcnow()
        )
        
        # 保存到存储
        storage_service = TenderStorageService()
        await storage_service.save_analysis_result(project, updated_analysis)
        
        # 更新项目状态
        project.status = TenderStatus.ANALYZED
        project.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "project_id": project_id,
            "analysis_result": updated_analysis.dict(),
            "updated_at": updated_analysis.extracted_at.isoformat(),
            "message": "分析结果更新成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新分析结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新分析结果失败: {str(e)}")


# ==================== 大纲生成接口 ====================

@router.post("/tender/projects/{project_id}/outline/generate", response_model=TaskResponse)
async def generate_outline(
    project_id: str,
    request: OutlineGenerateRequest,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep),
    db: Session = Depends(get_db)
):
    """
    生成方案大纲
    
    Args:
        project_id: 项目ID
        request: 大纲生成请求
        user_id: 用户ID
        tenant_id: 租户ID
        db: 数据库会话
        
    Returns:
        TaskResponse: 任务信息
    """
    try:
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 检查项目状态
        if project.status not in [TenderStatus.ANALYZED, TenderStatus.OUTLINED, TenderStatus.FAILED]:
            raise HTTPException(
                status_code=400, 
                detail=f"项目状态不正确，当前状态: {project.status.value}，需要先完成招标分析"
            )
        
        # 创建大纲生成服务并启动异步任务
        from app.services.outline_generation import OutlineGenerationService
        outline_service = OutlineGenerationService(db)
        
        task_id = await outline_service.generate_outline_async(
            project_id=project_id,
            tenant_id=tenant_id,
            user_id=user_id,
            custom_requirements=request.custom_requirements
        )
        
        return TaskResponse(
            task_id=task_id,
            status="created",
            message="方案大纲生成任务已创建，正在处理中..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建大纲生成任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建大纲生成任务失败: {str(e)}")


@router.get("/tender/projects/{project_id}/outline")
async def get_outline(
    project_id: str,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep),
    db: Session = Depends(get_db)
):
    """
    获取方案大纲
    
    Args:
        project_id: 项目ID
        user_id: 用户ID
        tenant_id: 租户ID
        db: 数据库会话
        
    Returns:
        Dict: 大纲信息
    """
    try:
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 检查项目状态
        if project.status in [TenderStatus.ANALYZING, TenderStatus.ANALYZED]:
            raise HTTPException(status_code=400, detail="大纲尚未生成，请先生成大纲")
        
        # 从存储中获取大纲
        storage_service = TenderStorageService()
        outline = await storage_service.load_outline(project)
        
        return {
            "project_id": project_id,
            "project_name": project.project_name,
            "status": project.status.value,
            "outline": outline.dict(),
            "generated_at": outline.generated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取大纲失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取大纲失败: {str(e)}")


@router.put("/tender/projects/{project_id}/outline")
async def update_outline(
    project_id: str,
    outline_data: Dict[str, Any] = Body(...),
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep),
    db: Session = Depends(get_db)
):
    """
    更新方案大纲
    
    Args:
        project_id: 项目ID
        outline_data: 大纲数据
        user_id: 用户ID
        tenant_id: 租户ID
        db: 数据库会话
        
    Returns:
        Dict: 更新后的大纲
    """
    try:
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 更新大纲
        from app.services.outline_generation import OutlineStructure
        updated_outline = OutlineStructure(
            chapters=outline_data.get("chapters", []),
            chapter_count=len(outline_data.get("chapters", [])),
            generated_at=datetime.utcnow()
        )
        
        # 保存到存储
        storage_service = TenderStorageService()
        await storage_service.save_outline(project, updated_outline)
        
        # 更新项目状态
        project.status = TenderStatus.OUTLINED
        project.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "project_id": project_id,
            "outline": updated_outline.dict(),
            "updated_at": updated_outline.generated_at.isoformat(),
            "message": "大纲更新成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新大纲失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新大纲失败: {str(e)}")


# ==================== 文档导出接口 ====================

@router.post("/tender/projects/{project_id}/export", response_model=TaskResponse)
async def export_document(
    project_id: str,
    request: ExportRequest,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep),
    db: Session = Depends(get_db)
):
    """
    导出标书文档
    
    Args:
        project_id: 项目ID
        request: 导出请求参数
        user_id: 用户ID
        tenant_id: 租户ID
        db: 数据库会话
        
    Returns:
        TaskResponse: 任务信息
    """
    try:
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 检查项目状态
        if project.status not in [TenderStatus.GENERATED, TenderStatus.COMPLETED]:
            raise HTTPException(
                status_code=400, 
                detail=f"项目状态不正确，当前状态: {project.status.value}，需要先完成内容生成"
            )
        
        # 验证导出格式
        if request.format not in ["pdf", "docx"]:
            raise HTTPException(status_code=400, detail="不支持的导出格式，支持: pdf, docx")
        
        # 创建文档导出服务并启动异步任务
        from app.services.document_export import DocumentExportService
        export_service = DocumentExportService(db)
        
        task_id = await export_service.export_document_async(
            project_id=project_id,
            format=request.format,
            template=request.template,
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        return TaskResponse(
            task_id=task_id,
            status="created",
            message=f"文档导出任务已创建，正在生成 {request.format.upper()} 格式文档..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建导出任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建导出任务失败: {str(e)}")


@router.get("/tender/projects/{project_id}/documents")
async def get_project_documents(
    project_id: str,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep),
    db: Session = Depends(get_db)
):
    """
    获取项目导出文档列表
    
    Args:
        project_id: 项目ID
        user_id: 用户ID
        tenant_id: 租户ID
        db: 数据库会话
        
    Returns:
        Dict: 文档列表
    """
    try:
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 从存储中获取文档列表
        from app.services.document_management import DocumentManagementService
        doc_service = DocumentManagementService(db)
        documents = await doc_service.get_project_documents(project_id)
        
        return {
            "project_id": project_id,
            "project_name": project.project_name,
            "total_documents": len(documents),
            "documents": [
                {
                    "document_id": doc.document_id,
                    "filename": doc.filename,
                    "format": doc.format,
                    "template": doc.template,
                    "file_size": doc.file_size,
                    "created_at": doc.created_at.isoformat(),
                    "download_url": f"/api/tender/documents/{doc.document_id}/download"
                }
                for doc in documents
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.get("/tender/documents/{document_id}/download")
async def download_document(
    document_id: str,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep),
    db: Session = Depends(get_db)
):
    """
    下载文档
    
    Args:
        document_id: 文档ID
        user_id: 用户ID
        tenant_id: 租户ID
        db: 数据库会话
        
    Returns:
        FileResponse: 文档文件
    """
    try:
        # 验证文档存在且属于当前用户
        from app.services.document_management import DocumentManagementService
        doc_service = DocumentManagementService(db)
        
        document = await doc_service.get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 验证权限
        project = db.query(TenderProject).filter(
            TenderProject.id == document.project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=403, detail="无权限下载此文档")
        
        # 生成下载链接或直接返回文件
        download_url = await doc_service.generate_download_url(document_id)
        
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=download_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载文档失败: {str(e)}")


# ==================== API中间件和安全控制 ====================

from functools import wraps
from fastapi import Request
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
from typing import Callable

# 简单的内存速率限制器
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.limits = {
            "default": (100, 3600),  # 100 requests per hour
            "analysis": (10, 3600),   # 10 analysis requests per hour
            "generation": (20, 3600), # 20 generation requests per hour
            "export": (5, 3600)       # 5 export requests per hour
        }
    
    def is_allowed(self, key: str, limit_type: str = "default") -> bool:
        now = time.time()
        limit, window = self.limits.get(limit_type, self.limits["default"])
        
        # 清理过期请求
        self.requests[key] = [req_time for req_time in self.requests[key] if now - req_time < window]
        
        # 检查是否超过限制
        if len(self.requests[key]) >= limit:
            return False
        
        # 记录当前请求
        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter()

def rate_limit(limit_type: str = "default"):
    """速率限制装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取request和user_id
            request = None
            user_id = None
            
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if 'user_id' in kwargs:
                user_id = kwargs['user_id']
            
            if user_id:
                rate_key = f"{user_id}:{limit_type}"
                if not rate_limiter.is_allowed(rate_key, limit_type):
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Rate limit exceeded",
                            "message": f"请求过于频繁，请稍后再试",
                            "limit_type": limit_type
                        }
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def validate_project_access(func: Callable):
    """项目访问权限验证装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException as e:
            # 记录安全相关的错误
            if e.status_code in [403, 404]:
                logger.warning(f"项目访问被拒绝: {e.detail}, user_id: {kwargs.get('user_id', 'unknown')}")
            raise
        except Exception as e:
            logger.error(f"项目访问验证失败: {str(e)}")
            raise HTTPException(status_code=500, detail="访问验证失败")
    return wrapper


class RequestValidator:
    """请求参数验证器"""
    
    @staticmethod
    def validate_project_name(name: str) -> bool:
        """验证项目名称"""
        if not name or len(name.strip()) == 0:
            return False
        if len(name) > 256:
            return False
        # 检查是否包含危险字符
        dangerous_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
        return not any(char in name for char in dangerous_chars)
    
    @staticmethod
    def validate_chapter_id(chapter_id: str) -> bool:
        """验证章节ID"""
        if not chapter_id or len(chapter_id.strip()) == 0:
            return False
        # 章节ID应该是数字和点的组合，如 "1.1", "2.3.1"
        import re
        pattern = r'^[\d\.]+$'
        return bool(re.match(pattern, chapter_id)) and len(chapter_id) <= 20
    
    @staticmethod
    def validate_content_length(content: str, max_length: int = 50000) -> bool:
        """验证内容长度"""
        return len(content) <= max_length
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """清理输入文本"""
        if not text:
            return ""
        # 移除潜在的危险字符
        import html
        return html.escape(text.strip())


def handle_api_errors(func: Callable):
    """统一API错误处理装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except ValueError as e:
            logger.warning(f"参数验证错误: {str(e)}")
            raise HTTPException(status_code=400, detail=f"参数错误: {str(e)}")
        except PermissionError as e:
            logger.warning(f"权限错误: {str(e)}")
            raise HTTPException(status_code=403, detail="权限不足")
        except FileNotFoundError as e:
            logger.warning(f"资源不存在: {str(e)}")
            raise HTTPException(status_code=404, detail="资源不存在")
        except Exception as e:
            logger.error(f"API内部错误: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="服务器内部错误")
    return wrapper


# 请求验证中间件
async def validate_request_middleware(request: Request, call_next):
    """请求验证中间件"""
    try:
        # 验证请求大小
        if hasattr(request, 'headers'):
            content_length = request.headers.get('content-length')
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB限制
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request too large", "message": "请求体过大，最大支持10MB"}
                )
        
        # 验证Content-Type
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('content-type', '')
            if not content_type.startswith('application/json') and not content_type.startswith('multipart/form-data'):
                return JSONResponse(
                    status_code=415,
                    content={"error": "Unsupported Media Type", "message": "不支持的媒体类型"}
                )
        
        response = await call_next(request)
        return response
        
    except Exception as e:
        logger.error(f"请求验证中间件错误: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "message": "服务器内部错误"}
        )


# 安全响应头中间件
async def security_headers_middleware(request: Request, call_next):
    """添加安全响应头"""
    response = await call_next(request)
    
    # 添加安全头
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return responsethod
    def sanitize_input(text: str) -> str:
        """清理输入文本"""
        if not text:
            return ""
        # 移除潜在的危险字符
        import html
        return html.escape(text.strip())


def handle_api_errors(func: Callable):
    """统一API错误处理装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except ValueError as e:
            logger.warning(f"参数验证错误: {str(e)}")
            raise HTTPException(status_code=400, detail=f"参数错误: {str(e)}")
        except PermissionError as e:
            logger.warning(f"权限错误: {str(e)}")
            raise HTTPException(status_code=403, detail="权限不足")
        except FileNotFoundError as e:
            logger.warning(f"资源不存在: {str(e)}")
            raise HTTPException(status_code=404, detail="资源不存在")
        except Exception as e:
            logger.error(f"API内部错误: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="服务器内部错误")
    return wrapper


# 应用安全装饰器到关键端点
# 注意：由于装饰器需要在路由定义时应用，这里提供装饰器函数供使用

def apply_security_to_endpoints():
    """为关键端点应用安全控制"""
    # 这个函数可以在应用启动时调用，为现有端点添加安全控制
    # 由于FastAPI的限制，我们通过中间件的方式来实现统一的安全控制
    pass


# 请求验证中间件
async def validate_request_middleware(request: Request, call_next):
    """请求验证中间件"""
    try:
        # 验证请求大小
        if hasattr(request, 'headers'):
            content_length = request.headers.get('content-length')
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB限制
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request too large", "message": "请求体过大，最大支持10MB"}
                )
        
        # 验证Content-Type
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('content-type', '')
            if not content_type.startswith('application/json') and not content_type.startswith('multipart/form-data'):
                return JSONResponse(
                    status_code=415,
                    content={"error": "Unsupported Media Type", "message": "不支持的媒体类型"}
                )
        
        response = await call_next(request)
        return response
        
    except Exception as e:
        logger.error(f"请求验证中间件错误: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "message": "服务器内部错误"}
        )


# 安全响应头中间件
async def security_headers_middleware(request: Request, call_next):
    """添加安全响应头"""
    response = await call_next(request)
    
    # 添加安全头
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return responsethod
    def sanitize_input(text: str) -> str:
        """清理输入文本"""
        if not text:
            return ""
        # 移除潜在的危险字符
        import html
        return html.escape(text.strip())


def handle_api_errors(func: Callable):
    """统一API错误处理装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except ValueError as e:
            logger.warning(f"参数验证错误: {str(e)}")
            raise HTTPException(status_code=400, detail=f"参数错误: {str(e)}")
        except PermissionError as e:
            logger.warning(f"权限错误: {str(e)}")
            raise HTTPException(status_code=403, detail="权限不足")
        except FileNotFoundError as e:
            logger.warning(f"资源不存在: {str(e)}")
            raise HTTPException(status_code=404, detail="资源不存在")
        except Exception as e:
            logger.error(f"API内部错误: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="服务器内部错误")
    return wrapper


# 重新装饰现有的API端点以添加安全控制
# 注意：由于Python装饰器的限制，我们需要在路由定义时应用这些装饰器

# ==================== 内容生成接口 ====================


@router.post("/tender/projects/{project_id}/content/generate-all", response_model=TaskResponse)
async def generate_all_content(
    project_id: str,
    request: ContentGenerationRequest,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    异步生成所有章节内容
    
    Args:
        project_id: 项目ID
        request: 生成请求参数
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        TaskResponse: 任务信息
    """
    try:
        # 创建内容生成服务
        from app.database import get_db
        db = next(get_db())
        
        content_service = ContentGenerationService(db)
        
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 检查项目状态
        if project.status not in [TenderStatus.OUTLINED, TenderStatus.GENERATED, TenderStatus.FAILED]:
            raise HTTPException(
                status_code=400, 
                detail=f"项目状态不正确，当前状态: {project.status.value}，需要先完成大纲生成"
            )
        
        # 创建异步任务
        task_id = await content_service.generate_all_content_async(
            project_id=project_id,
            tenant_id=tenant_id,
            user_id=user_id,
            regenerate_existing=request.regenerate_existing
        )
        
        return TaskResponse(
            task_id=task_id,
            status="created",
            message="内容生成任务已创建，正在处理中..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建内容生成任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.post("/tender/projects/{project_id}/content/generate-chapter", response_model=TaskResponse)
async def generate_chapter_content(
    project_id: str,
    request: ChapterGenerationRequest,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    异步生成单个章节内容
    
    Args:
        project_id: 项目ID
        request: 章节生成请求参数
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        TaskResponse: 任务信息
    """
    try:
        # 创建内容生成服务
        from app.database import get_db
        db = next(get_db())
        
        content_service = ContentGenerationService(db)
        
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 检查项目状态
        if project.status not in [TenderStatus.OUTLINED, TenderStatus.GENERATING, TenderStatus.GENERATED, TenderStatus.FAILED]:
            raise HTTPException(
                status_code=400, 
                detail=f"项目状态不正确，当前状态: {project.status.value}，需要先完成大纲生成"
            )
        
        # 创建异步任务
        task_id = await content_service.generate_chapter_content_async(
            project_id=project_id,
            chapter_id=request.chapter_id,
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        return TaskResponse(
            task_id=task_id,
            status="created",
            message=f"章节 {request.chapter_id} 内容生成任务已创建，正在处理中..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建章节生成任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.post("/tender/projects/{project_id}/content/regenerate-chapter", response_model=TaskResponse)
async def regenerate_chapter_content(
    project_id: str,
    request: ChapterGenerationRequest,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    异步重新生成章节内容
    
    Args:
        project_id: 项目ID
        request: 章节生成请求参数
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        TaskResponse: 任务信息
    """
    try:
        # 创建内容生成服务
        from app.database import get_db
        db = next(get_db())
        
        content_service = ContentGenerationService(db)
        
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 创建异步任务
        task_id = await content_service.regenerate_chapter_async(
            project_id=project_id,
            chapter_id=request.chapter_id,
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        return TaskResponse(
            task_id=task_id,
            status="created",
            message=f"章节 {request.chapter_id} 重新生成任务已创建，正在处理中..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建章节重新生成任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/tender/projects/{project_id}/content")
async def get_project_content(
    project_id: str,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    获取项目的所有章节内容
    
    Args:
        project_id: 项目ID
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        Dict: 项目内容信息
    """
    try:
        # 创建内容生成服务
        from app.database import get_db
        db = next(get_db())
        
        content_service = ContentGenerationService(db)
        
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 获取所有章节内容
        chapters = await content_service.get_all_content(project_id)
        
        # 获取内容统计
        statistics = await content_service.get_content_statistics(project_id)
        
        return {
            "project_id": project_id,
            "project_name": project.project_name,
            "status": project.status.value,
            "chapters": [
                {
                    "chapter_id": chapter.chapter_id,
                    "chapter_title": chapter.chapter_title,
                    "content": chapter.content,
                    "word_count": chapter.word_count,
                    "generated_at": chapter.generated_at.isoformat()
                }
                for chapter in chapters
            ],
            "statistics": statistics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取内容失败: {str(e)}")


@router.get("/tender/projects/{project_id}/content/{chapter_id}")
async def get_chapter_content(
    project_id: str,
    chapter_id: str,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    获取单个章节内容
    
    Args:
        project_id: 项目ID
        chapter_id: 章节ID
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        Dict: 章节内容信息
    """
    try:
        # 创建内容生成服务
        from app.database import get_db
        db = next(get_db())
        
        content_service = ContentGenerationService(db)
        
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 获取章节内容
        chapter = await content_service.get_chapter_content(project_id, chapter_id)
        
        if not chapter:
            raise HTTPException(status_code=404, detail="章节内容不存在")
        
        return {
            "project_id": project_id,
            "chapter_id": chapter.chapter_id,
            "chapter_title": chapter.chapter_title,
            "content": chapter.content,
            "word_count": chapter.word_count,
            "generated_at": chapter.generated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取章节内容失败: {str(e)}")


@router.put("/tender/projects/{project_id}/content/{chapter_id}")
async def update_chapter_content(
    project_id: str,
    chapter_id: str,
    content: str = Body(..., embed=True),
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    更新章节内容
    
    Args:
        project_id: 项目ID
        chapter_id: 章节ID
        content: 新的章节内容
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        Dict: 更新后的章节信息
    """
    try:
        # 创建内容生成服务
        from app.database import get_db
        db = next(get_db())
        
        content_service = ContentGenerationService(db)
        
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 更新章节内容
        updated_chapter = await content_service.update_chapter_content(
            project_id, chapter_id, content
        )
        
        if not updated_chapter:
            raise HTTPException(status_code=500, detail="更新章节内容失败")
        
        return {
            "project_id": project_id,
            "chapter_id": updated_chapter.chapter_id,
            "chapter_title": updated_chapter.chapter_title,
            "content": updated_chapter.content,
            "word_count": updated_chapter.word_count,
            "updated_at": updated_chapter.generated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新章节内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新章节内容失败: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    user_id: str = Depends(get_user_id)
):
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        user_id: 用户ID
        
    Returns:
        Dict: 任务状态信息
    """
    try:
        task_manager = get_task_manager()
        task_info = await task_manager.get_task_info(task_id)
        
        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 验证任务属于当前用户
        if task_info.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权限访问此任务")
        
        return {
            "task_id": task_info.task_id,
            "task_type": task_info.task_type.value,
            "status": task_info.status.value,
            "progress": task_info.progress,
            "title": task_info.title,
            "description": task_info.description,
            "project_id": task_info.project_id,
            "result": task_info.result,
            "error_message": task_info.error_message,
            "created_at": task_info.created_at.isoformat() if task_info.created_at else None,
            "started_at": task_info.started_at.isoformat() if task_info.started_at else None,
            "completed_at": task_info.completed_at.isoformat() if task_info.completed_at else None,
            "metadata": task_info.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    user_id: str = Depends(get_user_id)
):
    """
    取消任务
    
    Args:
        task_id: 任务ID
        user_id: 用户ID
        
    Returns:
        Dict: 取消结果
    """
    try:
        task_manager = get_task_manager()
        task_info = await task_manager.get_task_info(task_id)
        
        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 验证任务属于当前用户
        if task_info.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权限操作此任务")
        
        # 取消任务
        success = await task_manager.cancel_task(task_id)
        
        return {
            "task_id": task_id,
            "cancelled": success,
            "message": "任务取消成功" if success else "任务取消失败"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


@router.get("/users/{user_id}/tasks")
async def get_user_tasks(
    user_id: str,
    limit: int = 50,
    current_user_id: str = Depends(get_user_id)
):
    """
    获取用户的任务列表
    
    Args:
        user_id: 目标用户ID
        limit: 返回数量限制
        current_user_id: 当前用户ID
        
    Returns:
        List: 任务列表
    """
    try:
        # 验证权限（只能查看自己的任务）
        if user_id != current_user_id:
            raise HTTPException(status_code=403, detail="无权限访问其他用户的任务")
        
        task_manager = get_task_manager()
        tasks = await task_manager.get_user_tasks(user_id, limit)
        
        return {
            "user_id": user_id,
            "total_tasks": len(tasks),
            "tasks": [
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "status": task.status.value,
                    "progress": task.progress,
                    "title": task.title,
                    "description": task.description,
                    "project_id": task.project_id,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                }
                for task in tasks
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/projects/{project_id}/tasks")
async def get_project_tasks(
    project_id: str,
    limit: int = 50,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    获取项目的任务列表
    
    Args:
        project_id: 项目ID
        limit: 返回数量限制
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        List: 任务列表
    """
    try:
        # 验证项目存在且属于当前租户
        from app.database import get_db
        db = next(get_db())
        
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        task_manager = get_task_manager()
        tasks = await task_manager.get_project_tasks(project_id, limit)
        
        return {
            "project_id": project_id,
            "project_name": project.project_name,
            "total_tasks": len(tasks),
            "tasks": [
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "status": task.status.value,
                    "progress": task.progress,
                    "title": task.title,
                    "description": task.description,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                }
                for task in tasks
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目任务列表失败: {str(e)}")

# ==================== 内容管理相关接口 ====================

class ContentUpdateRequest(BaseModel):
    """内容更新请求模型"""
    content: str
    version_note: Optional[str] = None


class ContentSearchRequest(BaseModel):
    """内容搜索请求模型"""
    query: str
    search_type: str = "text"  # text, regex
    case_sensitive: bool = False
    limit: int = 20


class ContentVersionRestoreRequest(BaseModel):
    """内容版本恢复请求模型"""
    version_id: str
    restore_note: Optional[str] = None


@router.put("/tender/projects/{project_id}/content/{chapter_id}/manage")
async def update_chapter_content_with_version(
    project_id: str,
    chapter_id: str,
    request: ContentUpdateRequest,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    更新章节内容（带版本控制）
    
    Args:
        project_id: 项目ID
        chapter_id: 章节ID
        request: 内容更新请求
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        Dict: 更新后的章节信息
    """
    try:
        from app.database import get_db
        db = next(get_db())
        
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 创建内容管理服务
        content_mgmt_service = ContentManagementService(db)
        
        # 更新章节内容
        updated_chapter = await content_mgmt_service.update_chapter_content(
            project_id=project_id,
            chapter_id=chapter_id,
            content=request.content,
            user_id=user_id,
            version_note=request.version_note
        )
        
        return {
            "project_id": project_id,
            "chapter_id": updated_chapter.chapter_id,
            "chapter_title": updated_chapter.chapter_title,
            "content": updated_chapter.content,
            "word_count": updated_chapter.word_count,
            "updated_at": updated_chapter.generated_at.isoformat(),
            "message": "章节内容更新成功，已创建新版本"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新章节内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新章节内容失败: {str(e)}")


@router.get("/tender/projects/{project_id}/content/{chapter_id}/versions")
async def get_chapter_content_versions(
    project_id: str,
    chapter_id: str,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    获取章节内容版本列表
    
    Args:
        project_id: 项目ID
        chapter_id: 章节ID
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        Dict: 版本列表信息
    """
    try:
        from app.database import get_db
        db = next(get_db())
        
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 创建内容管理服务
        content_mgmt_service = ContentManagementService(db)
        
        # 获取版本列表
        versions = await content_mgmt_service.get_content_versions(project_id, chapter_id)
        
        return {
            "project_id": project_id,
            "chapter_id": chapter_id,
            "total_versions": len(versions),
            "versions": [
                {
                    "version_id": version.version_id,
                    "chapter_title": version.chapter_title,
                    "word_count": version.word_count,
                    "created_at": version.created_at.isoformat(),
                    "created_by": version.created_by,
                    "version_note": version.version_note,
                    "is_current": version.is_current
                }
                for version in versions
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节版本列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取版本列表失败: {str(e)}")


@router.post("/tender/projects/{project_id}/content/{chapter_id}/restore")
async def restore_chapter_content_version(
    project_id: str,
    chapter_id: str,
    request: ContentVersionRestoreRequest,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    恢复章节内容到指定版本
    
    Args:
        project_id: 项目ID
        chapter_id: 章节ID
        request: 版本恢复请求
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        Dict: 恢复后的章节信息
    """
    try:
        from app.database import get_db
        db = next(get_db())
        
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 创建内容管理服务
        content_mgmt_service = ContentManagementService(db)
        
        # 恢复版本
        restored_chapter = await content_mgmt_service.restore_content_version(
            project_id=project_id,
            chapter_id=chapter_id,
            version_id=request.version_id,
            user_id=user_id,
            restore_note=request.restore_note
        )
        
        return {
            "project_id": project_id,
            "chapter_id": restored_chapter.chapter_id,
            "chapter_title": restored_chapter.chapter_title,
            "content": restored_chapter.content,
            "word_count": restored_chapter.word_count,
            "restored_at": restored_chapter.generated_at.isoformat(),
            "restored_from_version": request.version_id,
            "message": "章节内容恢复成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复章节版本失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"恢复版本失败: {str(e)}")


@router.get("/tender/projects/{project_id}/content/{chapter_id}/history")
async def get_chapter_edit_history(
    project_id: str,
    chapter_id: str,
    limit: int = 50,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    获取章节编辑历史
    
    Args:
        project_id: 项目ID
        chapter_id: 章节ID
        limit: 返回记录数限制
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        Dict: 编辑历史信息
    """
    try:
        from app.database import get_db
        db = next(get_db())
        
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 创建内容管理服务
        content_mgmt_service = ContentManagementService(db)
        
        # 获取编辑历史
        history = await content_mgmt_service.get_edit_history(
            project_id, chapter_id, limit
        )
        
        return {
            "project_id": project_id,
            "chapter_id": chapter_id,
            "total_edits": len(history),
            "history": [
                {
                    "edit_id": edit.edit_id,
                    "action": edit.action,
                    "word_count_change": edit.word_count_change,
                    "edited_at": edit.edited_at.isoformat(),
                    "edited_by": edit.edited_by,
                    "edit_note": edit.edit_note
                }
                for edit in history
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取编辑历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取编辑历史失败: {str(e)}")


@router.post("/tender/projects/{project_id}/content/search")
async def search_project_content(
    project_id: str,
    request: ContentSearchRequest,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    搜索项目内容
    
    Args:
        project_id: 项目ID
        request: 搜索请求参数
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        Dict: 搜索结果
    """
    try:
        from app.database import get_db
        db = next(get_db())
        
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 创建内容管理服务
        content_mgmt_service = ContentManagementService(db)
        
        # 执行搜索
        search_results = await content_mgmt_service.search_content(
            project_id=project_id,
            query=request.query,
            search_type=request.search_type,
            case_sensitive=request.case_sensitive,
            limit=request.limit
        )
        
        return {
            "project_id": project_id,
            "query": request.query,
            "search_type": request.search_type,
            "total_results": len(search_results),
            "results": [
                {
                    "chapter_id": result.chapter_id,
                    "chapter_title": result.chapter_title,
                    "content_snippet": result.content_snippet,
                    "match_count": result.match_count,
                    "relevance_score": result.relevance_score
                }
                for result in search_results
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索项目内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索内容失败: {str(e)}")


@router.get("/tender/projects/{project_id}/content/statistics")
async def get_project_content_statistics(
    project_id: str,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    获取项目内容统计信息
    
    Args:
        project_id: 项目ID
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        Dict: 统计信息
    """
    try:
        from app.database import get_db
        db = next(get_db())
        
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 创建内容管理服务
        content_mgmt_service = ContentManagementService(db)
        
        # 获取统计信息
        statistics = await content_mgmt_service.get_content_statistics(project_id)
        
        return {
            "project_id": statistics.project_id,
            "total_chapters": statistics.total_chapters,
            "completed_chapters": statistics.completed_chapters,
            "completion_rate": statistics.completion_rate,
            "total_words": statistics.total_words,
            "average_words_per_chapter": statistics.average_words_per_chapter,
            "last_updated": statistics.last_updated.isoformat(),
            "chapter_statistics": statistics.chapter_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取内容统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/tender/projects/{project_id}/content/summary")
async def get_project_content_summary(
    project_id: str,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    获取项目内容摘要
    
    Args:
        project_id: 项目ID
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        Dict: 内容摘要信息
    """
    try:
        from app.database import get_db
        db = next(get_db())
        
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 创建内容管理服务
        content_mgmt_service = ContentManagementService(db)
        
        # 获取内容摘要
        summary = await content_mgmt_service.get_project_content_summary(project_id)
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取内容摘要失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取内容摘要失败: {str(e)}")


@router.get("/tender/projects/{project_id}/content/analytics")
async def get_project_content_analytics(
    project_id: str,
    days: int = 30,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    获取项目内容分析数据
    
    Args:
        project_id: 项目ID
        days: 分析天数
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        Dict: 分析数据
    """
    try:
        from app.database import get_db
        db = next(get_db())
        
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 创建内容管理服务
        content_mgmt_service = ContentManagementService(db)
        
        # 获取分析数据
        analytics = await content_mgmt_service.get_content_analytics(project_id, days)
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取内容分析数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分析数据失败: {str(e)}")


@router.delete("/tender/projects/{project_id}/content/{chapter_id}")
async def delete_chapter_content(
    project_id: str,
    chapter_id: str,
    delete_note: Optional[str] = None,
    user_id: str = Depends(get_user_id),
    tenant_id: str = Depends(get_tenant_id_dep)
):
    """
    删除章节内容
    
    Args:
        project_id: 项目ID
        chapter_id: 章节ID
        delete_note: 删除说明
        user_id: 用户ID
        tenant_id: 租户ID
        
    Returns:
        Dict: 删除结果
    """
    try:
        from app.database import get_db
        db = next(get_db())
        
        # 验证项目存在且属于当前租户
        project = db.query(TenderProject).filter(
            TenderProject.id == project_id,
            TenderProject.tenant_id == tenant_id,
            TenderProject.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
        
        # 创建内容管理服务
        content_mgmt_service = ContentManagementService(db)
        
        # 删除章节内容
        success = await content_mgmt_service.delete_chapter_content(
            project_id=project_id,
            chapter_id=chapter_id,
            user_id=user_id,
            delete_note=delete_note
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="删除章节内容失败")
        
        return {
            "project_id": project_id,
            "chapter_id": chapter_id,
            "deleted": True,
            "message": "章节内容删除成功，已备份到删除记录"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除章节内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除章节内容失败: {str(e)}")


# ==================== API中间件和安全控制 ====================

from functools import wraps
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
from typing import Callable

# 简单的内存速率限制器
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.limits = {
            "default": (100, 3600),  # 100 requests per hour
            "analysis": (10, 3600),   # 10 analysis requests per hour
            "generation": (20, 3600), # 20 generation requests per hour
            "export": (5, 3600)       # 5 export requests per hour
        }
    
    def is_allowed(self, key: str, limit_type: str = "default") -> bool:
        now = time.time()
        limit, window = self.limits.get(limit_type, self.limits["default"])
        
        # 清理过期请求
        self.requests[key] = [req_time for req_time in self.requests[key] if now - req_time < window]
        
        # 检查是否超过限制
        if len(self.requests[key]) >= limit:
            return False
        
        # 记录当前请求
        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter()

class RequestValidator:
    """请求参数验证器"""
    
    @staticmethod
    def validate_project_name(name: str) -> bool:
        """验证项目名称"""
        if not name or len(name.strip()) == 0:
            return False
        if len(name) > 256:
            return False
        # 检查是否包含危险字符
        dangerous_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
        return not any(char in name for char in dangerous_chars)
    
    @staticmethod
    def validate_chapter_id(chapter_id: str) -> bool:
        """验证章节ID"""
        if not chapter_id or len(chapter_id.strip()) == 0:
            return False
        # 章节ID应该是数字和点的组合，如 "1.1", "2.3.1"
        import re
        pattern = r'^[\d\.]+$'
        return bool(re.match(pattern, chapter_id)) and len(chapter_id) <= 20
    
    @staticmethod
    def validate_content_length(content: str, max_length: int = 50000) -> bool:
        """验证内容长度"""
        return len(content) <= max_length
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """清理输入文本"""
        if not text:
            return ""
        # 移除潜在的危险字符
        import html
        return html.escape(text.strip())


def handle_api_errors(func: Callable):
    """统一API错误处理装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except ValueError as e:
            logger.warning(f"参数验证错误: {str(e)}")
            raise HTTPException(status_code=400, detail=f"参数错误: {str(e)}")
        except PermissionError as e:
            logger.warning(f"权限错误: {str(e)}")
            raise HTTPException(status_code=403, detail="权限不足")
        except FileNotFoundError as e:
            logger.warning(f"资源不存在: {str(e)}")
            raise HTTPException(status_code=404, detail="资源不存在")
        except Exception as e:
            logger.error(f"API内部错误: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="服务器内部错误")
    return wrapper


# 请求验证中间件
async def validate_request_middleware(request: Request, call_next):
    """请求验证中间件"""
    try:
        # 验证请求大小
        if hasattr(request, 'headers'):
            content_length = request.headers.get('content-length')
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB限制
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request too large", "message": "请求体过大，最大支持10MB"}
                )
        
        # 验证Content-Type
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('content-type', '')
            if not content_type.startswith('application/json') and not content_type.startswith('multipart/form-data'):
                return JSONResponse(
                    status_code=415,
                    content={"error": "Unsupported Media Type", "message": "不支持的媒体类型"}
                )
        
        response = await call_next(request)
        return response
        
    except Exception as e:
        logger.error(f"请求验证中间件错误: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "message": "服务器内部错误"}
        )


# 安全响应头中间件
async def security_headers_middleware(request: Request, call_next):
    """添加安全响应头"""
    response = await call_next(request)
    
    # 添加安全头
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response


# 输入验证函数
def validate_create_project_request(request: ProjectCreateRequest):
    """验证创建项目请求"""
    if not RequestValidator.validate_project_name(request.project_name):
        raise ValueError("项目名称格式不正确")
    
    if request.source_file_id <= 0:
        raise ValueError("源文件ID无效")


def validate_chapter_request(request: ChapterGenerationRequest):
    """验证章节请求"""
    if not RequestValidator.validate_chapter_id(request.chapter_id):
        raise ValueError("章节ID格式不正确")


def validate_content_update(content: str):
    """验证内容更新"""
    if not RequestValidator.validate_content_length(content):
        raise ValueError("内容长度超过限制")