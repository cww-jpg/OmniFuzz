#!/usr/bin/env python3
"""
OmniFuzz performance evaluation script
Compare against baseline methods
"""

import torch
import yaml
import argparse
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

from src.evaluation.metrics_calculator import MetricsCalculator
from src.evaluation.baseline_comparison import BaselineComparator
from src.evaluation.vulnerability_analyzer import VulnerabilityAnalyzer

def evaluate_omnifuzz_performance():
    """Evaluate OmniFuzz performance"""
    
    parser = argparse.ArgumentParser(description='OmniFuzz performance evaluation')
    parser.add_argument('--config', type=str, default='config/default_config.yaml')
    parser.add_argument('--models_dir', type=str, default='models/')
    parser.add_argument('--output_dir', type=str, default='results/')
    parser.add_argument('--baselines', nargs='+', 
                       default=['Sulley', 'AFL', 'AFL++', 'Peach', 'SeqFuzzer', 
                               'DeepFuzz', 'DQNFuzzer', 'Q-Learning-Fuzzer'])
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    try:
        logger.info("Start performance evaluation...")
        
        # Initialize evaluation components
        metrics_calculator = MetricsCalculator()
        baseline_comparator = BaselineComparator(args.baselines)
        vulnerability_analyzer = VulnerabilityAnalyzer()
        
        # Evaluation metrics
        evaluation_metrics = [
            'time_to_first_attack',
            'effective_recognition_rate', 
            'dropped_cases_ratio',
            'critical_vulnerabilities',
            'total_vulnerabilities',
            'code_coverage'
        ]
        
        # Run evaluation
        results = {}
        
        logger.info("Evaluating OmniFuzz...")
        omnifuzz_results = metrics_calculator.evaluate_omnifuzz(
            models_dir=args.models_dir,
            protocols=config['protocols'].keys(),
            duration=1800  # 30 minutes
        )
        results['OmniFuzz'] = omnifuzz_results
        
        # Evaluate baselines
        for baseline in args.baselines:
            logger.info(f"Evaluating {baseline}...")
            baseline_results = baseline_comparator.evaluate_baseline(
                baseline_name=baseline,
                protocols=config['protocols'].keys(),
                duration=1800
            )
            results[baseline] = baseline_results
        
        # Generate comparison report
        comparison_report = baseline_comparator.generate_comparison_report(results)
        
        # Save results
        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save detailed results
        results_df = pd.DataFrame.from_dict(results, orient='index')
        results_df.to_csv(output_path / 'detailed_results.csv')
        
        # Save comparison report
        with open(output_path / 'comparison_report.md', 'w') as f:
            f.write(comparison_report)
        
        # Generate charts
        baseline_comparator.generate_performance_charts(results, output_path)
        
        logger.info("Performance evaluation completed!")
        logger.info(f"Results saved to: {args.output_dir}")
        
        # Print key metrics
        print("\n=== Key metrics comparison ===")
        for metric in evaluation_metrics:
            print(f"\n{metric.replace('_', ' ').title()}:")
            for method, result in results.items():
                if metric in result:
                    print(f"  {method:15}: {result[metric]}")
        
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        raise

if __name__ == "__main__":
    evaluate_omnifuzz_performance()