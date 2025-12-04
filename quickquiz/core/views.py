from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import default_storage
from django.conf import settings
import os
from .models import Document
from .services import (
    extract_text_from_image,
    extract_text_from_pdf,
    summarize_and_generate,
)
from quiz.models import Question
import json

def upload_document_view(request):
    if request.method == "POST" and request.FILES.get("file"):
        f = request.FILES["file"]
        saved_path = default_storage.save(f"uploads/{f.name}", f)

        doc = Document.objects.create(
            uploaded_file=saved_path,
            original_filename=f.name,
        )

        # OCR / extract
        content_type = f.content_type  # ví dụ "image/png", "application/pdf"
        # full_path = os.path.join(settings.MEDIA_ROOT, saved_path)
        # if content_type.startswith("image/"):
        #     text = extract_text_from_image(full_path)
        # elif content_type == "application/pdf":
        #     text = extract_text_from_pdf(full_path)
        # else:
        #     text = ""

        text =  """
            Mô hình ngôn ngữ lớn, còn gọi là LLM, là các mô hình học sâu rất lớn, được đào tạo trước dựa trên một lượng dữ liệu khổng lồ. Bộ chuyển hóa cơ bản là tập hợp các mạng nơ-ron có một bộ mã hóa và một bộ giải mã với khả năng tự tập trung. Bộ mã hóa và bộ giải mã trích xuất ý nghĩa từ một chuỗi văn bản và hiểu mối quan hệ giữa các từ và cụm từ trong đó.

            Bộ chuyển hóa LLM có khả năng đào tạo không có giám sát, mặc dù lời giải thích chính xác hơn là bộ chuyển hóa thực hiện việc tự học. Thông qua quá trình này, bộ chuyển hóa học cách hiểu ngữ pháp, ngôn ngữ và kiến thức cơ bản.

            Khác với các mạng nơ-ron hồi quy (RNN) trước đó thường xử lý tuần tự dữ liệu đầu vào, bộ chuyển hóa xử lý song song toàn bộ trình tự. Điều này cho phép các nhà khoa học dữ liệu sử dụng GPU để đào tạo các LLM dựa trên bộ chuyển hóa, qua đó giảm đáng kể thời gian đào tạo.

            Kiến trúc mạng nơ-ron của bộ chuyển hóa cho phép việc sử dụng các mô hình rất lớn, thường có hàng trăm tỷ tham số. Các mô hình quy mô lớn như vậy có thể thu nạp một lượng dữ liệu khổng lồ, thường là từ Internet, nhưng cũng từ các nguồn, ví dụ như Common Crawl với hơn 50 tỷ trang web, và Wikipedia với khoảng 57 triệu trang.
            """

        # DeepSeek call API
        deepseek_result = json.loads(summarize_and_generate(text))
        

        # summary
        summary = deepseek_result["summary"]

        # save back
        doc.extracted_text = text
        doc.summary_text = summary
        doc.save()

        # sinh câu hỏi và lưu xuống DB Question
        qs = deepseek_result["questions"]
        for q in qs:
            Question.objects.create(
                document=doc,
                question_text=q["question"],
                correct_answer=q["correct_answer"],
                options_answer=q.get("options_answer", None),
            )

        return redirect("document_detail", doc_id=doc.id)

    return render(request, "core/upload.html")


def document_detail_view(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    questions = doc.questions.all()

    return render(request, "core/document_detail.html", {
        "doc": doc,
        "questions": questions,
    })
