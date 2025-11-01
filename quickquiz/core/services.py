import io
from paddleocr import PaddleOCR
from PyPDF2 import PdfReader
import unicodedata
from PIL import Image
import numpy as np
from transformers import (
    TrOCRProcessor, 
    VisionEncoderDecoderModel,
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
)
from pdf2image import convert_from_bytes
from peft import PeftModel
import torch
import re
#=========================================================#
# Cấu hình OCR với TrOCR + PaddleOCR cho trích xuất text
#=========================================================#

# ✅ PaddleOCR chỉ dùng để detect bbox
paddleocr = PaddleOCR(lang="vi")

# ✅ Model TrOCR dành cho text in
TROCR_MODEL = "microsoft/trocr-base-printed"

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Device:", device)

# ✅ Load TrOCR – thêm trust_remote_code nếu version mới
TrOCR_processor = TrOCRProcessor.from_pretrained(
    TROCR_MODEL,
    trust_remote_code=True
)

TrOCR_model = VisionEncoderDecoderModel.from_pretrained(
    TROCR_MODEL,
    trust_remote_code=True
).to(device)

#=========================================================#
# Cấu hình Tóm tắt với ViT5 + LoRA
#=========================================================#

# ==== Cấu hình cơ bản ====
BASE_MODEL = "VietAI/vit5-base"
LORA_PATH = "./Models/ViT5_checkpoint_epochs4"

summarize_base_model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL)
summarize_model = PeftModel.from_pretrained(summarize_base_model, LORA_PATH)
summarize_tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, use_fast=True)
summarize_tokenizer.padding_side = "right"


def extract_text_from_image(file_obj):
    def detect_text_boxes(image_path):
        """
        Nhận đầu vào: path ảnh
        Trả về: list bbox dạng [x1, y1, x2, y2]
        """

        # Chạy detect
        result = paddleocr.predict(image_path)

        bboxes = []

        #debug
        # print(file_obj)
        # print("Kết quả detect:", result)

        if result and "rec_boxes" in result[0]:
            for box in result[0]["rec_boxes"]:
                bboxes.append(box)
        else:
            print("Không phát hiện được vùng chữ nào.")
            return []

        return bboxes
    
    def crop_boxes(image_path, bboxes):
        """
        Input:
            image_path: đường dẫn ảnh gốc
            bboxes: list bbox dạng [x1, y1, x2, y2]
        Output:
            list các ảnh crop (PIL.Image)
        """
        img = Image.open(image_path).convert("RGB")
        crops = []

        for (x1, y1, x2, y2) in bboxes:
            crop = img.crop((x1, y1, x2, y2))
            crops.append(crop)

        return crops
    
    def normalize_case(text):
        text = text.lower()  # toàn bộ lower
        text = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)  # viết hoa đầu câu
        if text: text = text[0].upper() + text[1:]
        return text
    
    def trocr_read(image):
        # image: PIL.Image crop
        
        inputs = TrOCR_processor(image, return_tensors="pt").pixel_values.to(device)

        with torch.no_grad():
            generated_ids = TrOCR_model.generate(
                inputs,
                max_new_tokens=256,
                num_beams=4,
                early_stopping=True
            )

        text = TrOCR_processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        return normalize_case(text)

    
    bboxes = detect_text_boxes(file_obj)
    crops = crop_boxes(file_obj, bboxes)
    texts = [trocr_read(c) for c in crops]

    return "\n".join(texts)

def extract_text_from_pdf(file_obj):
    def normalize_pdf_text(text):
        # xoá space thừa
        text = re.sub(r"\s{2,}", " ", text)

        # xoá space giữa chữ + dấu tiếng Việt (phần lớn các case)
        text = re.sub(r"(\w)\s+(?=[\u0300-\u036f])", r"\1", text)

        # xoá space giữa phụ âm Việt (th- ng- qu- gi-... cực kỳ thường gặp)
        patterns = [
            r"t\s*h", r"n\s*g", r"n\s*h", r"c\s*h", r"q\s*u", r"g\s*i",
            r"t\s*r", r"d\s*đ"
        ]
        for p in patterns:
            text = re.sub(p, p.replace(r"\s*", ""), text, flags=re.IGNORECASE)

        return text

    reader = PdfReader(file_obj)
    full_text = []

    for i, page in enumerate(reader.pages):
        txt = page.extract_text()
        if txt and txt.strip():
            txt = normalize_pdf_text(txt)
            full_text.append(txt)
        else:
            # OCR fallback
            pages = convert_from_bytes(file_obj.read(), first_page=i+1, last_page=i+1)
            img = pages[0]
            full_text.append(extract_text_from_image(img))

    return "\n".join(full_text)

def summarize_text(text):
    """
    Sử dụng model summaries để tóm tắt văn bản.
    Model: mT5, ViT5,...
    """
    inputs = summarize_tokenizer(
        f'''Tóm tắt: {text}''',
        return_tensors="pt",
        truncation=True,
        max_length=512
    ).to(device)

    outputs = summarize_model.generate(
        **inputs,
        max_length=256,
        num_beams=5,
        early_stopping=True,
    )

    return summarize_tokenizer.decode(outputs[0], skip_special_tokens=True)

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
