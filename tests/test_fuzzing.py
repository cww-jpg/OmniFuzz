import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from fuzzing.mutation_engine import MutationEngine, MutationAction
from fuzzing.test_case_generator import TestCaseGenerator, TestCasePriority
from fuzzing.coverage_tracker import CoverageTracker, LLVMCoverageTracker

class TestMutationEngine(unittest.TestCase):

    def setUp(self):
        self.protocol_config = {
            'fields': {
                'function_code': {
                    'position': [0, 1],
                    'is_flag': True,
                    'is_numeric': True
                },
                'data': {
                    'position': [1, 5]
                }
            }
        }
        self.mutation_engine = MutationEngine(self.protocol_config)

    def test_mutation_actions(self):
        """Test mutation operations"""
        original_message = b'\x01\x02\x03\x04\x05'
        mutation_actions = {
            'function_code': 0,  # FIELD_FLIPPING
            'data': 1  # FIELD_DELETION
        }
        
        mutated_message = self.mutation_engine.mutate_protocol_message(
            original_message, mutation_actions
        )
        
        self.assertIsInstance(mutated_message, bytes)
        self.assertNotEqual(mutated_message, original_message)

    def test_specific_mutations(self):
        """Test specific mutation operations"""
        test_message = b'\x01\x02\x03'
        
        # Test field flipping
        flipped = self.mutation_engine._flip_field(bytearray(test_message), 'function_code')
        self.assertNotEqual(bytes(flipped), test_message)
        
        # Test field deletion
        deleted = self.mutation_engine._delete_field(bytearray(test_message), 'data')
        self.assertEqual(deleted[1:], b'\x00\x00')  # deleted field should be zeroed

class TestTestCaseGenerator(unittest.TestCase):

    def setUp(self):
        self.protocol_configs = {
            'modbus_tcp': {
                'fields': {
                    'function_code': {'valid_values': [1, 2, 3, 4, 5, 6]}
                }
            }
        }
        self.test_generator = TestCaseGenerator(self.protocol_configs)

    def test_test_case_generation(self):
        """Test test-case generation"""
        test_cases = self.test_generator.generate_test_cases(
            protocol='modbus_tcp',
            count=10,
            priority=TestCasePriority.HIGH
        )
        
        self.assertEqual(len(test_cases), 10)
        
        for test_case in test_cases:
            self.assertIn('protocol', test_case)
            self.assertIn('mutated_data', test_case)
            self.assertIn('priority', test_case)
            self.assertEqual(test_case['protocol'], 'modbus_tcp')
            self.assertEqual(test_case['priority'], TestCasePriority.HIGH)

    def test_seed_statistics(self):
        """Test seed statistics"""
        stats = self.test_generator.get_seed_statistics()
        
        self.assertIn('modbus_tcp', stats)
        self.assertIn('seed_count', stats['modbus_tcp'])

class TestCoverageTracker(unittest.TestCase):

    def setUp(self):
        self.coverage_tracker = CoverageTracker()

    def test_coverage_recording(self):
        """Test coverage recording"""
        basic_blocks = ['bb1', 'bb2', 'bb3']
        functions = ['func1', 'func2']
        execution_sequence = ['bb1', 'bb2', 'bb1', 'bb3']
        
        coverage_data = self.coverage_tracker.record_execution(
            basic_blocks, functions, execution_sequence
        )
        
        self.assertIn('new_blocks', coverage_data)
        self.assertIn('new_functions', coverage_data)
        self.assertIn('path_depth', coverage_data)

    def test_coverage_summary(self):
        """Test coverage summary"""
        # Set totals
        self.coverage_tracker.set_total_counts(100, 50)
        
        # Record coverage data
        self.coverage_tracker.record_execution(
            ['bb1', 'bb2'], ['func1'], ['bb1', 'bb2']
        )
        
        summary = self.coverage_tracker.get_coverage_summary()
        
        self.assertIn('basic_block_coverage', summary)
        self.assertIn('function_coverage', summary)
        self.assertIn('path_coverage', summary)

if __name__ == '__main__':
    unittest.main()