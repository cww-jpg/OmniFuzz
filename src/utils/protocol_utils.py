import struct
import binascii
from typing import Dict, List, Any

class ProtocolUtils:
    """Protocol utilities"""

    @staticmethod
    def hex_dump(data: bytes, width: int = 16) -> str:
        """Generate hex dump string"""
        result = []
        for i in range(0, len(data), width):
            chunk = data[i:i+width]
            hex_str = ' '.join(f'{b:02x}' for b in chunk)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            result.append(f'{i:08x}: {hex_str:<{width*3}} {ascii_str}')
        return '\n'.join(result)

    @staticmethod
    def calculate_crc(data: bytes, crc_type: str = 'crc16_modbus') -> int:
        """Calculate CRC checksum"""
        if crc_type == 'crc16_modbus':
            return ProtocolUtils._crc16_modbus(data)
        elif crc_type == 'crc32':
            return binascii.crc32(data)
        else:
            raise ValueError(f"Unsupported CRC type: {crc_type}")

    @staticmethod
    def _crc16_modbus(data: bytes) -> int:
        """Compute Modbus CRC16"""
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
        """Parse TLV (Type-Length-Value) formatted data"""
        tlv_list = []
        offset = 0

        while offset < len(data):
            if offset + 4 > len(data):
                break

            # Assume type and length take 2 bytes each
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
        """Build Modbus request"""
        transaction_id = 1  # simple implementation, should increment in practice
        protocol_id = 0
        length = len(data) + 2  # unit_id + function_code + data

        header = struct.pack('>HHHB', transaction_id, protocol_id, length, unit_id)
        return header + bytes([function_code]) + data

    @staticmethod
    def validate_protocol_message(message: bytes, protocol: str) -> Dict[str, Any]:
        """Validate protocol message format"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        if protocol == 'modbus_tcp':
            if len(message) < 8:
                validation_result['valid'] = False
                validation_result['errors'].append('Message length less than 8 bytes')

            # Check whether length field matches
            if len(message) >= 6:
                length = struct.unpack('>H', message[4:6])[0]
                expected_length = len(message) - 6
                if length != expected_length:
                    validation_result['warnings'].append(
                        f'Length field mismatch: claims {length} bytes, actual {expected_length} bytes'
                    )

        elif protocol == 'ethernet_ip':
            if len(message) < 24:
                validation_result['valid'] = False
                validation_result['errors'].append('Message length less than 24 bytes')

        elif protocol == 'siemens_s7':
            if len(message) < 12:
                validation_result['valid'] = False
                validation_result['errors'].append('Message length less than 12 bytes')

        return validation_result