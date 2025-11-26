"""
Content Validator for Anti-Hallucination
=======================================

Validates AI-generated content to prevent hallucination and ensure accuracy.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of content validation."""

    question_id: str
    confidence_score: float
    is_valid: bool
    issues: List[str]
    suggestions: List[str]
    risk_level: str  # low, medium, high


class ContentValidator:
    """Validates quiz content to prevent AI hallucination."""

    def __init__(self):
        self.high_risk_keywords = {
            "temporal": ["năm", "tháng", "ngày", "recently", "latest", "current"],
            "specific_numbers": ["exactly", "precisely", "chính xác", "đúng"],
            "opinions": ["best", "worst", "tốt nhất", "tệ nhất", "should", "nên"],
            "medical": ["diagnose", "treatment", "chẩn đoán", "điều trị", "thuốc"],
            "legal": ["law", "legal", "luật", "pháp lý", "quy định"],
            "financial": ["investment", "stock", "đầu tư", "cổ phiếu", "giá"],
        }

        self.confidence_weights = {
            "question_clarity": 0.25,
            "answer_consistency": 0.30,
            "factual_claims": 0.25,
            "temporal_safety": 0.20,
        }

    def validate_quiz_questions(self, questions: List[Dict]) -> List[ValidationResult]:
        """Validate a list of quiz questions."""
        results = []

        for question in questions:
            result = self._validate_single_question(question)
            results.append(result)

            if result.risk_level == "high":
                logger.warning(
                    f"High-risk question detected: {question.get('id', 'unknown')}"
                )

        return results

    def _validate_single_question(self, question: Dict) -> ValidationResult:
        """Validate a single question."""
        q_id = question.get("id", "unknown")
        issues = []
        suggestions = []

        # 1. Check for high-risk content
        risk_analysis = self._analyze_risk_factors(question)
        issues.extend(risk_analysis["issues"])

        # 2. Validate answer consistency
        consistency_check = self._check_answer_consistency(question)
        if not consistency_check["is_consistent"]:
            issues.extend(consistency_check["issues"])
            suggestions.extend(consistency_check["suggestions"])

        # 3. Check for specific factual claims
        fact_analysis = self._analyze_factual_claims(question)
        if fact_analysis["has_risky_claims"]:
            issues.extend(fact_analysis["issues"])
            suggestions.append(
                "Consider using conceptual questions instead of specific facts"
            )

        # 4. Calculate confidence score
        confidence = self._calculate_confidence_score(question, issues)

        # 5. Determine risk level
        risk_level = self._determine_risk_level(confidence, issues)

        return ValidationResult(
            question_id=q_id,
            confidence_score=confidence,
            is_valid=confidence >= 0.6 and risk_level != "high",
            issues=issues,
            suggestions=suggestions,
            risk_level=risk_level,
        )

    def _analyze_risk_factors(self, question: Dict) -> Dict:
        """Analyze various risk factors in the question."""
        issues = []
        stem = question.get("stem", "")
        options = question.get("options", [])

        # Check for temporal information
        if self._contains_temporal_info(stem):
            issues.append("Contains time-sensitive information")

        # Check for specific numbers/dates
        if self._contains_specific_numbers(stem):
            issues.append("Contains specific numerical claims")

        # Check for high-risk domains
        risk_domain = self._detect_high_risk_domain(stem)
        if risk_domain:
            issues.append(f"Content in high-risk domain: {risk_domain}")

        # Check options consistency
        if isinstance(options, list) and len(options) > 1:
            if self._has_inconsistent_options(options):
                issues.append("Options appear inconsistent or confusing")

        return {"issues": issues}

    def _check_answer_consistency(self, question: Dict) -> Dict:
        """Check if the correct answer is consistent with the question."""
        q_type = question.get("type", "").lower()
        stem = question.get("stem", "")
        options = question.get("options", [])
        correct_answer = question.get("answer", "") or question.get(
            "correct_answer", ""
        )

        issues = []
        suggestions = []

        # For multiple choice questions
        if q_type in ["mcq", "multiple_choice"] and options:
            if correct_answer not in options:
                issues.append("Correct answer not found in options")
                suggestions.append(
                    "Verify that the correct answer matches one of the provided options"
                )

        # For true/false questions
        elif q_type in ["tf", "true_false"]:
            if correct_answer.lower() not in ["true", "false", "đúng", "sai"]:
                issues.append("True/False question has invalid answer format")
                suggestions.append("Answer should be 'True/False' or 'Đúng/Sai'")

        # For fill-in-the-blank
        elif q_type in ["fill_blank", "fill_in_blank"]:
            if "___" not in stem and "_" not in stem:
                issues.append("Fill-in-blank question missing blank indicator")
                suggestions.append(
                    "Add ___ or blanks to indicate where answer should go"
                )

        return {
            "is_consistent": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
        }

    def _analyze_factual_claims(self, question: Dict) -> Dict:
        """Analyze if question contains risky factual claims."""
        stem = question.get("stem", "")

        # Patterns that indicate specific factual claims
        risky_patterns = [
            r"\b(in|vào|năm)\s+\d{4}\b",  # Years
            r"\b\d+\s*(people|person|người)\b",  # Specific counts
            r"\b(exactly|chính xác)\s+\d+",  # Exact numbers
            r"\b(first|đầu tiên|founded|thành lập).*\d{4}\b",  # Historical firsts
            r"\b(CEO|president|chủ tịch)\s+of\b",  # Current positions
        ]

        risky_claims = []
        for pattern in risky_patterns:
            matches = re.findall(pattern, stem, re.IGNORECASE)
            if matches:
                risky_claims.extend(matches)

        has_risky = len(risky_claims) > 0
        issues = [f"Specific factual claim detected: {claim}" for claim in risky_claims]

        return {"has_risky_claims": has_risky, "claims": risky_claims, "issues": issues}

    def _contains_temporal_info(self, text: str) -> bool:
        """Check if text contains time-sensitive information."""
        temporal_keywords = self.high_risk_keywords["temporal"]
        return any(keyword in text.lower() for keyword in temporal_keywords)

    def _contains_specific_numbers(self, text: str) -> bool:
        """Check for specific numerical claims."""
        # Look for patterns like "exactly X", "precisely Y", etc.
        specific_patterns = [
            r"\b(exactly|precisely|chính xác)\s+\d+",
            r"\b\d+\s+(million|billion|triệu|tỷ)",
            r"\b\d{4}\s*(AD|BC|năm)",
        ]

        return any(
            re.search(pattern, text, re.IGNORECASE) for pattern in specific_patterns
        )

    def _detect_high_risk_domain(self, text: str) -> Optional[str]:
        """Detect if content is in high-risk domain."""
        text_lower = text.lower()

        for domain, keywords in self.high_risk_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return domain

        return None

    def _has_inconsistent_options(self, options: List[str]) -> bool:
        """Check if multiple choice options are inconsistent."""
        if len(options) < 2:
            return False

        # Check for duplicate options
        if len(set(options)) != len(options):
            return True

        # Check for obviously wrong patterns
        option_lengths = [len(opt) for opt in options]
        if max(option_lengths) > 10 * min(option_lengths):  # One option much longer
            return True

        return False

    def _calculate_confidence_score(self, question: Dict, issues: List[str]) -> float:
        """Calculate confidence score for the question."""
        base_score = 1.0

        # Penalty for each issue type
        issue_penalties = {
            "time-sensitive": 0.3,
            "specific": 0.25,
            "high-risk": 0.4,
            "inconsistent": 0.35,
            "factual": 0.2,
        }

        penalty = 0.0
        for issue in issues:
            issue_lower = issue.lower()
            for penalty_type, penalty_value in issue_penalties.items():
                if penalty_type in issue_lower:
                    penalty += penalty_value
                    break
            else:
                penalty += 0.15  # Default penalty for unclassified issues

        # Apply confidence weights
        final_score = max(0.0, base_score - penalty)

        return round(final_score, 3)

    def _determine_risk_level(self, confidence: float, issues: List[str]) -> str:
        """Determine risk level based on confidence and issues."""
        high_risk_indicators = ["medical", "legal", "financial", "high-risk domain"]

        # Check for high-risk content
        has_high_risk_content = any(
            any(indicator in issue.lower() for indicator in high_risk_indicators)
            for issue in issues
        )

        if has_high_risk_content or confidence < 0.4:
            return "high"
        elif confidence < 0.7 or len(issues) >= 3:
            return "medium"
        else:
            return "low"

    def get_validation_summary(
        self, validation_results: List[ValidationResult]
    ) -> Dict:
        """Generate a summary of validation results."""
        total = len(validation_results)
        if total == 0:
            return {"total": 0, "valid": 0, "risk_distribution": {}}

        valid_count = sum(1 for r in validation_results if r.is_valid)
        avg_confidence = sum(r.confidence_score for r in validation_results) / total

        risk_distribution = {"low": 0, "medium": 0, "high": 0}
        for result in validation_results:
            risk_distribution[result.risk_level] += 1

        return {
            "total_questions": total,
            "valid_questions": valid_count,
            "validation_rate": round(valid_count / total * 100, 2),
            "average_confidence": round(avg_confidence, 3),
            "risk_distribution": risk_distribution,
            "recommendations": self._generate_recommendations(validation_results),
        }

    def _generate_recommendations(self, results: List[ValidationResult]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        high_risk_count = sum(1 for r in results if r.risk_level == "high")
        if high_risk_count > 0:
            recommendations.append(
                f"Review {high_risk_count} high-risk questions before deployment"
            )

        low_confidence_count = sum(1 for r in results if r.confidence_score < 0.6)
        if low_confidence_count > 0:
            recommendations.append(
                f"Regenerate {low_confidence_count} low-confidence questions"
            )

        common_issues = {}
        for result in results:
            for issue in result.issues:
                common_issues[issue] = common_issues.get(issue, 0) + 1

        if common_issues:
            most_common = max(common_issues, key=common_issues.get)
            recommendations.append(f"Address common issue: {most_common}")

        return recommendations
