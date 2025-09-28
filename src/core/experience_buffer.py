import random
import numpy as np
from typing import List, Dict, Any
import torch

class ExperienceBuffer:
    """经验回放缓冲区"""
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = []
        self.position = 0
        
    def add(self, experience: Dict[str, Any]):
        """添加经验到缓冲区"""
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
        else:
            self.buffer[self.position] = experience
            
        self.position = (self.position + 1) % self.capacity
        
    def sample(self, batch_size: int) -> List[Dict[str, Any]]:
        """从缓冲区采样批次经验"""
        if len(self.buffer) < batch_size:
            return self.buffer.copy()
        else:
            return random.sample(self.buffer, batch_size)
    
    def __len__(self):
        return len(self.buffer)
    
    def clear(self):
        """清空缓冲区"""
        self.buffer = []
        self.position = 0

class PrioritizedExperienceBuffer(ExperienceBuffer):
    """带优先级的经验回放缓冲区"""
    
    def __init__(self, capacity: int, alpha: float = 0.6, beta: float = 0.4):
        super().__init__(capacity)
        self.alpha = alpha
        self.beta = beta
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.max_priority = 1.0
        
    def add(self, experience: Dict[str, Any]):
        """添加经验并设置初始优先级"""
        super().add(experience)
        self.priorities[self.position] = self.max_priority
        
    def sample(self, batch_size: int) -> List[Dict[str, Any]]:
        """根据优先级采样"""
        if len(self.buffer) < batch_size:
            indices = list(range(len(self.buffer)))
            weights = np.ones(len(self.buffer), dtype=np.float32)
        else:
            # 计算采样概率
            priorities = self.priorities[:len(self.buffer)]
            probs = priorities ** self.alpha
            probs /= probs.sum()
            
            # 采样索引
            indices = np.random.choice(len(self.buffer), batch_size, p=probs)
            
            # 计算重要性采样权重
            weights = (len(self.buffer) * probs[indices]) ** (-self.beta)
            weights /= weights.max()
            
        samples = [self.buffer[i] for i in indices]
        
        # 添加权重信息
        for i, sample in enumerate(samples):
            sample['weight'] = weights[i] if 'weights' in locals() else 1.0
            
        return samples
    
    def update_priorities(self, indices: List[int], priorities: List[float]):
        """更新经验的优先级"""
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority
            self.max_priority = max(self.max_priority, priority)