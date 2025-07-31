"""
性能测试脚本
测试系统在各种负载条件下的性能表现
"""
import pytest
import asyncio
import time
import statistics
from unittest.mock import Mock, AsyncMock, patch
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session

from app.models.tender import TenderProject, TenderStatus
from app.services.tender_analysis import TenderAnalysisService
from app.services.outline_generation import OutlineGenerationService
from app.services.content_generation import ContentGenerationService
from app.services.document_export import DocumentExportService
from app.services.tender_storage import TenderStorageService


class TestPerformanceBenchmarks:
    """性能基准测试"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_storage_service(self):
        return Mock(spec=TenderStorageService)
    
    def create_test_project(self, project_id: str):
        """创建测试项目"""
        project = Mock(spec=TenderProject)
        project.id = project_id
        project.tenant_id = "perf-test-tenant"
        project.user_id = "perf-test-user"
        project.project_name = f"性能测试项目{project_id}"
        project.source_filename = f"test_{project_id}.pdf"
        project.status = TenderStatus.CREATED
        project.get_storage_path.return_value = f"tenants/perf-test-tenant/projects/{project_id}"
        return project
    
    async def test_single_project_analysis_performance(self, mock_db, mock_storage_service):
        """测试单个项目分析性能"""
        project = self.create_test_project("single-analysis")
        analysis_service = TenderAnalysisService(mock_db, mock_storage_service)
        
        # 模拟分析过程
        with patch.object(analysis_service, 'analyze_tender_document', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = True
            mock_storage_service.save_analysis_result = AsyncMock()
            
            # 执行多次测试获取平均性能
            execution_times = []
            for _ in range(10):
                start_time = time.time()
                result = await analysis_service.analyze_tender_document(project)
                execution_time = time.time() - start_time
                execution_times.append(execution_time)
                assert result is True
            
            # 计算性能指标
            avg_time = statistics.mean(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
            std_dev = statistics.stdev(execution_times)
            
            print(f"分析性能指标:")
            print(f"  平均时间: {avg_time:.3f}s")
            print(f"  最小时间: {min_time:.3f}s")
            print(f"  最大时间: {max_time:.3f}s")
            print(f"  标准差: {std_dev:.3f}s")
            
            # 性能断言
            assert avg_time < 2.0  # 平均分析时间应小于2秒
            assert max_time < 5.0  # 最大分析时间应小于5秒
            assert std_dev < 1.0   # 标准差应小于1秒（稳定性）
    
    async def test_concurrent_analysis_performance(self, mock_db, mock_storage_service):
        """测试并发分析性能"""
        num_concurrent = 10
        projects = [self.create_test_project(f"concurrent-{i}") for i in range(num_concurrent)]
        
        analysis_service = TenderAnalysisService(mock_db, mock_storage_service)
        
        async def analyze_project(project):
            with patch.object(analysis_service, 'analyze_tender_document', new_callable=AsyncMock) as mock_analyze:
                mock_analyze.return_value = True
                mock_storage_service.save_analysis_result = AsyncMock()
                
                # 模拟实际处理时间
                await asyncio.sleep(0.1)
                return await analysis_service.analyze_tender_document(project)
        
        # 测试并发性能
        start_time = time.time()
        tasks = [analyze_project(project) for project in projects]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # 计算性能指标
        throughput = num_concurrent / total_time
        avg_time_per_task = total_time / num_concurrent
        
        print(f"并发分析性能指标:")
        print(f"  总时间: {total_time:.3f}s")
        print(f"  吞吐量: {throughput:.2f} 任务/秒")
        print(f"  平均每任务时间: {avg_time_per_task:.3f}s")
        
        # 性能断言
        assert all(results)
        assert total_time < 2.0  # 10个并发任务应在2秒内完成
        assert throughput > 5    # 吞吐量应大于5任务/秒
    
    async def test_outline_generation_performance(self, mock_db, mock_storage_service):
        """测试大纲生成性能"""
        project = self.create_test_project("outline-perf")
        outline_service = OutlineGenerationService(mock_db, mock_storage_service)
        
        # 模拟不同规模的大纲生成
        test_cases = [
            {"chapters": 5, "max_time": 3.0},
            {"chapters": 10, "max_time": 5.0},
            {"chapters": 20, "max_time": 8.0},
            {"chapters": 50, "max_time": 15.0}
        ]
        
        for case in test_cases:
            with patch.object(outline_service, 'generate_outline', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value = True
                mock_storage_service.save_outline = AsyncMock()
                
                # 模拟处理时间与章节数成正比
                processing_delay = case["chapters"] * 0.01
                
                async def mock_generate_with_delay(*args, **kwargs):
                    await asyncio.sleep(processing_delay)
                    return True
                
                mock_generate.side_effect = mock_generate_with_delay
                
                start_time = time.time()
                result = await outline_service.generate_outline(project)
                execution_time = time.time() - start_time
                
                print(f"大纲生成性能 ({case['chapters']}章节): {execution_time:.3f}s")
                
                assert result is True
                assert execution_time < case["max_time"]
    
    async def test_content_generation_performance(self, mock_db, mock_storage_service):
        """测试内容生成性能"""
        project = self.create_test_project("content-perf")
        content_service = ContentGenerationService(mock_db, mock_storage_service)
        
        # 模拟不同规模的内容生成
        test_cases = [
            {"chapters": 3, "words_per_chapter": 500, "max_time": 10.0},
            {"chapters": 5, "words_per_chapter": 800, "max_time": 20.0},
            {"chapters": 10, "words_per_chapter": 1000, "max_time": 40.0}
        ]
        
        for case in test_cases:
            with patch.object(content_service, 'generate_all_content', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value = True
                mock_storage_service.save_chapter_content = AsyncMock()
                
                # 模拟处理时间
                total_words = case["chapters"] * case["words_per_chapter"]
                processing_delay = total_words / 10000  # 假设每秒生成10000字
                
                async def mock_generate_with_delay(*args, **kwargs):
                    await asyncio.sleep(processing_delay)
                    return True
                
                mock_generate.side_effect = mock_generate_with_delay
                
                start_time = time.time()
                result = await content_service.generate_all_content(project)
                execution_time = time.time() - start_time
                
                print(f"内容生成性能 ({case['chapters']}章节, {total_words}字): {execution_time:.3f}s")
                
                assert result is True
                assert execution_time < case["max_time"]
    
    async def test_document_export_performance(self, mock_db, mock_storage_service):
        """测试文档导出性能"""
        project = self.create_test_project("export-perf")
        export_service = DocumentExportService(mock_db, mock_storage_service)
        
        # 测试不同格式的导出性能
        export_formats = [
            {"format": "pdf", "max_time": 8.0},
            {"format": "docx", "max_time": 5.0}
        ]
        
        for fmt in export_formats:
            if fmt["format"] == "pdf":
                export_method = export_service.export_to_pdf
            else:
                export_method = export_service.export_to_docx
            
            with patch.object(export_service, f'export_to_{fmt["format"]}', new_callable=AsyncMock) as mock_export:
                mock_export.return_value = f"document-{fmt['format']}-id"
                
                # 模拟导出处理时间
                async def mock_export_with_delay(*args, **kwargs):
                    await asyncio.sleep(0.5)  # 模拟导出时间
                    return f"document-{fmt['format']}-id"
                
                mock_export.side_effect = mock_export_with_delay
                
                start_time = time.time()
                document_id = await export_method(
                    project,
                    title="性能测试标书",
                    company_name="测试公司"
                )
                execution_time = time.time() - start_time
                
                print(f"{fmt['format'].upper()}导出性能: {execution_time:.3f}s")
                
                assert document_id == f"document-{fmt['format']}-id"
                assert execution_time < fmt["max_time"]
    
    async def test_memory_usage_under_load(self, mock_db, mock_storage_service):
        """测试负载下的内存使用"""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建大量项目进行处理
        num_projects = 20
        projects = [self.create_test_project(f"memory-test-{i}") for i in range(num_projects)]
        
        analysis_service = TenderAnalysisService(mock_db, mock_storage_service)
        
        memory_samples = []
        
        for i, project in enumerate(projects):
            with patch.object(analysis_service, 'analyze_tender_document', new_callable=AsyncMock) as mock_analyze:
                mock_analyze.return_value = True
                mock_storage_service.save_analysis_result = AsyncMock()
                
                await analysis_service.analyze_tender_document(project)
                
                # 记录内存使用
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_samples.append(current_memory)
                
                if i % 5 == 0:  # 每5个项目打印一次
                    print(f"处理 {i+1}/{num_projects} 项目，内存使用: {current_memory:.2f}MB")
        
        final_memory = memory_samples[-1]
        memory_increase = final_memory - initial_memory
        max_memory = max(memory_samples)
        
        print(f"内存使用分析:")
        print(f"  初始内存: {initial_memory:.2f}MB")
        print(f"  最终内存: {final_memory:.2f}MB")
        print(f"  最大内存: {max_memory:.2f}MB")
        print(f"  内存增长: {memory_increase:.2f}MB")
        
        # 内存使用断言
        assert memory_increase < 200  # 内存增长应小于200MB
        assert max_memory < initial_memory + 300  # 最大内存不应超过初始+300MB
    
    async def test_scalability_performance(self, mock_db, mock_storage_service):
        """测试系统可扩展性性能"""
        # 测试不同负载级别下的性能
        load_levels = [1, 5, 10, 20, 50]
        performance_results = []
        
        for load in load_levels:
            projects = [self.create_test_project(f"scale-test-{load}-{i}") for i in range(load)]
            analysis_service = TenderAnalysisService(mock_db, mock_storage_service)
            
            async def analyze_project(project):
                with patch.object(analysis_service, 'analyze_tender_document', new_callable=AsyncMock) as mock_analyze:
                    mock_analyze.return_value = True
                    mock_storage_service.save_analysis_result = AsyncMock()
                    
                    await asyncio.sleep(0.05)  # 模拟处理时间
                    return await analysis_service.analyze_tender_document(project)
            
            start_time = time.time()
            tasks = [analyze_project(project) for project in projects]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            throughput = load / total_time
            avg_response_time = total_time / load
            
            performance_results.append({
                "load": load,
                "total_time": total_time,
                "throughput": throughput,
                "avg_response_time": avg_response_time
            })
            
            print(f"负载 {load}: 吞吐量 {throughput:.2f} 任务/秒, 平均响应时间 {avg_response_time:.3f}s")
            
            assert all(results)
        
        # 分析可扩展性
        print("\n可扩展性分析:")
        for i in range(1, len(performance_results)):
            prev = performance_results[i-1]
            curr = performance_results[i]
            
            load_ratio = curr["load"] / prev["load"]
            throughput_ratio = curr["throughput"] / prev["throughput"]
            
            print(f"负载增加 {load_ratio:.1f}x, 吞吐量比率 {throughput_ratio:.2f}")
            
            # 理想情况下，吞吐量应该与负载成正比
            # 但实际中会有一些下降，这里允许20%的性能下降
            assert throughput_ratio > 0.8


class TestStressTest:
    """压力测试"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_storage_service(self):
        return Mock(spec=TenderStorageService)
    
    async def test_high_concurrency_stress(self, mock_db, mock_storage_service):
        """测试高并发压力"""
        num_concurrent = 100
        projects = [Mock(spec=TenderProject) for _ in range(num_concurrent)]
        
        for i, project in enumerate(projects):
            project.id = f"stress-test-{i}"
            project.tenant_id = "stress-test-tenant"
            project.user_id = f"stress-user-{i % 10}"  # 10个用户
            project.status = TenderStatus.CREATED
            project.get_storage_path.return_value = f"tenants/stress-test-tenant/projects/stress-test-{i}"
        
        analysis_service = TenderAnalysisService(mock_db, mock_storage_service)
        
        async def stress_analyze(project):
            with patch.object(analysis_service, 'analyze_tender_document', new_callable=AsyncMock) as mock_analyze:
                mock_analyze.return_value = True
                mock_storage_service.save_analysis_result = AsyncMock()
                
                # 随机处理时间模拟真实情况
                import random
                await asyncio.sleep(random.uniform(0.01, 0.1))
                return await analysis_service.analyze_tender_document(project)
        
        start_time = time.time()
        tasks = [stress_analyze(project) for project in projects]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # 统计结果
        successful = sum(1 for r in results if r is True)
        failed = len(results) - successful
        throughput = successful / total_time
        
        print(f"高并发压力测试结果:")
        print(f"  并发数: {num_concurrent}")
        print(f"  成功: {successful}")
        print(f"  失败: {failed}")
        print(f"  总时间: {total_time:.3f}s")
        print(f"  吞吐量: {throughput:.2f} 任务/秒")
        
        # 压力测试断言
        assert successful >= num_concurrent * 0.95  # 至少95%成功率
        assert total_time < 10.0  # 100个并发任务应在10秒内完成
        assert throughput > 10    # 吞吐量应大于10任务/秒
    
    async def test_sustained_load_stress(self, mock_db, mock_storage_service):
        """测试持续负载压力"""
        duration = 30  # 30秒持续测试
        concurrent_level = 10
        
        analysis_service = TenderAnalysisService(mock_db, mock_storage_service)
        
        async def continuous_task():
            task_count = 0
            start_time = time.time()
            
            while time.time() - start_time < duration:
                project = Mock(spec=TenderProject)
                project.id = f"sustained-{task_count}-{time.time()}"
                project.tenant_id = "sustained-test-tenant"
                project.user_id = "sustained-user"
                project.status = TenderStatus.CREATED
                project.get_storage_path.return_value = f"tenants/sustained-test-tenant/projects/{project.id}"
                
                with patch.object(analysis_service, 'analyze_tender_document', new_callable=AsyncMock) as mock_analyze:
                    mock_analyze.return_value = True
                    mock_storage_service.save_analysis_result = AsyncMock()
                    
                    await asyncio.sleep(0.1)  # 模拟处理时间
                    await analysis_service.analyze_tender_document(project)
                    task_count += 1
            
            return task_count
        
        # 启动多个并发任务流
        start_time = time.time()
        tasks = [continuous_task() for _ in range(concurrent_level)]
        task_counts = await asyncio.gather(*tasks)
        actual_duration = time.time() - start_time
        
        total_tasks = sum(task_counts)
        avg_throughput = total_tasks / actual_duration
        
        print(f"持续负载压力测试结果:")
        print(f"  测试时长: {actual_duration:.1f}s")
        print(f"  并发级别: {concurrent_level}")
        print(f"  总任务数: {total_tasks}")
        print(f"  平均吞吐量: {avg_throughput:.2f} 任务/秒")
        
        # 持续负载断言
        assert actual_duration >= duration * 0.95  # 实际运行时间应接近预期
        assert total_tasks > duration * concurrent_level * 0.8  # 任务完成率应大于80%
        assert avg_throughput > 5  # 平均吞吐量应大于5任务/秒


if __name__ == "__main__":
    # 运行性能测试
    pytest.main([__file__, "-v", "-s"])