"""
Calibration Analysis Script

Analyzes the calibration quality of confidence scores by comparing predicted
confidence with actual accuracy. Generates reliability diagrams and calibration metrics.

Usage:
    python calibration_analysis.py [--dataset PATH] [--output PATH] [--plot]
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from collections import defaultdict


class CalibrationAnalyzer:
    """Analyzes confidence score calibration quality."""

    def __init__(self, dataset_path: str):
        """
        Initialize CalibrationAnalyzer.

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

    def calculate_calibration_error(self, n_bins: int = 10) -> Dict:
        """
        Calculate Expected Calibration Error (ECE) and Maximum Calibration Error (MCE).

        Args:
            n_bins: Number of bins for calibration analysis

        Returns:
            Dictionary with ECE, MCE, and bin statistics
        """
        samples = self.data.get('samples', [])
        if not samples:
            return {'error': 'No samples in dataset'}

        # Create bins
        bin_edges = np.linspace(0, 1, n_bins + 1)
        bin_confidences = defaultdict(list)
        bin_accuracies = defaultdict(list)
        bin_counts = defaultdict(int)

        # Assign samples to bins
        for sample in samples:
            confidence = sample.get('confidence', 0)
            correct = sample.get('correct', False)

            # Find bin
            bin_idx = min(int(confidence * n_bins), n_bins - 1)

            bin_confidences[bin_idx].append(confidence)
            bin_accuracies[bin_idx].append(1.0 if correct else 0.0)
            bin_counts[bin_idx] += 1

        # Calculate calibration metrics
        total_samples = len(samples)
        ece = 0.0  # Expected Calibration Error
        mce = 0.0  # Maximum Calibration Error
        bin_stats = []

        for bin_idx in range(n_bins):
            if bin_idx not in bin_counts or bin_counts[bin_idx] == 0:
                continue

            avg_confidence = np.mean(bin_confidences[bin_idx])
            avg_accuracy = np.mean(bin_accuracies[bin_idx])
            count = bin_counts[bin_idx]

            calibration_error = abs(avg_confidence - avg_accuracy)
            ece += (count / total_samples) * calibration_error
            mce = max(mce, calibration_error)

            bin_stats.append({
                'bin_idx': bin_idx,
                'bin_range': f"{bin_edges[bin_idx]:.2f}-{bin_edges[bin_idx+1]:.2f}",
                'count': count,
                'avg_confidence': round(avg_confidence, 3),
                'avg_accuracy': round(avg_accuracy, 3),
                'calibration_error': round(calibration_error, 3)
            })

        return {
            'ece': round(ece, 4),
            'mce': round(mce, 4),
            'total_samples': total_samples,
            'n_bins': n_bins,
            'bin_statistics': bin_stats
        }

    def analyze_by_category(self) -> Dict:
        """
        Analyze calibration quality per category.

        Returns:
            Dictionary with per-category calibration metrics
        """
        samples = self.data.get('samples', [])
        category_data = defaultdict(lambda: {'correct': 0, 'total': 0, 'confidences': []})

        for sample in samples:
            category = sample.get('predicted_category', 'unknown')
            correct = sample.get('correct', False)
            confidence = sample.get('confidence', 0)

            category_data[category]['total'] += 1
            if correct:
                category_data[category]['correct'] += 1
            category_data[category]['confidences'].append(confidence)

        results = {}
        for category, data in category_data.items():
            accuracy = data['correct'] / data['total'] if data['total'] > 0 else 0
            avg_confidence = np.mean(data['confidences']) if data['confidences'] else 0

            results[category] = {
                'total_samples': data['total'],
                'accuracy': round(accuracy, 3),
                'avg_confidence': round(avg_confidence, 3),
                'calibration_gap': round(abs(avg_confidence - accuracy), 3)
            }

        return results

    def identify_miscalibration_patterns(self) -> Dict:
        """
        Identify patterns in miscalibration.

        Returns:
            Dictionary with identified patterns
        """
        samples = self.data.get('samples', [])

        overconfident = []  # High confidence but wrong
        underconfident = []  # Low confidence but correct
        well_calibrated = []  # Confidence matches correctness

        for sample in samples:
            confidence = sample.get('confidence', 0)
            correct = sample.get('correct', False)

            if confidence >= 0.8 and not correct:
                overconfident.append(sample)
            elif confidence < 0.6 and correct:
                underconfident.append(sample)
            elif (confidence >= 0.8 and correct) or (confidence < 0.6 and not correct):
                well_calibrated.append(sample)

        return {
            'overconfident_count': len(overconfident),
            'underconfident_count': len(underconfident),
            'well_calibrated_count': len(well_calibrated),
            'overconfident_examples': [
                {
                    'id': s['id'],
                    'subject': s['subject'][:50],
                    'predicted': s['predicted_category'],
                    'true': s['true_category'],
                    'confidence': s['confidence']
                }
                for s in overconfident[:5]
            ],
            'underconfident_examples': [
                {
                    'id': s['id'],
                    'subject': s['subject'][:50],
                    'predicted': s['predicted_category'],
                    'confidence': s['confidence']
                }
                for s in underconfident[:5]
            ]
        }

    def generate_report(self, output_path: str = None) -> Dict:
        """
        Generate comprehensive calibration report.

        Args:
            output_path: Optional path to save report JSON

        Returns:
            Complete calibration report
        """
        report = {
            'dataset_info': self.data.get('metadata', {}),
            'overall_calibration': self.calculate_calibration_error(),
            'category_analysis': self.analyze_by_category(),
            'miscalibration_patterns': self.identify_miscalibration_patterns()
        }

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"Report saved to: {output_path}")

        return report

    def plot_reliability_diagram(self, output_path: str = None):
        """
        Generate reliability diagram (calibration plot).

        Args:
            output_path: Path to save plot image
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Warning: matplotlib not installed. Skipping plot generation.")
            print("Install with: pip install matplotlib")
            return

        calibration_data = self.calculate_calibration_error()
        bin_stats = calibration_data.get('bin_statistics', [])

        if not bin_stats:
            print("No bin statistics available for plotting")
            return

        confidences = [b['avg_confidence'] for b in bin_stats]
        accuracies = [b['avg_accuracy'] for b in bin_stats]
        counts = [b['count'] for b in bin_stats]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Reliability diagram
        ax1.plot([0, 1], [0, 1], 'k--', label='Perfect calibration')
        ax1.scatter(confidences, accuracies, s=[c*10 for c in counts], alpha=0.6, label='Observed')
        ax1.set_xlabel('Confidence')
        ax1.set_ylabel('Accuracy')
        ax1.set_title('Reliability Diagram')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Confidence histogram
        ax2.bar(range(len(bin_stats)), counts, alpha=0.6)
        ax2.set_xlabel('Confidence Bin')
        ax2.set_ylabel('Sample Count')
        ax2.set_title('Confidence Distribution')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Plot saved to: {output_path}")
        else:
            plt.show()


def main():
    parser = argparse.ArgumentParser(description='Analyze confidence score calibration')
    parser.add_argument(
        '--dataset',
        default='../data/calibration_dataset.json',
        help='Path to calibration dataset'
    )
    parser.add_argument(
        '--output',
        default='../reports/calibration_report.json',
        help='Path to save report'
    )
    parser.add_argument(
        '--plot',
        action='store_true',
        help='Generate reliability diagram'
    )
    parser.add_argument(
        '--plot-output',
        default='../reports/reliability_diagram.png',
        help='Path to save plot'
    )

    args = parser.parse_args()

    # Resolve paths relative to script location
    script_dir = Path(__file__).parent
    dataset_path = script_dir / args.dataset
    output_path = script_dir / args.output

    print(f"Loading dataset from: {dataset_path}")
    analyzer = CalibrationAnalyzer(dataset_path)

    print("\n=== Calibration Analysis ===\n")
    report = analyzer.generate_report(output_path)

    # Print summary
    overall = report['overall_calibration']
    print(f"Expected Calibration Error (ECE): {overall['ece']:.4f}")
    print(f"Maximum Calibration Error (MCE): {overall['mce']:.4f}")
    print(f"Total Samples: {overall['total_samples']}")

    print("\n=== Per-Category Analysis ===\n")
    for category, stats in report['category_analysis'].items():
        print(f"{category}:")
        print(f"  Samples: {stats['total_samples']}")
        print(f"  Accuracy: {stats['accuracy']:.3f}")
        print(f"  Avg Confidence: {stats['avg_confidence']:.3f}")
        print(f"  Calibration Gap: {stats['calibration_gap']:.3f}")

    patterns = report['miscalibration_patterns']
    print(f"\n=== Miscalibration Patterns ===\n")
    print(f"Overconfident predictions: {patterns['overconfident_count']}")
    print(f"Underconfident predictions: {patterns['underconfident_count']}")
    print(f"Well-calibrated predictions: {patterns['well_calibrated_count']}")

    if args.plot:
        plot_path = script_dir / args.plot_output
        print(f"\nGenerating reliability diagram...")
        analyzer.plot_reliability_diagram(plot_path)


if __name__ == '__main__':
    main()
