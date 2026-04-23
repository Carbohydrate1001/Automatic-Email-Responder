"""
System Evaluation Script

Calculates classification metrics (accuracy, precision, recall, F1),
auto-send performance, and reply quality scores.
Generates JSON reports in backend/reports/.

Usage:
    python evaluate_system.py [--output PATH] [--start-date DATE] [--end-date DATE]
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict
from models.database import get_db_connection
from utils.logger import get_logger


logger = get_logger('evaluation')


class SystemEvaluator:
    """Evaluates system performance across classification, auto-send, and reply quality."""

    def __init__(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        self.start_date = start_date
        self.end_date = end_date

    def _date_filter(self, alias: str = "") -> tuple:
        prefix = f"{alias}." if alias else ""
        conditions = []
        params = []
        if self.start_date:
            conditions.append(f"{prefix}created_at >= ?")
            params.append(self.start_date)
        if self.end_date:
            conditions.append(f"{prefix}created_at <= ?")
            params.append(self.end_date)
        clause = " AND ".join(conditions) if conditions else "1=1"
        return clause, params

    def evaluate_classification(self) -> Dict[str, Any]:
        """Evaluate classification performance."""
        where, params = self._date_filter()

        with get_db_connection() as conn:
            rows = conn.execute(
                f"SELECT category, confidence, status FROM emails WHERE {where}", params
            ).fetchall()

        if not rows:
            return {'total': 0, 'message': 'No data'}

        categories = Counter(r['category'] for r in rows)
        confidences = [r['confidence'] for r in rows if r['confidence'] is not None]

        per_category = {}
        for cat, count in categories.items():
            cat_confs = [r['confidence'] for r in rows if r['category'] == cat and r['confidence'] is not None]
            per_category[cat] = {
                'count': count,
                'percentage': round(count / len(rows) * 100, 1),
                'avg_confidence': round(sum(cat_confs) / len(cat_confs), 3) if cat_confs else 0,
                'min_confidence': round(min(cat_confs), 3) if cat_confs else 0,
                'max_confidence': round(max(cat_confs), 3) if cat_confs else 0,
            }

        return {
            'total_emails': len(rows),
            'unique_categories': len(categories),
            'category_distribution': per_category,
            'overall_avg_confidence': round(sum(confidences) / len(confidences), 3) if confidences else 0,
            'confidence_histogram': self._histogram(confidences, bins=10),
        }

    def evaluate_auto_send(self) -> Dict[str, Any]:
        """Evaluate auto-send performance."""
        where, params = self._date_filter()

        with get_db_connection() as conn:
            rows = conn.execute(
                f"SELECT status, category, confidence FROM emails WHERE {where}", params
            ).fetchall()

        if not rows:
            return {'total': 0, 'message': 'No data'}

        total = len(rows)
        statuses = Counter(r['status'] for r in rows)

        auto_sent = statuses.get('auto_sent', 0)
        pending = statuses.get('pending_review', 0)
        ignored = statuses.get('ignored_no_reply', 0)
        failed = statuses.get('send_failed', 0)

        auto_sent_by_cat = Counter(r['category'] for r in rows if r['status'] == 'auto_sent')
        pending_by_cat = Counter(r['category'] for r in rows if r['status'] == 'pending_review')

        return {
            'total_emails': total,
            'status_distribution': dict(statuses),
            'auto_send_rate': round(auto_sent / total * 100, 1) if total else 0,
            'manual_review_rate': round(pending / total * 100, 1) if total else 0,
            'ignore_rate': round(ignored / total * 100, 1) if total else 0,
            'failure_rate': round(failed / total * 100, 1) if total else 0,
            'auto_sent_by_category': dict(auto_sent_by_cat),
            'pending_by_category': dict(pending_by_cat),
        }

    def evaluate_reply_quality(self) -> Dict[str, Any]:
        """Evaluate reply quality based on validation results."""
        where, params = self._date_filter("r")

        with get_db_connection() as conn:
            rows = conn.execute(
                f"""SELECT r.validation_passed, r.reply_validation_scores, r.validation_issues,
                           e.category
                    FROM replies r
                    JOIN emails e ON r.email_id = e.id
                    WHERE {where}""",
                params
            ).fetchall()

        if not rows:
            return {'total': 0, 'message': 'No data'}

        total = len(rows)
        passed = sum(1 for r in rows if r['validation_passed'] == 1)
        validated = sum(1 for r in rows if r['reply_validation_scores'] is not None)

        issue_counts = Counter()
        for r in rows:
            if r['validation_issues']:
                try:
                    issues = json.loads(r['validation_issues'])
                    for issue in issues:
                        issue_counts[str(issue)] += 1
                except (json.JSONDecodeError, TypeError):
                    pass

        return {
            'total_replies': total,
            'validated_count': validated,
            'validation_pass_rate': round(passed / total * 100, 1) if total else 0,
            'top_issues': dict(issue_counts.most_common(10)),
        }

    def evaluate_latency(self) -> Dict[str, Any]:
        """Evaluate processing latency from email receipt to reply."""
        where, params = self._date_filter("e")

        with get_db_connection() as conn:
            rows = conn.execute(
                f"""SELECT e.received_at, e.created_at, r.created_at as reply_created_at
                    FROM emails e
                    LEFT JOIN replies r ON e.id = r.email_id
                    WHERE {where}""",
                params
            ).fetchall()

        if not rows:
            return {'total': 0, 'message': 'No data'}

        latencies = []
        for r in rows:
            if r['received_at'] and r['reply_created_at']:
                try:
                    received = datetime.fromisoformat(r['received_at'].replace('Z', '+00:00'))
                    replied = datetime.fromisoformat(r['reply_created_at'].replace('Z', '+00:00'))
                    delta = (replied - received).total_seconds()
                    if delta >= 0:
                        latencies.append(delta)
                except (ValueError, TypeError):
                    pass

        if not latencies:
            return {'total': len(rows), 'latency_data': 'insufficient'}

        latencies.sort()
        n = len(latencies)

        return {
            'total_with_latency': n,
            'mean_seconds': round(sum(latencies) / n, 2),
            'median_seconds': round(latencies[n // 2], 2),
            'p95_seconds': round(latencies[int(n * 0.95)], 2) if n >= 20 else None,
            'p99_seconds': round(latencies[int(n * 0.99)], 2) if n >= 100 else None,
            'min_seconds': round(latencies[0], 2),
            'max_seconds': round(latencies[-1], 2),
        }

    def generate_full_report(self) -> Dict[str, Any]:
        """Generate comprehensive evaluation report."""
        report = {
            'report_date': datetime.utcnow().isoformat(),
            'date_range': {'start': self.start_date, 'end': self.end_date},
            'classification': self.evaluate_classification(),
            'auto_send': self.evaluate_auto_send(),
            'reply_quality': self.evaluate_reply_quality(),
            'latency': self.evaluate_latency(),
        }

        logger.info("Evaluation report generated", {
            'total_emails': report['classification'].get('total_emails', 0)
        })

        return report

    @staticmethod
    def _histogram(values: List[float], bins: int = 10) -> Dict[str, int]:
        if not values:
            return {}
        min_v, max_v = min(values), max(values)
        if min_v == max_v:
            return {f"{min_v:.2f}": len(values)}
        bin_width = (max_v - min_v) / bins
        hist = {}
        for i in range(bins):
            lo = min_v + i * bin_width
            hi = lo + bin_width
            label = f"{lo:.2f}-{hi:.2f}"
            count = sum(1 for v in values if lo <= v < hi or (i == bins - 1 and v == hi))
            hist[label] = count
        return hist


def main():
    parser = argparse.ArgumentParser(description='System evaluation')
    parser.add_argument('--output', default=None, help='Output path for report JSON')
    parser.add_argument('--start-date', default=None, help='Start date filter (ISO format)')
    parser.add_argument('--end-date', default=None, help='End date filter (ISO format)')
    args = parser.parse_args()

    evaluator = SystemEvaluator(start_date=args.start_date, end_date=args.end_date)
    report = evaluator.generate_full_report()

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(__file__).parent.parent / 'reports' / f"evaluation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Report saved to: {output_path}")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
