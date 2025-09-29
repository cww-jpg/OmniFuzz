import struct
from typing import Dict, List, Any, Tuple
import logging

class ProtocolParser:
    """Industrial Protocol Parser"""
    
    def __init__(self, protocol_type: str, config: Dict[str, Any]):
        self.protocol_type = protocol_type
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Protocol-specific configuration
        self.protocol_config = config['protocols'].get(protocol_type, {})
        self.field_definitions = self.protocol_config.get('fields', {})
        
    def parse_message(self, message: bytes) -> Dict[str, Any]:
        """Parse protocol message"""
        try:
            if self.protocol_type == 'modbus_tcp':
                return self._parse_modbus_tcp(message)
            elif self.protocol_type == 'ethernet_ip':
                return self._parse_ethernet_ip(message)
            elif self.protocol_type == 'siemens_s7':
                return self._parse_siemens_s7(message)
            else:
                return self._parse_generic(message)
        except Exception as e:
            self.logger.error(f"Error parsing {self.protocol_type} message: {e}")
            return {'raw': message, 'error': str(e)}
    
    def mutate_message(self, original_message: bytes, 
                      field_actions: Dict[str, int]) -> bytes:
        """Mutate message based on agent actions"""
        parsed_message = self.parse_message(original_message)
        mutated_fields = {}
        
        for field_name, action_idx in field_actions.items():
            if field_name in parsed_message:
                action = self._get_mutation_action(action_idx)
                mutated_value = self._apply_mutation(
                    parsed_message[field_name], action, field_name
                )
                mutated_fields[field_name] = mutated_value
        
        # Rebuild mutated message
        return self._rebuild_message(parsed_message, mutated_fields)
    
    def _parse_modbus_tcp(self, message: bytes) -> Dict[str, Any]:
        """Parse Modbus TCP message"""
        if len(message) < 8:
            return {'error': 'Message too short'}
            
        return {
            'transaction_id': struct.unpack('>H', message[0:2])[0],
            'protocol_id': struct.unpack('>H', message[2:4])[0],
            'length': struct.unpack('>H', message[4:6])[0],
            'unit_id': message[6],
            'function_code': message[7],
            'data': message[8:] if len(message) > 8 else b''
        }
    
    def _parse_ethernet_ip(self, message: bytes) -> Dict[str, Any]:
        """Parse EtherNet/IP message"""
        if len(message) < 24:
            return {'error': 'Message too short'}
            
        return {
            'command': struct.unpack('>H', message[0:2])[0],
            'length': struct.unpack('>H', message[2:4])[0],
            'session_handle': struct.unpack('>I', message[4:8])[0],
            'status': struct.unpack('>I', message[8:12])[0],
            'sender_context': message[12:20],
            'options': struct.unpack('>I', message[20:24])[0],
            'data': message[24:] if len(message) > 24 else b''
        }
    
    def _parse_siemens_s7(self, message: bytes) -> Dict[str, Any]:
        """Parse Siemens S7 message"""
        if len(message) < 12:
            return {'error': 'Message too short'}
            
        return {
            'rosctr': message[0],
            'reserved': message[1],
            'protocol_data_unit_reference': struct.unpack('>H', message[2:4])[0],
            'parameter_length': struct.unpack('>H', message[4:6])[0],
            'data_length': struct.unpack('>H', message[6:8])[0],
            'data': message[8:] if len(message) > 8 else b''
        }
    
    def _parse_generic(self, message: bytes) -> Dict[str, Any]:
        """Generic parsing method"""
        return {
            'length': len(message),
            'raw': message,
            'hex': message.hex()
        }
    
    def _get_mutation_action(self, action_idx: int) -> str:
        """Get mutation operation based on action index"""
        actions = [
            'flip', 'delete', 'duplicate', 'truncate', 
            'pad', 'invalid_flag', 'reorder', 'semantic'
        ]
        return actions[action_idx % len(actions)]
    
    def _apply_mutation(self, original_value: Any, action: str, field_name: str) -> Any:
        """Apply mutation operation"""
        if action == 'flip':
            return self._flip_value(original_value)
        elif action == 'delete':
            return self._delete_value(original_value, field_name)
        elif action == 'duplicate':
            return self._duplicate_value(original_value)
        elif action == 'truncate':
            return self._truncate_value(original_value)
        elif action == 'pad':
            return self._pad_value(original_value)
        elif action == 'invalid_flag':
            return self._inject_invalid_flag(original_value, field_name)
        elif action == 'reorder':
            return self._reorder_value(original_value)
        elif action == 'semantic':
            return self._semantic_mutation(original_value, field_name)
        else:
            return original_value
    
    def _flip_value(self, value: Any) -> Any:
        """Flip value bits"""
        if isinstance(value, (bytes, bytearray)):
            return bytes(b ^ 0xFF for b in value)
        elif isinstance(value, int):
            return value ^ 0xFFFFFFFF
        else:
            return value
    
    def _delete_value(self, value: Any, field_name: str) -> Any:
        """Delete value (set to zero or empty)"""
        field_config = self.field_definitions.get(field_name, {})
        default_value = field_config.get('default', 0)
        
        if isinstance(value, (bytes, bytearray)):
            return bytes([0] * len(value))
        else:
            return default_value
    
    def _duplicate_value(self, value: Any) -> Any:
        """Duplicate value"""
        if isinstance(value, (bytes, bytearray)):
            return value * 2
        elif isinstance(value, (int, float)):
            return value
        else:
            return value
    
    def _truncate_value(self, value: Any) -> Any:
        """Truncate value"""
        if isinstance(value, (bytes, bytearray)):
            return value[:max(1, len(value) // 2)]
        else:
            return value
    
    def _pad_value(self, value: Any) -> Any:
        """Pad value with additional data"""
        if isinstance(value, (bytes, bytearray)):
            padding = bytes([0xFF] * 10)  # Pad with 10 0xFF bytes
            return value + padding
        else:
            return value
    
    def _inject_invalid_flag(self, value: Any, field_name: str) -> Any:
        """Inject invalid flag value"""
        field_config = self.field_definitions.get(field_name, {})
        
        if field_config.get('is_flag', False):
            if isinstance(value, int):
                invalid_values = [0xFF, 0x00, 0x7F]
                import random
                return random.choice(invalid_values)
        
        return value
    
    def _reorder_value(self, value: Any) -> Any:
        """Reorder value components"""
        if isinstance(value, (bytes, bytearray)):
            value_list = list(value)
            import random
            random.shuffle(value_list)
            return bytes(value_list)
        else:
            return value
    
    def _semantic_mutation(self, value: Any, field_name: str) -> Any:
        """Apply semantic mutation"""
        field_config = self.field_definitions.get(field_name, {})
        
        if field_config.get('is_numeric', False) and isinstance(value, int):
            # Boundary value testing
            boundary_values = [0, -1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF]
            import random
            return random.choice(boundary_values)
        
        return value
    
    def _rebuild_message(self, original_parsed: Dict[str, Any], 
                        mutated_fields: Dict[str, Any]) -> bytes:
        """Rebuild mutated message"""
        # Merge original and mutated fields
        merged_fields = original_parsed.copy()
        merged_fields.update(mutated_fields)
        
        # Rebuild message based on protocol type
        if self.protocol_type == 'modbus_tcp':
            return self._rebuild_modbus_tcp(merged_fields)
        elif self.protocol_type == 'ethernet_ip':
            return self._rebuild_ethernet_ip(merged_fields)
        elif self.protocol_type == 'siemens_s7':
            return self._rebuild_siemens_s7(merged_fields)
        else:
            return merged_fields.get('raw', b'')
    
    def _rebuild_modbus_tcp(self, fields: Dict[str, Any]) -> bytes:
        """Rebuild Modbus TCP message"""
        message = b''
        message += struct.pack('>H', fields.get('transaction_id', 0))
        message += struct.pack('>H', fields.get('protocol_id', 0))
        message += struct.pack('>H', fields.get('length', 0))
        message += bytes([fields.get('unit_id', 0)])
        message += bytes([fields.get('function_code', 0)])
        message += fields.get('data', b'')
        return message
    
    def _rebuild_ethernet_ip(self, fields: Dict[str, Any]) -> bytes:
        """Rebuild EtherNet/IP message"""
        message = b''
        message += struct.pack('>H', fields.get('command', 0))
        message += struct.pack('>H', fields.get('length', 0))
        message += struct.pack('>I', fields.get('session_handle', 0))
        message += struct.pack('>I', fields.get('status', 0))
        message += fields.get('sender_context', b'\x00' * 8)
        message += struct.pack('>I', fields.get('options', 0))
        message += fields.get('data', b'')
        return message
    
    def _rebuild_siemens_s7(self, fields: Dict[str, Any]) -> bytes:
        """Rebuild Siemens S7 message"""
        message = b''
        message += bytes([fields.get('rosctr', 0)])
        message += bytes([fields.get('reserved', 0)])
        message += struct.pack('>H', fields.get('protocol_data_unit_reference', 0))
        message += struct.pack('>H', fields.get('parameter_length', 0))
        message += struct.pack('>H', fields.get('data_length', 0))
        message += fields.get('data', b'')
        return message
    