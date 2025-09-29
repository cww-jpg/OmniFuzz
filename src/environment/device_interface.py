import socket
import time
import logging
from typing import Optional, Dict, Any
import subprocess
import select

class DeviceInterface:
    """Power Internet of Things Device Interface"""
    
    def __init__(self, protocol: str, config: Dict[str, Any]):
        self.protocol = protocol
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Protocol-specific configuration
        protocol_config = config['protocols'].get(protocol, {})
        self.port = protocol_config.get('port', 502)
        self.timeout = protocol_config.get('timeout', 5.0)
        
        # Device connection information
        self.target_ip = config.get('target_ip', '127.0.0.1')
        self.socket = None
        
    def connect(self) -> bool:
        """Connect to the target device"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.target_ip, self.port))
            self.logger.info(f"Successfully connected to {self.target_ip}:{self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the device"""
        if self.socket:
            self.socket.close()
            self.socket = None
    
    def send_message(self, message: bytes, wait_response: bool = True) -> Dict[str, Any]:
        """Send message to device and get response"""
        if not self.socket:
            if not self.connect():
                return {'error': 'Connection failed', 'status': 'connection_error'}
        
        try:
            # Send message
            start_time = time.time()
            self.socket.send(message)
            self.logger.debug(f"Sent {len(message)} bytes to device")
            
            response_data = None
            if wait_response:
                # Wait for response
                response_data = self._receive_response()
            
            execution_time = time.time() - start_time
            
            # Analyze response
            analysis = self._analyze_response(message, response_data, execution_time)
            return analysis
            
        except socket.timeout:
            self.logger.warning("Device response timed out")
            return {
                'status': 'timeout',
                'execution_time': self.timeout,
                'vulnerability': self._detect_timeout_vulnerability(message)
            }
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'vulnerability': self._detect_exception_vulnerability(message, str(e))
            }
    
    def _receive_response(self) -> bytes:
        """Receive device response"""
        response = b''
        self.socket.settimeout(2.0)  # Set shorter timeout for chunked reception
        
        try:
            while True:
                ready = select.select([self.socket], [], [], 1.0)
                if ready[0]:
                    chunk = self.socket.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                else:
                    # No more data
                    break
        except socket.timeout:
            # Timeout on receive, return received data
            pass
        
        return response
    
    def _analyze_response(self, request: bytes, response: Optional[bytes], 
                         execution_time: float) -> Dict[str, Any]:
        """Analyze device response"""
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
            analysis['response_hex'] = response.hex()[:100]  # Record first 100 characters in hex
            
            # Determine status based on response content
            if len(response) == 0:
                analysis['status'] = 'empty_response'
            elif self._is_error_response(response):
                analysis['status'] = 'error_response'
                analysis['vulnerability'] = self._detect_error_response_vulnerability(request, response)
            elif self._is_valid_response(response):
                analysis['status'] = 'valid_response'
            else:
                analysis['status'] = 'unexpected_response'
        
        # Detect abnormal execution time
        if execution_time > self.config.get('max_normal_execution_time', 10.0):
            analysis['status'] = 'slow_response'
            analysis['vulnerability'] = self._detect_slow_response_vulnerability(request, execution_time)
        
        return analysis
    
    def _is_error_response(self, response: bytes) -> bool:
        """Determine if response is an error response"""
        # Protocol-specific error detection logic
        if self.protocol == 'modbus_tcp' and len(response) >= 8:
            # Modbus TCP exception response: highest bit of function code is 1
            function_code = response[7] if len(response) > 7 else 0
            return (function_code & 0x80) != 0
            
        elif self.protocol == 'ethernet_ip' and len(response) >= 12:
            # EtherNet/IP non-zero status field indicates error
            status = int.from_bytes(response[8:12], 'big')
            return status != 0
            
        return False
    
    def _is_valid_response(self, response: bytes) -> bool:
        """Determine if response is valid"""
        # Basic validation: response is not empty and has reasonable length
        if len(response) == 0:
            return False
            
        # Protocol-specific valid response detection
        if self.protocol == 'modbus_tcp':
            return len(response) >= 8  # Modbus TCP header length
            
        elif self.protocol == 'ethernet_ip':
            return len(response) >= 24  # EtherNet/IP basic header length
            
        elif self.protocol == 'siemens_s7':
            return len(response) >= 12  # S7 basic header length
            
        return True
    
    def _detect_timeout_vulnerability(self, request: bytes) -> Dict[str, Any]:
        """Detect timeout-related vulnerabilities"""
        return {
            'type': 'denial_of_service',
            'severity': 'major',
            'description': 'Message caused device response timeout',
            'request_sample': request.hex()[:50]
        }
    
    def _detect_no_response_vulnerability(self, request: bytes) -> Dict[str, Any]:
        """Detect no-response-related vulnerabilities"""
        return {
            'type': 'service_disruption', 
            'severity': 'critical',
            'description': 'Message caused device to stop responding',
            'request_sample': request.hex()[:50]
        }
    
    def _detect_error_response_vulnerability(self, request: bytes, response: bytes) -> Dict[str, Any]:
        """Detect error response-related vulnerabilities"""
        return {
            'type': 'protocol_error',
            'severity': 'minor',
            'description': 'Message triggered protocol error response',
            'request_sample': request.hex()[:50],
            'response_sample': response.hex()[:50]
        }
    
    def _detect_slow_response_vulnerability(self, request: bytes, execution_time: float) -> Dict[str, Any]:
        """Detect slow response-related vulnerabilities"""
        return {
            'type': 'performance_degradation',
            'severity': 'minor', 
            'description': f'Message caused slow device response ({execution_time:.2f}s)',
            'request_sample': request.hex()[:50]
        }
    
    def _detect_exception_vulnerability(self, request: bytes, error: str) -> Dict[str, Any]:
        """Detect exception-related vulnerabilities"""
        return {
            'type': 'exception_triggered',
            'severity': 'major',
            'description': f'Message caused device exception: {error}',
            'request_sample': request.hex()[:50]
        }
