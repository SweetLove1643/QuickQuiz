#!/usr/bin/env python3
"""
Quiz Generator - Simple Function Interface

Tạo câu hỏi trắc nghiệm từ nội dung văn bản sử dụng Google Gemini API.
Hỗ trợ 3 loại câu hỏi: MCQ (trắc nghiệm), TF (đúng/sai), Fill-blank (điền khuyết).
"""

import json
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from quiz_generator.tasks import generate_quiz_job


def generate_quiz(input_data: dict) -> str:
    """
    Tạo câu hỏi từ nội dung đầu vào.

    Args:
        input_data (dict): Dữ liệu đầu vào với format:
        {
            "sections": [
                {"id": "s1", "summary": "Nội dung tóm tắt 1"},
                {"id": "s2", "summary": "Nội dung tóm tắt 2"}
            ],
            "config": {
                "n_questions": 3,
                "types": ["mcq", "tf", "fill_blank"]
            }
        }

    Returns:
        str: Chuỗi JSON chứa kết quả quiz đã được tạo

    Raises:
        ValueError: Nếu input không hợp lệ
        RuntimeError: Nếu không thể tạo quiz (lỗi API, network, etc.)
    """
    try:
        # Validate input
        if not isinstance(input_data, dict):
            raise ValueError("Input phải là dict")

        if "sections" not in input_data or not input_data["sections"]:
            raise ValueError("Cần có ít nhất 1 section trong input")

        # Generate quiz using existing pipeline
        result = generate_quiz_job("api-job", input_data)

        # Return JSON string
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        raise RuntimeError(f"Không thể tạo quiz: {e}")


def main():
    """Demo function với dữ liệu mẫu"""

    # Dữ liệu mẫu
    sample_input = {
        "sections": [
            {
                "id": "s1",
                "summary": "Việt Nam là một quốc gia ở Đông Nam Á với thủ đô là Hà Nội. Diện tích khoảng 331,000 km² với dân số gần 98 triệu người.",
            },
            {
                "id": "s2",
                "summary": "Python là ngôn ngữ lập trình phổ biến, dễ học với cú pháp đơn giản. Được sử dụng rộng rãi trong AI, web development và data science.",
            },
        ],
        "config": {"n_questions": 4, "types": ["mcq", "tf", "fill_blank"]},
    }

    try:
        print("🚀 Quiz Generator Demo")
        print("=" * 50)
        print("📝 Input:")
        print(json.dumps(sample_input, ensure_ascii=False, indent=2))
        print("\n🔄 Đang tạo câu hỏi...")

        # Gọi function tạo quiz
        result_json = generate_quiz(sample_input)

        print("\n✅ Kết quả:")
        print(result_json)

    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
