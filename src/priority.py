"""Explainable prototype priority scoring, shared by pipeline and dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_WEIGHTS = {
    "coverage limitation": 40,
    "distance to infrastructure": 25,
    "provider diversity": 15,
    "digital inclusion / remoteness context": 20,
}

COMPONENT_COLUMNS = {
    "coverage limitation": "coverage_limitation_component",
    "distance to infrastructure": "distance_component",
    "provider diversity": "provider_diversity_component",
    "digital inclusion / remoteness context": "context_component",
}


def apply_priority_weights(frame: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """Score rows using only available components and disclose each contribution."""
    result = frame.copy()
    names = list(COMPONENT_COLUMNS)
    matrix = result[[COMPONENT_COLUMNS[name] for name in names]].to_numpy(dtype=float)
    configured = np.asarray([max(0.0, float(weights.get(name, 0))) for name in names])
    present = np.isfinite(matrix)
    effective_weights = present * configured
    denominator = effective_weights.sum(axis=1)
    proportions = np.divide(
        effective_weights,
        denominator[:, None],
        out=np.zeros_like(effective_weights, dtype=float),
        where=denominator[:, None] > 0,
    )
    for column, name in enumerate(names):
        result[f"{COMPONENT_COLUMNS[name]}_weight_pct"] = proportions[:, column] * 100
        result[f"{COMPONENT_COLUMNS[name]}_contribution"] = np.where(
            present[:, column], matrix[:, column], 0
        ) * proportions[:, column]
    result["priority_score"] = np.divide(
        np.sum(np.where(present, matrix, 0) * proportions, axis=1),
        np.ones(len(result)),
        out=np.full(len(result), np.nan),
        where=denominator > 0,
    ).round(1)
    result["priority_band"] = pd.cut(
        result["priority_score"],
        bins=[-0.001, 33, 66, 100],
        labels=["Lower", "Moderate", "Higher"],
    ).astype("string")

    def explain(row_number: int) -> str:
        parts = [
            f"{name}: {matrix[row_number, column]:.0f}/100 "
            f"({proportions[row_number, column] * 100:.2f}% of available weight)"
            for column, name in enumerate(names)
            if present[row_number, column] and proportions[row_number, column] > 0
        ]
        if not parts:
            return "No supported components are available; no score assigned."
        omitted = [
            name
            for column, name in enumerate(names)
            if not present[row_number, column] or configured[column] == 0
        ]
        explanation = "Included: " + "; ".join(parts) + "."
        if omitted:
            explanation += " Not included: " + ", ".join(omitted) + "."
        return explanation

    result["priority_explanation"] = [explain(index) for index in range(len(result))]
    return result
