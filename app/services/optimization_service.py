from __future__ import annotations

from math import ceil

from app.schemas.optimization import CapacityOptimizationRequest


class UnderwriterCapacityOptimizationService:
    def optimize(self, request: CapacityOptimizationRequest, risk_scores: list[float]) -> dict:
        if not risk_scores:
            risk_scores = [0.12, 0.18, 0.24, 0.35, 0.41, 0.52, 0.61, 0.67, 0.72, 0.81]

        high_risk_baseline = [score for score in risk_scores if score >= 0.65]
        baseline_count = len(high_risk_baseline)

        scenarios: list[dict] = []
        threshold = request.min_threshold
        while threshold <= request.max_threshold + 1e-9:
            flagged_rate = sum(score >= threshold for score in risk_scores) / len(risk_scores)
            expected_manual_reviews = int(round(flagged_rate * request.daily_applications))
            required_underwriters = max(
                1,
                ceil(expected_manual_reviews / request.review_capacity_per_underwriter),
            )

            if baseline_count == 0:
                captured_high_risk_rate = 0.0
            else:
                captured_high_risk_rate = (
                    sum(score >= threshold for score in high_risk_baseline) / baseline_count
                )

            excess_or_shortfall = request.current_underwriters - required_underwriters
            staffing_penalty = max(0, required_underwriters - request.max_underwriters) * 0.25
            staffing_delta_penalty = abs(excess_or_shortfall) * 0.01
            objective = captured_high_risk_rate - staffing_penalty - staffing_delta_penalty

            scenarios.append(
                {
                    "threshold": round(threshold, 3),
                    "expected_manual_reviews": expected_manual_reviews,
                    "required_underwriters": required_underwriters,
                    "excess_or_shortfall": excess_or_shortfall,
                    "captured_high_risk_rate": round(float(captured_high_risk_rate), 4),
                    "objective": objective,
                }
            )
            threshold += request.step

        scenarios_sorted = sorted(scenarios, key=lambda item: item["objective"], reverse=True)
        best = scenarios_sorted[0]

        return {
            "recommended_threshold": best["threshold"],
            "recommended_underwriters": best["required_underwriters"],
            "scenarios": [
                {
                    "threshold": item["threshold"],
                    "expected_manual_reviews": item["expected_manual_reviews"],
                    "required_underwriters": item["required_underwriters"],
                    "excess_or_shortfall": item["excess_or_shortfall"],
                    "captured_high_risk_rate": item["captured_high_risk_rate"],
                }
                for item in scenarios_sorted
            ],
        }
