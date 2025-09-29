import random
import struct
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

class TestCasePriority(Enum):
    HIGH = 3
    MEDIUM = 2
    LOW = 1

class TestCaseGenerator:
    """Test case generator"""
    
    def __init__(self, protocol_configs: Dict[str, Any]):
        self.protocol_configs = protocol_configs
        self.logger = logging.getLogger(__name__)
        
        # Seed test case repository
        self.seed_cases = self._initialize_seed_cases()
        
        # Mutation strategy weights
        self.mutation_weights = {
            'field_flipping': 0.2,
            'field_deletion': 0.15,
            'field_duplication': 0.1,
            'field_truncation': 0.1,
            'field_padding': 0.15,
            'invalid_flag_injection': 0.1,
            'fields_reordering': 0.1,
            'semantic_mutation': 0.1
        }
    
    def _initialize_seed_cases(self) -> Dict[str, List[bytes]]:
        """Initialize seed test cases"""
        seed_cases = {}
        
        for protocol, config in self.protocol_configs.items():
            seed_cases[protocol] = self._generate_protocol_seeds(protocol, config)
            
        return seed_cases
    
    def _generate_protocol_seeds(self, protocol: str, config: Dict[str, Any]) -> List[bytes]:
        """Generate protocol-specific seed cases"""
        seeds = []
        
        if protocol == 'modbus_tcp':
            seeds.extend(self._generate_modbus_seeds(config))
        elif protocol == 'ethernet_ip':
            seeds.extend(self._generate_ethernet_ip_seeds(config))
        elif protocol == 'siemens_s7':
            seeds.extend(self._generate_siemens_s7_seeds(config))
        
        return seeds
    
    def _generate_modbus_seeds(self, config: Dict[str, Any]) -> List[bytes]:
        """Generate Modbus TCP seed cases"""
        seeds = []
        
        # Requests for common function codes
        function_codes = [1, 2, 3, 4, 5, 6, 15, 16]
        
        for func_code in function_codes:
            # Basic request structure
            transaction_id = 1
            protocol_id = 0
            unit_id = 1
            
            if func_code in [1, 2, 3, 4]:  # read operations
                # Read request: start address + count
                data = struct.pack('>HH', 0, 10)  # read 10 from address 0
                length = len(data) + 2  # data length + unit_id and function_code
                
                seed = (struct.pack('>HHH', transaction_id, protocol_id, length) +
                        bytes([unit_id, func_code]) + data)
                seeds.append(seed)
                
            elif func_code in [5, 6]:  # write single
                # Write single request: address + value
                data = struct.pack('>HH', 0, 1)  # write 1 to address 0
                length = len(data) + 2
                
                seed = (struct.pack('>HHH', transaction_id, protocol_id, length) +
                        bytes([unit_id, func_code]) + data)
                seeds.append(seed)
                
            elif func_code in [15, 16]:  # write multiple
                # Write multiple request
                if func_code == 15:  # write multiple coils
                    data = struct.pack('>HHB', 0, 8, 1) + b'\x55'  # 8 coils, value 0x55
                else:  # write multiple registers
                    data = struct.pack('>HHB', 0, 2, 4) + struct.pack('>HH', 1, 2)
                
                length = len(data) + 2
                seed = (struct.pack('>HHH', transaction_id, protocol_id, length) +
                        bytes([unit_id, func_code]) + data)
                seeds.append(seed)
        
        return seeds
    
    def _generate_ethernet_ip_seeds(self, config: Dict[str, Any]) -> List[bytes]:
        """Generate EtherNet/IP seed cases"""
        seeds = []
        
        # ListIdentity request
        list_identity = struct.pack('>HHII', 0x63, 0, 0, 0) + b'\x00' * 8 + struct.pack('>I', 0)
        seeds.append(list_identity)
        
        # RegisterSession request
        register_session = struct.pack('>HHII', 0x65, 4, 0, 0) + b'\x00' * 8 + struct.pack('>HH', 1, 0)
        seeds.append(register_session)
        
        # SendRRData request
        send_rr_data = (struct.pack('>HHII', 0x6F, 0, 0, 0) + b'\x00' * 8 +
                       struct.pack('>HH', 2, 0) +  # 2 CPF items
                       struct.pack('>HI', 0, 0) +   # Address item
                       struct.pack('>HI', 0xB2, 0) + b'\x00' * 8)  # Data item
        seeds.append(send_rr_data)
        
        return seeds
    
    def _generate_siemens_s7_seeds(self, config: Dict[str, Any]) -> List[bytes]:
        """Generate Siemens S7 seed cases"""
        seeds = []
        
        # Connection request
        connect_request = (b'\x11' +  # ROSCTR: Job
                          b'\x00' +  # Reserved
                          struct.pack('>H', 1) +  # PDU Reference
                          struct.pack('>H', 0) +  # Parameter Length
                          struct.pack('>H', 0) +  # Data Length
                          b'\x00' * 8)  # Parameters and data
        seeds.append(connect_request)
        
        # Read request
        read_request = (b'\x11' +  # ROSCTR: Job
                       b'\x00' +  # Reserved
                       struct.pack('>H', 2) +  # PDU Reference
                       struct.pack('>H', 10) +  # Parameter Length
                       struct.pack('>H', 0) +  # Data Length
                       b'\x00' * 10)  # Parameters
        seeds.append(read_request)
        
        # Write request
        write_request = (b'\x11' +  # ROSCTR: Job
                        b'\x00' +  # Reserved
                        struct.pack('>H', 3) +  # PDU Reference
                        struct.pack('>H', 10) +  # Parameter Length
                        struct.pack('>H', 4) +  # Data Length
                        b'\x00' * 10 +  # Parameters
                        b'\x00' * 4)  # Data
        seeds.append(write_request)
        
        return seeds
    
    def generate_test_cases(self, protocol: str, count: int, 
                           priority: TestCasePriority = TestCasePriority.MEDIUM,
                           mutation_strategy: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate test cases"""
        test_cases = []
        
        if protocol not in self.seed_cases:
            self.logger.warning(f"Protocol {protocol} has no seed cases")
            return test_cases
        
        seeds = self.seed_cases[protocol]
        
        for i in range(count):
            # Choose seed
            seed = random.choice(seeds)
            
            # Generate mutated case
            if mutation_strategy:
                mutated_case = self._mutate_with_strategy(seed, protocol, mutation_strategy)
            else:
                mutated_case = self._mutate_randomly(seed, protocol)
            
            test_case = {
                'id': f"{protocol}_test_{i}",
                'protocol': protocol,
                'original_seed': seed,
                'mutated_data': mutated_case,
                'priority': priority,
                'mutation_history': self._get_mutation_history(),
                'generation_strategy': mutation_strategy or 'random'
            }
            
            test_cases.append(test_case)
        
        return test_cases
    
    def _mutate_with_strategy(self, seed: bytes, protocol: str, strategy: str) -> bytes:
        """Mutate seed using a specific strategy"""
        if strategy == 'boundary_values':
            return self._mutate_boundary_values(seed, protocol)
        elif strategy == 'format_specific':
            return self._mutate_format_specific(seed, protocol)
        elif strategy == 'protocol_semantic':
            return self._mutate_protocol_semantic(seed, protocol)
        else:
            return self._mutate_randomly(seed, protocol)
    
    def _mutate_randomly(self, seed: bytes, protocol: str) -> bytes:
        """Randomly mutate seed"""
        mutated = bytearray(seed)
        
        # Apply random mutations
        num_mutations = random.randint(1, 5)
        
        for _ in range(num_mutations):
            mutation_type = random.choices(
                list(self.mutation_weights.keys()),
                weights=list(self.mutation_weights.values())
            )[0]
            
            mutated = self._apply_single_mutation(mutated, mutation_type, protocol)
        
        return bytes(mutated)
    
    def _apply_single_mutation(self, data: bytearray, mutation_type: str, protocol: str) -> bytearray:
        """Apply a single mutation operation"""
        if mutation_type == 'field_flipping' and data:
            # Randomly flip some bytes
            for i in range(min(10, len(data))):
                if random.random() < 0.3:
                    data[i] ^= 0xFF
                    
        elif mutation_type == 'field_deletion' and len(data) > 4:
            # Delete part of the data
            del_start = random.randint(0, len(data) - 1)
            del_end = min(len(data), del_start + random.randint(1, len(data) // 4))
            del data[del_start:del_end]
            
        elif mutation_type == 'field_duplication' and data:
            # Duplicate part of the data
            dup_start = random.randint(0, len(data) - 1)
            dup_end = min(len(data), dup_start + random.randint(1, len(data) // 4))
            duplicated = data[dup_start:dup_end]
            data.extend(duplicated)
            
        elif mutation_type == 'field_truncation' and len(data) > 4:
            # Truncate data
            new_length = random.randint(1, len(data) - 1)
            del data[new_length:]
            
        elif mutation_type == 'field_padding':
            # Add padding
            padding_length = random.randint(1, 100)
            padding = bytes([random.randint(0, 255) for _ in range(padding_length)])
            data.extend(padding)
            
        elif mutation_type == 'invalid_flag_injection' and data:
            # Inject invalid flags
            for i in range(min(5, len(data))):
                if random.random() < 0.2:
                    data[i] = 0xFF if random.random() < 0.5 else 0x00
                    
        elif mutation_type == 'fields_reordering' and len(data) > 2:
            # Reorder bytes
            idx1, idx2 = random.sample(range(len(data)), 2)
            data[idx1], data[idx2] = data[idx2], data[idx1]
            
        elif mutation_type == 'semantic_mutation' and data:
            # Semantic mutation - insert boundary values
            boundary_values = [0, 1, 0x7F, 0x80, 0xFF]
            for i in range(min(3, len(data))):
                if random.random() < 0.1:
                    data[i] = random.choice(boundary_values)
        
        return data
    
    def _mutate_boundary_values(self, seed: bytes, protocol: str) -> bytes:
        """Boundary value mutation"""
        mutated = bytearray(seed)
        
        # Insert boundary values at key positions
        boundary_positions = self._get_boundary_positions(protocol)
        
        for pos in boundary_positions:
            if pos < len(mutated):
                boundary_value = random.choice([0, 1, 0x7F, 0x80, 0xFF])
                mutated[pos] = boundary_value
        
        return bytes(mutated)
    
    def _mutate_format_specific(self, seed: bytes, protocol: str) -> bytes:
        """Format-specific mutation"""
        # Perform intelligent mutation based on protocol format
        if protocol == 'modbus_tcp' and len(seed) >= 8:
            mutated = bytearray(seed)
            
            # Mutate function code to invalid value
            if len(mutated) > 7:
                mutated[7] = random.choice([0, 0x80, 0xFF])
                
            # Mutate length field
            if len(mutated) > 5:
                mutated[4] = 0xFF  # set oversized length
                mutated[5] = 0xFF
                
            return bytes(mutated)
        
        return seed
    
    def _mutate_protocol_semantic(self, seed: bytes, protocol: str) -> bytes:
        """Protocol semantic mutation"""
            # Change the semantic meaning of the message
        if protocol == 'modbus_tcp' and len(seed) >= 8:
            mutated = bytearray(seed)
            
            # Change read operation to write or vice versa
            if len(mutated) > 7:
                func_code = mutated[7]
                if func_code in [1, 2, 3, 4]:  # read
                    mutated[7] = random.choice([5, 6, 15, 16])  # write
                elif func_code in [5, 6, 15, 16]:  # write
                    mutated[7] = random.choice([1, 2, 3, 4])  # read
            
            return bytes(mutated)
        
        return seed
    
    def _get_boundary_positions(self, protocol: str) -> List[int]:
        """Get key boundary positions for a protocol"""
        # Protocol-specific key field positions
        boundary_positions = {
            'modbus_tcp': [4, 5, 6, 7],  # length, Unit ID, function code
            'ethernet_ip': [0, 1, 2, 3, 8, 9, 10, 11],  # command, length, status
            'siemens_s7': [0, 4, 5, 6, 7]  # ROSCTR, parameter length, data length
        }
        
        return boundary_positions.get(protocol, [0])
    
    def _get_mutation_history(self) -> List[str]:
        """Get mutation history (simplified)"""
        return ['random_mutation']  # should record detailed mutation steps in practice
    
    def add_seed_case(self, protocol: str, test_case: bytes):
        """Add a new seed case"""
        if protocol not in self.seed_cases:
            self.seed_cases[protocol] = []
        
        self.seed_cases[protocol].append(test_case)
        self.logger.info(f"Added new seed case for protocol {protocol}, length: {len(test_case)}")
    
    def get_seed_statistics(self) -> Dict[str, Any]:
        """Get seed case statistics"""
        stats = {}
        
        for protocol, seeds in self.seed_cases.items():
            stats[protocol] = {
                'seed_count': len(seeds),
                'avg_length': sum(len(seed) for seed in seeds) / len(seeds) if seeds else 0,
                'min_length': min(len(seed) for seed in seeds) if seeds else 0,
                'max_length': max(len(seed) for seed in seeds) if seeds else 0
            }
        
        return stats