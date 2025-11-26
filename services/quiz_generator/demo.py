#!/usr/bin/env python3
"""
Demo sử dụng Quiz Generator như một function

Cách sử dụng:
python demo.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from quiz_generator.main import generate_quiz
import json


def demo_basic():
    """Demo cơ bản với dữ liệu mẫu"""
    print("=" * 60)
    print("🎯 DEMO CƠ BẢN - Quiz Generator Function")
    print("=" * 60)

    # Dữ liệu đầu vào
    input_data = {
        "sections": [
            {
                "id": "s1",
                "summary": "Việt Nam là một quốc gia Đông Nam Á với thủ đô Hà Nội, diện tích 331,212 km², dân số 97 triệu người.",
            }
        ],
        "config": {"n_questions": 2, "types": ["mcq", "tf"]},
    }

    print("📝 INPUT:")
    print(json.dumps(input_data, ensure_ascii=False, indent=2))

    print("\n🔄 Generating quiz...")

    try:
        result = generate_quiz(input_data)
        print("\n✅ OUTPUT:")
        print(result)

    except Exception as e:
        print(f"\n❌ Error: {e}")


def demo_advanced():
    """Demo với nhiều section và loại câu hỏi"""
    print("\n" + "=" * 60)
    print("🚀 DEMO NÂNG CAO - Nhiều Section & Loại Câu Hỏi")
    print("=" * 60)

    input_data = {
        "sections": [
            {
                "id": "python_intro",
                "summary": "Python là ngôn ngữ lập trình cấp cao, dễ học, có cú pháp đơn giản và rõ ràng.",
            },
            {
                "id": "python_usage",
                "summary": "Python được sử dụng trong AI, machine learning, web development và data science.",
            },
            {
                "id": "vietnam_geo",
                "summary": "Việt Nam nằm ở Đông Nam Á, giáp Trung Quốc, Lào, Campuchia và biển Đông.",
            },
        ],
        "config": {"n_questions": 5, "types": ["mcq", "tf", "fill_blank"]},
    }

    print("📝 INPUT:")
    print(json.dumps(input_data, ensure_ascii=False, indent=2))

    print("\n🔄 Generating quiz...")

    try:
        result = generate_quiz(input_data)
        print("\n✅ OUTPUT:")
        print(result)

        # Parse và hiển thị summary
        quiz_data = json.loads(result)
        print(f"\n📊 SUMMARY:")
        print(f"   Quiz ID: {quiz_data['id']}")
        print(f"   Số câu hỏi: {len(quiz_data['questions'])}")

        for i, q in enumerate(quiz_data["questions"], 1):
            print(f"   Câu {i}: {q['type'].upper()} - {q['stem'][:50]}...")

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    demo_basic()
    demo_advanced()

    print(f"\n" + "=" * 60)
    print("🎉 Demo hoàn thành!")
    print("📚 Tài liệu: Xem README.md để biết thêm chi tiết")
    print("=" * 60)
