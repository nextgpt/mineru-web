"""
内容存储和管理服务
提供内容版本控制、编辑历史和搜索统计功能
"""
import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from dataclasses import dataclass

from app.models.tender import (
    TenderProject, 
    ChapterContent,
    OutlineStructure
)
from app.services.tender_storage import TenderStorageService
from app.utils.minio_client import minio_client as default_minio_client, MINIO_BUCKET

logger = logging.getLogger(__name__)


@dataclass
class ContentVersion:
    """内容版本信息"""
    version_id: str
    chapter_id: str
    chapter_title: str
    content: str
    word_count: int
    created_at: datetime
    created_by: str
    version_note: Optional[str] = None
    is_current: bool = False


@dataclass
class ContentEditHistory:
    """内容编辑历史"""
    edit_id: str
    chapter_id: str
    action: str  # create, update, delete, restore
    old_content: Optional[str]
    new_content: Optional[str]
    word_count_change: int
    edited_at: datetime
    edited_by: str
    edit_note: Optional[str] = None


@dataclass
class ContentSearchResult:
    """内容搜索结果"""
    chapter_id: str
    chapter_title: str
    content_snippet: str
    match_count: int
    relevance_score: float


@dataclass
class ContentStatistics:
    """内容统计信息"""
    project_id: str
    total_chapters: int
    completed_chapters: int
    total_words: int
    average_words_per_chapter: int
    completion_rate: float
    last_updated: datetime
    chapter_stats: List[Dict[str, Any]]


class ContentManagementService:
    """内容存储和管理服务"""
    
    def __init__(self, db: Session, storage_service: TenderStorageService = None):
        self.db = db
        self.storage_service = storage_service or TenderStorageService()
        self.minio_client = default_minio_client
        self.bucket_name = MINIO_BUCKET
    
    # ==================== 内容数据操作接口 ====================
    
    async def create_chapter_content(
        self, 
        project_id: str, 
        chapter_id: str, 
        chapter_title: str,
        content: str,
        user_id: str,
        version_note: Optional[str] = None
    ) -> ChapterContent:
        """
        创建章节内容
        
        Args:
            project_id: 项目ID
            chapter_id: 章节ID
            chapter_title: 章节标题
            content: 内容
            user_id: 用户ID
            version_note: 版本说明
            
        Returns:
            ChapterContent: 创建的章节内容
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        # 创建章节内容对象
        chapter_content = ChapterContent(
            chapter_id=chapter_id,
            chapter_title=chapter_title,
            content=content,
            word_count=len(content),
            generated_at=datetime.utcnow()
        )
        
        # 保存内容
        await self.storage_service.save_chapter_content(project, chapter_content)
        
        # 创建版本记录
        await self._create_content_version(
            project, chapter_content, user_id, version_note, is_current=True
        )
        
        # 记录编辑历史
        await self._record_edit_history(
            project, chapter_id, "create", None, content, user_id, version_note
        )
        
        logger.info(f"创建章节内容: {project_id}/{chapter_id}")
        return chapter_content
    
    async def update_chapter_content(
        self, 
        project_id: str, 
        chapter_id: str, 
        content: str,
        user_id: str,
        version_note: Optional[str] = None
    ) -> ChapterContent:
        """
        更新章节内容
        
        Args:
            project_id: 项目ID
            chapter_id: 章节ID
            content: 新内容
            user_id: 用户ID
            version_note: 版本说明
            
        Returns:
            ChapterContent: 更新后的章节内容
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        # 获取现有内容
        try:
            old_content = await self.storage_service.load_chapter_content(project, chapter_id)
            old_content_text = old_content.content
        except FileNotFoundError:
            raise ValueError(f"章节 {chapter_id} 不存在")
        
        # 备份当前版本
        await self._backup_current_version(project, old_content, user_id)
        
        # 创建新的章节内容
        updated_content = ChapterContent(
            chapter_id=chapter_id,
            chapter_title=old_content.chapter_title,
            content=content,
            word_count=len(content),
            generated_at=datetime.utcnow()
        )
        
        # 保存更新后的内容
        await self.storage_service.save_chapter_content(project, updated_content)
        
        # 创建新版本记录
        await self._create_content_version(
            project, updated_content, user_id, version_note, is_current=True
        )
        
        # 记录编辑历史
        await self._record_edit_history(
            project, chapter_id, "update", old_content_text, content, user_id, version_note
        )
        
        logger.info(f"更新章节内容: {project_id}/{chapter_id}")
        return updated_content
    
    async def delete_chapter_content(
        self, 
        project_id: str, 
        chapter_id: str,
        user_id: str,
        delete_note: Optional[str] = None
    ) -> bool:
        """
        删除章节内容
        
        Args:
            project_id: 项目ID
            chapter_id: 章节ID
            user_id: 用户ID
            delete_note: 删除说明
            
        Returns:
            bool: 删除是否成功
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        # 获取要删除的内容
        try:
            content_to_delete = await self.storage_service.load_chapter_content(project, chapter_id)
        except FileNotFoundError:
            logger.warning(f"章节内容不存在: {project_id}/{chapter_id}")
            return True  # 内容不存在视为删除成功
        
        # 备份内容到删除记录
        await self._backup_deleted_content(project, content_to_delete, user_id, delete_note)
        
        # 删除当前内容文件
        content_path = f"{project.get_storage_path()}/content/chapter_{chapter_id}.json"
        try:
            self.minio_client.remove_object(self.bucket_name, content_path)
        except Exception as e:
            logger.error(f"删除内容文件失败: {str(e)}")
            return False
        
        # 记录编辑历史
        await self._record_edit_history(
            project, chapter_id, "delete", content_to_delete.content, None, user_id, delete_note
        )
        
        logger.info(f"删除章节内容: {project_id}/{chapter_id}")
        return True
    
    async def get_chapter_content(
        self, 
        project_id: str, 
        chapter_id: str
    ) -> Optional[ChapterContent]:
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
    
    async def list_chapter_contents(
        self, 
        project_id: str
    ) -> List[ChapterContent]:
        """
        列出项目的所有章节内容
        
        Args:
            project_id: 项目ID
            
        Returns:
            List[ChapterContent]: 章节内容列表
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            return []
        
        return await self.storage_service.load_all_chapters(project)
    
    # ==================== 版本控制功能 ====================
    
    async def _create_content_version(
        self, 
        project: TenderProject, 
        content: ChapterContent, 
        user_id: str,
        version_note: Optional[str] = None,
        is_current: bool = False
    ) -> str:
        """创建内容版本记录"""
        version_id = f"v_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{content.chapter_id}"
        
        version_data = {
            "version_id": version_id,
            "chapter_id": content.chapter_id,
            "chapter_title": content.chapter_title,
            "content": content.content,
            "word_count": content.word_count,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": user_id,
            "version_note": version_note,
            "is_current": is_current
        }
        
        # 保存版本文件
        version_path = f"{project.get_storage_path()}/versions/{content.chapter_id}/{version_id}.json"
        await self.storage_service._save_json(version_path, version_data)
        
        # 如果是当前版本，更新版本索引
        if is_current:
            await self._update_current_version_index(project, content.chapter_id, version_id)
        
        return version_id
    
    async def _backup_current_version(
        self, 
        project: TenderProject, 
        content: ChapterContent, 
        user_id: str
    ):
        """备份当前版本"""
        # 将当前版本标记为非当前版本
        await self._create_content_version(
            project, content, user_id, "自动备份", is_current=False
        )
    
    async def _backup_deleted_content(
        self, 
        project: TenderProject, 
        content: ChapterContent, 
        user_id: str,
        delete_note: Optional[str] = None
    ):
        """备份被删除的内容"""
        deleted_data = {
            "chapter_id": content.chapter_id,
            "chapter_title": content.chapter_title,
            "content": content.content,
            "word_count": content.word_count,
            "original_created_at": content.generated_at.isoformat(),
            "deleted_at": datetime.utcnow().isoformat(),
            "deleted_by": user_id,
            "delete_note": delete_note
        }
        
        # 保存到删除记录
        deleted_path = f"{project.get_storage_path()}/deleted/{content.chapter_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        await self.storage_service._save_json(deleted_path, deleted_data)
    
    async def get_content_versions(
        self, 
        project_id: str, 
        chapter_id: str
    ) -> List[ContentVersion]:
        """
        获取章节内容的所有版本
        
        Args:
            project_id: 项目ID
            chapter_id: 章节ID
            
        Returns:
            List[ContentVersion]: 版本列表
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            return []
        
        versions = []
        versions_path = f"{project.get_storage_path()}/versions/{chapter_id}/"
        
        try:
            objects = self.minio_client.list_objects(
                self.bucket_name,
                prefix=versions_path,
                recursive=True
            )
            
            for obj in objects:
                if obj.object_name.endswith('.json'):
                    try:
                        version_data = await self.storage_service._load_json(obj.object_name)
                        version = ContentVersion(
                            version_id=version_data["version_id"],
                            chapter_id=version_data["chapter_id"],
                            chapter_title=version_data["chapter_title"],
                            content=version_data["content"],
                            word_count=version_data["word_count"],
                            created_at=datetime.fromisoformat(version_data["created_at"]),
                            created_by=version_data["created_by"],
                            version_note=version_data.get("version_note"),
                            is_current=version_data.get("is_current", False)
                        )
                        versions.append(version)
                    except Exception as e:
                        logger.warning(f"加载版本数据失败 {obj.object_name}: {str(e)}")
                        continue
            
            # 按创建时间倒序排列
            versions.sort(key=lambda x: x.created_at, reverse=True)
            return versions
            
        except Exception as e:
            logger.error(f"获取内容版本失败: {str(e)}")
            return []
    
    async def restore_content_version(
        self, 
        project_id: str, 
        chapter_id: str, 
        version_id: str,
        user_id: str,
        restore_note: Optional[str] = None
    ) -> ChapterContent:
        """
        恢复到指定版本
        
        Args:
            project_id: 项目ID
            chapter_id: 章节ID
            version_id: 版本ID
            user_id: 用户ID
            restore_note: 恢复说明
            
        Returns:
            ChapterContent: 恢复后的内容
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        # 加载指定版本
        version_path = f"{project.get_storage_path()}/versions/{chapter_id}/{version_id}.json"
        try:
            version_data = await self.storage_service._load_json(version_path)
        except FileNotFoundError:
            raise ValueError(f"版本 {version_id} 不存在")
        
        # 备份当前版本（如果存在）
        try:
            current_content = await self.storage_service.load_chapter_content(project, chapter_id)
            await self._backup_current_version(project, current_content, user_id)
            old_content = current_content.content
        except FileNotFoundError:
            old_content = None
        
        # 恢复内容
        restored_content = ChapterContent(
            chapter_id=version_data["chapter_id"],
            chapter_title=version_data["chapter_title"],
            content=version_data["content"],
            word_count=version_data["word_count"],
            generated_at=datetime.utcnow()
        )
        
        # 保存恢复的内容
        await self.storage_service.save_chapter_content(project, restored_content)
        
        # 创建新版本记录
        await self._create_content_version(
            project, restored_content, user_id, f"恢复到版本 {version_id}: {restore_note}", is_current=True
        )
        
        # 记录编辑历史
        await self._record_edit_history(
            project, chapter_id, "restore", old_content, restored_content.content, 
            user_id, f"恢复到版本 {version_id}: {restore_note}"
        )
        
        logger.info(f"恢复内容版本: {project_id}/{chapter_id} -> {version_id}")
        return restored_content
    
    async def _update_current_version_index(
        self, 
        project: TenderProject, 
        chapter_id: str, 
        version_id: str
    ):
        """更新当前版本索引"""
        index_data = {
            "chapter_id": chapter_id,
            "current_version_id": version_id,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        index_path = f"{project.get_storage_path()}/versions/{chapter_id}/current.json"
        await self.storage_service._save_json(index_path, index_data)
    
    # ==================== 编辑历史功能 ====================
    
    async def _record_edit_history(
        self, 
        project: TenderProject, 
        chapter_id: str, 
        action: str,
        old_content: Optional[str], 
        new_content: Optional[str], 
        user_id: str,
        edit_note: Optional[str] = None
    ):
        """记录编辑历史"""
        edit_id = f"edit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{chapter_id}"
        
        # 计算字数变化
        old_word_count = len(old_content) if old_content else 0
        new_word_count = len(new_content) if new_content else 0
        word_count_change = new_word_count - old_word_count
        
        history_data = {
            "edit_id": edit_id,
            "chapter_id": chapter_id,
            "action": action,
            "old_content": old_content,
            "new_content": new_content,
            "word_count_change": word_count_change,
            "edited_at": datetime.utcnow().isoformat(),
            "edited_by": user_id,
            "edit_note": edit_note
        }
        
        # 保存编辑历史
        history_path = f"{project.get_storage_path()}/history/{edit_id}.json"
        await self.storage_service._save_json(history_path, history_data)
    
    async def get_edit_history(
        self, 
        project_id: str, 
        chapter_id: Optional[str] = None,
        limit: int = 50
    ) -> List[ContentEditHistory]:
        """
        获取编辑历史
        
        Args:
            project_id: 项目ID
            chapter_id: 章节ID（可选，不指定则获取所有章节的历史）
            limit: 返回记录数限制
            
        Returns:
            List[ContentEditHistory]: 编辑历史列表
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            return []
        
        history_list = []
        history_path = f"{project.get_storage_path()}/history/"
        
        try:
            objects = self.minio_client.list_objects(
                self.bucket_name,
                prefix=history_path,
                recursive=True
            )
            
            for obj in objects:
                if obj.object_name.endswith('.json'):
                    try:
                        history_data = await self.storage_service._load_json(obj.object_name)
                        
                        # 如果指定了章节ID，则过滤
                        if chapter_id and history_data["chapter_id"] != chapter_id:
                            continue
                        
                        history = ContentEditHistory(
                            edit_id=history_data["edit_id"],
                            chapter_id=history_data["chapter_id"],
                            action=history_data["action"],
                            old_content=history_data.get("old_content"),
                            new_content=history_data.get("new_content"),
                            word_count_change=history_data["word_count_change"],
                            edited_at=datetime.fromisoformat(history_data["edited_at"]),
                            edited_by=history_data["edited_by"],
                            edit_note=history_data.get("edit_note")
                        )
                        history_list.append(history)
                    except Exception as e:
                        logger.warning(f"加载编辑历史失败 {obj.object_name}: {str(e)}")
                        continue
            
            # 按编辑时间倒序排列
            history_list.sort(key=lambda x: x.edited_at, reverse=True)
            
            # 限制返回数量
            return history_list[:limit]
            
        except Exception as e:
            logger.error(f"获取编辑历史失败: {str(e)}")
            return []
    
    # ==================== 内容搜索功能 ====================
    
    async def search_content(
        self, 
        project_id: str, 
        query: str,
        search_type: str = "text",  # text, regex
        case_sensitive: bool = False,
        limit: int = 20
    ) -> List[ContentSearchResult]:
        """
        搜索内容
        
        Args:
            project_id: 项目ID
            query: 搜索查询
            search_type: 搜索类型 (text, regex)
            case_sensitive: 是否区分大小写
            limit: 返回结果数限制
            
        Returns:
            List[ContentSearchResult]: 搜索结果列表
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            return []
        
        # 获取所有章节内容
        all_contents = await self.storage_service.load_all_chapters(project)
        
        search_results = []
        
        for content in all_contents:
            try:
                matches = self._search_in_content(
                    content.content, query, search_type, case_sensitive
                )
                
                if matches:
                    # 生成内容摘要
                    snippet = self._generate_content_snippet(
                        content.content, query, case_sensitive
                    )
                    
                    # 计算相关性分数
                    relevance_score = self._calculate_relevance_score(
                        content.content, query, len(matches)
                    )
                    
                    result = ContentSearchResult(
                        chapter_id=content.chapter_id,
                        chapter_title=content.chapter_title,
                        content_snippet=snippet,
                        match_count=len(matches),
                        relevance_score=relevance_score
                    )
                    search_results.append(result)
                    
            except Exception as e:
                logger.warning(f"搜索章节内容失败 {content.chapter_id}: {str(e)}")
                continue
        
        # 按相关性分数排序
        search_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return search_results[:limit]
    
    def _search_in_content(
        self, 
        content: str, 
        query: str, 
        search_type: str, 
        case_sensitive: bool
    ) -> List[Tuple[int, str]]:
        """在内容中搜索匹配项"""
        matches = []
        
        if search_type == "regex":
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.compile(query, flags)
                for match in pattern.finditer(content):
                    matches.append((match.start(), match.group()))
            except re.error as e:
                logger.warning(f"正则表达式错误: {str(e)}")
                return []
        else:
            # 文本搜索
            search_content = content if case_sensitive else content.lower()
            search_query = query if case_sensitive else query.lower()
            
            start = 0
            while True:
                pos = search_content.find(search_query, start)
                if pos == -1:
                    break
                matches.append((pos, content[pos:pos+len(query)]))
                start = pos + 1
        
        return matches
    
    def _generate_content_snippet(
        self, 
        content: str, 
        query: str, 
        case_sensitive: bool,
        snippet_length: int = 200
    ) -> str:
        """生成内容摘要"""
        search_content = content if case_sensitive else content.lower()
        search_query = query if case_sensitive else query.lower()
        
        pos = search_content.find(search_query)
        if pos == -1:
            return content[:snippet_length] + "..." if len(content) > snippet_length else content
        
        # 计算摘要范围
        start = max(0, pos - snippet_length // 2)
        end = min(len(content), pos + len(query) + snippet_length // 2)
        
        snippet = content[start:end]
        
        # 添加省略号
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def _calculate_relevance_score(
        self, 
        content: str, 
        query: str, 
        match_count: int
    ) -> float:
        """计算相关性分数"""
        # 基础分数：匹配次数
        base_score = match_count
        
        # 长度因子：较短的内容中的匹配更相关
        length_factor = 1000 / (len(content) + 1000)
        
        # 查询长度因子：较长的查询匹配更相关
        query_factor = len(query) / 100
        
        # 计算最终分数
        relevance_score = base_score * (1 + length_factor + query_factor)
        
        return round(relevance_score, 2)
    
    # ==================== 内容统计功能 ====================
    
    async def get_content_statistics(
        self, 
        project_id: str
    ) -> ContentStatistics:
        """
        获取内容统计信息
        
        Args:
            project_id: 项目ID
            
        Returns:
            ContentStatistics: 统计信息
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        # 获取大纲和内容
        try:
            outline = await self.storage_service.load_outline(project)
            total_chapters = outline.chapter_count if outline else 0
        except FileNotFoundError:
            total_chapters = 0
            outline = None
        
        all_contents = await self.storage_service.load_all_chapters(project)
        completed_chapters = len(all_contents)
        
        # 计算字数统计
        total_words = sum(content.word_count for content in all_contents)
        average_words = total_words // completed_chapters if completed_chapters > 0 else 0
        
        # 计算完成率
        completion_rate = (completed_chapters / total_chapters * 100) if total_chapters > 0 else 0
        
        # 获取最后更新时间
        last_updated = max(
            (content.generated_at for content in all_contents), 
            default=datetime.utcnow()
        )
        
        # 生成章节统计
        chapter_stats = []
        if outline:
            for chapter in outline.chapters:
                chapter_content = None
                for content in all_contents:
                    if content.chapter_id == chapter.chapter_id:
                        chapter_content = content
                        break
                
                chapter_stat = {
                    "chapter_id": chapter.chapter_id,
                    "title": chapter.title,
                    "has_content": chapter_content is not None,
                    "word_count": chapter_content.word_count if chapter_content else 0,
                    "generated_at": chapter_content.generated_at.isoformat() if chapter_content else None,
                    "completion_status": "completed" if chapter_content else "pending"
                }
                chapter_stats.append(chapter_stat)
        
        return ContentStatistics(
            project_id=project_id,
            total_chapters=total_chapters,
            completed_chapters=completed_chapters,
            total_words=total_words,
            average_words_per_chapter=average_words,
            completion_rate=completion_rate,
            last_updated=last_updated,
            chapter_stats=chapter_stats
        )
    
    async def get_project_content_summary(
        self, 
        project_id: str
    ) -> Dict[str, Any]:
        """
        获取项目内容摘要
        
        Args:
            project_id: 项目ID
            
        Returns:
            Dict: 内容摘要信息
        """
        try:
            stats = await self.get_content_statistics(project_id)
            
            # 获取最近的编辑历史
            recent_edits = await self.get_edit_history(project_id, limit=5)
            
            return {
                "project_id": project_id,
                "statistics": {
                    "total_chapters": stats.total_chapters,
                    "completed_chapters": stats.completed_chapters,
                    "completion_rate": stats.completion_rate,
                    "total_words": stats.total_words,
                    "average_words_per_chapter": stats.average_words_per_chapter,
                    "last_updated": stats.last_updated.isoformat()
                },
                "recent_activities": [
                    {
                        "action": edit.action,
                        "chapter_id": edit.chapter_id,
                        "edited_at": edit.edited_at.isoformat(),
                        "edited_by": edit.edited_by,
                        "word_count_change": edit.word_count_change
                    }
                    for edit in recent_edits
                ],
                "chapter_overview": [
                    {
                        "chapter_id": chapter["chapter_id"],
                        "title": chapter["title"],
                        "status": chapter["completion_status"],
                        "word_count": chapter["word_count"]
                    }
                    for chapter in stats.chapter_stats
                ]
            }
            
        except Exception as e:
            logger.error(f"获取项目内容摘要失败: {str(e)}")
            return {
                "project_id": project_id,
                "error": str(e)
            }
    
    async def get_content_analytics(
        self, 
        project_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取内容分析数据
        
        Args:
            project_id: 项目ID
            days: 分析天数
            
        Returns:
            Dict: 分析数据
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            return {"error": "项目不存在"}
        
        # 获取指定时间范围内的编辑历史
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        all_history = await self.get_edit_history(project_id, limit=1000)
        
        # 过滤时间范围
        recent_history = [
            edit for edit in all_history 
            if edit.edited_at >= cutoff_date
        ]
        
        # 统计编辑活动
        activity_by_day = {}
        activity_by_user = {}
        activity_by_action = {}
        word_count_changes = []
        
        for edit in recent_history:
            # 按天统计
            day_key = edit.edited_at.strftime('%Y-%m-%d')
            activity_by_day[day_key] = activity_by_day.get(day_key, 0) + 1
            
            # 按用户统计
            activity_by_user[edit.edited_by] = activity_by_user.get(edit.edited_by, 0) + 1
            
            # 按操作类型统计
            activity_by_action[edit.action] = activity_by_action.get(edit.action, 0) + 1
            
            # 字数变化
            if edit.word_count_change != 0:
                word_count_changes.append({
                    "date": edit.edited_at.strftime('%Y-%m-%d'),
                    "change": edit.word_count_change,
                    "chapter_id": edit.chapter_id
                })
        
        # 计算总字数变化
        total_word_change = sum(edit.word_count_change for edit in recent_history)
        
        return {
            "project_id": project_id,
            "analysis_period": f"{days} days",
            "total_edits": len(recent_history),
            "total_word_change": total_word_change,
            "activity_by_day": activity_by_day,
            "activity_by_user": activity_by_user,
            "activity_by_action": activity_by_action,
            "word_count_changes": word_count_changes,
            "most_active_day": max(activity_by_day.items(), key=lambda x: x[1])[0] if activity_by_day else None,
            "most_active_user": max(activity_by_user.items(), key=lambda x: x[1])[0] if activity_by_user else None
        }


# 全局服务实例
def get_content_management_service(db: Session) -> ContentManagementService:
    """获取内容管理服务实例"""
    return ContentManagementService(db)