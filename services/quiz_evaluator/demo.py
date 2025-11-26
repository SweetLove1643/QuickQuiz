"""
Quiz Evaluator Demo
==================

This module demonstrates how to use the quiz_evaluator package
to evaluate quiz results and provide learning analytics.
"""

import json
from tasks import evaluate_quiz


def demo_basic_evaluation():
    """Demo: Đánh giá cơ bản một bài kiểm tra Python."""

    request_data = {
        "submission": {
            "quiz_id": "quiz-python-basics-001",
            "questions": [
                {
                    "id": "q1",
                    "type": "mcq",
                    "stem": "Python là ngôn ngữ lập trình gì?",
                    "options": ["Compiled", "Interpreted", "Assembly"],
                    "correct_answer": "Interpreted",
                    "user_answer": "Interpreted",
                    "topic": "Python Basics",
                },
                {
                    "id": "q2",
                    "type": "tf",
                    "stem": "Python hỗ trợ lập trình hướng đối tượng.",
                    "options": ["Đúng", "Sai"],
                    "correct_answer": "Đúng",
                    "user_answer": "Sai",
                    "topic": "Python OOP",
                },
                {
                    "id": "q3",
                    "type": "fill_blank",
                    "stem": "Để khai báo biến trong Python: x _____ 10",
                    "options": None,
                    "correct_answer": "=",
                    "user_answer": "=",
                    "topic": "Python Syntax",
                },
                {
                    "id": "q4",
                    "type": "mcq",
                    "stem": "Vòng lặp nào dùng để lặp qua danh sách?",
                    "options": ["for", "while", "do-while"],
                    "correct_answer": "for",
                    "user_answer": "while",
                    "topic": "Python Loops",
                },
                {
                    "id": "q5",
                    "type": "tf",
                    "stem": "List trong Python có thể chứa nhiều kiểu dữ liệu.",
                    "options": ["Đúng", "Sai"],
                    "correct_answer": "Đúng",
                    "user_answer": None,  # Không trả lời
                    "topic": "Python Data Types",
                },
            ],
            "user_info": {
                "user_id": "student123",
                "completion_time": 180,  # 3 minutes
                "session_id": "session_demo_001",
            },
        },
        "config": {
            "include_explanations": True,
            "include_ai_analysis": True,
            "save_history": True,
        },
    }

    print("=== Demo: Basic Quiz Evaluation ===")
    print("Input:")
    print(json.dumps(request_data, ensure_ascii=False, indent=2))
    print("\nOutput:")

    result = evaluate_quiz(request_data)
    formatted_result = json.loads(result)
    print(json.dumps(formatted_result, ensure_ascii=False, indent=2))

    return result


def demo_advanced_evaluation():
    """Demo: Đánh giá nâng cao với nhiều chủ đề."""

    request_data = {
        "submission": {
            "quiz_id": "quiz-mixed-topics-002",
            "questions": [
                {
                    "id": "q1",
                    "type": "mcq",
                    "stem": "HTML là viết tắt của gì?",
                    "options": [
                        "HyperText Markup Language",
                        "High Tech Modern Language",
                        "Home Tool Markup Language",
                    ],
                    "correct_answer": "HyperText Markup Language",
                    "user_answer": "HyperText Markup Language",
                    "topic": "Web Development",
                    "difficulty": "easy",
                },
                {
                    "id": "q2",
                    "type": "fill_blank",
                    "stem": "CSS dùng để _____ trang web.",
                    "options": None,
                    "correct_answer": "tạo kiểu",
                    "user_answer": "thiết kế",
                    "topic": "Web Development",
                    "difficulty": "medium",
                },
                {
                    "id": "q3",
                    "type": "mcq",
                    "stem": "Thuật toán sắp xếp nào có độ phức tạp O(n log n)?",
                    "options": ["Bubble Sort", "Merge Sort", "Selection Sort"],
                    "correct_answer": "Merge Sort",
                    "user_answer": "Bubble Sort",
                    "topic": "Algorithms",
                    "difficulty": "hard",
                },
                {
                    "id": "q4",
                    "type": "tf",
                    "stem": "JavaScript chỉ chạy được trong browser.",
                    "options": ["Đúng", "Sai"],
                    "correct_answer": "Sai",
                    "user_answer": "Đúng",
                    "topic": "JavaScript",
                    "difficulty": "medium",
                },
                {
                    "id": "q5",
                    "type": "fill_blank",
                    "stem": "SQL là viết tắt của Structured _____ Language.",
                    "options": None,
                    "correct_answer": "Query",
                    "user_answer": "Query",
                    "topic": "Database",
                    "difficulty": "easy",
                },
            ],
            "user_info": {
                "user_id": "student456",
                "completion_time": 420,  # 7 minutes
                "session_id": "session_demo_002",
            },
        },
        "config": {
            "include_explanations": True,
            "include_ai_analysis": True,
            "save_history": False,
            "grading_scale": {
                "A": (95, 100),
                "B": (85, 94),
                "C": (75, 84),
                "D": (65, 74),
                "F": (0, 64),
            },
        },
    }

    print("\n=== Demo: Advanced Multi-Topic Evaluation ===")
    print("Input:")
    print(json.dumps(request_data, ensure_ascii=False, indent=2))
    print("\nOutput:")

    result = evaluate_quiz(request_data)
    formatted_result = json.loads(result)
    print(json.dumps(formatted_result, ensure_ascii=False, indent=2))

    return result


def demo_simple_scoring():
    """Demo: Chỉ tính điểm không có AI analysis."""

    request_data = {
        "submission": {
            "quiz_id": "quiz-simple-001",
            "questions": [
                {
                    "id": "q1",
                    "type": "tf",
                    "stem": "Trái Đất quay quanh Mặt Trời.",
                    "options": ["Đúng", "Sai"],
                    "correct_answer": "Đúng",
                    "user_answer": "Đúng",
                    "topic": "Astronomy",
                },
                {
                    "id": "q2",
                    "type": "mcq",
                    "stem": "Thủ đô của Việt Nam là?",
                    "options": ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng"],
                    "correct_answer": "Hà Nội",
                    "user_answer": "Hà Nội",
                    "topic": "Geography",
                },
            ],
            "user_info": {"completion_time": 30},
        },
        "config": {
            "include_explanations": False,
            "include_ai_analysis": False,  # Tắt AI analysis
            "save_history": False,
        },
    }

    print("\n=== Demo: Simple Scoring Only ===")
    print("Input:")
    print(json.dumps(request_data, ensure_ascii=False, indent=2))
    print("\nOutput:")

    result = evaluate_quiz(request_data)
    formatted_result = json.loads(result)
    print(json.dumps(formatted_result, ensure_ascii=False, indent=2))

    return result


def run_all_demos():
    """Run all available demos."""
    print("Quiz Evaluator - All Demos")
    print("=" * 60)

    try:
        demo_basic_evaluation()
        demo_advanced_evaluation()
        demo_simple_scoring()

        print("\n" + "=" * 60)
        print("All demos completed successfully!")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    run_all_demos()
