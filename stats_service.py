"""
stats_service.py
StatisticsService: turns raw complaint records into decision-making insight.

Implements descriptive statistics (mean, median, mode, min, max, range,
variance, standard deviation), frequency distributions, and quartile /
IQR-based outlier fences for resolution times - required for the
Statistics (Batch 4) benchmark.
"""

import statistics as pystats
from collections import Counter


class StatisticsService:

    def resolution_time_stats(self, complaints):
        """Descriptive stats on resolution time (hours) for resolved complaints."""
        times = [c["resolution_time_hours"] for c in complaints
                 if c.get("resolution_time_hours") is not None]

        if not times:
            return {
                "count": 0, "mean": None, "median": None, "mode": None,
                "min": None, "max": None, "range": None,
                "variance": None, "std_dev": None,
                "q1": None, "q3": None, "iqr": None,
                "lower_fence": None, "upper_fence": None,
                "outliers": [],
            }

        times_sorted = sorted(times)
        mean_val = round(pystats.mean(times), 2)
        median_val = round(pystats.median(times), 2)
        try:
            mode_val = round(pystats.mode(times), 2)
        except pystats.StatisticsError:
            mode_val = None
        variance_val = round(pystats.pvariance(times), 2) if len(times) > 1 else 0
        std_dev_val = round(pystats.pstdev(times), 2) if len(times) > 1 else 0

        if len(times) >= 4:
            q1 = round(pystats.median(times_sorted[:len(times_sorted) // 2]), 2)
            upper_half = times_sorted[(len(times_sorted) + 1) // 2:]
            q3 = round(pystats.median(upper_half), 2)
        else:
            q1, q3 = times_sorted[0], times_sorted[-1]

        iqr = round(q3 - q1, 2)
        lower_fence = round(q1 - 1.5 * iqr, 2)
        upper_fence = round(q3 + 1.5 * iqr, 2)
        outliers = [t for t in times if t < lower_fence or t > upper_fence]

        return {
            "count": len(times),
            "mean": mean_val,
            "median": median_val,
            "mode": mode_val,
            "min": min(times),
            "max": max(times),
            "range": round(max(times) - min(times), 2),
            "variance": variance_val,
            "std_dev": std_dev_val,
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "lower_fence": lower_fence,
            "upper_fence": upper_fence,
            "outliers": outliers,
        }

    def frequency_distribution(self, complaints, field):
        counter = Counter(c.get(field) or "Unknown" for c in complaints)
        total = sum(counter.values()) or 1
        return [
            {"label": label, "count": count, "percent": round(count / total * 100, 1)}
            for label, count in sorted(counter.items(), key=lambda x: -x[1])
        ]

    def summary_counts(self, complaints):
        total = len(complaints)
        resolved = sum(1 for c in complaints if c.get("status") == "Resolved")
        open_count = sum(1 for c in complaints if c.get("status") == "Open")
        in_progress = sum(1 for c in complaints if c.get("status") in ("Assigned", "In Progress"))
        critical = sum(1 for c in complaints if c.get("priority") == "Critical")
        return {
            "total": total,
            "resolved": resolved,
            "open": open_count,
            "in_progress": in_progress,
            "critical": critical,
            "resolution_rate": round(resolved / total * 100, 1) if total else 0,
        }

    def full_report(self, complaints):
        return {
            "summary": self.summary_counts(complaints),
            "category_distribution": self.frequency_distribution(complaints, "category"),
            "priority_distribution": self.frequency_distribution(complaints, "priority"),
            "department_distribution": self.frequency_distribution(complaints, "assigned_department"),
            "resolution_time": self.resolution_time_stats(complaints),
        }
