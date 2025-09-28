import random
import struct
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

class TestCasePriority(Enum):
    HIGH = 3
    MEDIUM = 2
    LOW = 1

class TestCaseGenerator:
    """测试用例生成器"""
    
    def __init__(self, protocol_configs: Dict[str, Any]):
        self.protocol_configs = protocol_configs
        self.logger = logging.getLogger(__name__)
        
        # 种子测试用例库
        self.seed_cases = self._initialize_seed_cases()
        
        # 变异策略权重
        self.mutation_weights = {
            'field_flipping': 0.2,
            'field_deletion': 0.15,
            'field_duplication': 0.1,
            'field_truncation': 0.1,
            'field_padding': 0.15,
            'invalid_flag_injection': 0.1,
            'fields_reordering': 0.1,
            'semantic_mutation': 0.1
        }
    
    def _initialize_seed_cases(self) -> Dict[str, List[bytes]]:
        """初始化种子测试用例"""
        seed_cases = {}
        
        for protocol, config in self.protocol_configs.items():
            seed_cases[protocol] = self._generate_protocol_seeds(protocol, config)
            
        return seed_cases
    
    def _generate_protocol_seeds(self, protocol: str, config: Dict[str, Any]) -> List[bytes]:
        """生成协议特定的种子用例"""
        seeds = []
        
        if protocol == 'modbus_tcp':
            seeds.extend(self._generate_modbus_seeds(config))
        elif protocol == 'ethernet_ip':
            seeds.extend(self._generate_ethernet_ip_seeds(config))
        elif protocol == 'siemens_s7':
            seeds.extend(self._generate_siemens_s7_seeds(config))
        
        return seeds
    
    def _generate_modbus_seeds(self, config: Dict[str, Any]) -> List[bytes]:
        """生成Modbus TCP种子用例"""
        seeds = []
        
        # 常见功能码的请求
        function_codes = [1, 2, 3, 4, 5, 6, 15, 16]  # 读线圈, 读离散输入, 读保持寄存器等
        
        for func_code in function_codes:
            # 基本请求结构
            transaction_id = 1
            protocol_id = 0
            unit_id = 1
            
            if func_code in [1, 2, 3, 4]:  # 读操作
                # 读请求: 起始地址 + 数量
                data = struct.pack('>HH', 0, 10)  # 从地址0读10个
                length = len(data) + 2  # 数据长度 + unit_id和function_code
                
                seed = (struct.pack('>HHH', transaction_id, protocol_id, length) +
                        bytes([unit_id, func_code]) + data)
                seeds.append(seed)
                
            elif func_code in [5, 6]:  # 写单个
                # 写单个请求: 地址 + 值
                data = struct.pack('>HH', 0, 1)  # 地址0写1
                length = len(data) + 2
                
                seed = (struct.pack('>HHH', transaction_id, protocol_id, length) +
                        bytes([unit_id, func_code]) + data)
                seeds.append(seed)
                
            elif func_code in [15, 16]:  # 写多个
                # 写多个请求
                if func_code == 15:  # 写多个线圈
                    data = struct.pack('>HHB', 0, 8, 1) + b'\x55'  # 8个线圈，值0x55
                else:  # 写多个寄存器
                    data = struct.pack('>HHB', 0, 2, 4) + struct.pack('>HH', 1, 2)
                
                length = len(data) + 2
                seed = (struct.pack('>HHH', transaction_id, protocol_id, length) +
                        bytes([unit_id, func_code]) + data)
                seeds.append(seed)
        
        return seeds
    
    def _generate_ethernet_ip_seeds(self, config: Dict[str, Any]) -> List[bytes]:
        """生成EtherNet/IP种子用例"""
        seeds = []
        
        # ListIdentity 请求
        list_identity = struct.pack('>HHII', 0x63, 0, 0, 0) + b'\x00' * 8 + struct.pack('>I', 0)
        seeds.append(list_identity)
        
        # RegisterSession 请求
        register_session = struct.pack('>HHII', 0x65, 4, 0, 0) + b'\x00' * 8 + struct.pack('>HH', 1, 0)
        seeds.append(register_session)
        
        # SendRRData 请求
        send_rr_data = (struct.pack('>HHII', 0x6F, 0, 0, 0) + b'\x00' * 8 +
                       struct.pack('>HH', 2, 0) +  # 2个CPF项
                       struct.pack('>HI', 0, 0) +   # 地址项
                       struct.pack('>HI', 0xB2, 0) + b'\x00' * 8)  # 数据项
        seeds.append(send_rr_data)
        
        return seeds
    
    def _generate_siemens_s7_seeds(self, config: Dict[str, Any]) -> List[bytes]:
        """生成Siemens S7种子用例"""
        seeds = []
        
        # 连接请求
        connect_request = (b'\x11' +  # ROSCTR: Job
                          b'\x00' +  # Reserved
                          struct.pack('>H', 1) +  # PDU Reference
                          struct.pack('>H', 0) +  # Parameter Length
                          struct.pack('>H', 0) +  # Data Length
                          b'\x00' * 8)  # 参数和数据
        seeds.append(connect_request)
        
        # 读请求
        read_request = (b'\x11' +  # ROSCTR: Job
                       b'\x00' +  # Reserved
                       struct.pack('>H', 2) +  # PDU Reference
                       struct.pack('>H', 10) +  # Parameter Length
                       struct.pack('>H', 0) +  # Data Length
                       b'\x00' * 10)  # 参数
        seeds.append(read_request)
        
        # 写请求
        write_request = (b'\x11' +  # ROSCTR: Job
                        b'\x00' +  # Reserved
                        struct.pack('>H', 3) +  # PDU Reference
                        struct.pack('>H', 10) +  # Parameter Length
                        struct.pack('>H', 4) +  # Data Length
                        b'\x00' * 10 +  # 参数
                        b'\x00' * 4)  # 数据
        seeds.append(write_request)
        
        return seeds
    
    def generate_test_cases(self, protocol: str, count: int, 
                           priority: TestCasePriority = TestCasePriority.MEDIUM,
                           mutation_strategy: Optional[str] = None) -> List[Dict[str, Any]]:
        """生成测试用例"""
        test_cases = []
        
        if protocol not in self.seed_cases:
            self.logger.warning(f"协议 {protocol} 没有种子用例")
            return test_cases
        
        seeds = self.seed_cases[protocol]
        
        for i in range(count):
            # 选择种子
            seed = random.choice(seeds)
            
            # 生成变异用例
            if mutation_strategy:
                mutated_case = self._mutate_with_strategy(seed, protocol, mutation_strategy)
            else:
                mutated_case = self._mutate_randomly(seed, protocol)
            
            test_case = {
                'id': f"{protocol}_test_{i}",
                'protocol': protocol,
                'original_seed': seed,
                'mutated_data': mutated_case,
                'priority': priority,
                'mutation_history': self._get_mutation_history(),
                'generation_strategy': mutation_strategy or 'random'
            }
            
            test_cases.append(test_case)
        
        return test_cases
    
    def _mutate_with_strategy(self, seed: bytes, protocol: str, strategy: str) -> bytes:
        """使用特定策略变异种子"""
        if strategy == 'boundary_values':
            return self._mutate_boundary_values(seed, protocol)
        elif strategy == 'format_specific':
            return self._mutate_format_specific(seed, protocol)
        elif strategy == 'protocol_semantic':
            return self._mutate_protocol_semantic(seed, protocol)
        else:
            return self._mutate_randomly(seed, protocol)
    
    def _mutate_randomly(self, seed: bytes, protocol: str) -> bytes:
        """随机变异种子"""
        mutated = bytearray(seed)
        
        # 应用随机变异
        num_mutations = random.randint(1, 5)
        
        for _ in range(num_mutations):
            mutation_type = random.choices(
                list(self.mutation_weights.keys()),
                weights=list(self.mutation_weights.values())
            )[0]
            
            mutated = self._apply_single_mutation(mutated, mutation_type, protocol)
        
        return bytes(mutated)
    
    def _apply_single_mutation(self, data: bytearray, mutation_type: str, protocol: str) -> bytearray:
        """应用单个变异操作"""
        if mutation_type == 'field_flipping' and data:
            # 随机翻转一些字节
            for i in range(min(10, len(data))):
                if random.random() < 0.3:
                    data[i] ^= 0xFF
                    
        elif mutation_type == 'field_deletion' and len(data) > 4:
            # 删除部分数据
            del_start = random.randint(0, len(data) - 1)
            del_end = min(len(data), del_start + random.randint(1, len(data) // 4))
            del data[del_start:del_end]
            
        elif mutation_type == 'field_duplication' and data:
            # 复制部分数据
            dup_start = random.randint(0, len(data) - 1)
            dup_end = min(len(data), dup_start + random.randint(1, len(data) // 4))
            duplicated = data[dup_start:dup_end]
            data.extend(duplicated)
            
        elif mutation_type == 'field_truncation' and len(data) > 4:
            # 截断数据
            new_length = random.randint(1, len(data) - 1)
            del data[new_length:]
            
        elif mutation_type == 'field_padding':
            # 添加填充
            padding_length = random.randint(1, 100)
            padding = bytes([random.randint(0, 255) for _ in range(padding_length)])
            data.extend(padding)
            
        elif mutation_type == 'invalid_flag_injection' and data:
            # 注入无效标志
            for i in range(min(5, len(data))):
                if random.random() < 0.2:
                    data[i] = 0xFF if random.random() < 0.5 else 0x00
                    
        elif mutation_type == 'fields_reordering' and len(data) > 2:
            # 重新排序字节
            idx1, idx2 = random.sample(range(len(data)), 2)
            data[idx1], data[idx2] = data[idx2], data[idx1]
            
        elif mutation_type == 'semantic_mutation' and data:
            # 语义变异 - 插入边界值
            boundary_values = [0, 1, 0x7F, 0x80, 0xFF]
            for i in range(min(3, len(data))):
                if random.random() < 0.1:
                    data[i] = random.choice(boundary_values)
        
        return data
    
    def _mutate_boundary_values(self, seed: bytes, protocol: str) -> bytes:
        """边界值变异"""
        mutated = bytearray(seed)
        
        # 在关键位置插入边界值
        boundary_positions = self._get_boundary_positions(protocol)
        
        for pos in boundary_positions:
            if pos < len(mutated):
                boundary_value = random.choice([0, 1, 0x7F, 0x80, 0xFF])
                mutated[pos] = boundary_value
        
        return bytes(mutated)
    
    def _mutate_format_specific(self, seed: bytes, protocol: str) -> bytes:
        """格式特定变异"""
        # 根据协议格式进行智能变异
        if protocol == 'modbus_tcp' and len(seed) >= 8:
            mutated = bytearray(seed)
            
            # 变异功能码为无效值
            if len(mutated) > 7:
                mutated[7] = random.choice([0, 0x80, 0xFF])
                
            # 变异长度字段
            if len(mutated) > 5:
                mutated[4] = 0xFF  # 设置超大长度
                mutated[5] = 0xFF
                
            return bytes(mutated)
        
        return seed
    
    def _mutate_protocol_semantic(self, seed: bytes, protocol: str) -> bytes:
        """协议语义变异"""
        # 改变协议消息的语义含义
        if protocol == 'modbus_tcp' and len(seed) >= 8:
            mutated = bytearray(seed)
            
            # 将读操作改为写操作或反之
            if len(mutated) > 7:
                func_code = mutated[7]
                if func_code in [1, 2, 3, 4]:  # 读操作
                    mutated[7] = random.choice([5, 6, 15, 16])  # 写操作
                elif func_code in [5, 6, 15, 16]:  # 写操作
                    mutated[7] = random.choice([1, 2, 3, 4])  # 读操作
            
            return bytes(mutated)
        
        return seed
    
    def _get_boundary_positions(self, protocol: str) -> List[int]:
        """获取协议的关键边界位置"""
        # 协议特定的关键字段位置
        boundary_positions = {
            'modbus_tcp': [4, 5, 6, 7],  # 长度, Unit ID, 功能码
            'ethernet_ip': [0, 1, 2, 3, 8, 9, 10, 11],  # 命令, 长度, 状态
            'siemens_s7': [0, 4, 5, 6, 7]  # ROSCTR, 参数长度, 数据长度
        }
        
        return boundary_positions.get(protocol, [0])
    
    def _get_mutation_history(self) -> List[str]:
        """获取变异历史（简化实现）"""
        return ['random_mutation']  # 实际应该记录详细的变异步骤
    
    def add_seed_case(self, protocol: str, test_case: bytes):
        """添加新的种子用例"""
        if protocol not in self.seed_cases:
            self.seed_cases[protocol] = []
        
        self.seed_cases[protocol].append(test_case)
        self.logger.info(f"为协议 {protocol} 添加新的种子用例，长度: {len(test_case)}")
    
    def get_seed_statistics(self) -> Dict[str, Any]:
        """获取种子用例统计"""
        stats = {}
        
        for protocol, seeds in self.seed_cases.items():
            stats[protocol] = {
                'seed_count': len(seeds),
                'avg_length': sum(len(seed) for seed in seeds) / len(seeds) if seeds else 0,
                'min_length': min(len(seed) for seed in seeds) if seeds else 0,
                'max_length': max(len(seed) for seed in seeds) if seeds else 0
            }
        
        return stats