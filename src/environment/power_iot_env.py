import torch
import numpy as np
from typing import Dict, List, Any, Tuple
import logging

class PowerIoTEnvironment:
    """Power IoT environment"""
    
    def __init__(self, protocols: List[str], config: Dict[str, Any]):
        self.protocols = protocols
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Protocol parsers
        self.protocol_parsers = self._initialize_parsers()
        
        # Device interfaces
        self.device_interfaces = self._initialize_interfaces()
        
        # State tracking
        self.current_state = {}
        self.execution_depth = {}
        self.vulnerabilities_found = []
        
    def _initialize_parsers(self) -> Dict[str, Any]:
        """Initialize protocol parsers"""
        parsers = {}
        for protocol in self.protocols:
            # Initialize corresponding parser based on protocol type
            parsers[protocol] = ProtocolParser(protocol, self.config)
        return parsers
    
    def _initialize_interfaces(self) -> Dict[str, Any]:
        """Initialize device interfaces"""
        interfaces = {}
        for protocol in self.protocols:
            # Initialize corresponding device interface based on protocol type
            interfaces[protocol] = DeviceInterface(protocol, self.config)
        return interfaces
    
    def reset(self) -> Dict[str, torch.Tensor]:
        """Reset environment state"""
        self.current_state = {}
        self.execution_depth = {}
        self.vulnerabilities_found = []
        
        # Initialize state for each protocol
        initial_observations = {}
        for protocol in self.protocols:
            protocol_state = self._get_initial_protocol_state(protocol)
            self.current_state[protocol] = protocol_state
            initial_observations[protocol] = self._state_to_observation(protocol_state)
            
        return initial_observations
    
    def step(self, actions: Dict[str, Dict[str, torch.Tensor]]) -> Tuple[Dict, float, bool, Dict]:
        """Execute one environment step"""
        
        # Apply mutations
        mutated_messages = self._apply_mutations(actions)
        
        # Send test cases to target devices
        fuzzing_results = self._send_test_cases(mutated_messages)
        
        # Calculate reward
        reward = self._calculate_reward(fuzzing_results)
        
        # Update state
        new_observations = self._update_state(fuzzing_results)
        
        # Check termination (max steps reached or critical vulnerabilities found)
        done = self._check_termination(fuzzing_results)
        
        # Extra information
        info = {
            'fuzzing_results': fuzzing_results,
            'vulnerabilities_found': self.vulnerabilities_found,
            'execution_depth': self.execution_depth
        }
        
        return new_observations, reward, done, info
    
    def _apply_mutations(self, actions: Dict[str, Dict[str, torch.Tensor]]) -> Dict[str, List[bytes]]:
        """Apply mutations to generate test cases"""
        mutated_messages = {}
        
        for protocol, field_actions in actions.items():
            if protocol in self.protocol_parsers:
                parser = self.protocol_parsers[protocol]
                original_message = self._get_protocol_template(protocol)
                
                # Apply mutations
                mutated_message = parser.mutate_message(original_message, field_actions)
                mutated_messages[protocol] = [mutated_message]  # simplified to a single message
                
        return mutated_messages
    
    def _send_test_cases(self, test_cases: Dict[str, List[bytes]]) -> Dict[str, Any]:
        """Send test cases to target devices and collect results"""
        results = {}
        
        for protocol, messages in test_cases.items():
            if protocol in self.device_interfaces:
                interface = self.device_interfaces[protocol]
                protocol_results = []
                
                for message in messages:
                    try:
                        # Send message and get response
                        response = interface.send_message(message)
                        
                        # Analyze response
                        analysis = self._analyze_response(protocol, message, response)
                        protocol_results.append(analysis)
                        
                    except Exception as e:
                        # Record exception (potential vulnerability)
                        vulnerability = self._detect_vulnerability(protocol, message, str(e))
                        if vulnerability:
                            self.vulnerabilities_found.append(vulnerability)
                        protocol_results.append({
                            'status': 'error',
                            'exception': str(e),
                            'vulnerability': vulnerability
                        })
                
                results[protocol] = protocol_results
                
        return results
    
    def _calculate_reward(self, fuzzing_results: Dict[str, Any]) -> float:
        """Compute reward value"""
        # Implement the multi-objective reward described in the paper
        # Including number of vulnerabilities, path depth, diversity, etc.
        
        reward = 0.0
        
        for protocol, results in fuzzing_results.items():
            for result in results:
                if result.get('vulnerability'):
                    # Reward based on vulnerability severity
                    severity = result['vulnerability'].get('severity', 'general')
                    reward += self._get_vulnerability_reward(severity)
                
                # Path depth reward
                if 'execution_depth' in result:
                    reward += result['execution_depth'] * 0.1
                    
        return reward
    
    def _update_state(self, fuzzing_results: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        """Update environment state"""
        new_observations = {}
        
        for protocol in self.protocols:
            if protocol in fuzzing_results:
                # Update protocol state
                protocol_state = self._update_protocol_state(protocol, fuzzing_results[protocol])
                self.current_state[protocol] = protocol_state
                new_observations[protocol] = self._state_to_observation(protocol_state)
                
        return new_observations
    
    def _get_initial_protocol_state(self, protocol: str) -> Dict[str, Any]:
        """Get initial state for a protocol"""
        return {
            'message_count': 0,
            'vulnerability_count': 0,
            'coverage': 0.0,
            'last_action': None,
            'execution_path': []
        }
    
    def _state_to_observation(self, state: Dict[str, Any]) -> torch.Tensor:
        """Convert state to observation vector"""
        # Convert state dict into numeric vector
        features = [
            state['message_count'],
            state['vulnerability_count'],
            state['coverage'],
            # Add more features if needed
        ]
        
        return torch.tensor(features, dtype=torch.float32)
    
    def _get_vulnerability_reward(self, severity: str) -> float:
        """Get reward by vulnerability severity"""
        reward_map = {
            'critical': 4.0,
            'major': 3.0,
            'minor': 2.0,
            'general': 1.0,
            'none': 0.0
        }
        return reward_map.get(severity, 0.0)
    
    def _check_termination(self, fuzzing_results: Dict[str, Any]) -> bool:
        """Check whether to terminate"""
        # Check if critical vulnerabilities are found
        critical_vulnerabilities = [
            vuln for vuln in self.vulnerabilities_found 
            if vuln.get('severity') == 'critical'
        ]
        
        if len(critical_vulnerabilities) >= 3:  # more than 3 critical vulns
            return True
            
        # Check if max number of messages is reached
        total_messages = sum(
            len(results) for results in fuzzing_results.values()
        )
        
        if total_messages > 10000:  # max messages
            return True
            
        return False