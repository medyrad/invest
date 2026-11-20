from dataclasses import dataclass

THRESHOLDS = {"extraction": 0.95, "citation": 0.98, "persian": 0.90}


@dataclass(frozen=True)
class Assessment:
    eligible: bool
    recommendation: str | None
    reasons: list[str]


def assess(sol, luna):
    reasons = []
    for name, result in (("sol", sol), ("luna", luna)):
        if result.get("critical", 0):
            reasons.append(f"{name}:critical")
        for metric, threshold in THRESHOLDS.items():
            value = result.get("overall", {}).get(metric)
            if value is None or value < threshold:
                reasons.append(f"{name}:{metric}")
        if not result.get("human_persian_complete"):
            reasons.append(f"{name}:human-persian-open")
    for family, sol_metrics in sol.get("families", {}).items():
        luna_metrics = luna.get("families", {}).get(family, {})
        for metric, sol_value in sol_metrics.items():
            luna_value = luna_metrics.get(metric)
            if luna_value is None:
                reasons.append(f"luna:{family}:{metric}:missing")
            elif sol_value - luna_value > 0.05:
                reasons.append(f"luna:{family}:{metric}:degradation")
    if reasons:
        return Assessment(False, None, reasons)
    return Assessment(True, "gpt-6-luna", [])
