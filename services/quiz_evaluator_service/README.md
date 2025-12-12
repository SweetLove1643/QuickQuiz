# Quiz Evaluator

Hệ thống đánh giá kết quả bài kiểm tra tự động và phân tích học tập thông minh sử dụng Google Gemini AI.

## Tính năng

- **Tự động tính điểm** và xếp loại (A, B, C, D, F)
- **Phân tích theo chủ đề** - hiệu suất từng topic/category
- **AI-powered recommendations** - đề xuất cải thiện từ Gemini AI
- **Giải thích chi tiết** cho câu trả lời sai
- **Lưu lịch sử đánh giá** để theo dõi tiến bộ
- **JSON I/O thuần túy** - không lưu file, chỉ xử lý dữ liệu
- **REST API với FastAPI** - tích hợp dễ dàng với frontend

## Cài đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd Hackathon_11_2025
```

### 2. Cài đặt dependencies

```bash
cd quiz_evaluator
pip install -r requirements.txt
```

### 3. Cấu hình API key

Tạo file `.env` trong thư mục gốc:

```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

## Sử dụng

### 1. Import và sử dụng trực tiếp

```python
from quiz_evaluator.tasks import evaluate_quiz

# Chuẩn bị dữ liệu đánh giá
request_data = {
    "submission": {
        "quiz_id": "quiz-python-001",
        "questions": [
            {
                "id": "q1",
                "type": "mcq",
                "stem": "Python là ngôn ngữ gì?",
                "options": ["Compiled", "Interpreted", "Assembly"],
                "correct_answer": "Interpreted",
                "user_answer": "Interpreted",
                "topic": "Python Basics"
            }
        ],
        "user_info": {
            "user_id": "student123",
            "completion_time": 180
        }
    },
    "config": {
        "include_explanations": True,
        "include_ai_analysis": True,
        "save_history": True
    }
}

# Đánh giá kết quả
result_json = evaluate_quiz(request_data)
print(result_json)
```

### 2. Sử dụng qua command line

```bash
# Tạo input.json
echo '{"submission": {...}, "config": {...}}' > input.json

# Chạy evaluator
cd quiz_evaluator
python -m quiz_evaluator.main < ../input.json
```

### 3. Chạy API server

```bash
cd quiz_evaluator
python api.py

# Server chạy trên http://127.0.0.1:8005
# Docs: http://127.0.0.1:8005/docs
```

### 4. Chạy demo

```python
from quiz_evaluator.demo import run_all_demos
run_all_demos()
```

## Format dữ liệu

### Input Format

```json
{
  "submission": {
    "quiz_id": "quiz-12345",
    "questions": [
      {
        "id": "q1",
        "type": "mcq",
        "stem": "Câu hỏi...",
        "options": ["A", "B", "C"],
        "correct_answer": "A",
        "user_answer": "B",
        "topic": "Python Basics"
      }
    ],
    "user_info": {
      "user_id": "student123",
      "completion_time": 300,
      "session_id": "session456"
    }
  },
  "config": {
    "include_explanations": true,
    "include_ai_analysis": true,
    "save_history": true
  }
}
```

### Output Format

```json
{
  "evaluation_id": "eval-abc123",
  "quiz_id": "quiz-12345",
  "timestamp": "2025-11-15T10:30:00",
  "summary": {
    "total_questions": 5,
    "correct_answers": 3,
    "incorrect_answers": 1,
    "unanswered": 1,
    "score_percentage": 60.0,
    "total_points": 3.0,
    "max_points": 5.0,
    "grade": "D"
  },
  "question_results": [
    {
      "question_id": "q1",
      "is_correct": false,
      "topic": "Python Basics",
      "question_type": "mcq",
      "correct_answer": "A",
      "user_answer": "B",
      "explanation": "Đáp án đúng là 'A'. Bạn đã chọn 'B'.",
      "points": 0.0
    }
  ],
  "topic_breakdown": [
    {
      "topic": "Python Basics",
      "total_questions": 3,
      "correct_answers": 2,
      "accuracy_rate": 66.7,
      "recommendations": ["Củng cố kiến thức về Python Basics"]
    }
  ],
  "analysis": {
    "strengths": ["Hiểu tốt về cú pháp cơ bản"],
    "weaknesses": ["Cần cải thiện về OOP"],
    "recommendations": ["Học lại Classes và Objects"],
    "study_plan": ["Tuần 1: Ôn OOP basics", "Tuần 2: Practice projects"],
    "overall_feedback": "Bạn có nền tảng tốt, cần tập trung vào OOP",
    "improvement_areas": ["Object-Oriented Programming"]
  }
}
```

## Loại câu hỏi hỗ trợ

- **mcq** (Multiple Choice) - Trắc nghiệm nhiều lựa chọn
- **tf** (True/False) - Đúng/Sai
- **fill_blank** (Fill in the Blank) - Điền khuyết

## Hệ thống xếp loại

| Grade | Score Range | Mô tả      |
| ----- | ----------- | ---------- |
| A     | 90-100%     | Xuất sắc   |
| B     | 80-89%      | Tốt        |
| C     | 70-79%      | Khá        |
| D     | 60-69%      | Trung bình |
| F     | <60%        | Yếu        |

## API Endpoints

### Quiz Evaluator API (Port 8005):

- `GET /health` - Health check
- `POST /quiz/evaluate` - Đánh giá kết quả bài kiểm tra
- `GET /quiz/grading-scale` - Xem thang điểm hiện tại
- `GET /docs` - Interactive API documentation

### Test với PowerShell:

```powershell
# Health check
Invoke-RestMethod -Uri "http://127.0.0.1:8005/health" -Method GET

# Xem thang điểm
Invoke-RestMethod -Uri "http://127.0.0.1:8005/quiz/grading-scale" -Method GET

# Đánh giá quiz (cần chuẩn bị $body với JSON data)
$body = '{"submission": {...}, "config": {...}}'
Invoke-RestMethod -Uri "http://127.0.0.1:8005/quiz/evaluate" -Method POST -Body $body -ContentType "application/json"
```

## Cấu hình Environment

| Biến             | Mô tả                                | Mặc định         |
| ---------------- | ------------------------------------ | ---------------- |
| `GEMINI_API_KEY` | API key cho Google Gemini (bắt buộc) | -                |
| `GEMINI_MODEL`   | Model Gemini sử dụng                 | gemini-2.5-flash |
| `USE_CANNED_LLM` | Sử dụng response giả (test)          | 0                |

## AI Analysis Features

### Phân tích thông minh:

- **Strengths** - Điểm mạnh của học viên
- **Weaknesses** - Điểm yếu cần cải thiện
- **Recommendations** - Đề xuất học tập cụ thể
- **Study Plan** - Kế hoạch học tập từng bước
- **Overall Feedback** - Nhận xét tổng quan
- **Improvement Areas** - Lĩnh vực ưu tiên cải thiện

### Topic Analysis:

- Phân tích hiệu suất theo từng chủ đề
- Tỷ lệ chính xác từng topic
- Đề xuất cụ thể cho topic yếu
- Ưu tiên các chủ đề cần học lại

## Ví dụ sử dụng

### Đánh giá bài kiểm tra Python cơ bản

```python
python_quiz = {
    "submission": {
        "quiz_id": "python-basics-001",
        "questions": [
            {
                "id": "q1",
                "type": "mcq",
                "stem": "Python là ngôn ngữ gì?",
                "options": ["Compiled", "Interpreted", "Assembly"],
                "correct_answer": "Interpreted",
                "user_answer": "Compiled",  # Sai
                "topic": "Python Basics"
            },
            {
                "id": "q2",
                "type": "tf",
                "stem": "Python hỗ trợ OOP.",
                "options": ["Đúng", "Sai"],
                "correct_answer": "Đúng",
                "user_answer": "Đúng",  # Đúng
                "topic": "Python OOP"
            }
        ]
    },
    "config": {
        "include_ai_analysis": True,
        "save_history": True
    }
}

result = evaluate_quiz(python_quiz)
```

## Troubleshooting

### Lỗi thường gặp:

**1. API Key missing:**

```bash
# Kiểm tra .env file
cat .env | grep GEMINI_API_KEY
```

**2. JSON format error:**

```python
# Validate input schema trước khi gửi
from quiz_evaluator.schemas import QuizSubmission
submission = QuizSubmission(**your_data)
```

**3. AI analysis failed:**

```bash
# Test với canned response
export USE_CANNED_LLM=1
python demo.py
```

## Architecture

```
quiz_evaluator/
├── __init__.py          # Package exports
├── main.py              # CLI entry point
├── api.py               # FastAPI REST server
├── tasks.py             # Core evaluation logic
├── llm_adapter.py       # Gemini AI analysis adapter
├── schemas.py           # Pydantic data models
├── demo.py              # Usage examples
├── requirements.txt     # Dependencies
└── README.md            # Documentation
```

## Integration với Quiz Generator

Quiz Evaluator hoạt động hoàn hảo với output từ Quiz Generator:

```python
# 1. Tạo quiz
quiz_data = generate_quiz(content)
quiz_result = json.loads(quiz_data)

# 2. Người dùng làm bài và submit answers
# 3. Đánh giá kết quả
evaluation_input = {
    "submission": {
        "quiz_id": quiz_result["id"],
        "questions": quiz_result["questions"],  # Thêm user_answer cho mỗi question
        # ...
    }
}
evaluation_result = evaluate_quiz(evaluation_input)
```

## License

MIT License - xem file LICENSE để biết thêm chi tiết.

## Đóng góp

1. Fork repository
2. Tạo feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Mở Pull Request

## Liên hệ

Nếu có vấn đề hoặc đóng góp ý kiến, vui lòng tạo issue trên GitHub repository.
