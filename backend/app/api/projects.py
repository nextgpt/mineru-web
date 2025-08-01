from fastapi import APIRouter, Query, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from app.database import get_db
from app.models.project import Project, ProjectStatus
from app.models.requirement_analysis import RequirementAnalysis
from app.models.bid_outline import BidOutline
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

# Outline related Pydantic models
class OutlineCreate(BaseModel):
    title: str
    level: int
    parent_id: Optional[int] = None
    content: Optional[str] = None

class OutlineUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    order_index: Optional[int] = None

class OutlineResponse(BaseModel):
    id: int
    title: str
    level: int
    sequence: str
    parent_id: Optional[int]
    order_index: int
    content: Optional[str]
    children: Optional[List['OutlineResponse']] = None

# Enable forward references for recursive model
OutlineResponse.model_rebuild()

class OutlineGenerateResponse(BaseModel):
    status: str
    message: str
    outline_count: Optional[int] = None

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

# Outline management endpoints
@router.post("/projects/{project_id}/generate-outline")
def generate_outline(
    project_id: int,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """生成标书大纲"""
    # 验证项目存在
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查是否有需求分析结果
    analysis = db.query(RequirementAnalysis).filter(
        RequirementAnalysis.project_id == project_id,
        RequirementAnalysis.user_id == user_id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=400, detail="请先完成需求分析")
    
    # 检查是否已有大纲
    existing_outline = db.query(BidOutline).filter(
        BidOutline.project_id == project_id,
        BidOutline.user_id == user_id
    ).first()
    
    if existing_outline:
        outline_count = db.query(BidOutline).filter(
            BidOutline.project_id == project_id,
            BidOutline.user_id == user_id
        ).count()
        return OutlineGenerateResponse(
            status="exists",
            message="大纲已存在",
            outline_count=outline_count
        )
    
    # 更新项目状态
    project.status = ProjectStatus.OUTLINE_GENERATED
    db.commit()
    
    # 启动后台大纲生成任务
    background_tasks.add_task(
        generate_outline_task,
        project_id,
        user_id,
        analysis.to_dict()
    )
    
    return OutlineGenerateResponse(
        status="started",
        message="大纲生成已开始，请稍后查看结果"
    )

@router.get("/projects/{project_id}/outline")
def get_outline(
    project_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取标书大纲"""
    # 验证项目存在
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取大纲树形结构
    outlines = db.query(BidOutline).filter(
        BidOutline.project_id == project_id,
        BidOutline.user_id == user_id
    ).order_by(BidOutline.order_index, BidOutline.sequence).all()
    
    if not outlines:
        return {
            "status": "empty",
            "message": "大纲尚未生成",
            "outline": []
        }
    
    # 构建树形结构
    outline_tree = build_outline_tree(outlines)
    
    return {
        "status": "success",
        "message": "获取大纲成功",
        "outline": outline_tree
    }

@router.post("/projects/{project_id}/outline")
def create_outline_node(
    project_id: int,
    outline_data: OutlineCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """创建大纲节点"""
    # 验证项目存在
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 验证父节点存在（如果指定了parent_id）
    if outline_data.parent_id:
        parent = db.query(BidOutline).filter(
            BidOutline.id == outline_data.parent_id,
            BidOutline.project_id == project_id,
            BidOutline.user_id == user_id
        ).first()
        
        if not parent:
            raise HTTPException(status_code=400, detail="父节点不存在")
        
        if outline_data.level != parent.level + 1:
            raise HTTPException(status_code=400, detail="层级设置错误")
    
    # 生成序号
    sequence = generate_outline_sequence(db, project_id, user_id, outline_data.level, outline_data.parent_id)
    
    # 获取排序索引
    max_order = db.query(BidOutline).filter(
        BidOutline.project_id == project_id,
        BidOutline.user_id == user_id,
        BidOutline.parent_id == outline_data.parent_id
    ).count()
    
    # 创建大纲节点
    outline = BidOutline(
        project_id=project_id,
        user_id=user_id,
        title=outline_data.title,
        level=outline_data.level,
        sequence=sequence,
        parent_id=outline_data.parent_id,
        order_index=max_order + 1,
        content=outline_data.content
    )
    
    db.add(outline)
    db.commit()
    db.refresh(outline)
    
    return outline.to_dict()

@router.put("/projects/{project_id}/outline/{outline_id}")
def update_outline_node(
    project_id: int,
    outline_id: int,
    outline_data: OutlineUpdate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """更新大纲节点"""
    # 验证项目和大纲节点存在
    outline = db.query(BidOutline).filter(
        BidOutline.id == outline_id,
        BidOutline.project_id == project_id,
        BidOutline.user_id == user_id
    ).first()
    
    if not outline:
        raise HTTPException(status_code=404, detail="大纲节点不存在")
    
    # 更新字段
    if outline_data.title is not None:
        outline.title = outline_data.title
    if outline_data.content is not None:
        outline.content = outline_data.content
    if outline_data.order_index is not None:
        outline.order_index = outline_data.order_index
    
    db.commit()
    db.refresh(outline)
    
    return outline.to_dict()

@router.delete("/projects/{project_id}/outline/{outline_id}")
def delete_outline_node(
    project_id: int,
    outline_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """删除大纲节点"""
    # 验证项目和大纲节点存在
    outline = db.query(BidOutline).filter(
        BidOutline.id == outline_id,
        BidOutline.project_id == project_id,
        BidOutline.user_id == user_id
    ).first()
    
    if not outline:
        raise HTTPException(status_code=404, detail="大纲节点不存在")
    
    try:
        # 删除节点（级联删除子节点）
        db.delete(outline)
        db.commit()
        
        # 重新排序同级节点
        reorder_outline_siblings(db, project_id, user_id, outline.parent_id)
        
        return {"message": "大纲节点删除成功"}
    except Exception as e:
        db.rollback()
        logger.error(f"删除大纲节点失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除大纲节点失败")

@router.put("/projects/{project_id}/outline/reorder")
def reorder_outline(
    project_id: int,
    outline_orders: List[dict],  # [{"id": 1, "order_index": 1}, ...]
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """重新排序大纲"""
    # 验证项目存在
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    try:
        # 更新排序
        for order_data in outline_orders:
            outline = db.query(BidOutline).filter(
                BidOutline.id == order_data["id"],
                BidOutline.project_id == project_id,
                BidOutline.user_id == user_id
            ).first()
            
            if outline:
                outline.order_index = order_data["order_index"]
        
        db.commit()
        return {"message": "大纲排序更新成功"}
    except Exception as e:
        db.rollback()
        logger.error(f"大纲排序失败: {str(e)}")
        raise HTTPException(status_code=500, detail="大纲排序失败")

@router.put("/projects/{project_id}/outline/{outline_id}/move")
def move_outline_node_endpoint(
    project_id: int,
    outline_id: int,
    move_data: dict,  # {"new_parent_id": int|null, "new_position": int}
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """移动大纲节点到新位置"""
    # 验证项目存在
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    new_parent_id = move_data.get("new_parent_id")
    new_position = move_data.get("new_position", 0)
    
    success = move_outline_node(db, project_id, user_id, outline_id, new_parent_id, new_position)
    
    if success:
        return {"message": "大纲节点移动成功"}
    else:
        raise HTTPException(status_code=400, detail="大纲节点移动失败")

@router.post("/projects/{project_id}/outline/{outline_id}/copy")
def copy_outline_node_endpoint(
    project_id: int,
    outline_id: int,
    copy_data: dict,  # {"target_parent_id": int|null}
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """复制大纲节点"""
    # 验证项目存在
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    target_parent_id = copy_data.get("target_parent_id")
    
    new_node = copy_outline_node(db, project_id, user_id, outline_id, target_parent_id)
    
    if new_node:
        return {
            "message": "大纲节点复制成功",
            "new_node": new_node.to_dict()
        }
    else:
        raise HTTPException(status_code=400, detail="大纲节点复制失败")

@router.get("/projects/{project_id}/outline/validate")
def validate_outline_structure_endpoint(
    project_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """验证大纲结构"""
    # 验证项目存在
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    validation_result = validate_outline_structure(db, project_id, user_id)
    
    return {
        "validation": validation_result,
        "message": "结构验证完成" if validation_result["is_valid"] else "发现结构问题"
    }

@router.put("/projects/{project_id}/outline/regenerate-sequences")
def regenerate_sequences_endpoint(
    project_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """重新生成大纲序号"""
    # 验证项目存在
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    try:
        regenerate_outline_sequences(db, project_id, user_id)
        db.commit()
        return {"message": "大纲序号重新生成成功"}
    except Exception as e:
        db.rollback()
        logger.error(f"重新生成序号失败: {str(e)}")
        raise HTTPException(status_code=500, detail="重新生成序号失败")

@router.get("/projects/{project_id}/outline/statistics")
def get_outline_statistics(
    project_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取大纲统计信息"""
    # 验证项目存在
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取统计信息
    total_nodes = db.query(BidOutline).filter(
        BidOutline.project_id == project_id,
        BidOutline.user_id == user_id
    ).count()
    
    level_counts = {}
    for level in [1, 2, 3]:
        count = db.query(BidOutline).filter(
            BidOutline.project_id == project_id,
            BidOutline.user_id == user_id,
            BidOutline.level == level
        ).count()
        level_counts[f"level_{level}"] = count
    
    # 获取最深层级
    max_level_result = db.query(BidOutline.level).filter(
        BidOutline.project_id == project_id,
        BidOutline.user_id == user_id
    ).order_by(BidOutline.level.desc()).first()
    
    max_level = max_level_result[0] if max_level_result else 0
    
    # 获取有内容的节点数量
    nodes_with_content = db.query(BidOutline).filter(
        BidOutline.project_id == project_id,
        BidOutline.user_id == user_id,
        BidOutline.content.isnot(None),
        BidOutline.content != ""
    ).count()
    
    return {
        "total_nodes": total_nodes,
        "level_counts": level_counts,
        "max_level": max_level,
        "nodes_with_content": nodes_with_content,
        "completion_rate": round((nodes_with_content / total_nodes * 100), 2) if total_nodes > 0 else 0
    }

# Helper functions
def build_outline_tree(outlines: List[BidOutline]) -> List[dict]:
    """构建大纲树形结构"""
    outline_dict = {outline.id: outline.to_dict() for outline in outlines}
    tree = []
    
    for outline in outlines:
        outline_data = outline_dict[outline.id]
        outline_data['children'] = []
        
        if outline.parent_id is None:
            tree.append(outline_data)
        else:
            if outline.parent_id in outline_dict:
                outline_dict[outline.parent_id]['children'].append(outline_data)
    
    return tree

def generate_outline_sequence(db: Session, project_id: int, user_id: str, level: int, parent_id: Optional[int]) -> str:
    """生成大纲序号"""
    if level == 1:
        # 一级标题：1, 2, 3...
        count = db.query(BidOutline).filter(
            BidOutline.project_id == project_id,
            BidOutline.user_id == user_id,
            BidOutline.level == 1
        ).count()
        return str(count + 1)
    
    elif level == 2:
        # 二级标题：1.1, 1.2, 1.3...
        parent = db.query(BidOutline).filter(
            BidOutline.id == parent_id,
            BidOutline.project_id == project_id,
            BidOutline.user_id == user_id
        ).first()
        
        if not parent:
            raise HTTPException(status_code=400, detail="父节点不存在")
        
        count = db.query(BidOutline).filter(
            BidOutline.project_id == project_id,
            BidOutline.user_id == user_id,
            BidOutline.level == 2,
            BidOutline.parent_id == parent_id
        ).count()
        
        return f"{parent.sequence}.{count + 1}"
    
    elif level == 3:
        # 三级标题：1.1.1, 1.1.2, 1.1.3...
        parent = db.query(BidOutline).filter(
            BidOutline.id == parent_id,
            BidOutline.project_id == project_id,
            BidOutline.user_id == user_id
        ).first()
        
        if not parent:
            raise HTTPException(status_code=400, detail="父节点不存在")
        
        count = db.query(BidOutline).filter(
            BidOutline.project_id == project_id,
            BidOutline.user_id == user_id,
            BidOutline.level == 3,
            BidOutline.parent_id == parent_id
        ).count()
        
        return f"{parent.sequence}.{count + 1}"
    
    else:
        raise HTTPException(status_code=400, detail="不支持的层级")

def reorder_outline_siblings(db: Session, project_id: int, user_id: str, parent_id: Optional[int]):
    """重新排序同级大纲节点"""
    siblings = db.query(BidOutline).filter(
        BidOutline.project_id == project_id,
        BidOutline.user_id == user_id,
        BidOutline.parent_id == parent_id
    ).order_by(BidOutline.order_index).all()
    
    for i, sibling in enumerate(siblings):
        sibling.order_index = i + 1
    
    db.commit()

def move_outline_node(db: Session, project_id: int, user_id: str, node_id: int, 
                     new_parent_id: Optional[int], new_position: int) -> bool:
    """移动大纲节点到新位置"""
    try:
        # 获取要移动的节点
        node = db.query(BidOutline).filter(
            BidOutline.id == node_id,
            BidOutline.project_id == project_id,
            BidOutline.user_id == user_id
        ).first()
        
        if not node:
            return False
        
        # 验证新父节点
        if new_parent_id:
            new_parent = db.query(BidOutline).filter(
                BidOutline.id == new_parent_id,
                BidOutline.project_id == project_id,
                BidOutline.user_id == user_id
            ).first()
            
            if not new_parent:
                return False
            
            # 检查层级关系是否合理
            if new_parent.level >= node.level:
                return False
            
            # 更新节点层级
            level_diff = (new_parent.level + 1) - node.level
            update_node_level_recursive(db, node, level_diff)
        else:
            # 移动到根级别
            level_diff = 1 - node.level
            update_node_level_recursive(db, node, level_diff)
        
        # 更新父节点关系
        old_parent_id = node.parent_id
        node.parent_id = new_parent_id
        
        # 重新生成序号
        regenerate_outline_sequences(db, project_id, user_id)
        
        # 重新排序原父节点的子节点
        if old_parent_id != new_parent_id:
            reorder_outline_siblings(db, project_id, user_id, old_parent_id)
            reorder_outline_siblings(db, project_id, user_id, new_parent_id)
        
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"移动大纲节点失败: {str(e)}")
        return False

def update_node_level_recursive(db: Session, node: BidOutline, level_diff: int):
    """递归更新节点及其子节点的层级"""
    node.level += level_diff
    
    # 更新所有子节点
    children = db.query(BidOutline).filter(BidOutline.parent_id == node.id).all()
    for child in children:
        update_node_level_recursive(db, child, level_diff)

def regenerate_outline_sequences(db: Session, project_id: int, user_id: str):
    """重新生成所有大纲节点的序号"""
    # 获取所有节点，按层级和排序索引排序
    all_nodes = db.query(BidOutline).filter(
        BidOutline.project_id == project_id,
        BidOutline.user_id == user_id
    ).order_by(BidOutline.level, BidOutline.order_index).all()
    
    # 构建层级计数器
    level_counters = {}
    parent_sequences = {}
    
    for node in all_nodes:
        if node.level == 1:
            # 一级标题
            if 1 not in level_counters:
                level_counters[1] = 0
            level_counters[1] += 1
            node.sequence = str(level_counters[1])
            parent_sequences[node.id] = node.sequence
            
        elif node.level == 2:
            # 二级标题
            if node.parent_id and node.parent_id in parent_sequences:
                parent_seq = parent_sequences[node.parent_id]
                key = f"{parent_seq}_2"
                if key not in level_counters:
                    level_counters[key] = 0
                level_counters[key] += 1
                node.sequence = f"{parent_seq}.{level_counters[key]}"
                parent_sequences[node.id] = node.sequence
                
        elif node.level == 3:
            # 三级标题
            if node.parent_id and node.parent_id in parent_sequences:
                parent_seq = parent_sequences[node.parent_id]
                key = f"{parent_seq}_3"
                if key not in level_counters:
                    level_counters[key] = 0
                level_counters[key] += 1
                node.sequence = f"{parent_seq}.{level_counters[key]}"
                parent_sequences[node.id] = node.sequence

def copy_outline_node(db: Session, project_id: int, user_id: str, node_id: int, 
                     target_parent_id: Optional[int] = None) -> Optional[BidOutline]:
    """复制大纲节点（包括子节点）"""
    try:
        # 获取源节点
        source_node = db.query(BidOutline).filter(
            BidOutline.id == node_id,
            BidOutline.project_id == project_id,
            BidOutline.user_id == user_id
        ).first()
        
        if not source_node:
            return None
        
        # 确定新的层级
        new_level = 1
        if target_parent_id:
            parent = db.query(BidOutline).filter(
                BidOutline.id == target_parent_id,
                BidOutline.project_id == project_id,
                BidOutline.user_id == user_id
            ).first()
            if parent:
                new_level = parent.level + 1
        
        # 创建新节点
        new_node = BidOutline(
            project_id=project_id,
            user_id=user_id,
            title=f"{source_node.title} (副本)",
            level=new_level,
            sequence="",  # 稍后生成
            parent_id=target_parent_id,
            order_index=0,  # 稍后调整
            content=source_node.content
        )
        
        db.add(new_node)
        db.flush()  # 获取ID
        
        # 递归复制子节点
        copy_children_recursive(db, source_node.id, new_node.id, project_id, user_id)
        
        # 重新生成序号和排序
        regenerate_outline_sequences(db, project_id, user_id)
        reorder_outline_siblings(db, project_id, user_id, target_parent_id)
        
        db.commit()
        return new_node
        
    except Exception as e:
        db.rollback()
        logger.error(f"复制大纲节点失败: {str(e)}")
        return None

def copy_children_recursive(db: Session, source_parent_id: int, new_parent_id: int, 
                          project_id: int, user_id: str):
    """递归复制子节点"""
    children = db.query(BidOutline).filter(
        BidOutline.parent_id == source_parent_id,
        BidOutline.project_id == project_id,
        BidOutline.user_id == user_id
    ).all()
    
    for child in children:
        new_child = BidOutline(
            project_id=project_id,
            user_id=user_id,
            title=child.title,
            level=child.level,
            sequence="",  # 稍后生成
            parent_id=new_parent_id,
            order_index=child.order_index,
            content=child.content
        )
        
        db.add(new_child)
        db.flush()
        
        # 递归复制子节点的子节点
        copy_children_recursive(db, child.id, new_child.id, project_id, user_id)

def validate_outline_structure(db: Session, project_id: int, user_id: str) -> Dict[str, Any]:
    """验证大纲结构的完整性"""
    issues = []
    warnings = []
    
    try:
        # 获取所有节点
        nodes = db.query(BidOutline).filter(
            BidOutline.project_id == project_id,
            BidOutline.user_id == user_id
        ).all()
        
        if not nodes:
            return {
                "is_valid": True,
                "issues": [],
                "warnings": ["大纲为空"],
                "node_count": 0
            }
        
        # 检查层级关系
        for node in nodes:
            if node.parent_id:
                parent = db.query(BidOutline).filter(
                    BidOutline.id == node.parent_id,
                    BidOutline.project_id == project_id,
                    BidOutline.user_id == user_id
                ).first()
                
                if not parent:
                    issues.append(f"节点 '{node.title}' 的父节点不存在")
                elif parent.level >= node.level:
                    issues.append(f"节点 '{node.title}' 的层级关系错误")
        
        # 检查序号格式
        for node in nodes:
            if not node.sequence:
                issues.append(f"节点 '{node.title}' 缺少序号")
            elif not validate_sequence_format(node.sequence, node.level):
                issues.append(f"节点 '{node.title}' 的序号格式错误: {node.sequence}")
        
        # 检查是否有孤立节点
        root_nodes = [n for n in nodes if n.parent_id is None]
        if not root_nodes:
            issues.append("缺少根级别节点")
        
        # 检查重复序号
        sequences = [n.sequence for n in nodes]
        duplicate_sequences = [seq for seq in set(sequences) if sequences.count(seq) > 1]
        if duplicate_sequences:
            issues.append(f"存在重复序号: {', '.join(duplicate_sequences)}")
        
        # 性能警告
        if len(nodes) > 100:
            warnings.append("大纲节点过多，可能影响性能")
        
        max_depth = max([n.level for n in nodes]) if nodes else 0
        if max_depth > 4:
            warnings.append("大纲层级过深，建议控制在4级以内")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "node_count": len(nodes),
            "max_depth": max_depth
        }
        
    except Exception as e:
        logger.error(f"验证大纲结构失败: {str(e)}")
        return {
            "is_valid": False,
            "issues": [f"验证过程出错: {str(e)}"],
            "warnings": [],
            "node_count": 0
        }

def validate_sequence_format(sequence: str, level: int) -> bool:
    """验证序号格式是否正确"""
    import re
    
    if level == 1:
        return re.match(r'^\d+$', sequence) is not None
    elif level == 2:
        return re.match(r'^\d+\.\d+$', sequence) is not None
    elif level == 3:
        return re.match(r'^\d+\.\d+\.\d+$', sequence) is not None
    else:
        return False

def generate_outline_task(project_id: int, user_id: str, analysis_data: dict):
    """生成大纲的后台任务"""
    from app.database import SessionLocal
    from app.services.bid_generation_service import BidGenerationService
    
    db = SessionLocal()
    try:
        # 获取需求分析对象
        analysis = db.query(RequirementAnalysis).filter(
            RequirementAnalysis.project_id == project_id,
            RequirementAnalysis.user_id == user_id
        ).first()
        
        if not analysis:
            raise Exception("需求分析结果不存在")
        
        # 使用大纲生成服务
        bid_service = BidGenerationService()
        outlines = bid_service.generate_outline(db, project_id, user_id, analysis)
        
        # 更新项目状态
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.OUTLINE_GENERATED
            db.commit()
        
        logger.info(f"项目 {project_id} 大纲生成完成，共生成 {len(outlines)} 个节点")
        
    except Exception as e:
        db.rollback()
        logger.error(f"项目 {project_id} 大纲生成失败: {str(e)}")
        
        # 更新项目状态为失败
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.FAILED
            db.commit()
    
    finally:
        db.close()

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