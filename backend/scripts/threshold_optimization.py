"""
Threshold Optimization Script

Analyzes precision/recall curves for different confidence thresholds and optimizes
thresholds based on business objectives (e.g., 95% precision for auto-send).

Usage:
    python threshold_optimization.py [--dataset PATH] [--objective OBJECTIVE] [--output PATH]
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from collections import defaultdict


class ThresholdOptimizer:
    """Optimizes decision thresholds based on business objectives."""

    def __init__(self, dataset_path: str):
        """
        Initialize ThresholdOptimizer.

        Args:
            dataset_path: Path to calibration_dataset.json
        """
        self.dataset_path = Path(dataset_path)
        self.data = self._load_dataset()

    def _load_dataset(self) -> Dict:
        """Load calibration dataset from JSON file."""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")

        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def calculate_metrics_at_threshold(self, threshold: float, samples: List[Dict] = None) -> Dict:
        """
        Calculate precision, recall, F1 at a given threshold.

        Args:
            threshold: Confidence threshold
            samples: List of samples (uses all if None)

        Returns:
            Dictionary with metrics
        """
        if samples is None:
            samples = self.data.get('samples', [])

        if not samples:
            return {'error': 'No samples provided'}

        # Predictions above threshold
        above_threshold = [s for s in samples if s.get('confidence', 0) >= threshold]
        correct_above = [s for s in above_threshold if s.get('correct', False)]

        # All correct predictions
        all_correct = [s for s in samples if s.get('correct', False)]

        # Calculate metrics
        tp = len(correct_above)  # True positives (correct predictions above threshold)
        fp = len(above_threshold) - tp  # False positives (wrong predictions above threshold)
        fn = len(all_correct) - tp  # False negatives (correct predictions below threshold)

        precision = tp / len(above_threshold) if above_threshold else 0
        recall = tp / len(all_correct) if all_correct else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        auto_send_rate = len(above_threshold) / len(samples) if samples else 0

        return {
            'threshold': round(threshold, 3),
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1, 4),
            'auto_send_rate': round(auto_send_rate, 4),
            'samples_above_threshold': len(above_threshold),
            'correct_above_threshold': tp,
            'total_samples': len(samples)
        }

    def generate_precision_recall_curve(self, n_points: int = 20) -> List[Dict]:
        """
        Generate precision-recall curve data.

        Args:
            n_points: Number of threshold points to evaluate

        Returns:
            List of metrics at different thresholds
        """
        thresholds = np.linspace(0, 1, n_points)
        curve_data = []

        for threshold in thresholds:
            metrics = self.calculate_metrics_at_threshold(threshold)
            curve_data.append(metrics)

        return curve_data

    def optimize_for_precision(self, target_precision: float = 0.95) -> Dict:
        """
        Find optimal threshold to achieve target precision.

        Args:
            target_precision: Target precision (e.g., 0.95 for 95%)

        Returns:
            Optimal threshold and metrics
        """
        thresholds = np.linspace(0, 1, 100)
        best_threshold = None
        best_metrics = None

        for threshold in thresholds:
            metrics = self.calculate_metrics_at_threshold(threshold)
            precision = metrics['precision']

            # Find lowest threshold that meets precision target
            if precision >= target_precision:
                if best_threshold is None or threshold < best_threshold:
                    best_threshold = threshold
                    best_metrics = metrics

        if best_threshold is None:
            # If target not achievable, return threshold with highest precision
            all_metrics = [self.calculate_metrics_at_threshold(t) for t in thresholds]
            best_metrics = max(all_metrics, key=lambda x: x['precision'])
            best_threshold = best_metrics['threshold']

        return {
            'objective': f'precision >= {target_precision}',
            'optimal_threshold': round(best_threshold, 3),
            'achieved_precision': best_metrics['precision'],
            'recall': best_metrics['recall'],
            'f1_score': best_metrics['f1_score'],
            'auto_send_rate': best_metrics['auto_send_rate']
        }

    def optimize_for_f1(self) -> Dict:
        """
        Find threshold that maximizes F1 score.

        Returns:
            Optimal threshold and metrics
        """
        thresholds = np.linspace(0, 1, 100)
        all_metrics = [self.calculate_metrics_at_threshold(t) for t in thresholds]
        best_metrics = max(all_metrics, key=lambda x: x['f1_score'])

        return {
            'objective': 'maximize F1 score',
            'optimal_threshold': best_metrics['threshold'],
            'precision': best_metrics['precision'],
            'recall': best_metrics['recall'],
            'f1_score': best_metrics['f1_score'],
            'auto_send_rate': best_metrics['auto_send_rate']
        }

    def optimize_for_auto_send_rate(self, target_rate: float = 0.50) -> Dict:
        """
        Find threshold to achieve target auto-send rate while maximizing precision.

        Args:
            target_rate: Target auto-send rate (e.g., 0.50 for 50%)

        Returns:
            Optimal threshold and metrics
        """
        thresholds = np.linspace(0, 1, 100)
        best_threshold = None
        best_metrics = None
        min_diff = float('inf')

        for threshold in thresholds:
            metrics = self.calculate_metrics_at_threshold(threshold)
            rate_diff = abs(metrics['auto_send_rate'] - target_rate)

            if rate_diff < min_diff:
                min_diff = rate_diff
                best_threshold = threshold
                best_metrics = metrics

        return {
            'objective': f'auto_send_rate ≈ {target_rate}',
            'optimal_threshold': best_metrics['threshold'],
            'achieved_auto_send_rate': best_metrics['auto_send_rate'],
            'precision': best_metrics['precision'],
            'recall': best_metrics['recall'],
            'f1_score': best_metrics['f1_score']
        }

    def optimize_by_category(self, objective: str = 'precision', target: float = 0.95) -> Dict:
        """
        Optimize thresholds per category.

        Args:
            objective: 'precision', 'f1', or 'auto_send_rate'
            target: Target value for the objective

        Returns:
            Dictionary with per-category optimal thresholds
        """
        samples = self.data.get('samples', [])
        category_samples = defaultdict(list)

        for sample in samples:
            category = sample.get('predicted_category', 'unknown')
            category_samples[category].append(sample)

        results = {}
        for category, cat_samples in category_samples.items():
            if objective == 'precision':
                result = self._optimize_category_precision(cat_samples, target)
            elif objective == 'f1':
                result = self._optimize_category_f1(cat_samples)
            elif objective == 'auto_send_rate':
                result = self._optimize_category_auto_send_rate(cat_samples, target)
            else:
                result = {'error': f'Unknown objective: {objective}'}

            results[category] = result

        return results

    def _optimize_category_precision(self, samples: List[Dict], target: float) -> Dict:
        """Optimize threshold for precision target on specific category."""
        thresholds = np.linspace(0, 1, 100)
        best_threshold = None
        best_metrics = None

        for threshold in thresholds:
            metrics = self.calculate_metrics_at_threshold(threshold, samples)
            if metrics['precision'] >= target:
                if best_threshold is None or threshold < best_threshold:
                    best_threshold = threshold
                    best_metrics = metrics

        if best_threshold is None:
            all_metrics = [self.calculate_metrics_at_threshold(t, samples) for t in thresholds]
            best_metrics = max(all_metrics, key=lambda x: x['precision'])

        return best_metrics

    def _optimize_category_f1(self, samples: List[Dict]) -> Dict:
        """Optimize threshold for F1 score on specific category."""
        thresholds = np.linspace(0, 1, 100)
        all_metrics = [self.calculate_metrics_at_threshold(t, samples) for t in thresholds]
        return max(all_metrics, key=lambda x: x['f1_score'])

    def _optimize_category_auto_send_rate(self, samples: List[Dict], target: float) -> Dict:
        """Optimize threshold for auto-send rate on specific category."""
        thresholds = np.linspace(0, 1, 100)
        best_metrics = None
        min_diff = float('inf')

        for threshold in thresholds:
            metrics = self.calculate_metrics_at_threshold(threshold, samples)
            rate_diff = abs(metrics['auto_send_rate'] - target)
            if rate_diff < min_diff:
                min_diff = rate_diff
                best_metrics = metrics

        return best_metrics

    def generate_optimization_report(self, output_path: str = None) -> Dict:
        """
        Generate comprehensive threshold optimization report.

        Args:
            output_path: Optional path to save report JSON

        Returns:
            Complete optimization report
        """
        report = {
            'dataset_info': self.data.get('metadata', {}),
            'precision_recall_curve': self.generate_precision_recall_curve(),
            'optimization_strategies': {
                'high_precision': self.optimize_for_precision(0.95),
                'balanced_f1': self.optimize_for_f1(),
                'moderate_auto_send': self.optimize_for_auto_send_rate(0.50)
            },
            'category_specific_thresholds': self.optimize_by_category('precision', 0.90)
        }

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"Report saved to: {output_path}")

        return report

    def plot_precision_recall_curve(self, output_path: str = None):
        """
        Plot precision-recall curve.

        Args:
            output_path: Path to save plot image
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Warning: matplotlib not installed. Skipping plot generation.")
            return

        curve_data = self.generate_precision_recall_curve(50)

        thresholds = [d['threshold'] for d in curve_data]
        precisions = [d['precision'] for d in curve_data]
        recalls = [d['recall'] for d in curve_data]
        f1_scores = [d['f1_score'] for d in curve_data]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Precision-Recall curve
        ax1.plot(recalls, precisions, 'b-', linewidth=2, label='PR Curve')
        ax1.set_xlabel('Recall')
        ax1.set_ylabel('Precision')
        ax1.set_title('Precision-Recall Curve')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # Metrics vs Threshold
        ax2.plot(thresholds, precisions, 'b-', label='Precision', linewidth=2)
        ax2.plot(thresholds, recalls, 'r-', label='Recall', linewidth=2)
        ax2.plot(thresholds, f1_scores, 'g-', label='F1 Score', linewidth=2)
        ax2.set_xlabel('Confidence Threshold')
        ax2.set_ylabel('Score')
        ax2.set_title('Metrics vs Threshold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Plot saved to: {output_path}")
        else:
            plt.show()


def main():
    parser = argparse.ArgumentParser(description='Optimize confidence thresholds')
    parser.add_argument(
        '--dataset',
        default='../data/calibration_dataset.json',
        help='Path to calibration dataset'
    )
    parser.add_argument(
        '--objective',
        choices=['precision', 'f1', 'auto_send_rate'],
        default='precision',
        help='Optimization objective'
    )
    parser.add_argument(
        '--target',
        type=float,
        default=0.95,
        help='Target value for objective (e.g., 0.95 for 95%% precision)'
    )
    parser.add_argument(
        '--output',
        default='../reports/threshold_optimization.json',
        help='Path to save report'
    )
    parser.add_argument(
        '--plot',
        action='store_true',
        help='Generate precision-recall curve plot'
    )
    parser.add_argument(
        '--plot-output',
        default='../reports/precision_recall_curve.png',
        help='Path to save plot'
    )

    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent
    dataset_path = script_dir / args.dataset
    output_path = script_dir / args.output

    print(f"Loading dataset from: {dataset_path}")
    optimizer = ThresholdOptimizer(dataset_path)

    print("\n=== Threshold Optimization ===\n")
    report = optimizer.generate_optimization_report(output_path)

    # Print optimization strategies
    strategies = report['optimization_strategies']

    print("High Precision Strategy (95% precision):")
    hp = strategies['high_precision']
    print(f"  Threshold: {hp['optimal_threshold']}")
    print(f"  Precision: {hp['achieved_precision']:.3f}")
    print(f"  Recall: {hp['recall']:.3f}")
    print(f"  Auto-send Rate: {hp['auto_send_rate']:.1%}")

    print("\nBalanced F1 Strategy:")
    bf = strategies['balanced_f1']
    print(f"  Threshold: {bf['optimal_threshold']}")
    print(f"  Precision: {bf['precision']:.3f}")
    print(f"  Recall: {bf['recall']:.3f}")
    print(f"  F1 Score: {bf['f1_score']:.3f}")

    print("\nModerate Auto-Send Strategy (50% rate):")
    mas = strategies['moderate_auto_send']
    print(f"  Threshold: {mas['optimal_threshold']}")
    print(f"  Precision: {mas['precision']:.3f}")
    print(f"  Auto-send Rate: {mas['achieved_auto_send_rate']:.1%}")

    print("\n=== Category-Specific Thresholds ===\n")
    for category, metrics in report['category_specific_thresholds'].items():
        print(f"{category}:")
        print(f"  Optimal Threshold: {metrics['threshold']}")
        print(f"  Precision: {metrics['precision']:.3f}")
        print(f"  Samples: {metrics['total_samples']}")

    if args.plot:
        plot_path = script_dir / args.plot_output
        print(f"\nGenerating precision-recall curve...")
        optimizer.plot_precision_recall_curve(plot_path)


if __name__ == '__main__':
    main()
