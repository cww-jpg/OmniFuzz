import socket
import time
import logging
from typing import Optional, Dict, Any
import subprocess
import select

class DeviceInterface:
    """电力物联网设备接口"""
    
    def __init__(self, protocol: str, config: Dict[str, Any]):
        self.protocol = protocol
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 协议特定配置
        protocol_config = config['protocols'].get(protocol, {})
        self.port = protocol_config.get('port', 502)
        self.timeout = protocol_config.get('timeout', 5.0)
        
        # 设备连接信息
        self.target_ip = config.get('target_ip', '127.0.0.1')
        self.socket = None
        
    def connect(self) -> bool:
        """连接到目标设备"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.target_ip, self.port))
            self.logger.info(f"成功连接到 {self.target_ip}:{self.port}")
            return True
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.socket:
            self.socket.close()
            self.socket = None
    
    def send_message(self, message: bytes, wait_response: bool = True) -> Dict[str, Any]:
        """发送消息到设备并获取响应"""
        if not self.socket:
            if not self.connect():
                return {'error': '连接失败', 'status': 'connection_error'}
        
        try:
            # 发送消息
            start_time = time.time()
            self.socket.send(message)
            self.logger.debug(f"发送 {len(message)} 字节到设备")
            
            response_data = None
            if wait_response:
                # 等待响应
                response_data = self._receive_response()
            
            execution_time = time.time() - start_time
            
            # 分析响应
            analysis = self._analyze_response(message, response_data, execution_time)
            return analysis
            
        except socket.timeout:
            self.logger.warning("设备响应超时")
            return {
                'status': 'timeout',
                'execution_time': self.timeout,
                'vulnerability': self._detect_timeout_vulnerability(message)
            }
        except Exception as e:
            self.logger.error(f"发送消息时出错: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'vulnerability': self._detect_exception_vulnerability(message, str(e))
            }
    
    def _receive_response(self) -> bytes:
        """接收设备响应"""
        response = b''
        self.socket.settimeout(2.0)  # 设置较短的超时用于分片接收
        
        try:
            while True:
                ready = select.select([self.socket], [], [], 1.0)
                if ready[0]:
                    chunk = self.socket.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                else:
                    # 没有更多数据
                    break
        except socket.timeout:
            # 接收超时，返回已接收的数据
            pass
        
        return response
    
    def _analyze_response(self, request: bytes, response: Optional[bytes], 
                         execution_time: float) -> Dict[str, Any]:
        """分析设备响应"""
        analysis = {
            'request_length': len(request),
            'execution_time': execution_time,
            'status': 'unknown'
        }
        
        if response is None:
            analysis['status'] = 'no_response'
            analysis['vulnerability'] = self._detect_no_response_vulnerability(request)
        else:
            analysis['response_length'] = len(response)
            analysis['response_hex'] = response.hex()[:100]  # 记录前100个字符的十六进制
            
            # 根据响应内容判断状态
            if len(response) == 0:
                analysis['status'] = 'empty_response'
            elif self._is_error_response(response):
                analysis['status'] = 'error_response'
                analysis['vulnerability'] = self._detect_error_response_vulnerability(request, response)
            elif self._is_valid_response(response):
                analysis['status'] = 'valid_response'
            else:
                analysis['status'] = 'unexpected_response'
        
        # 检测执行时间异常
        if execution_time > self.config.get('max_normal_execution_time', 10.0):
            analysis['status'] = 'slow_response'
            analysis['vulnerability'] = self._detect_slow_response_vulnerability(request, execution_time)
        
        return analysis
    
    def _is_error_response(self, response: bytes) -> bool:
        """判断是否为错误响应"""
        # 协议特定的错误检测逻辑
        if self.protocol == 'modbus_tcp' and len(response) >= 8:
            # Modbus TCP异常响应：功能码最高位为1
            function_code = response[7] if len(response) > 7 else 0
            return (function_code & 0x80) != 0
            
        elif self.protocol == 'ethernet_ip' and len(response) >= 12:
            # EtherNet/IP状态字段非零表示错误
            status = int.from_bytes(response[8:12], 'big')
            return status != 0
            
        return False
    
    def _is_valid_response(self, response: bytes) -> bool:
        """判断是否为有效响应"""
        # 基本验证：响应不为空且长度合理
        if len(response) == 0:
            return False
            
        # 协议特定的有效响应检测
        if self.protocol == 'modbus_tcp':
            return len(response) >= 8  # Modbus TCP头部长度
            
        elif self.protocol == 'ethernet_ip':
            return len(response) >= 24  # EtherNet/IP基本头部长度
            
        elif self.protocol == 'siemens_s7':
            return len(response) >= 12  # S7基本头部长度
            
        return True
    
    def _detect_timeout_vulnerability(self, request: bytes) -> Dict[str, Any]:
        """检测超时相关的漏洞"""
        return {
            'type': 'denial_of_service',
            'severity': 'major',
            'description': '消息导致设备响应超时',
            'request_sample': request.hex()[:50]
        }
    
    def _detect_no_response_vulnerability(self, request: bytes) -> Dict[str, Any]:
        """检测无响应相关的漏洞"""
        return {
            'type': 'service_disruption', 
            'severity': 'critical',
            'description': '消息导致设备停止响应',
            'request_sample': request.hex()[:50]
        }
    
    def _detect_error_response_vulnerability(self, request: bytes, response: bytes) -> Dict[str, Any]:
        """检测错误响应相关的漏洞"""
        return {
            'type': 'protocol_error',
            'severity': 'minor',
            'description': '消息触发协议错误响应',
            'request_sample': request.hex()[:50],
            'response_sample': response.hex()[:50]
        }
    
    def _detect_slow_response_vulnerability(self, request: bytes, execution_time: float) -> Dict[str, Any]:
        """检测慢响应相关的漏洞"""
        return {
            'type': 'performance_degradation',
            'severity': 'minor', 
            'description': f'消息导致设备响应缓慢 ({execution_time:.2f}s)',
            'request_sample': request.hex()[:50]
        }
    
    def _detect_exception_vulnerability(self, request: bytes, error: str) -> Dict[str, Any]:
        """检测异常相关的漏洞"""
        return {
            'type': 'exception_triggered',
            'severity': 'major',
            'description': f'消息导致设备异常: {error}',
            'request_sample': request.hex()[:50]
        }