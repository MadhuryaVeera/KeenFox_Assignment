"""Guardrails service for competitor validation and audit."""

import logging
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GuardrailsService:
    """Validate discovered competitors and generate an audit trail."""

    def __init__(self, llm_service=None):
        self.llm_service = llm_service

    def evaluate_competitors(
        self,
        brand_name: str,
        category: str,
        candidates: List[str],
        limit: int = 8,
    ) -> Dict[str, Any]:
        """Run deterministic and optional LLM checks over candidate competitors."""
        normalized_brand = (brand_name or "").strip().lower()
        approved_scored: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []
        seen = set()

        for raw_candidate in candidates or []:
            candidate = (raw_candidate or "").strip()
            if not candidate:
                continue

            candidate_norm = candidate.lower()
            if candidate_norm in seen:
                continue
            seen.add(candidate_norm)

            score = 1.0
            reasons: List[str] = []

            if candidate_norm == normalized_brand:
                score -= 1.0
                reasons.append("same_as_brand")

            if candidate_norm in {"unknown", "n/a", "none", "null", "competitor", "brand"}:
                score -= 1.0
                reasons.append("placeholder_name")

            if any(token in candidate_norm for token in ["http://", "https://", ".com/", "/pricing"]):
                score -= 1.0
                reasons.append("looks_like_url")

            if len(candidate) < 2:
                score -= 1.0
                reasons.append("too_short")

            similarity = SequenceMatcher(None, normalized_brand, candidate_norm).ratio()
            if similarity >= 0.9:
                score -= 1.0
                reasons.append("brand_name_similarity_too_high")

            if any(char.isdigit() for char in candidate) and len(candidate) <= 3:
                score -= 0.5
                reasons.append("suspicious_short_numeric_name")

            score = max(0.0, min(1.0, score))

            if score < 0.5:
                rejected.append(
                    {
                        "name": candidate,
                        "score": round(score, 2),
                        "reasons": reasons or ["low_confidence"],
                    }
                )
            else:
                approved_scored.append(
                    {
                        "name": candidate,
                        "score": round(score, 2),
                        "reasons": reasons,
                    }
                )

        approved_names = [item["name"] for item in approved_scored]
        llm_validation_used = False

        # Optional LLM validation pass for semantic relevance.
        if approved_names and self.llm_service is not None:
            try:
                llm_validated = self.llm_service.validate_competitor_relevance(
                    brand_name=brand_name,
                    category=category,
                    competitors=approved_names,
                )
                if llm_validated:
                    llm_validation_used = True
                    llm_validated_set = {name.strip().lower() for name in llm_validated}
                    filtered_approved = []
                    for item in approved_scored:
                        if item["name"].strip().lower() in llm_validated_set:
                            filtered_approved.append(item)
                        else:
                            rejected.append(
                                {
                                    "name": item["name"],
                                    "score": item["score"],
                                    "reasons": ["rejected_by_llm_relevance_check"],
                                }
                            )
                    approved_scored = filtered_approved
            except Exception as exc:
                logger.warning(f"LLM guardrail validation skipped: {exc}")

        approved_scored = sorted(approved_scored, key=lambda item: item["score"], reverse=True)
        approved_competitors = [item["name"] for item in approved_scored[:limit]]

        return {
            "version": "1.0",
            "brand_name": brand_name,
            "category": category,
            "input_candidates_count": len(candidates or []),
            "approved_count": len(approved_competitors),
            "rejected_count": len(rejected),
            "approved_competitors": approved_competitors,
            "approved_scored": approved_scored[:limit],
            "rejected_competitors": rejected,
            "checks": {
                "deterministic": [
                    "same_as_brand",
                    "placeholder_name",
                    "looks_like_url",
                    "brand_name_similarity_too_high",
                    "suspicious_short_numeric_name",
                ],
                "llm_relevance_validation_used": llm_validation_used,
            },
        }
