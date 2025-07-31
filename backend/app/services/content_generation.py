"""
内容生成服务
基于大纲结构智能生成标书内容
"""
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.tender import (
    TenderProject, 
    TenderStatus, 
    AnalysisResult,
    OutlineStructure,
    ChapterContent
)
from app.services.tender_storage import TenderStorageService
from app.services.ai_client import get_ai_client, AIServiceError, PromptTemplates
from app.services.task_manager import get_task_manager, TaskType, TaskInfo

logger = logging.getLogger(__name__)


class ContentGenerationService:
    """内容生成服务"""
    
    def __init__(self, db: Session, storage_service: TenderStorageService = None, ai_client=None):
        self.db = db
        self.storage_service = storage_service or TenderStorageService()
        self.ai_client = ai_client or get_ai_client()
        self.task_manager = get_task_manager()
        
        # 注册任务处理器
        self._register_task_handlers()
    
    def _register_task_handlers(self):
        """注册任务处理器"""
        self.task_manager.register_handler(
            TaskType.CONTENT_GENERATION, 
            self._handle_content_generation_task
        )
    
    async def generate_all_content_async(
        self, 
        project_id: str, 
        tenant_id: str, 
        user_id: str,
        regenerate_existing: bool = False
    ) -> str:
        """
        异步生成所有章节内容
        
        Args:
            project_id: 项目ID
            tenant_id: 租户ID
            user_id: 用户ID
            regenerate_existing: 是否重新生成已存在的内容
            
        Returns:
            str: 任务ID
        """
        # 创建异步任务
        task_id = await self.task_manager.create_task(
            task_type=TaskType.CONTENT_GENERATION,
            project_id=project_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title="生成标书内容",
            description="正在生成所有章节的标书内容...",
            metadata={
                "regenerate_existing": regenerate_existing,
                "operation": "generate_all"
            }
        )
        
        # 启动任务
        await self.task_manager.start_task(task_id)
        
        logger.info(f"创建内容生成任务: {task_id}, 项目: {project_id}")
        return task_id
    
    async def generate_chapter_content_async(
        self,
        project_id: str,
        chapter_id: str,
        tenant_id: str,
        user_id: str
    ) -> str:
        """
        异步生成单个章节内容
        
        Args:
            project_id: 项目ID
            chapter_id: 章节ID
            tenant_id: 租户ID
            user_id: 用户ID
            
        Returns:
            str: 任务ID
        """
        # 创建异步任务
        task_id = await self.task_manager.create_task(
            task_type=TaskType.CONTENT_GENERATION,
            project_id=project_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title=f"生成章节内容",
            description=f"正在生成章节 {chapter_id} 的内容...",
            metadata={
                "chapter_id": chapter_id,
                "operation": "generate_chapter"
            }
        )
        
        # 启动任务
        await self.task_manager.start_task(task_id)
        
        logger.info(f"创建章节内容生成任务: {task_id}, 项目: {project_id}, 章节: {chapter_id}")
        return task_id
    
    async def regenerate_chapter_async(
        self,
        project_id: str,
        chapter_id: str,
        tenant_id: str,
        user_id: str
    ) -> str:
        """
        异步重新生成章节内容
        
        Args:
            project_id: 项目ID
            chapter_id: 章节ID
            tenant_id: 租户ID
            user_id: 用户ID
            
        Returns:
            str: 任务ID
        """
        # 创建异步任务
        task_id = await self.task_manager.create_task(
            task_type=TaskType.CONTENT_GENERATION,
            project_id=project_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title=f"重新生成章节内容",
            description=f"正在重新生成章节 {chapter_id} 的内容...",
            metadata={
                "chapter_id": chapter_id,
                "operation": "regenerate_chapter"
            }
        )
        
        # 启动任务
        await self.task_manager.start_task(task_id)
        
        logger.info(f"创建章节重新生成任务: {task_id}, 项目: {project_id}, 章节: {chapter_id}")
        return task_id
    
    async def _handle_content_generation_task(self, task_info: TaskInfo, task_manager) -> Dict[str, Any]:
        """
        处理内容生成任务
        
        Args:
            task_info: 任务信息
            task_manager: 任务管理器
            
        Returns:
            Dict: 任务结果
        """
        try:
            operation = task_info.metadata.get("operation", "generate_all")
            project_id = task_info.project_id
            
            logger.info(f"开始处理内容生成任务: {task_info.task_id}, 操作: {operation}")
            
            if operation == "generate_all":
                return await self._handle_generate_all_task(task_info, task_manager)
            elif operation == "generate_chapter":
                return await self._handle_generate_chapter_task(task_info, task_manager)
            elif operation == "regenerate_chapter":
                return await self._handle_regenerate_chapter_task(task_info, task_manager)
            else:
                raise ValueError(f"未知的操作类型: {operation}")
                
        except Exception as e:
            logger.error(f"内容生成任务处理失败: {task_info.task_id}, 错误: {str(e)}")
            raise
    
    async def _handle_generate_all_task(self, task_info: TaskInfo, task_manager) -> Dict[str, Any]:
        """处理生成所有内容的任务"""
        project_id = task_info.project_id
        regenerate_existing = task_info.metadata.get("regenerate_existing", False)
        
        # 获取项目信息
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        # 更新任务进度
        await task_manager.update_task_progress(task_info.task_id, 5, "正在加载项目数据...")
        
        # 加载大纲结构
        outline = await self.storage_service.load_outline(project)
        if not outline or outline.chapter_count == 0:
            raise ValueError("项目大纲不存在或为空，请先生成大纲")
        
        # 加载分析结果
        analysis = await self.storage_service.load_analysis_result(project)
        
        # 更新项目状态
        project.status = TenderStatus.GENERATING
        self.db.commit()
        
        # 统计信息
        total_chapters = outline.chapter_count
        generated_count = 0
        skipped_count = 0
        failed_count = 0
        
        # 逐章节生成内容
        for i, chapter in enumerate(outline.chapters):
            try:
                # 检查任务是否被取消
                current_task = await task_manager.get_task_info(task_info.task_id)
                if current_task and current_task.status.value == "cancelled":
                    logger.info(f"任务被取消: {task_info.task_id}")
                    break
                
                # 更新进度
                progress = 10 + int((i / total_chapters) * 80)  # 10-90%
                await task_manager.update_task_progress(
                    task_info.task_id, 
                    progress, 
                    f"正在生成章节: {chapter.title} ({i+1}/{total_chapters})"
                )
                
                # 检查是否已存在内容
                if not regenerate_existing:
                    try:
                        existing_content = await self.storage_service.load_chapter_content(
                            project, chapter.chapter_id
                        )
                        if existing_content and existing_content.content:
                            logger.info(f"跳过已存在的章节内容: {chapter.chapter_id}")
                            skipped_count += 1
                            continue
                    except FileNotFoundError:
                        pass  # 内容不存在，继续生成
                
                # 生成章节内容
                content = await self.generate_chapter_content(
                    project_id, chapter.chapter_id, analysis, outline
                )
                
                if content:
                    generated_count += 1
                    logger.info(f"成功生成章节内容: {chapter.chapter_id}")
                else:
                    failed_count += 1
                    logger.warning(f"章节内容生成失败: {chapter.chapter_id}")
            
            except Exception as e:
                failed_count += 1
                logger.error(f"生成章节 {chapter.chapter_id} 内容时发生错误: {str(e)}")
                continue
        
        # 更新最终进度
        await task_manager.update_task_progress(task_info.task_id, 95, "正在完成任务...")
        
        # 更新项目状态
        if failed_count == 0:
            project.status = TenderStatus.GENERATED
        elif generated_count > 0:
            project.status = TenderStatus.GENERATED  # 部分成功也算生成完成
        else:
            project.status = TenderStatus.FAILED
        
        self.db.commit()
        
        result = {
            "total_chapters": total_chapters,
            "generated_count": generated_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "success_rate": (generated_count / total_chapters) * 100 if total_chapters > 0 else 0,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"内容生成任务完成，项目ID: {project_id}, 结果: {result}")
        return result
    
    async def _handle_generate_chapter_task(self, task_info: TaskInfo, task_manager) -> Dict[str, Any]:
        """处理生成单个章节的任务"""
        project_id = task_info.project_id
        chapter_id = task_info.metadata.get("chapter_id")
        
        if not chapter_id:
            raise ValueError("章节ID未指定")
        
        # 更新任务进度
        await task_manager.update_task_progress(task_info.task_id, 10, "正在加载项目数据...")
        
        # 生成章节内容
        await task_manager.update_task_progress(task_info.task_id, 30, f"正在生成章节内容: {chapter_id}")
        
        content = await self.generate_chapter_content(project_id, chapter_id)
        
        if not content:
            raise ValueError(f"章节 {chapter_id} 内容生成失败")
        
        await task_manager.update_task_progress(task_info.task_id, 90, "内容生成完成")
        
        result = {
            "chapter_id": chapter_id,
            "chapter_title": content.chapter_title,
            "word_count": content.word_count,
            "generated_at": content.generated_at.isoformat()
        }
        
        logger.info(f"章节内容生成任务完成，章节ID: {chapter_id}")
        return result
    
    async def _handle_regenerate_chapter_task(self, task_info: TaskInfo, task_manager) -> Dict[str, Any]:
        """处理重新生成章节的任务"""
        project_id = task_info.project_id
        chapter_id = task_info.metadata.get("chapter_id")
        
        if not chapter_id:
            raise ValueError("章节ID未指定")
        
        # 更新任务进度
        await task_manager.update_task_progress(task_info.task_id, 10, "正在备份现有内容...")
        
        # 重新生成章节内容
        await task_manager.update_task_progress(task_info.task_id, 30, f"正在重新生成章节内容: {chapter_id}")
        
        content = await self.regenerate_chapter(project_id, chapter_id)
        
        if not content:
            raise ValueError(f"章节 {chapter_id} 内容重新生成失败")
        
        await task_manager.update_task_progress(task_info.task_id, 90, "内容重新生成完成")
        
        result = {
            "chapter_id": chapter_id,
            "chapter_title": content.chapter_title,
            "word_count": content.word_count,
            "regenerated_at": content.generated_at.isoformat()
        }
        
        logger.info(f"章节内容重新生成任务完成，章节ID: {chapter_id}")
        return result
    
    async def generate_all_content(self, project_id: str, regenerate_existing: bool = False) -> Dict[str, Any]:
        """
        生成所有章节内容
        
        Args:
            project_id: 项目ID
            regenerate_existing: 是否重新生成已存在的内容
            
        Returns:
            Dict: 生成结果统计
            
        Raises:
            ValueError: 项目不存在或大纲不存在
            AIServiceError: AI服务调用失败
        """
        # 获取项目信息
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        logger.info(f"开始生成所有内容，项目ID: {project_id}")
        
        try:
            # 更新项目状态为内容生成中
            project.status = TenderStatus.GENERATING
            project.progress = 0
            self.db.commit()
            
            # 加载大纲结构
            outline = await self.storage_service.load_outline(project)
            if not outline or outline.chapter_count == 0:
                raise ValueError("项目大纲不存在或为空，请先生成大纲")
            
            # 加载分析结果
            analysis = await self.storage_service.load_analysis_result(project)
            
            # 统计信息
            total_chapters = outline.chapter_count
            generated_count = 0
            skipped_count = 0
            failed_count = 0
            
            # 逐章节生成内容
            for i, chapter in enumerate(outline.chapters):
                try:
                    # 更新进度
                    progress = int((i / total_chapters) * 90)  # 预留10%给最后的状态更新
                    project.progress = progress
                    self.db.commit()
                    
                    # 检查是否已存在内容
                    if not regenerate_existing:
                        try:
                            existing_content = await self.storage_service.load_chapter_content(
                                project, chapter.chapter_id
                            )
                            if existing_content and existing_content.content:
                                logger.info(f"跳过已存在的章节内容: {chapter.chapter_id}")
                                skipped_count += 1
                                continue
                        except FileNotFoundError:
                            pass  # 内容不存在，继续生成
                    
                    # 生成章节内容
                    content = await self.generate_chapter_content(
                        project_id, chapter.chapter_id, analysis, outline
                    )
                    
                    if content:
                        generated_count += 1
                        logger.info(f"成功生成章节内容: {chapter.chapter_id}")
                    else:
                        failed_count += 1
                        logger.warning(f"章节内容生成失败: {chapter.chapter_id}")
                
                except Exception as e:
                    failed_count += 1
                    logger.error(f"生成章节 {chapter.chapter_id} 内容时发生错误: {str(e)}")
                    continue
            
            # 更新项目状态
            if failed_count == 0:
                project.status = TenderStatus.GENERATED
            elif generated_count > 0:
                project.status = TenderStatus.GENERATED  # 部分成功也算生成完成
            else:
                project.status = TenderStatus.FAILED
            
            project.progress = 100
            self.db.commit()
            
            result = {
                "total_chapters": total_chapters,
                "generated_count": generated_count,
                "skipped_count": skipped_count,
                "failed_count": failed_count,
                "success_rate": (generated_count / total_chapters) * 100 if total_chapters > 0 else 0,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"内容生成完成，项目ID: {project_id}, 结果: {result}")
            return result
            
        except Exception as e:
            # 更新项目状态为失败
            project.status = TenderStatus.FAILED
            self.db.commit()
            logger.error(f"内容生成失败，项目ID: {project_id}, 错误: {str(e)}")
            raise
    
    async def generate_chapter_content(
        self, 
        project_id: str, 
        chapter_id: str,
        analysis: AnalysisResult = None,
        outline: OutlineStructure = None
    ) -> Optional[ChapterContent]:
        """
        生成单个章节内容
        
        Args:
            project_id: 项目ID
            chapter_id: 章节ID
            analysis: 分析结果（可选，如果不提供会自动加载）
            outline: 大纲结构（可选，如果不提供会自动加载）
            
        Returns:
            ChapterContent: 生成的章节内容，失败时返回None
        """
        # 获取项目信息
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        logger.info(f"开始生成章节内容，项目ID: {project_id}, 章节ID: {chapter_id}")
        
        try:
            # 加载必要数据
            if analysis is None:
                analysis = await self.storage_service.load_analysis_result(project)
            
            if outline is None:
                outline = await self.storage_service.load_outline(project)
            
            # 查找目标章节
            target_chapter = None
            for chapter in outline.chapters:
                if chapter.chapter_id == chapter_id:
                    target_chapter = chapter
                    break
            
            if not target_chapter:
                raise ValueError(f"章节 {chapter_id} 在大纲中不存在")
            
            # 构建内容生成提示词
            prompt = self._build_content_generation_prompt(
                target_chapter, analysis, outline
            )
            
            # 调用AI服务生成内容
            response = await self.ai_client.generate(
                prompt=prompt,
                max_tokens=4000,
                temperature=0.7
            )
            
            if not response.success:
                logger.error(f"AI生成章节内容失败: {response.error_message}")
                return None
            
            # 创建章节内容对象
            content = ChapterContent(
                chapter_id=chapter_id,
                chapter_title=target_chapter.title,
                content=response.content,
                word_count=len(response.content),
                generated_at=datetime.utcnow()
            )
            
            # 保存章节内容
            await self.storage_service.save_chapter_content(project, content)
            
            logger.info(f"章节内容生成完成，章节ID: {chapter_id}, 字数: {content.word_count}")
            return content
            
        except Exception as e:
            logger.error(f"生成章节内容失败，章节ID: {chapter_id}, 错误: {str(e)}")
            return None
    
    async def regenerate_chapter(self, project_id: str, chapter_id: str) -> Optional[ChapterContent]:
        """
        重新生成章节内容
        
        Args:
            project_id: 项目ID
            chapter_id: 章节ID
            
        Returns:
            ChapterContent: 重新生成的章节内容
        """
        logger.info(f"重新生成章节内容，项目ID: {project_id}, 章节ID: {chapter_id}")
        
        # 备份现有内容（如果存在）
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if project:
            try:
                existing_content = await self.storage_service.load_chapter_content(
                    project, chapter_id
                )
                if existing_content:
                    # 创建备份
                    backup_suffix = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    backup_path = f"{project.get_storage_path()}/content/backups/chapter_{chapter_id}_{backup_suffix}.json"
                    await self.storage_service._save_json(backup_path, existing_content.model_dump())
                    logger.info(f"已备份现有章节内容: {backup_path}")
            except FileNotFoundError:
                pass  # 没有现有内容，无需备份
        
        # 重新生成内容
        return await self.generate_chapter_content(project_id, chapter_id)
    
    async def get_chapter_content(self, project_id: str, chapter_id: str) -> Optional[ChapterContent]:
        """
        获取章节内容
        
        Args:
            project_id: 项目ID
            chapter_id: 章节ID
            
        Returns:
            ChapterContent: 章节内容，不存在时返回None
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            return None
        
        try:
            return await self.storage_service.load_chapter_content(project, chapter_id)
        except FileNotFoundError:
            return None
    
    async def get_all_content(self, project_id: str) -> List[ChapterContent]:
        """
        获取项目的所有章节内容
        
        Args:
            project_id: 项目ID
            
        Returns:
            List[ChapterContent]: 所有章节内容列表
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            return []
        
        return await self.storage_service.load_all_chapters(project)
    
    async def update_chapter_content(
        self, 
        project_id: str, 
        chapter_id: str, 
        content: str
    ) -> Optional[ChapterContent]:
        """
        更新章节内容
        
        Args:
            project_id: 项目ID
            chapter_id: 章节ID
            content: 新的内容
            
        Returns:
            ChapterContent: 更新后的章节内容
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        try:
            # 加载现有内容
            existing_content = await self.storage_service.load_chapter_content(
                project, chapter_id
            )
            
            # 更新内容
            updated_content = ChapterContent(
                chapter_id=chapter_id,
                chapter_title=existing_content.chapter_title,
                content=content,
                word_count=len(content),
                generated_at=datetime.utcnow()
            )
            
            # 保存更新后的内容
            await self.storage_service.save_chapter_content(project, updated_content)
            
            logger.info(f"章节内容更新完成，章节ID: {chapter_id}")
            return updated_content
            
        except FileNotFoundError:
            # 如果章节不存在，创建新的
            logger.info(f"章节不存在，创建新章节: {chapter_id}")
            
            # 需要从大纲获取章节标题
            try:
                outline = await self.storage_service.load_outline(project)
                chapter_title = "未知章节"
                for chapter in outline.chapters:
                    if chapter.chapter_id == chapter_id:
                        chapter_title = chapter.title
                        break
                
                new_content = ChapterContent(
                    chapter_id=chapter_id,
                    chapter_title=chapter_title,
                    content=content,
                    word_count=len(content),
                    generated_at=datetime.utcnow()
                )
                
                await self.storage_service.save_chapter_content(project, new_content)
                return new_content
                
            except Exception as e:
                logger.error(f"创建新章节内容失败: {str(e)}")
                return None
    
    async def get_content_statistics(self, project_id: str) -> Dict[str, Any]:
        """
        获取内容生成统计信息
        
        Args:
            project_id: 项目ID
            
        Returns:
            Dict: 统计信息
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            return {"error": "项目不存在"}
        
        try:
            # 加载大纲和内容
            outline = await self.storage_service.load_outline(project)
            all_content = await self.storage_service.load_all_chapters(project)
            
            # 统计信息
            total_chapters = outline.chapter_count if outline else 0
            generated_chapters = len(all_content)
            total_words = sum(content.word_count for content in all_content)
            
            # 计算完成率
            completion_rate = (generated_chapters / total_chapters * 100) if total_chapters > 0 else 0
            
            # 按章节统计
            chapter_stats = []
            if outline:
                for chapter in outline.chapters:
                    chapter_content = None
                    for content in all_content:
                        if content.chapter_id == chapter.chapter_id:
                            chapter_content = content
                            break
                    
                    chapter_stats.append({
                        "chapter_id": chapter.chapter_id,
                        "title": chapter.title,
                        "has_content": chapter_content is not None,
                        "word_count": chapter_content.word_count if chapter_content else 0,
                        "generated_at": chapter_content.generated_at.isoformat() if chapter_content else None
                    })
            
            return {
                "project_id": project_id,
                "total_chapters": total_chapters,
                "generated_chapters": generated_chapters,
                "completion_rate": completion_rate,
                "total_words": total_words,
                "average_words_per_chapter": total_words / generated_chapters if generated_chapters > 0 else 0,
                "chapter_statistics": chapter_stats,
                "last_updated": max(
                    (content.generated_at for content in all_content), 
                    default=datetime.utcnow()
                ).isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取内容统计失败: {str(e)}")
            return {"error": str(e)}
    
    def _build_content_generation_prompt(
        self, 
        chapter: Any, 
        analysis: AnalysisResult, 
        outline: OutlineStructure
    ) -> str:
        """
        构建内容生成AI提示词
        
        Args:
            chapter: 目标章节信息
            analysis: 分析结果
            outline: 大纲结构
            
        Returns:
            str: AI提示词
        """
        # 检测章节类型
        chapter_type = self._detect_chapter_type(chapter.title, chapter.description)
        
        # 如果是特定类型的章节，使用专门的提示词模板
        if chapter_type:
            try:
                return PromptTemplates.format_chapter_specific_prompt(
                    chapter_type=chapter_type,
                    project_info=analysis.project_info,
                    technical_requirements=analysis.technical_requirements,
                    evaluation_criteria=analysis.evaluation_criteria
                )
            except Exception as e:
                logger.warning(f"使用特定章节模板失败，降级到通用模板: {str(e)}")
        
        # 使用通用模板
        return self._build_generic_content_prompt(chapter, analysis, outline)
    
    def _detect_chapter_type(self, title: str, description: str) -> Optional[str]:
        """
        检测章节类型
        
        Args:
            title: 章节标题
            description: 章节描述
            
        Returns:
            str: 章节类型，如果无法识别返回None
        """
        title_lower = title.lower()
        description_lower = description.lower()
        
        # 项目理解类型
        if any(keyword in title_lower for keyword in ["项目理解", "需求理解", "项目背景", "需求分析"]):
            return "project_understanding"
        
        # 技术方案类型
        if any(keyword in title_lower for keyword in ["技术方案", "系统设计", "架构设计", "技术设计"]):
            return "technical_solution"
        
        # 实施计划类型
        if any(keyword in title_lower for keyword in ["实施计划", "实施方案", "项目计划", "进度安排"]):
            return "implementation_plan"
        
        # 质量保证类型
        if any(keyword in title_lower for keyword in ["质量保证", "质量管理", "测试方案", "质量控制"]):
            return "quality_assurance"
        
        # 服务保障类型
        if any(keyword in title_lower for keyword in ["服务保障", "售后服务", "技术支持", "运维支持"]):
            return "service_support"
        
        return None
    
    def _build_generic_content_prompt(
        self, 
        chapter: Any, 
        analysis: AnalysisResult, 
        outline: OutlineStructure
    ) -> str:
        """
        构建通用内容生成AI提示词
        
        Args:
            chapter: 目标章节信息
            analysis: 分析结果
            outline: 大纲结构
            
        Returns:
            str: AI提示词
        """
        # 构建上下文信息
        project_context = {
            "项目名称": analysis.project_info.get("project_name", "未知项目"),
            "项目概述": analysis.project_info.get("project_overview", ""),
            "项目预算": analysis.project_info.get("budget", ""),
            "项目工期": analysis.project_info.get("duration", "")
        }
        
        # 技术要求摘要
        tech_summary = []
        if analysis.technical_requirements:
            if analysis.technical_requirements.get("functional_requirements"):
                tech_summary.extend(analysis.technical_requirements["functional_requirements"][:5])
            if analysis.technical_requirements.get("performance_requirements"):
                perf_req = analysis.technical_requirements["performance_requirements"]
                if isinstance(perf_req, dict):
                    tech_summary.extend([f"{k}: {v}" for k, v in perf_req.items()])
                else:
                    tech_summary.append(f"性能要求: {perf_req}")
        
        # 评分标准摘要
        eval_summary = ""
        if analysis.evaluation_criteria:
            tech_weight = analysis.evaluation_criteria.get("technical_score", {}).get("weight", 0)
            comm_weight = analysis.evaluation_criteria.get("commercial_score", {}).get("weight", 0)
            eval_summary = f"技术分权重: {tech_weight}%, 商务分权重: {comm_weight}%"
        
        # 子章节信息
        subsections_text = ""
        if chapter.subsections:
            subsections_text = "本章节应包含以下子章节:\n"
            for subsection in chapter.subsections:
                subsections_text += f"- {subsection.get('title', subsection.get('id', ''))}\n"
        
        # 使用通用提示词模板
        return PromptTemplates.format_content_generation_prompt(
            chapter_title=chapter.title,
            chapter_description=chapter.description,
            project_context=project_context,
            subsections_info=subsections_text,
            technical_requirements="\n".join(f"- {req}" for req in tech_summary[:10]),
            evaluation_criteria=eval_summary
        )
    
    async def generate_content_with_context(
        self,
        project_id: str,
        chapter_id: str,
        additional_context: Dict[str, Any] = None
    ) -> Optional[ChapterContent]:
        """
        基于上下文生成章节内容
        
        Args:
            project_id: 项目ID
            chapter_id: 章节ID
            additional_context: 额外的上下文信息
            
        Returns:
            ChapterContent: 生成的章节内容
        """
        # 获取项目信息
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        logger.info(f"基于上下文生成章节内容，项目ID: {project_id}, 章节ID: {chapter_id}")
        
        try:
            # 加载必要数据
            analysis = await self.storage_service.load_analysis_result(project)
            outline = await self.storage_service.load_outline(project)
            
            # 查找目标章节
            target_chapter = None
            for chapter in outline.chapters:
                if chapter.chapter_id == chapter_id:
                    target_chapter = chapter
                    break
            
            if not target_chapter:
                raise ValueError(f"章节 {chapter_id} 在大纲中不存在")
            
            # 获取已生成的其他章节内容作为上下文
            existing_chapters = await self.storage_service.load_all_chapters(project)
            context_content = []
            
            for existing_chapter in existing_chapters:
                if existing_chapter.chapter_id != chapter_id:
                    context_content.append({
                        "title": existing_chapter.chapter_title,
                        "content_summary": existing_chapter.content[:200] + "..." if len(existing_chapter.content) > 200 else existing_chapter.content
                    })
            
            # 构建增强的提示词
            base_prompt = self._build_content_generation_prompt(target_chapter, analysis, outline)
            
            # 添加上下文信息
            if context_content:
                context_text = "\n\n已生成的其他章节内容摘要（供参考，保持内容一致性）:\n"
                for ctx in context_content:
                    context_text += f"- {ctx['title']}: {ctx['content_summary']}\n"
                base_prompt += context_text
            
            # 添加额外上下文
            if additional_context:
                extra_context = "\n\n额外上下文信息:\n"
                for key, value in additional_context.items():
                    extra_context += f"- {key}: {value}\n"
                base_prompt += extra_context
            
            # 调用AI服务生成内容
            response = await self.ai_client.generate(
                prompt=base_prompt,
                max_tokens=4000,
                temperature=0.7
            )
            
            if not response.success:
                logger.error(f"AI生成章节内容失败: {response.error_message}")
                return None
            
            # 创建章节内容对象
            content = ChapterContent(
                chapter_id=chapter_id,
                chapter_title=target_chapter.title,
                content=response.content,
                word_count=len(response.content),
                generated_at=datetime.utcnow()
            )
            
            # 保存章节内容
            await self.storage_service.save_chapter_content(project, content)
            
            logger.info(f"基于上下文的章节内容生成完成，章节ID: {chapter_id}, 字数: {content.word_count}")
            return content
            
        except Exception as e:
            logger.error(f"基于上下文生成章节内容失败，章节ID: {chapter_id}, 错误: {str(e)}")
            return None