import logging
import uuid
import json
from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict

from llm_adapter import GeminiEvaluationAdapter
from schemas import (
    QuizSubmission,
    EvaluationResult,
    EvaluationConfig,
    EvaluationSummary,
    QuestionResult,
    TopicBreakdown,
    Analysis,
    Grade,
    QuestionType,
)

logger = logging.getLogger(__name__)


def evaluate_quiz(data: Dict[str, Any]) -> str:
    """Đánh giá kết quả bài kiểm tra và phân tích học tập.

    Args:
        data: Dictionary chứa submission và config

    Returns:
        JSON string chứa kết quả đánh giá hoàn chỉnh

    Raises:
        ValueError: Nếu dữ liệu đầu vào không hợp lệ
        RuntimeError: Nếu phân tích AI thất bại
    """
    try:
        # Parse và validate input
        submission = QuizSubmission(**data.get("submission", {}))
        config = EvaluationConfig(**data.get("config", {}))

        # Tạo ID đánh giá
        evaluation_id = f"eval-{uuid.uuid4().hex[:8]}"

        # Bước 1: Tính điểm cơ bản
        summary, question_results = _calculate_scores(submission, config)

        # Bước 2: Phân tích theo topic/category
        topic_breakdown = _analyze_by_topic(question_results)

        # Bước 3: AI analysis (nếu được bật)
        analysis = Analysis()  # Default empty analysis
        if config.include_ai_analysis:
            analysis = _get_ai_analysis(
                submission, summary, topic_breakdown, question_results
            )

        # Bước 4: Tạo kết quả cuối cùng
        result = EvaluationResult(
            evaluation_id=evaluation_id,
            quiz_id=submission.quiz_id,
            timestamp=datetime.now(),
            summary=summary,
            question_results=question_results,
            topic_breakdown=topic_breakdown,
            analysis=analysis,
            config=config,
            metadata={
                "total_time": (
                    submission.user_info.completion_time
                    if submission.user_info
                    else None
                ),
                "user_id": (
                    submission.user_info.user_id if submission.user_info else None
                ),
                "session_id": (
                    submission.user_info.session_id if submission.user_info else None
                ),
            },
        )

        # Bước 5: Lưu lịch sử (nếu được bật)
        if config.save_history:
            _save_evaluation_history(result)

        logger.info(
            f"Completed evaluation {evaluation_id} - Score: {summary.score_percentage:.1f}%"
        )

        return result.model_dump_json(ensure_ascii=False)

    except Exception as e:
        logger.error(f"Error evaluating quiz: {e}")
        raise


def _calculate_scores(
    submission: QuizSubmission, config: EvaluationConfig
) -> tuple[EvaluationSummary, List[QuestionResult]]:
    """Tính điểm số và tạo kết quả từng câu hỏi."""

    question_results = []
    correct_count = 0
    incorrect_count = 0
    unanswered_count = 0
    total_points = 0.0
    max_points = 0.0

    for question in submission.questions:
        # Điểm cho mỗi câu (có thể custom theo difficulty)
        points_per_question = 1.0
        if question.difficulty == "hard":
            points_per_question = 1.5
        elif question.difficulty == "easy":
            points_per_question = 0.8

        max_points += points_per_question

        # Check câu trả lời
        user_answer = question.user_answer.strip() if question.user_answer else None
        correct_answer = question.correct_answer.strip()

        is_correct = False
        earned_points = 0.0
        explanation = None

        if not user_answer:
            unanswered_count += 1
            explanation = "Câu hỏi chưa được trả lời"
        elif user_answer.lower() == correct_answer.lower():
            is_correct = True
            correct_count += 1
            earned_points = points_per_question
            total_points += points_per_question
        else:
            incorrect_count += 1
            explanation = _generate_explanation(question, user_answer, correct_answer)

        question_result = QuestionResult(
            question_id=question.id,
            is_correct=is_correct,
            topic=question.topic or "General",
            question_type=question.type,
            correct_answer=correct_answer,
            user_answer=user_answer,
            explanation=explanation if config.include_explanations else None,
            points=earned_points,
        )

        question_results.append(question_result)

    # Tính phần trăm và xếp loại
    total_questions = len(submission.questions)
    score_percentage = (
        (correct_count / total_questions * 100) if total_questions > 0 else 0
    )
    grade = _determine_grade(score_percentage, config.grading_scale)

    summary = EvaluationSummary(
        total_questions=total_questions,
        correct_answers=correct_count,
        incorrect_answers=incorrect_count,
        unanswered=unanswered_count,
        score_percentage=score_percentage,
        total_points=total_points,
        max_points=max_points,
        grade=grade,
    )

    return summary, question_results


def _analyze_by_topic(question_results: List[QuestionResult]) -> List[TopicBreakdown]:
    """Phân tích kết quả theo topic/category."""

    topic_stats = defaultdict(lambda: {"total": 0, "correct": 0})

    # Collect stats by topic
    for result in question_results:
        topic = result.topic or "General"
        topic_stats[topic]["total"] += 1
        if result.is_correct:
            topic_stats[topic]["correct"] += 1

    # Build topic breakdown
    topic_breakdown = []
    for topic, stats in topic_stats.items():
        accuracy = (
            (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        )

        # Đề xuất cơ bản dựa trên accuracy
        recommendations = []
        if accuracy < 50:
            recommendations.append(f"Cần học lại toàn bộ chủ đề {topic}")
            recommendations.append(f"Làm thêm bài tập cơ bản về {topic}")
        elif accuracy < 70:
            recommendations.append(f"Cần ôn luyện thêm về {topic}")
            recommendations.append(f"Tập trung vào các khái niệm khó trong {topic}")
        elif accuracy < 90:
            recommendations.append(f"Củng cố kiến thức về {topic}")

        breakdown = TopicBreakdown(
            topic=topic,
            total_questions=stats["total"],
            correct_answers=stats["correct"],
            accuracy_rate=accuracy,
            recommendations=recommendations,
        )

        topic_breakdown.append(breakdown)

    # Sort by accuracy (worst first để ưu tiên cải thiện)
    topic_breakdown.sort(key=lambda x: x.accuracy_rate)

    return topic_breakdown


def _get_ai_analysis(
    submission: QuizSubmission,
    summary: EvaluationSummary,
    topic_breakdown: List[TopicBreakdown],
    question_results: List[QuestionResult],
) -> Analysis:
    """Lấy phân tích AI từ Gemini."""

    try:
        # Chuẩn bị data cho AI
        quiz_data = {"quiz_id": submission.quiz_id, "questions": []}

        for i, question in enumerate(submission.questions):
            quiz_data["questions"].append(
                {
                    "id": question.id,
                    "type": question.type.value,
                    "stem": question.stem,
                    "topic": question.topic or "General",
                    "correct_answer": question.correct_answer,
                    "user_answer": question.user_answer,
                    "is_correct": (
                        question_results[i].is_correct
                        if i < len(question_results)
                        else False
                    ),
                }
            )

        # Topic breakdown để truyền cho AI
        topic_data = []
        for topic in topic_breakdown:
            topic_data.append(
                {
                    "topic": topic.topic,
                    "total_questions": topic.total_questions,
                    "correct_answers": topic.correct_answers,
                    "accuracy_rate": topic.accuracy_rate,
                }
            )

        # Gọi AI
        gemini = GeminiEvaluationAdapter()
        ai_response = gemini.analyze_quiz_results(
            quiz_data=quiz_data,
            correct_count=summary.correct_answers,
            total_count=summary.total_questions,
            topic_breakdown=topic_data,
        )

        # Parse AI response
        analysis_data = _parse_ai_analysis(ai_response)

        return Analysis(**analysis_data)

    except Exception as e:
        logger.error(f"AI analysis failed: {e}")

        # Fallback analysis
        return Analysis(
            strengths=["Hoàn thành bài kiểm tra"],
            weaknesses=(
                ["Cần cải thiện kết quả"] if summary.score_percentage < 70 else []
            ),
            recommendations=["Ôn luyện thêm các chủ đề yếu"],
            study_plan=["Học lại từng chủ đề một cách có hệ thống"],
            overall_feedback=f"Bạn đạt {summary.score_percentage:.1f}% - {'Cần cố gắng thêm' if summary.score_percentage < 70 else 'Kết quả tốt'}",
            improvement_areas=["Cần xác định dựa trên kết quả chi tiết"],
        )


def _parse_ai_analysis(raw_response: str) -> Dict[str, Any]:
    """Parse response từ AI thành format Analysis."""

    try:
        # Clean up response
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Parse JSON
        analysis_data = json.loads(cleaned)

        # Validate required fields và set defaults
        required_fields = [
            "strengths",
            "weaknesses",
            "recommendations",
            "study_plan",
            "overall_feedback",
            "improvement_areas",
        ]
        for field in required_fields:
            if field not in analysis_data:
                analysis_data[field] = (
                    [] if field != "overall_feedback" else "Phân tích không khả dụng"
                )

        return analysis_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI analysis JSON: {e}")
        logger.error(f"Raw response was: {raw_response}")

        # Return default analysis
        return {
            "strengths": ["Tham gia làm bài kiểm tra"],
            "weaknesses": ["Cần phân tích chi tiết hơn"],
            "recommendations": ["Xem lại các câu trả lời sai"],
            "study_plan": ["Lập kế hoạch học tập dựa trên kết quả"],
            "overall_feedback": "Phân tích AI tạm thời không khả dụng. Vui lòng xem kết quả chi tiết.",
            "improvement_areas": ["Cần đánh giá thủ công"],
        }


def _generate_explanation(question, user_answer: str, correct_answer: str) -> str:
    """Tạo giải thích cơ bản cho câu trả lời sai."""

    if question.type == QuestionType.mcq:
        return f"Đáp án đúng là '{correct_answer}'. Bạn đã chọn '{user_answer}'."
    elif question.type == QuestionType.tf:
        return f"Đáp án đúng là '{correct_answer}'. Câu này là {'đúng' if correct_answer.lower() in ['true', 'đúng'] else 'sai'}."
    elif question.type == QuestionType.fill_blank:
        return f"Từ/cụm từ đúng cần điền là '{correct_answer}'. Bạn đã điền '{user_answer}'."
    else:
        return f"Đáp án đúng: {correct_answer}. Bạn trả lời: {user_answer}."


def _determine_grade(score_percentage: float, grading_scale: Dict[str, tuple]) -> Grade:
    """Xác định grade dựa trên điểm số và thang điểm."""

    for grade_letter, (min_score, max_score) in grading_scale.items():
        if min_score <= score_percentage <= max_score:
            return Grade(grade_letter)

    # Default fallback
    return Grade.F


def _save_evaluation_history(result: EvaluationResult) -> None:
    """Lưu lịch sử đánh giá (stub implementation)."""

    # TODO: Implement actual storage (database, file system, etc.)
    logger.info(f"Saving evaluation history for {result.evaluation_id}")

    # For now, just log the save action
    # In production, this could save to:
    # - SQLite database
    # - PostgreSQL
    # - JSON file
    # - Cloud storage
    pass


__all__ = ["evaluate_quiz"]
