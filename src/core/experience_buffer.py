import random
import numpy as np
from typing import List, Dict, Any
import torch

class ExperienceBuffer:
    """Experience replay buffer"""
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = []
        self.position = 0
        
    def add(self, experience: Dict[str, Any]):
        """Add experience to buffer"""
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
        else:
            self.buffer[self.position] = experience
            
        self.position = (self.position + 1) % self.capacity
        
    def sample(self, batch_size: int) -> List[Dict[str, Any]]:
        """Sample a batch of experiences from buffer"""
        if len(self.buffer) < batch_size:
            return self.buffer.copy()
        else:
            return random.sample(self.buffer, batch_size)
    
    def __len__(self):
        return len(self.buffer)
    
    def clear(self):
        """Clear buffer"""
        self.buffer = []
        self.position = 0

class PrioritizedExperienceBuffer(ExperienceBuffer):
    """Prioritized experience replay buffer"""
    
    def __init__(self, capacity: int, alpha: float = 0.6, beta: float = 0.4):
        super().__init__(capacity)
        self.alpha = alpha
        self.beta = beta
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.max_priority = 1.0
        
    def add(self, experience: Dict[str, Any]):
        """Add experience and set initial priority"""
        super().add(experience)
        self.priorities[self.position] = self.max_priority
        
    def sample(self, batch_size: int) -> List[Dict[str, Any]]:
        """Sample according to priority"""
        if len(self.buffer) < batch_size:
            indices = list(range(len(self.buffer)))
            weights = np.ones(len(self.buffer), dtype=np.float32)
        else:
            # Compute sampling probabilities
            priorities = self.priorities[:len(self.buffer)]
            probs = priorities ** self.alpha
            probs /= probs.sum()
            
            # Sample indices
            indices = np.random.choice(len(self.buffer), batch_size, p=probs)
            
            # Compute importance-sampling weights
            weights = (len(self.buffer) * probs[indices]) ** (-self.beta)
            weights /= weights.max()
            
        samples = [self.buffer[i] for i in indices]
        
        # Attach weight info
        for i, sample in enumerate(samples):
            sample['weight'] = weights[i] if 'weights' in locals() else 1.0
            
        return samples
    
    def update_priorities(self, indices: List[int], priorities: List[float]):
        """Update priorities for experiences"""
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority
            self.max_priority = max(self.max_priority, priority)