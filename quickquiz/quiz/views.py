from django.shortcuts import render, redirect, get_object_or_404
from core.models import Document
from .models import Question, UserAnswer
from core.services import score_answer

def take_quiz_view(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    questions = Question.objects.filter(document=doc)

    return render(request, "quiz/take_quiz.html", {
        "doc": doc,
        "questions": questions,
    })

def submit_quiz_view(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    questions = Question.objects.filter(document=doc)

    if request.method == "POST":
        for q in questions:
            user_resp = request.POST.get(f"answer_{q.id}", "")
            score, feedback = score_answer(user_resp, q.ideal_answer)

            UserAnswer.objects.create(
                question=q,
                user_response=user_resp,
                score=score,
                feedback=feedback,
            )

        return redirect("quiz_result", doc_id=doc_id)

    # fallback nếu truy cập GET
    return redirect("take_quiz", doc_id=doc_id)

def result_view(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    questions = Question.objects.filter(document=doc)

    # gom kết quả để render
    qa_pairs = []
    total = 0
    count = 0
    for q in questions:
        # lấy câu trả lời mới nhất của user (ở đây đơn giản: cái cuối cùng)
        ans = q.user_answers.order_by('-created_at').first()
        if ans:
            qa_pairs.append({
                "question": q.question_text,
                "ideal": q.ideal_answer,
                "user": ans.user_response,
                "score": ans.score,
                "feedback": ans.feedback,
            })
            if ans.score is not None:
                total += ans.score
                count += 1

    avg_score = round(total / count, 2) if count else 0.0

    return render(request, "quiz/result.html", {
        "doc": doc,
        "qa_pairs": qa_pairs,
        "avg_score": avg_score,
    })
