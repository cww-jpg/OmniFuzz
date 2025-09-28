import hashlib
import logging
from typing import Dict, List, Set, Any
from collections import defaultdict

class CoverageTracker:
    """代码覆盖率跟踪器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 覆盖率数据
        self.basic_blocks_covered = set()
        self.functions_covered = set()
        self.execution_paths = set()
        
        # 统计信息
        self.coverage_stats = {
            'total_basic_blocks': 0,
            'total_functions': 0,
            'unique_paths': 0,
            'coverage_over_time': []
        }
        
        # 路径深度跟踪
        self.path_depths = defaultdict(int)
    
    def record_execution(self, basic_blocks: List[str], functions: List[str], 
                        execution_sequence: List[str]) -> Dict[str, Any]:
        """记录执行信息"""
        # 记录基本块
        new_blocks = set(basic_blocks) - self.basic_blocks_covered
        self.basic_blocks_covered.update(basic_blocks)
        
        # 记录函数
        new_functions = set(functions) - self.functions_covered
        self.functions_covered.update(functions)
        
        # 记录执行路径
        path_hash = self._hash_execution_path(execution_sequence)
        is_new_path = path_hash not in self.execution_paths
        if is_new_path:
            self.execution_paths.add(path_hash)
        
        # 计算路径深度
        path_depth = self._calculate_path_depth(execution_sequence)
        
        # 更新统计
        coverage_data = self._update_coverage_stats()
        coverage_data.update({
            'new_blocks': len(new_blocks),
            'new_functions': len(new_functions),
            'new_path': is_new_path,
            'path_depth': path_depth
        })
        
        return coverage_data
    
    def _hash_execution_path(self, execution_sequence: List[str]) -> str:
        """哈希执行路径用于去重"""
        path_string = '->'.join(execution_sequence)
        return hashlib.md5(path_string.encode()).hexdigest()
    
    def _calculate_path_depth(self, execution_sequence: List[str]) -> int:
        """计算路径深度"""
        # 路径深度 = 执行序列中的基本块数量
        depth = len(execution_sequence)
        
        # 记录路径深度分布
        self.path_depths[depth] += 1
        
        return depth
    
    def _update_coverage_stats(self) -> Dict[str, Any]:
        """更新覆盖率统计"""
        basic_block_coverage = len(self.basic_blocks_covered) / max(1, self.coverage_stats['total_basic_blocks'])
        function_coverage = len(self.functions_covered) / max(1, self.coverage_stats['total_functions'])
        path_coverage = len(self.execution_paths)
        
        coverage_data = {
            'basic_block_coverage': basic_block_coverage,
            'function_coverage': function_coverage,
            'path_coverage': path_coverage,
            'total_paths': path_coverage,
            'unique_basic_blocks': len(self.basic_blocks_covered),
            'unique_functions': len(self.functions_covered)
        }
        
        # 记录覆盖率随时间变化
        self.coverage_stats['coverage_over_time'].append(coverage_data)
        
        return coverage_data
    
    def get_coverage_summary(self) -> Dict[str, Any]:
        """获取覆盖率摘要"""
        if self.coverage_stats['total_basic_blocks'] == 0:
            return {'error': '未设置总基本块数量'}
        
        return {
            'basic_block_coverage': {
                'covered': len(self.basic_blocks_covered),
                'total': self.coverage_stats['total_basic_blocks'],
                'percentage': len(self.basic_blocks_covered) / self.coverage_stats['total_basic_blocks'] * 100
            },
            'function_coverage': {
                'covered': len(self.functions_covered),
                'total': self.coverage_stats['total_functions'],
                'percentage': len(self.functions_covered) / max(1, self.coverage_stats['total_functions']) * 100
            },
            'path_coverage': {
                'unique_paths': len(self.execution_paths),
                'path_depth_distribution': dict(self.path_depths)
            },
            'coverage_trend': self._calculate_coverage_trend()
        }
    
    def _calculate_coverage_trend(self) -> str:
        """计算覆盖率趋势"""
        if len(self.coverage_stats['coverage_over_time']) < 2:
            return "unknown"
        
        recent_coverage = self.coverage_stats['coverage_over_time'][-10:]
        if len(recent_coverage) < 2:
            return "stable"
        
        # 分析基本块覆盖率趋势
        coverage_values = [data['basic_block_coverage'] for data in recent_coverage]
        first_half = coverage_values[:len(coverage_values)//2]
        second_half = coverage_values[len(coverage_values)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        if avg_second > avg_first + 0.01:
            return "improving"
        elif avg_second < avg_first - 0.01:
            return "declining"
        else:
            return "stable"
    
    def set_total_counts(self, total_basic_blocks: int, total_functions: int):
        """设置总基本块和函数数量"""
        self.coverage_stats['total_basic_blocks'] = total_basic_blocks
        self.coverage_stats['total_functions'] = total_functions
    
    def reset_coverage(self):
        """重置覆盖率数据"""
        self.basic_blocks_covered.clear()
        self.functions_covered.clear()
        self.execution_paths.clear()
        self.coverage_stats['coverage_over_time'].clear()
        self.path_depths.clear()

class LLVMCoverageTracker(CoverageTracker):
    """基于LLVM的覆盖率跟踪器"""
    
    def __init__(self, llvm_tool_path: str = ""):
        super().__init__()
        self.llvm_tool_path = llvm_tool_path
        self.instrumented_binaries = set()
    
    def instrument_binary(self, binary_path: str, output_path: str) -> bool:
        """使用LLVM插桩二进制文件"""
        try:
            # 这里应该调用LLVM工具进行实际插桩
            # 简化实现
            self.logger.info(f"插桩二进制文件: {binary_path} -> {output_path}")
            self.instrumented_binaries.add(output_path)
            return True
        except Exception as e:
            self.logger.error(f"二进制插桩失败: {e}")
            return False
    
    def parse_coverage_data(self, coverage_file: str) -> Dict[str, Any]:
        """解析LLVM覆盖率数据"""
        try:
            # 这里应该解析实际的LLVM覆盖率文件
            # 简化实现 - 返回模拟数据
            return {
                'basic_blocks': ['bb1', 'bb2', 'bb3'],
                'functions': ['func1', 'func2'],
                'execution_count': 100,
                'file_path': coverage_file
            }
        except Exception as e:
            self.logger.error(f"解析覆盖率数据失败: {e}")
            return {}