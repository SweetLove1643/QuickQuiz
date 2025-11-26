# Quiz Generator

Hệ thống tạo câu hỏi trắc nghiệm tự động từ nội dung văn bản sử dụng Google Gemini API.

## 🎯 Tính năng

- **3 loại câu hỏi**: Trắc nghiệm (MCQ), Đúng/Sai (TF), Điền khuyết (Fill-blank)
- **Tiếng Việt**: Được tối ưu hóa cho nội dung tiếng Việt
- **API Gemini**: Sử dụng Google Gemini 2.5 Flash cho chất lượng cao và tốc độ nhanh
- **JSON I/O**: Input và output đều là định dạng JSON
- **Function Interface**: Sử dụng như một function Python đơn giản

## 🚀 Cài đặt

```bash
pip install -r requirements.txt
```

## 📖 Cách sử dụng

### Sử dụng như Function

```python
from quiz_generator.main import generate_quiz
import json

# Dữ liệu đầu vào
input_data = {
    "sections": [
        {
            "id": "s1",
            "summary": "Việt Nam là một quốc gia ở Đông Nam Á với thủ đô là Hà Nội."
        },
        {
            "id": "s2",
            "summary": "Python là ngôn ngữ lập trình phổ biến với cú pháp đơn giản."
        }
    ],
    "config": {
        "n_questions": 3,
        "types": ["mcq", "tf", "fill_blank"]
    }
}

# Tạo quiz
result_json = generate_quiz(input_data)
result = json.loads(result_json)

print(f"Quiz ID: {result['id']}")
print(f"Số câu hỏi: {len(result['questions'])}")
```

### Chạy Demo

```bash
# Demo cơ bản
python main.py

# Demo nâng cao với nhiều ví dụ
python demo.py
```

## 📋 Định dạng dữ liệu

### Input Format

```json
{
  "sections": [
    {
      "id": "section_1",
      "summary": "Nội dung tóm tắt phần 1..."
    },
    {
      "id": "section_2",
      "summary": "Nội dung tóm tắt phần 2..."
    }
  ],
  "config": {
    "n_questions": 5,
    "types": ["mcq", "tf", "fill_blank"]
  }
}
```

### Output Format

```json
{
  "id": "quiz-abc123",
  "questions": [
    {
      "id": "q1",
      "type": "mcq",
      "stem": "Câu hỏi trắc nghiệm?",
      "options": ["Đáp án A", "Đáp án B", "Đáp án C", "Đáp án D"],
      "answer": "Đáp án A",
      "source_sections": ["section_1"]
    },
    {
      "id": "q2",
      "type": "tf",
      "stem": "Câu hỏi đúng/sai?",
      "options": ["Đúng", "Sai"],
      "answer": "Đúng",
      "source_sections": ["section_1"]
    },
    {
      "id": "q3",
      "type": "fill_blank",
      "stem": "Câu hỏi điền _____ khuyết?",
      "options": null,
      "answer": "từ",
      "source_sections": ["section_2"]
    }
  ],
  "meta": {
    "source_count": 2
  }
}
```

## 🛠️ Cấu hình

### Biến môi trường (.env)

Tạo file `.env` trong thư mục gốc của project:

```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
USE_CANNED_LLM=0
```

> **Lấy API key**: Truy cập [Google AI Studio](https://makersuite.google.com/app/apikey) để tạo API key miễn phí.

| Biến             | Mô tả                      | Mặc định           |
| ---------------- | -------------------------- | ------------------ |
| `GEMINI_API_KEY` | API key của Google Gemini  | _Bắt buộc_         |
| `GEMINI_MODEL`   | Tên model Gemini           | `gemini-2.5-flash` |
| `USE_CANNED_LLM` | Sử dụng response giả (0/1) | `0`                |

### Loại câu hỏi

- **`mcq`**: Trắc nghiệm 4 lựa chọn
- **`tf`**: Đúng/Sai
- **`fill_blank`**: Điền từ khuyết (sử dụng dấu `_____`)

## 📁 Cấu trúc thư mục

```
quiz_generator/
├── main.py           # Entry point chính
├── demo.py           # File demo với các ví dụ
├── tasks.py          # Logic tạo quiz
├── llm_adapter.py    # Adapter cho Gemini API
├── schemas.py        # Data models
├── requirements.txt  # Dependencies
├── README.md         # Tài liệu này
└── __init__.py
```

## 🔧 Development

### Chạy tests

```bash
# Test function cơ bản
python main.py

# Test với dữ liệu custom
python demo.py
```

### Troubleshooting

**Lỗi API 404:**

- Kiểm tra API key có đúng không
- Đảm bảo model name là `gemini-2.5-flash` hoặc `gemini-2.5-pro`

**Lỗi network/timeout:**

- Kiểm tra kết nối internet
- Thử tăng timeout trong `llm_adapter.py`

**Test với canned response:**

```bash
# Set USE_CANNED_LLM=1 để test mà không cần API key
export USE_CANNED_LLM=1  # Linux/Mac
set USE_CANNED_LLM=1     # Windows
```

## 🏗️ Components

- **`main.py`** — Entry point và function interface chính
- **`demo.py`** — File demo với các ví dụ sử dụng
- **`tasks.py`** — Logic tạo quiz và xử lý pipeline
- **`llm_adapter.py`** — Adapter cho Google Gemini API
- **`schemas.py`** — Data models và validation với Pydantic
