# Data Directory

This directory contains datasets used for model calibration, evaluation, and testing.

## Files

### calibration_dataset.json
Human-labeled dataset for confidence score calibration. Used to:
- Calculate calibration error (reliability)
- Train calibration models (Platt scaling, isotonic regression)
- Validate threshold settings

**Structure:**
```json
{
  "metadata": {...},
  "samples": [
    {
      "id": "unique_id",
      "subject": "email subject",
      "body": "email body",
      "predicted_category": "category from classifier",
      "true_category": "human-labeled ground truth",
      "confidence": 0.85,
      "correct": true/false
    }
  ]
}
```

**Target Size:** 200+ samples across all categories

**How to Add Samples:**
1. Run the system on real emails
2. Have human reviewers label the true category
3. Record predicted category, confidence, and correctness
4. Add to the samples array

## Usage

- `calibration_analysis.py` - Analyzes calibration quality
- `threshold_optimization.py` - Optimizes decision thresholds
- `scoring_service.py` - Loads calibration model for inference
