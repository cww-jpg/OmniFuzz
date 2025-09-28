import struct
import binascii
from typing import Dict, List, Any

class ProtocolUtils:
    """协议工具类"""

    @staticmethod
    def hex_dump(data: bytes, width: int = 16) -> str:
        """生成十六进制转储字符串"""
        result = []
        for i in range(0, len(data), width):
            chunk = data[i:i+width]
            hex_str = ' '.join(f'{b:02x}' for b in chunk)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            result.append(f'{i:08x}: {hex_str:<{width*3}} {ascii_str}')
        return '\n'.join(result)

    @staticmethod
    def calculate_crc(data: bytes, crc_type: str = 'crc16_modbus') -> int:
        """计算CRC校验和"""
        if crc_type == 'crc16_modbus':
            return ProtocolUtils._crc16_modbus(data)
        elif crc_type == 'crc32':
            return binascii.crc32(data)
        else:
            raise ValueError(f"不支持的CRC类型: {crc_type}")

    @staticmethod
    def _crc16_modbus(data: bytes) -> int:
        """计算Modbus CRC16"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc = crc >> 1
        return crc

    @staticmethod
    def parse_tlv(data: bytes) -> List[Dict[str, Any]]:
        """解析TLV（类型-长度-值）格式数据"""
        tlv_list = []
        offset = 0

        while offset < len(data):
            if offset + 4 > len(data):
                break

            # 假设类型和长度各占2字节
            type_val = struct.unpack('>H', data[offset:offset+2])[0]
            length = struct.unpack('>H', data[offset+2:offset+4])[0]

            if offset + 4 + length > len(data):
                break

            value = data[offset+4:offset+4+length]
            tlv_list.append({
                'type': type_val,
                'length': length,
                'value': value,
                'value_hex': value.hex()
            })

            offset += 4 + length

        return tlv_list

    @staticmethod
    def build_modbus_request(unit_id: int, function_code: int, data: bytes) -> bytes:
        """构建Modbus请求"""
        transaction_id = 1  # 简单实现，实际应该递增
        protocol_id = 0
        length = len(data) + 2  # unit_id + function_code + data

        header = struct.pack('>HHHB', transaction_id, protocol_id, length, unit_id)
        return header + bytes([function_code]) + data

    @staticmethod
    def validate_protocol_message(message: bytes, protocol: str) -> Dict[str, Any]:
        """验证协议消息格式"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        if protocol == 'modbus_tcp':
            if len(message) < 8:
                validation_result['valid'] = False
                validation_result['errors'].append('消息长度不足8字节')

            # 检查长度字段是否匹配
            if len(message) >= 6:
                length = struct.unpack('>H', message[4:6])[0]
                expected_length = len(message) - 6
                if length != expected_length:
                    validation_result['warnings'].append(
                        f'长度字段不匹配: 声明{length}字节，实际{expected_length}字节'
                    )

        elif protocol == 'ethernet_ip':
            if len(message) < 24:
                validation_result['valid'] = False
                validation_result['errors'].append('消息长度不足24字节')

        elif protocol == 'siemens_s7':
            if len(message) < 12:
                validation_result['valid'] = False
                validation_result['errors'].append('消息长度不足12字节')

        return validation_result