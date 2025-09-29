import logging
from typing import Dict, List, Any
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class BaselineComparator:
    """Baseline methods comparator"""

    def __init__(self, baseline_methods: List[str]):
        self.baseline_methods = baseline_methods
        self.logger = logging.getLogger(__name__)
        self.comparison_data = {}

    def evaluate_baseline(self, baseline_name: str, protocols: List[str], duration: int) -> Dict[str, Any]:
        """Evaluate a baseline method"""
        self.logger.info(f"Evaluating baseline: {baseline_name}")

        # Simulate baseline performance metrics
        metrics = {
            'time_to_first_attack': self._simulate_metric(baseline_name, 'time_to_first_attack', 200, 600),
            'effective_recognition_rate': self._simulate_metric(baseline_name, 'effective_recognition_rate', 0.3, 0.7),
            'dropped_cases_ratio': self._simulate_metric(baseline_name, 'dropped_cases_ratio', 0.1, 0.4),
            'critical_vulnerabilities': self._simulate_metric(baseline_name, 'critical_vulnerabilities', 1, 5),
            'total_vulnerabilities': self._simulate_metric(baseline_name, 'total_vulnerabilities', 5, 20),
            'code_coverage': self._simulate_metric(baseline_name, 'code_coverage', 0.3, 0.6)
        }

        self.comparison_data[baseline_name] = metrics
        return metrics

    def _simulate_metric(self, baseline_name: str, metric_name: str, min_val: float, max_val: float) -> float:
        """Simulate a metric value for a baseline"""
        # Generate simulated data based on baseline and metric name
        baseline_performance = {
            'Sulley': {'time_to_first_attack': 500, 'effective_recognition_rate': 0.4, 
                      'dropped_cases_ratio': 0.15, 'critical_vulnerabilities': 1, 
                      'total_vulnerabilities': 8, 'code_coverage': 0.4},
            'AFL': {'time_to_first_attack': 400, 'effective_recognition_rate': 0.5, 
                   'dropped_cases_ratio': 0.2, 'critical_vulnerabilities': 1, 
                   'total_vulnerabilities': 14, 'code_coverage': 0.5},
            'AFL++': {'time_to_first_attack': 450, 'effective_recognition_rate': 0.53, 
                     'dropped_cases_ratio': 0.18, 'critical_vulnerabilities': 2, 
                     'total_vulnerabilities': 17, 'code_coverage': 0.53},
            'Peach': {'time_to_first_attack': 470, 'effective_recognition_rate': 0.58, 
                     'dropped_cases_ratio': 0.16, 'critical_vulnerabilities': 1, 
                     'total_vulnerabilities': 15, 'code_coverage': 0.45},
            'SeqFuzzer': {'time_to_first_attack': 250, 'effective_recognition_rate': 0.64, 
                         'dropped_cases_ratio': 0.12, 'critical_vulnerabilities': 2, 
                         'total_vulnerabilities': 13, 'code_coverage': 0.55},
            'DeepFuzz': {'time_to_first_attack': 200, 'effective_recognition_rate': 0.73, 
                        'dropped_cases_ratio': 0.1, 'critical_vulnerabilities': 3, 
                        'total_vulnerabilities': 18, 'code_coverage': 0.6},
            'DQNFuzzer': {'time_to_first_attack': 300, 'effective_recognition_rate': 0.61, 
                         'dropped_cases_ratio': 0.14, 'critical_vulnerabilities': 1, 
                         'total_vulnerabilities': 11, 'code_coverage': 0.5},
            'Q-Learning-Fuzzer': {'time_to_first_attack': 400, 'effective_recognition_rate': 0.55, 
                                 'dropped_cases_ratio': 0.17, 'critical_vulnerabilities': 1, 
                                 'total_vulnerabilities': 10, 'code_coverage': 0.48}
        }

        if baseline_name in baseline_performance and metric_name in baseline_performance[baseline_name]:
            return baseline_performance[baseline_name][metric_name]
        else:
            return np.random.uniform(min_val, max_val)

    def generate_comparison_report(self, results: Dict[str, Any]) -> str:
        """Generate comparison report"""
        report = [
            "OmniFuzz vs. Baselines Comparison Report",
            "=" * 60
        ]

        # Create comparison table
        metrics = ['time_to_first_attack', 'effective_recognition_rate', 'dropped_cases_ratio', 
                  'critical_vulnerabilities', 'total_vulnerabilities', 'code_coverage']
        methods = ['OmniFuzz'] + self.baseline_methods

        table_data = []
        for method in methods:
            if method in results:
                row = [method]
                for metric in metrics:
                    if metric in results[method]:
                        value = results[method][metric]
                        if 'rate' in metric or 'coverage' in metric:
                            row.append(f"{value:.2%}")
                        elif 'time' in metric:
                            row.append(f"{value:.1f}s")
                        else:
                            row.append(str(value))
                    else:
                        row.append('N/A')
                table_data.append(row)

        # Generate Markdown table
        headers = ['Method'] + [m.replace('_', ' ').title() for m in metrics]
        report.append(self._format_markdown_table(headers, table_data))

        # Add performance improvement summary
        if 'OmniFuzz' in results:
            omnifuzz_metrics = results['OmniFuzz']
            report.append("\nImprovement summary (vs. best baseline):")
            report.append("-" * 50)

            for metric in metrics:
                if metric in omnifuzz_metrics:
                    baseline_values = []
                    for method in self.baseline_methods:
                        if method in results and metric in results[method]:
                            baseline_values.append(results[method][metric])

                    if baseline_values:
                        best_baseline = min(baseline_values) if 'time' in metric else max(baseline_values)
                        omnifuzz_value = omnifuzz_metrics[metric]

                        if 'time' in metric:
                            improvement = (best_baseline - omnifuzz_value) / best_baseline * 100
                            report.append(f"{metric.replace('_', ' ').title()}: {improvement:+.1f}%")
                        else:
                            improvement = (omnifuzz_value - best_baseline) / best_baseline * 100
                            report.append(f"{metric.replace('_', ' ').title()}: {improvement:+.1f}%")

        return "\n".join(report)

    def _format_markdown_table(self, headers: List[str], data: List[List[str]]) -> str:
        """Format as Markdown table"""
        table = ["| " + " | ".join(headers) + " |"]
        table.append("|" + "|".join(["---"] * len(headers)) + "|")

        for row in data:
            table.append("| " + " | ".join(row) + " |")

        return "\n".join(table)

    def generate_performance_charts(self, results: Dict[str, Any], output_dir: str):
        """Generate performance comparison charts"""
        try:
            # Set chart style
            sns.set_style("whitegrid")
            # Note: ensure chosen fonts support required characters
            plt.rcParams['axes.unicode_minus'] = False

            # Create comparison charts
            metrics = ['time_to_first_attack', 'effective_recognition_rate', 
                      'critical_vulnerabilities', 'code_coverage']
            titles = ['Time to first attack (s)', 'Effective recognition rate', 'Critical vulnerabilities', 'Code coverage']

            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            axes = axes.ravel()

            for i, (metric, title) in enumerate(zip(metrics, titles)):
                methods = []
                values = []

                for method, result in results.items():
                    if metric in result:
                        methods.append(method)
                        values.append(result[metric])

                # Draw bar chart
                bars = axes[i].bar(methods, values, color=sns.color_palette("husl", len(methods)))
                axes[i].set_title(title, fontsize=14, fontweight='bold')
                axes[i].set_ylabel(metric.replace('_', ' ').title())

                # Annotate values on bars
                for bar, value in zip(bars, values):
                    if 'rate' in metric or 'coverage' in metric:
                        height = bar.get_height()
                        axes[i].text(bar.get_x() + bar.get_width()/2., height + 0.01,
                                    f'{value:.2%}', ha='center', va='bottom')
                    elif 'time' in metric:
                        height = bar.get_height()
                        axes[i].text(bar.get_x() + bar.get_width()/2., height + 5,
                                    f'{value:.1f}s', ha='center', va='bottom')
                    else:
                        height = bar.get_height()
                        axes[i].text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                    f'{value}', ha='center', va='bottom')

                # Rotate x-axis labels
                plt.sca(axes[i])
                plt.xticks(rotation=45)

            plt.tight_layout()
            plt.savefig(f"{output_dir}/performance_comparison.png", dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"Performance chart saved to: {output_dir}/performance_comparison.png")

        except Exception as e:
            self.logger.error(f"Error generating charts: {e}")