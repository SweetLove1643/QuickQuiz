from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import default_storage
from django.conf import settings
import os
from .models import Document
from .services import (
    extract_text_from_image,
    extract_text_from_pdf,
    summarize_text,
    generate_questions,
)
from quiz.models import Question

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
        full_path = os.path.join(settings.MEDIA_ROOT, saved_path)
        if content_type.startswith("image/"):
            text = extract_text_from_image(full_path)
        elif content_type == "application/pdf":
            text = extract_text_from_pdf(full_path)
        else:
            text = ""

        # summary
        summary = summarize_text(text)

        # save back
        doc.extracted_text = text
        doc.summary_text = summary
        doc.save()

        # sinh câu hỏi và lưu xuống DB Question
        qs = generate_questions(text)
        for q in qs:
            Question.objects.create(
                document=doc,
                question_text=q["question_text"],
                ideal_answer=q["ideal_answer"],
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
