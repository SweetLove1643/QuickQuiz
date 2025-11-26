# Ngăn chặn AI Hallucination trong QuickQuiz

## 🚨 Vấn đề AI Hallucination

### Định nghĩa

AI Hallucination xảy ra khi mô hình AI tạo ra thông tin sai lệch, không chính xác hoặc bịa đặt mà vẫn trình bày một cách tự tin.

### Rủi ro trong QuickQuiz

1. **Quiz Generator**: Tạo câu hỏi với thông tin sai, đáp án không chính xác
2. **Quiz Evaluator**: Phân tích kết quả sai lệch, lời khuyên không phù hợp

## 🛡️ Chiến lược ngăn chặn

### 1. Content Validation Pipeline

```python
# services/shared/validators.py
class ContentValidator:
    def validate_quiz_content(self, questions):
        """Kiểm tra độ tin cậy nội dung câu hỏi"""
        validation_results = []

        for q in questions:
            result = {
                'question_id': q['id'],
                'confidence_score': 0.0,
                'issues': [],
                'suggestions': []
            }

            # 1. Fact-checking cơ bản
            if self._contains_specific_facts(q):
                result['issues'].append('Contains specific facts - needs verification')

            # 2. Kiểm tra logic đáp án
            if not self._validate_answer_logic(q):
                result['issues'].append('Answer logic inconsistent')

            # 3. Kiểm tra tính cập nhật
            if self._contains_temporal_info(q):
                result['issues'].append('Contains time-sensitive information')

            validation_results.append(result)

        return validation_results
```

### 2. Multi-Model Consensus

```python
# services/shared/consensus.py
class ModelConsensus:
    def __init__(self):
        self.models = ['gemini-2.5-flash', 'gemini-2.5-pro']

    def generate_with_consensus(self, prompt, min_agreement=0.8):
        """Tạo nội dung với sự đồng thuận từ nhiều model"""
        results = []

        for model in self.models:
            try:
                result = self.adapter.generate(prompt, model=model)
                results.append(result)
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")

        # So sánh kết quả và tính độ đồng thuận
        consensus_score = self._calculate_consensus(results)

        if consensus_score >= min_agreement:
            return self._merge_results(results)
        else:
            raise ValidationError(f"Low consensus score: {consensus_score}")
```

### 3. Prompt Engineering Anti-Hallucination

```python
# services/quiz_generator/prompts.py
def get_anti_hallucination_prompt():
    return """
Bạn là chuyên gia tạo câu hỏi giáo dục. QUAN TRỌNG:

⚠️ QUY TẮC CHỐNG SAI LỆCH THÔNG TIN:
1. CHỈ sử dụng thông tin bạn CHẮC CHẮN là đúng
2. Nếu KHÔNG CHẮC về thông tin, hãy tạo câu hỏi về khái niệm chung thay vì sự kiện cụ thể
3. Với câu hỏi về số liệu, ngày tháng, sự kiện lịch sử: hãy ghi chú "Cần kiểm tra thông tin"
4. Ưu tiên câu hỏi về nguyên lý, khái niệm, logic thay vì sự kiện cụ thể
5. Đối với thông tin khoa học/kỹ thuật: chỉ sử dụng kiến thức cơ bản được công nhận rộng rãi

📋 TEMPLATE AN TOÀN:
- "Khái niệm X có đặc điểm gì?" (thay vì "X được phát minh năm nào?")
- "Nguyên lý Y hoạt động như thế nào?" (thay vì "Công ty Z có bao nhiêu nhân viên?")
- "Điều gì xảy ra khi..." (thay vì "Vào ngày DD/MM/YYYY điều gì đã xảy ra?")

🎯 NỘI DUNG CẦN TẠO: {content_topic}
"""
```

### 4. Real-time Fact Checking

```python
# services/shared/fact_checker.py
class FactChecker:
    def __init__(self):
        self.knowledge_bases = {
            'wikipedia_api': 'https://en.wikipedia.org/api/rest_v1/',
            'wolfram_alpha': 'http://api.wolframalpha.com/v2/',
        }

    def verify_factual_claims(self, question_data):
        """Kiểm tra tính chính xác của thông tin trong câu hỏi"""
        claims = self._extract_claims(question_data)
        verification_results = []

        for claim in claims:
            result = {
                'claim': claim,
                'verified': False,
                'confidence': 0.0,
                'sources': []
            }

            # Kiểm tra với các nguồn đáng tin cậy
            if self._check_against_knowledge_base(claim):
                result['verified'] = True
                result['confidence'] = 0.85

            verification_results.append(result)

        return verification_results
```

### 5. Human-in-the-loop Review

```python
# services/shared/review_queue.py
class ReviewQueue:
    def __init__(self):
        self.review_criteria = {
            'high_risk_topics': ['medicine', 'law', 'finance', 'current_events'],
            'confidence_threshold': 0.7,
            'consensus_threshold': 0.8
        }

    def flag_for_review(self, content, metadata):
        """Đánh dấu nội dung cần review thủ công"""
        risk_score = self._calculate_risk_score(content, metadata)

        if risk_score > self.review_criteria['confidence_threshold']:
            return {
                'requires_review': True,
                'priority': 'high' if risk_score > 0.9 else 'medium',
                'reasons': self._get_risk_reasons(content),
                'suggested_reviewers': self._get_expert_reviewers(content)
            }

        return {'requires_review': False}
```

## 🔍 Detection Methods

### 1. Confidence Scoring

```python
def calculate_confidence_score(response_data, model_metadata):
    """Tính điểm tin cậy của response"""
    factors = {
        'response_length': len(response_data.get('text', '')),
        'specific_claims': count_specific_facts(response_data),
        'model_temperature': model_metadata.get('temperature', 0.7),
        'prompt_specificity': analyze_prompt_specificity(model_metadata.get('prompt'))
    }

    # Logic tính toán confidence score
    confidence = base_score * modifier_factors
    return min(confidence, 1.0)
```

### 2. Inconsistency Detection

```python
def detect_inconsistencies(quiz_questions):
    """Phát hiện mâu thuẫn trong bộ câu hỏi"""
    inconsistencies = []

    for i, q1 in enumerate(quiz_questions):
        for j, q2 in enumerate(quiz_questions[i+1:], i+1):
            if self._questions_contradict(q1, q2):
                inconsistencies.append({
                    'question_1': q1['id'],
                    'question_2': q2['id'],
                    'type': 'contradiction',
                    'description': self._describe_contradiction(q1, q2)
                })

    return inconsistencies
```

## 📊 Monitoring & Logging

### 1. Hallucination Metrics

```python
# services/shared/metrics.py
class HallucinationMetrics:
    def track_metrics(self):
        return {
            'daily_flagged_content': self._count_flagged_today(),
            'verification_success_rate': self._get_verification_rate(),
            'human_override_rate': self._get_override_rate(),
            'confidence_score_distribution': self._get_confidence_distribution()
        }
```

### 2. Audit Trail

```python
# services/shared/audit.py
class ContentAudit:
    def log_generation_process(self, content_id, process_data):
        """Ghi log quá trình tạo nội dung"""
        audit_entry = {
            'content_id': content_id,
            'timestamp': datetime.now(),
            'model_used': process_data['model'],
            'prompt_hash': hashlib.sha256(process_data['prompt'].encode()).hexdigest(),
            'confidence_score': process_data['confidence'],
            'validation_results': process_data['validations'],
            'review_status': process_data.get('review_status', 'pending')
        }

        self.audit_db.insert(audit_entry)
```

## 🎯 Implementation Checklist

### Giai đoạn 1: Foundation (Tuần 1-2)

- [ ] Tạo ContentValidator class
- [ ] Implement confidence scoring
- [ ] Setup audit logging
- [ ] Add hallucination detection metrics

### Giai đoạn 2: Advanced Validation (Tuần 3-4)

- [ ] Multi-model consensus system
- [ ] Fact-checking integration
- [ ] Inconsistency detection
- [ ] Review queue system

### Giai đoạn 3: Monitoring (Tuần 5-6)

- [ ] Dashboard cho hallucination metrics
- [ ] Alert system cho high-risk content
- [ ] A/B testing cho validation methods
- [ ] Performance optimization

## 🚦 Quality Gates

### Before Production Deployment

1. ✅ Confidence score > 0.75 cho tất cả câu hỏi
2. ✅ Multi-model consensus > 80%
3. ✅ Zero high-risk content flags
4. ✅ Human review completed cho medium-risk content

### Runtime Monitoring

1. 📊 Track hallucination detection rate
2. 🔔 Alert nếu confidence score giảm dưới threshold
3. 📈 Monitor user feedback về content quality
4. 🔍 Regular audit của flagged content

---

💡 **Remember**: Mục tiêu không phải là loại bỏ hoàn toàn rủi ro, mà là giảm thiểu tối đa và có hệ thống phát hiện kịp thời.
