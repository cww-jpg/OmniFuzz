#!/usr/bin/env python3
"""
OmniFuzz 性能评估脚本
与基线方法进行比较评估
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
    """评估OmniFuzz性能"""
    
    parser = argparse.ArgumentParser(description='OmniFuzz 性能评估')
    parser.add_argument('--config', type=str, default='config/default_config.yaml')
    parser.add_argument('--models_dir', type=str, default='models/')
    parser.add_argument('--output_dir', type=str, default='results/')
    parser.add_argument('--baselines', nargs='+', 
                       default=['Sulley', 'AFL', 'AFL++', 'Peach', 'SeqFuzzer', 
                               'DeepFuzz', 'DQNFuzzer', 'Q-Learning-Fuzzer'])
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 加载配置
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    try:
        logger.info("开始性能评估...")
        
        # 初始化评估组件
        metrics_calculator = MetricsCalculator()
        baseline_comparator = BaselineComparator(args.baselines)
        vulnerability_analyzer = VulnerabilityAnalyzer()
        
        # 评估指标
        evaluation_metrics = [
            'time_to_first_attack',
            'effective_recognition_rate', 
            'dropped_cases_ratio',
            'critical_vulnerabilities',
            'total_vulnerabilities',
            'code_coverage'
        ]
        
        # 运行评估
        results = {}
        
        logger.info("评估 OmniFuzz...")
        omnifuzz_results = metrics_calculator.evaluate_omnifuzz(
            models_dir=args.models_dir,
            protocols=config['protocols'].keys(),
            duration=1800  # 30分钟
        )
        results['OmniFuzz'] = omnifuzz_results
        
        # 评估基线方法
        for baseline in args.baselines:
            logger.info(f"评估 {baseline}...")
            baseline_results = baseline_comparator.evaluate_baseline(
                baseline_name=baseline,
                protocols=config['protocols'].keys(),
                duration=1800
            )
            results[baseline] = baseline_results
        
        # 生成比较报告
        comparison_report = baseline_comparator.generate_comparison_report(results)
        
        # 保存结果
        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 保存详细结果
        results_df = pd.DataFrame.from_dict(results, orient='index')
        results_df.to_csv(output_path / 'detailed_results.csv')
        
        # 保存比较报告
        with open(output_path / 'comparison_report.md', 'w') as f:
            f.write(comparison_report)
        
        # 生成可视化图表
        baseline_comparator.generate_performance_charts(results, output_path)
        
        logger.info("性能评估完成!")
        logger.info(f"结果保存在: {args.output_dir}")
        
        # 输出关键指标比较
        print("\n=== 关键性能指标比较 ===")
        for metric in evaluation_metrics:
            print(f"\n{metric.replace('_', ' ').title()}:")
            for method, result in results.items():
                if metric in result:
                    print(f"  {method:15}: {result[metric]}")
        
    except Exception as e:
        logger.error(f"评估过程中发生错误: {e}")
        raise

if __name__ == "__main__":
    evaluate_omnifuzz_performance()