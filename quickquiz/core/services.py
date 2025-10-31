import io
from paddleocr import PaddleOCR
from PyPDF2 import PdfReader
from PIL import Image
import numpy as np

ocr_model = PaddleOCR(lang='vi')  # nếu bạn muốn vi: lang='vi' (cần model vi)

def extract_text_from_image(file_obj):
    img = Image.open(file_obj).convert("RGB")
    np_img = np.array(img)
    result = ocr_model.ocr(np_img)

    lines = []

    # result là danh sách batch; mỗi batch là danh sách dòng OCR
    if not result or not result[0]:
        return ""

    for line in result[0]:
        # mỗi line thường có dạng: [ [box], [text, conf] ]
        if len(line) < 2:
            continue
        text_part = line[1]

        if isinstance(text_part, (list, tuple)):
            text = text_part[0] if len(text_part) > 0 else ""
            conf = text_part[1] if len(text_part) > 1 else None
        elif isinstance(text_part, str):
            text = text_part
            conf = None
        else:
            text = str(text_part)
            conf = None

        if text.strip():
            lines.append(text.strip())

    return "\n".join(lines)

def extract_text_from_pdf(file_obj):
    # cố gắng đọc text layer trước
    reader = PdfReader(file_obj)
    full_text = []
    for page in reader.pages:
        full_text.append(page.extract_text() or "")
    text_joined = "\n".join(full_text).strip()

    if text_joined:
        return text_joined

    # fallback: render trang -> OCR từng trang (phức tạp hơn vì cần convert PDF page -> image)
    # để đơn giản trong bản MVP ta tạm coi PDF có text layer
    # (Bạn có thể dùng pdf2image + PaddleOCR cho bản nâng cao)
    return text_joined

def summarize_text(raw_text, max_sentences=3):
    """
    MVP: tóm tắt thô = lấy các câu đầu tiên.
    Sau này bạn thay bằng LLM.
    """
    sentences = raw_text.split(".")
    summary = ". ".join(sentences[:max_sentences]).strip()
    return summary

def generate_questions(raw_text, num_questions=3):
    """
    MVP: sinh câu hỏi kiểu 'nội dung chính của đoạn X là gì?'
    Sau này thay bằng LLM.
    Trả về list dict [{question_text, ideal_answer}, ...]
    """
    # Lấy 3 câu đầu làm nguồn câu hỏi
    sentences = [s.strip() for s in raw_text.split(".") if s.strip()]
    questions = []
    for i, s in enumerate(sentences[:num_questions]):
        q = {
            "question_text": f"Câu hỏi {i+1}: Ý chính của câu sau là gì?\n\"{s}\"",
            "ideal_answer": s
        }
        questions.append(q)
    return questions

def score_answer(user_resp, ideal):
    """
    MVP chấm điểm: dựa trên tỉ lệ overlap từ khoá.
    Rất thô nhưng chạy offline không cần AI.
    """
    user_words = set(user_resp.lower().split())
    ideal_words = set(ideal.lower().split())

    if not ideal_words:
        return 0.0, "Không có đáp án mẫu để so sánh."

    overlap = user_words.intersection(ideal_words)
    score_ratio = len(overlap) / len(ideal_words)

    feedback = (
        f"Tỉ lệ ý trùng: {round(score_ratio*100, 1)}%. "
        "Cố gắng trả lời sát nội dung quan trọng hơn."
    )

    # bạn có thể map thành thang 0-100
    return score_ratio * 100.0, feedback
