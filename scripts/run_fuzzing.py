#!/usr/bin/env python3
"""
OmniFuzz fuzzing runner script
Run concurrent multi-protocol fuzzing with trained models
"""

import torch
import yaml
import argparse
import logging
import time
from pathlib import Path
from typing import Dict, List, Any

from src.core.agent_array import AgentArray
from src.core.value_network import ValueNetwork
from src.environment.power_iot_env import PowerIoTEnvironment
from src.fuzzing.mutation_engine import MutationEngine
from src.fuzzing.coverage_tracker import CoverageTracker
from src.utils.monitoring import ResourceMonitor

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('omnifuzz_fuzzing.log'),
            logging.StreamHandler()
        ]
    )

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def load_trained_models(models_dir: str, protocols: List[str], 
                       config: Dict[str, Any], device: torch.device) -> Dict[str, AgentArray]:
    """Load trained models"""
    agent_arrays = {}
    models_path = Path(models_dir)
    
    for protocol in protocols:
        protocol_path = models_path / protocol
        
        if not protocol_path.exists():
            logging.warning(f"Model directory for protocol {protocol} does not exist: {protocol_path}")
            continue
            
        # Create shared value network
        state_dim = config['protocols'][protocol].get('state_dim', 1000)
        action_dim = config['protocols'][protocol].get('action_dim', 8)
        shared_value_network = ValueNetwork(
            state_dim=state_dim,
            action_dim=action_dim
        ).to(device)
        
        # Load value network
        value_net_path = protocol_path / "value_network.pth"
        if value_net_path.exists():
            shared_value_network.load_state_dict(torch.load(value_net_path))
        
        # Create agent array
        protocol_config = config['protocols'][protocol]
        agent_array = AgentArray(
            protocol_name=protocol,
            field_config=protocol_config['fields'],
            shared_value_network=shared_value_network,
            device=device
        )
        
        # Load each agent's policy network
        for agent in agent_array.agents:
            model_path = protocol_path / f"agent_{agent.field_name}.pth"
            if model_path.exists():
                agent.policy_network.load_state_dict(torch.load(model_path))
            else:
                logging.warning(f"Model file for agent {agent.field_name} does not exist: {model_path}")
        
        agent_arrays[protocol] = agent_array
        logging.info(f"Loaded models for protocol {protocol} with {len(agent_array.agents)} agents")
    
    return agent_arrays

def main():
    parser = argparse.ArgumentParser(description='OmniFuzz fuzzing runner')
    parser.add_argument('--models_dir', type=str, default='models/',
                       help='Directory of trained models')
    parser.add_argument('--config', type=str, default='config/default_config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--protocols', nargs='+', 
                       default=['modbus_tcp', 'ethernet_ip', 'siemens_s7'],
                       help='List of protocols to test')
    parser.add_argument('--duration', type=int, default=3600,
                       help='Test duration (seconds)')
    parser.add_argument('--output_dir', type=str, default='fuzzing_results/',
                       help='Output directory')
    parser.add_argument('--device', type=str, default='cuda',
                       help='Device (cuda/cpu)')
    
    args = parser.parse_args()
    
    # Configure logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load config
    config = load_config(args.config)
    logger.info(f"Loaded config file: {args.config}")
    
    # Select device
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Start resource monitoring
        resource_monitor = ResourceMonitor(interval=5.0)
        resource_monitor.start_monitoring()
        
        # Load trained models
        logger.info("Loading trained models...")
        agent_arrays = load_trained_models(
            args.models_dir, args.protocols, config, device
        )
        
        if not agent_arrays:
            logger.error("No models loaded. Please check the model directory")
            return
        
        # Create environment
        environment = PowerIoTEnvironment(
            protocols=args.protocols,
            config=config
        )
        
        # Create coverage tracker
        coverage_tracker = CoverageTracker()
        
        # Create mutation engines
        mutation_engines = {}
        for protocol in args.protocols:
            protocol_config = config['protocols'][protocol]
            mutation_engines[protocol] = MutationEngine(protocol_config)
        
        logger.info(f"Start fuzzing, duration: {args.duration} seconds")
        start_time = time.time()
        
        # Main fuzzing loop
        test_cases_sent = 0
        vulnerabilities_found = []
        protocol_stats = {protocol: {'messages_sent': 0, 'crashes': 0} 
                         for protocol in args.protocols}
        
        while time.time() - start_time < args.duration:
            # Reset environment
            observations = environment.reset()
            
            # Run one fuzzing episode
            episode_vulnerabilities = run_fuzzing_episode(
                agent_arrays, environment, mutation_engines, 
                observations, coverage_tracker, config
            )
            
            vulnerabilities_found.extend(episode_vulnerabilities)
            test_cases_sent += sum(stats['messages_sent'] for stats in protocol_stats.values())
            
            # Log progress
            elapsed = time.time() - start_time
            if int(elapsed) % 60 == 0:  # once per minute
                logger.info(
                    f"Progress: {elapsed:.0f}/{args.duration}s | "
                    f"Test cases: {test_cases_sent} | "
                    f"Vulnerabilities: {len(vulnerabilities_found)}"
                )
        
        # Stop resource monitoring
        resource_monitor.stop_monitoring()
        
        # Generate report
        generate_fuzzing_report(
            output_dir, vulnerabilities_found, protocol_stats,
            coverage_tracker, resource_monitor, args.duration
        )
        
        logger.info(f"Fuzzing completed! Results saved to: {args.output_dir}")
        
    except Exception as e:
        logger.error(f"Error during fuzzing: {e}")
        raise

def run_fuzzing_episode(agent_arrays, environment, mutation_engines, 
                       observations, coverage_tracker, config) -> List[Dict]:
    """Run one fuzzing episode"""
    vulnerabilities = []
    step_count = 0
    max_steps = config.get('fuzzing', {}).get('max_steps_per_episode', 100)
    
    while step_count < max_steps:
        # Agents select actions
        actions = {}
        for protocol, agent_array in agent_arrays.items():
            if protocol in observations:
                protocol_actions = agent_array.select_actions(observations[protocol])
                actions[protocol] = protocol_actions
        
        # Step environment
        next_observations, reward, done, info = environment.step(actions)
        
        # Record vulnerabilities
        if 'vulnerabilities_found' in info:
            vulnerabilities.extend(info['vulnerabilities_found'])
        
        # Record coverage
        if 'coverage_data' in info:
            coverage_tracker.record_execution(
                basic_blocks=info['coverage_data'].get('basic_blocks', []),
                functions=info['coverage_data'].get('functions', []),
                execution_sequence=info['coverage_data'].get('execution_sequence', [])
            )
        
        observations = next_observations
        step_count += 1
        
        if done:
            break
    
    return vulnerabilities

def generate_fuzzing_report(output_dir: Path, vulnerabilities: List[Dict], 
                          protocol_stats: Dict, coverage_tracker: CoverageTracker,
                          resource_monitor: ResourceMonitor, duration: int):
    """Generate fuzzing report"""
    
    # Vulnerability statistics
    vulnerability_stats = {}
    for vuln in vulnerabilities:
        vuln_type = vuln.get('type', 'unknown')
        severity = vuln.get('severity', 'unknown')
        
        if vuln_type not in vulnerability_stats:
            vulnerability_stats[vuln_type] = {'count': 0, 'severities': {}}
        
        vulnerability_stats[vuln_type]['count'] += 1
        vulnerability_stats[vuln_type]['severities'][severity] = \
            vulnerability_stats[vuln_type]['severities'].get(severity, 0) + 1
    
    # Build report
    report = [
        "OmniFuzz Fuzzing Report",
        "=" * 50,
        f"Test duration: {duration} seconds",
        f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total test cases: {sum(stats['messages_sent'] for stats in protocol_stats.values())}",
        f"Total vulnerabilities: {len(vulnerabilities)}",
        "",
        "Protocol statistics:"
    ]
    
    for protocol, stats in protocol_stats.items():
        crash_rate = stats['crashes'] / max(1, stats['messages_sent']) * 100
        report.append(
            f"  {protocol}: {stats['messages_sent']} messages, "
            f"{stats['crashes']} crashes ({crash_rate:.2f}%)"
        )
    
    report.append("\nVulnerability statistics:")
    for vuln_type, stats in vulnerability_stats.items():
        report.append(f"  {vuln_type}: {stats['count']}")
        for severity, count in stats['severities'].items():
            report.append(f"    {severity}: {count}")
    
    # Coverage report
    coverage_summary = coverage_tracker.get_coverage_summary()
    if 'error' not in coverage_summary:
        report.extend([
            "",
            "Code coverage:",
            f"  Basic block coverage: {coverage_summary['basic_block_coverage']['percentage']:.2f}%",
            f"  Function coverage: {coverage_summary['function_coverage']['percentage']:.2f}%",
            f"  Unique paths: {coverage_summary['path_coverage']['unique_paths']}"
        ])
    
    # Resource usage report
    resource_report = resource_monitor.generate_report()
    report.extend(["", "Resource usage:", resource_report])
    
    # Save report
    report_path = output_dir / "fuzzing_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    # Save vulnerability details
    if vulnerabilities:
        vuln_details = []
        for i, vuln in enumerate(vulnerabilities, 1):
            vuln_details.append(f"Vulnerability #{i}:")
            for key, value in vuln.items():
                vuln_details.append(f"  {key}: {value}")
            vuln_details.append("")
        
        vuln_path = output_dir / "vulnerability_details.txt"
        with open(vuln_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(vuln_details))
    
    logging.info(f"Report generated: {report_path}")

if __name__ == "__main__":
    main()