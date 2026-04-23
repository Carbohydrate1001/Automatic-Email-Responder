"""
Train Calibration Model Script

Trains a calibration model (Platt scaling or isotonic regression) using the
calibration dataset to improve confidence score reliability.

Usage:
    python train_calibration_model.py [--dataset PATH] [--method METHOD] [--output PATH]
"""

import json
import pickle
import argparse
from pathlib import Path
from typing import Dict, List
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


class CalibrationModelTrainer:
    """Trains calibration models to improve confidence score reliability."""

    def __init__(self, dataset_path: str):
        """
        Initialize CalibrationModelTrainer.

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

    def prepare_training_data(self) -> tuple:
        """
        Prepare training data from calibration dataset.

        Returns:
            Tuple of (confidences, labels) as numpy arrays
        """
        samples = self.data.get('samples', [])

        if len(samples) < 10:
            raise ValueError(f"Insufficient samples for training: {len(samples)}. Need at least 10.")

        confidences = []
        labels = []

        for sample in samples:
            confidence = sample.get('confidence', 0)
            correct = sample.get('correct', False)

            confidences.append(confidence)
            labels.append(1 if correct else 0)

        return np.array(confidences).reshape(-1, 1), np.array(labels)

    def train_platt_scaling(self) -> object:
        """
        Train Platt scaling calibration model (logistic regression).

        Returns:
            Trained calibration model
        """
        X, y = self.prepare_training_data()

        # Platt scaling uses logistic regression
        model = LogisticRegression(solver='lbfgs', max_iter=1000)
        model.fit(X, y)

        return model

    def train_isotonic_regression(self) -> object:
        """
        Train isotonic regression calibration model.

        Returns:
            Trained calibration model
        """
        X, y = self.prepare_training_data()

        # Isotonic regression (non-parametric)
        model = IsotonicRegression(out_of_bounds='clip')
        model.fit(X.ravel(), y)

        return model

    def evaluate_calibration(self, model, method: str) -> Dict:
        """
        Evaluate calibration model performance.

        Args:
            model: Trained calibration model
            method: 'platt' or 'isotonic'

        Returns:
            Dictionary with evaluation metrics
        """
        X, y = self.prepare_training_data()

        # Get calibrated predictions
        if method == 'platt':
            calibrated_probs = model.predict_proba(X)[:, 1]
        else:  # isotonic
            calibrated_probs = model.predict(X.ravel())

        # Calculate metrics
        raw_confidences = X.ravel()

        # Mean absolute calibration error
        from sklearn.metrics import brier_score_loss

        raw_brier = brier_score_loss(y, raw_confidences)
        calibrated_brier = brier_score_loss(y, calibrated_probs)

        return {
            'method': method,
            'samples_used': len(y),
            'raw_brier_score': round(raw_brier, 4),
            'calibrated_brier_score': round(calibrated_brier, 4),
            'improvement': round(raw_brier - calibrated_brier, 4),
            'improvement_percent': round((raw_brier - calibrated_brier) / raw_brier * 100, 2) if raw_brier > 0 else 0
        }

    def train_and_save(self, method: str = 'isotonic', output_path: str = None) -> Dict:
        """
        Train calibration model and save to disk.

        Args:
            method: 'platt' or 'isotonic'
            output_path: Path to save model pickle file

        Returns:
            Training report with evaluation metrics
        """
        print(f"Training {method} calibration model...")

        if method == 'platt':
            model = self.train_platt_scaling()
        elif method == 'isotonic':
            model = self.train_isotonic_regression()
        else:
            raise ValueError(f"Unknown method: {method}. Use 'platt' or 'isotonic'")

        # Evaluate
        evaluation = self.evaluate_calibration(model, method)

        # Save model
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                pickle.dump(model, f)

            print(f"Model saved to: {output_path}")
            evaluation['model_path'] = str(output_path)

        return evaluation


def main():
    parser = argparse.ArgumentParser(description='Train confidence calibration model')
    parser.add_argument(
        '--dataset',
        default='../data/calibration_dataset.json',
        help='Path to calibration dataset'
    )
    parser.add_argument(
        '--method',
        choices=['platt', 'isotonic'],
        default='isotonic',
        help='Calibration method (platt=logistic regression, isotonic=non-parametric)'
    )
    parser.add_argument(
        '--output',
        default='../models/calibration_model.pkl',
        help='Path to save trained model'
    )

    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent
    dataset_path = script_dir / args.dataset
    output_path = script_dir / args.output

    print(f"Loading dataset from: {dataset_path}")
    trainer = CalibrationModelTrainer(dataset_path)

    print(f"\n=== Training Calibration Model ===\n")
    print(f"Method: {args.method}")

    try:
        report = trainer.train_and_save(args.method, output_path)

        print(f"\n=== Training Results ===\n")
        print(f"Samples used: {report['samples_used']}")
        print(f"Raw Brier score: {report['raw_brier_score']:.4f}")
        print(f"Calibrated Brier score: {report['calibrated_brier_score']:.4f}")
        print(f"Improvement: {report['improvement']:.4f} ({report['improvement_percent']:.2f}%)")

        if report['improvement'] > 0:
            print("\n✓ Calibration improved confidence reliability!")
        else:
            print("\n⚠ Warning: Calibration did not improve scores. Consider:")
            print("  - Collecting more calibration samples")
            print("  - Trying a different calibration method")
            print("  - Checking if raw scores are already well-calibrated")

    except ValueError as e:
        print(f"\n✗ Error: {e}")
        print("\nTo train a calibration model, you need:")
        print("  1. At least 10 labeled samples in calibration_dataset.json")
        print("  2. A mix of correct and incorrect predictions")
        print("  3. Diverse confidence scores (not all high or all low)")


if __name__ == '__main__':
    main()
