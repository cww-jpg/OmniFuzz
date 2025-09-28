import numpy as np
import torch
from typing import List, Dict, Any
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN

class DataPreprocessor:
    """工业协议数据预处理器"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.cluster_model = DBSCAN(eps=0.5, min_samples=5)
        self.protocol_formats = {}
        
    def preprocess_protocol_data(self, raw_packets: List[bytes], 
                               protocol_type: str) -> Dict[str, Any]:
        """预处理协议数据"""
        
        # 1. 协议数据聚类和样本扩展
        clustered_data = self._cluster_packets_by_length(raw_packets)
        
        # 2. 数据格式转换和编码标准化
        normalized_data = self._normalize_encoding(clustered_data)
        
        # 3. 数据归一化
        preprocessed_data = self._normalize_data(normalized_data)
        
        return {
            'clustered_data': clustered_data,
            'normalized_data': normalized_data,
            'preprocessed_data': preprocessed_data,
            'feature_vectors': self._extract_features(preprocessed_data)
        }
    
    def _cluster_packets_by_length(self, packets: List[bytes]) -> Dict[int, List[bytes]]:
        """基于数据包长度进行聚类"""
        length_groups = {}
        
        for packet in packets:
            length = len(packet)
            if length not in length_groups:
                length_groups[length] = []
            length_groups[length].append(packet)
            
        return length_groups
    
    def _normalize_encoding(self, clustered_data: Dict[int, List[bytes]]) -> List[np.ndarray]:
        """标准化编码格式（转换为8位八进制序列）"""
        normalized_packets = []
        
        for length_group in clustered_data.values():
            for packet in length_group:
                # 转换为二进制流，然后转换为8位八进制序列
                binary_stream = ''.join(format(byte, '08b') for byte in packet)
                
                # 转换为8维one-hot向量（简化实现）
                one_hot_vectors = []
                for byte in packet:
                    # 每个字符编码为8维one-hot向量
                    one_hot = np.zeros(8)
                    one_hot[byte % 8] = 1  # 简化实现
                    one_hot_vectors.append(one_hot)
                    
                normalized_packets.append(np.array(one_hot_vectors).flatten())
                
        return normalized_packets
    
    def _normalize_data(self, normalized_data: List[np.ndarray]) -> np.ndarray:
        """数据归一化"""
        if not normalized_data:
            return np.array([])
            
        # 找到最大长度进行填充
        max_length = max(len(vec) for vec in normalized_data)
        padded_data = []
        
        for vec in normalized_data:
            if len(vec) < max_length:
                # 使用字节重复和随机填充的混合方法
                padding_length = max_length - len(vec)
                padding = np.random.choice([0, 1], size=padding_length)
                padded_vec = np.concatenate([vec, padding])
            else:
                padded_vec = vec[:max_length]
                
            padded_data.append(padded_vec)
            
        return np.array(padded_data)
    
    def _extract_features(self, preprocessed_data: np.ndarray) -> np.ndarray:
        """提取特征向量"""
        if preprocessed_data.size == 0:
            return np.array([])
            
        # 使用标准化器
        if hasattr(self.scaler, 'n_samples_seen_') and self.scaler.n_samples_seen_ > 0:
            features = self.scaler.transform(preprocessed_data)
        else:
            features = self.scaler.fit_transform(preprocessed_data)
            
        return features
    
    def apply_smote_augmentation(self, data: np.ndarray, labels: np.ndarray) -> tuple:
        """应用SMOTE过采样技术增强少数类数据"""
        # 这里简化实现，实际应使用imbalanced-learn库
        unique_labels, counts = np.unique(labels, return_counts=True)
        max_count = np.max(counts)
        
        augmented_data = [data]
        augmented_labels = [labels]
        
        for label, count in zip(unique_labels, counts):
            if count < max_count:
                # 复制少数类样本以达到平衡
                minority_indices = np.where(labels == label)[0]
                replication_factor = max_count // count
                
                for _ in range(replication_factor - 1):
                    replicated_data = data[minority_indices].copy()
                    # 添加少量噪声
                    noise = np.random.normal(0, 0.01, replicated_data.shape)
                    replicated_data += noise
                    
                    augmented_data.append(replicated_data)
                    augmented_labels.append(np.full(len(minority_indices), label))
        
        return (np.vstack(augmented_data), 
                np.concatenate(augmented_labels))