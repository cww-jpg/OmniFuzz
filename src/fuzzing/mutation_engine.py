import random
import struct
from typing import List, Dict, Any, Union
from enum import Enum

class MutationAction(Enum):
    """Mutation operation enumeration"""
    FIELD_FLIPPING = "field_flipping"
    FIELD_DELETION = "field_deletion"
    FIELD_DUPLICATION = "field_duplication"
    FIELD_TRUNCATION = "field_truncation"
    FIELD_PADDING = "field_padding"
    INVALID_FLAG_INJECTION = "invalid_flag_injection"
    FIELDS_REORDERING = "fields_reordering"
    SEMANTIC_MUTATION = "semantic_mutation"

class MutationEngine:
    """Protocol field mutation engine"""
    
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
        """Mutate protocol message based on agent-selected actions"""
        mutated_message = bytearray(original_message)
        
        for field_name, action_idx in mutation_actions.items():
            if field_name in self.protocol_config['fields']:
                action = list(MutationAction)[action_idx % len(MutationAction)]
                strategy = self.mutation_strategies.get(action)
                
                if strategy:
                    mutated_message = strategy(mutated_message, field_name)
        
        return bytes(mutated_message)
    
    def _flip_field(self, message: bytearray, field_name: str) -> bytearray:
        """Flip field values"""
        field_info = self.protocol_config['fields'][field_name]
        start, end = field_info['position']
        
        # Randomly flip some bits in the field
        for i in range(start, min(end, len(message))):
            if random.random() < 0.3:  # 30% probability to flip each byte
                message[i] ^= 0xFF
                
        return message
    
    def _delete_field(self, message: bytearray, field_name: str) -> bytearray:
        """Delete field"""
        field_info = self.protocol_config['fields'][field_name]
        start, end = field_info['position']
        
        # Fill deleted field with zeros
        for i in range(start, min(end, len(message))):
            message[i] = 0x00
            
        return message
    
    def _duplicate_field(self, message: bytearray, field_name: str) -> bytearray:
        """Duplicate field"""
        field_info = self.protocol_config['fields'][field_name]
        start, end = field_info['position']
        field_length = end - start
        
        # Duplicate field at the end of the message
        field_data = message[start:end]
        message.extend(field_data)
        
        return message
    
    def _truncate_message(self, message: bytearray, field_name: str) -> bytearray:
        """Truncate protocol message"""
        # Randomly truncate to 50%-90% of original length
        new_length = random.randint(len(message) // 2, int(len(message) * 0.9))
        return message[:new_length]
    
    def _pad_field(self, message: bytearray, field_name: str) -> bytearray:
        """Add padding bytes"""
        # Add random padding bytes
        padding_length = random.randint(1, 100)
        padding = bytes([random.randint(0, 255) for _ in range(padding_length)])
        message.extend(padding)
        
        return message
    
    def _inject_invalid_flag(self, message: bytearray, field_name: str) -> bytearray:
        """Inject invalid flag"""
        field_info = self.protocol_config['fields'][field_name]
        
        if field_info.get('is_flag', False):
            start, end = field_info['position']
            # Set to invalid flag value
            invalid_value = random.choice([0xFF, 0x00, 0x7F])
            for i in range(start, min(end, len(message))):
                message[i] = invalid_value
                
        return message
    
    def _reorder_fields(self, message: bytearray, field_name: str) -> bytearray:
        """Reorder field sequence"""
        # This is a complex operation that would normally require parsing and rebuilding
        # Here simplified to randomly swapping some byte positions
        if len(message) >= 2:
            idx1, idx2 = random.sample(range(len(message)), 2)
            message[idx1], message[idx2] = message[idx2], message[idx1]
            
        return message
    
    def _mutate_semantics(self, message: bytearray, field_name: str) -> bytearray:
        """Semantic mutation"""
        field_info = self.protocol_config['fields'][field_name]
        start, end = field_info['position']
        
        # Perform boundary value testing on numeric fields
        if field_info.get('is_numeric', False):
            # Try extreme values: 0, -1, maximum value, minimum value, etc.
            extreme_values = [0, -1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF]
            extreme_value = random.choice(extreme_values)
            
            # Write extreme value to field (assuming 4-byte integer)
            if end - start >= 4:
                packed_value = struct.pack('>I', extreme_value & 0xFFFFFFFF)
                for i, byte_val in enumerate(packed_value):
                    if start + i < len(message):
                        message[start + i] = byte_val
                        
        return message
    