import random
import struct
from typing import List, Dict, Any, Union
from enum import Enum

class MutationAction(Enum):
    """变异操作枚举"""
    FIELD_FLIPPING = "field_flipping"
    FIELD_DELETION = "field_deletion"
    FIELD_DUPLICATION = "field_duplication"
    FIELD_TRUNCATION = "field_truncation"
    FIELD_PADDING = "field_padding"
    INVALID_FLAG_INJECTION = "invalid_flag_injection"
    FIELDS_REORDERING = "fields_reordering"
    SEMANTIC_MUTATION = "semantic_mutation"

class MutationEngine:
    """协议字段变异引擎"""
    
    def __init__(self, protocol_config: Dict[str, Any]):
        self.protocol_config = protocol_config
        self.mutation_strategies = {
            MutationAction.FIELD_FLIPPING: self._flip_field,
            MutationAction.FIELD_DELETION: self._delete_field,
            MutationAction.FIELD_DUPLICATION: self._duplicate_field,
            MutationAction.FIELD_TRUNCATION: self._truncate_message,
            MutationAction.FIELD_PADDING: self._pad_field,
            MutationAction.INVALID_FLAG_INJECTION: self._inject_invalid_flag,
            MutationAction.FIELDS_REORDERING: self._reorder_fields,
            MutationAction.SEMANTIC_MUTATION: self._mutate_semantics
        }
    
    def mutate_protocol_message(self, original_message: bytes, 
                               mutation_actions: Dict[str, int]) -> bytes:
        """根据智能体选择的动作变异协议消息"""
        mutated_message = bytearray(original_message)
        
        for field_name, action_idx in mutation_actions.items():
            if field_name in self.protocol_config['fields']:
                action = list(MutationAction)[action_idx % len(MutationAction)]
                strategy = self.mutation_strategies.get(action)
                
                if strategy:
                    mutated_message = strategy(mutated_message, field_name)
        
        return bytes(mutated_message)
    
    def _flip_field(self, message: bytearray, field_name: str) -> bytearray:
        """翻转字段值"""
        field_info = self.protocol_config['fields'][field_name]
        start, end = field_info['position']
        
        # 随机翻转字段中的一些位
        for i in range(start, min(end, len(message))):
            if random.random() < 0.3:  # 30%的概率翻转每个字节
                message[i] ^= 0xFF
                
        return message
    
    def _delete_field(self, message: bytearray, field_name: str) -> bytearray:
        """删除字段"""
        field_info = self.protocol_config['fields'][field_name]
        start, end = field_info['position']
        
        # 用零填充删除的字段
        for i in range(start, min(end, len(message))):
            message[i] = 0x00
            
        return message
    
    def _duplicate_field(self, message: bytearray, field_name: str) -> bytearray:
        """复制字段"""
        field_info = self.protocol_config['fields'][field_name]
        start, end = field_info['position']
        field_length = end - start
        
        # 在消息末尾复制字段
        field_data = message[start:end]
        message.extend(field_data)
        
        return message
    
    def _truncate_message(self, message: bytearray, field_name: str) -> bytearray:
        """截断协议消息"""
        # 随机截断到原始长度的50%-90%
        new_length = random.randint(len(message) // 2, int(len(message) * 0.9))
        return message[:new_length]
    
    def _pad_field(self, message: bytearray, field_name: str) -> bytearray:
        """填充额外字节"""
        # 添加随机填充字节
        padding_length = random.randint(1, 100)
        padding = bytes([random.randint(0, 255) for _ in range(padding_length)])
        message.extend(padding)
        
        return message
    
    def _inject_invalid_flag(self, message: bytearray, field_name: str) -> bytearray:
        """注入无效标志"""
        field_info = self.protocol_config['fields'][field_name]
        
        if field_info.get('is_flag', False):
            start, end = field_info['position']
            # 设置为无效的标志值
            invalid_value = random.choice([0xFF, 0x00, 0x7F])
            for i in range(start, min(end, len(message))):
                message[i] = invalid_value
                
        return message
    
    def _reorder_fields(self, message: bytearray, field_name: str) -> bytearray:
        """重新排列字段顺序"""
        # 这是一个复杂的操作，需要解析和重建消息
        # 这里简化为随机交换一些字节位置
        if len(message) >= 2:
            idx1, idx2 = random.sample(range(len(message)), 2)
            message[idx1], message[idx2] = message[idx2], message[idx1]
            
        return message
    
    def _mutate_semantics(self, message: bytearray, field_name: str) -> bytearray:
        """语义变异"""
        field_info = self.protocol_config['fields'][field_name]
        start, end = field_info['position']
        
        # 对数值字段进行边界值测试
        if field_info.get('is_numeric', False):
            # 尝试极值：0, -1, 最大值, 最小值等
            extreme_values = [0, -1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF]
            extreme_value = random.choice(extreme_values)
            
            # 将极值写入字段（假设为4字节整数）
            if end - start >= 4:
                packed_value = struct.pack('>I', extreme_value & 0xFFFFFFFF)
                for i, byte_val in enumerate(packed_value):
                    if start + i < len(message):
                        message[start + i] = byte_val
                        
        return message