from fastapi import APIRouter, Query, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from app.database import get_db
from app.models.project import Project, ProjectStatus
from app.models.requirement_analysis import RequirementAnalysis
from app.models.file import File as FileModel
from app.models.parsed_content import ParsedContent
from app.utils.user_dep import get_user_id
from app.services.ai_analysis_service import AIAnalysisService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for request/response
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class AnalysisResponse(BaseModel):
    status: str
    message: str
    analysis_id: Optional[int] = None

@router.get("/projects")
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query('', description="按项目名搜索"),
    status: str = Query('', description="按状态筛选"),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    query = db.query(Project).filter(Project.user_id == user_id)
    
    if search:
        query = query.filter(Project.name.contains(search))
    if status:
        try:
            status_enum = ProjectStatus(status.lower())
            query = query.filter(Project.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的状态值")
    
    total = query.count()
    projects = query.order_by(Project.created_at.desc()) \
        .offset((page-1)*page_size).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "projects": [p.to_dict() for p in projects]
    }

@router.post("/projects")
def create_project(
    project: ProjectCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """创建新项目"""
    db_project = Project(
        user_id=user_id,
        name=project.name,
        description=project.description,
        status=ProjectStatus.CREATED
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return db_project.to_dict()

@router.get("/projects/{project_id}")
def get_project(
    project_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取项目详情"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return project.to_dict()

@router.put("/projects/{project_id}")
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """更新项目信息"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if project_update.name is not None:
        project.name = project_update.name
    if project_update.description is not None:
        project.description = project_update.description
    
    db.commit()
    db.refresh(project)
    
    return project.to_dict()

@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """删除项目"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    try:
        db.delete(project)
        db.commit()
        return {"message": "项目删除成功"}
    except Exception as e:
        db.rollback()
        logger.error(f"删除项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除项目失败")

# Analysis related endpoints
@router.post("/projects/{project_id}/analyze")
def start_analysis(
    project_id: int,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """开始需求分析"""
    # 验证项目存在
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查项目是否有关联的文件
    if not project.original_file_id:
        raise HTTPException(status_code=400, detail="项目未关联招标文件")
    
    # 检查文件是否已解析
    parsed_content = db.query(ParsedContent).filter(
        ParsedContent.file_id == project.original_file_id,
        ParsedContent.user_id == user_id
    ).first()
    
    if not parsed_content or not parsed_content.content:
        raise HTTPException(status_code=400, detail="招标文件尚未解析或解析失败")
    
    # 检查是否已有分析结果
    existing_analysis = db.query(RequirementAnalysis).filter(
        RequirementAnalysis.project_id == project_id,
        RequirementAnalysis.user_id == user_id
    ).first()
    
    if existing_analysis:
        return AnalysisResponse(
            status="exists",
            message="分析结果已存在",
            analysis_id=existing_analysis.id
        )
    
    # 更新项目状态为分析中
    project.status = ProjectStatus.ANALYZING
    db.commit()
    
    # 启动后台分析任务
    background_tasks.add_task(
        perform_analysis_task,
        project_id,
        user_id,
        parsed_content.content
    )
    
    return AnalysisResponse(
        status="started",
        message="分析已开始，请稍后查看结果"
    )

@router.get("/projects/{project_id}/analysis")
def get_analysis_result(
    project_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取分析结果"""
    # 验证项目存在
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取分析结果
    analysis = db.query(RequirementAnalysis).filter(
        RequirementAnalysis.project_id == project_id,
        RequirementAnalysis.user_id == user_id
    ).first()
    
    if not analysis:
        return {
            "status": project.status.value,
            "message": "分析尚未完成" if project.status == ProjectStatus.ANALYZING else "分析结果不存在",
            "analysis": None
        }
    
    return {
        "status": project.status.value,
        "message": "分析完成",
        "analysis": analysis.to_dict()
    }

@router.put("/projects/{project_id}/analysis")
def update_analysis_result(
    project_id: int,
    analysis_data: dict,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """更新分析结果"""
    # 验证项目存在
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取分析结果
    analysis = db.query(RequirementAnalysis).filter(
        RequirementAnalysis.project_id == project_id,
        RequirementAnalysis.user_id == user_id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="分析结果不存在")
    
    # 更新分析结果
    for field, value in analysis_data.items():
        if hasattr(analysis, field):
            setattr(analysis, field, value)
    
    db.commit()
    db.refresh(analysis)
    
    return analysis.to_dict()

@router.get("/projects/{project_id}/analysis/status")
def get_analysis_status(
    project_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取分析状态和进度"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    analysis = db.query(RequirementAnalysis).filter(
        RequirementAnalysis.project_id == project_id,
        RequirementAnalysis.user_id == user_id
    ).first()
    
    return {
        "project_status": project.status.value,
        "has_analysis": analysis is not None,
        "analysis_created_at": analysis.created_at.isoformat() if analysis else None
    }

def perform_analysis_task(project_id: int, user_id: str, content: str):
    """执行分析任务的后台函数"""
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        # 获取AI分析服务
        ai_service = AIAnalysisService()
        
        # 执行分析
        analysis_result = ai_service.analyze_tender_document(project_id, content)
        
        # 保存分析结果
        db_analysis = RequirementAnalysis(
            project_id=project_id,
            user_id=user_id,
            project_overview=analysis_result.get('project_overview'),
            client_info=analysis_result.get('client_info'),
            budget_info=analysis_result.get('budget_info'),
            detailed_requirements=analysis_result.get('detailed_requirements'),
            critical_requirements=analysis_result.get('critical_requirements'),
            important_requirements=analysis_result.get('important_requirements'),
            general_requirements=analysis_result.get('general_requirements')
        )
        
        db.add(db_analysis)
        
        # 更新项目状态
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.ANALYZING  # 可以根据需要调整状态
        
        db.commit()
        
        logger.info(f"项目 {project_id} 分析完成")
        
    except Exception as e:
        db.rollback()
        logger.error(f"项目 {project_id} 分析失败: {str(e)}")
        
        # 更新项目状态为失败
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.FAILED
            db.commit()
    
    finally:
        db.close()