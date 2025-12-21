import os
import json
import uuid
import logging
import time
import hashlib
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

from schemas import GenerateRequest, Quiz, QuizQuestion
from llm_adapter import GeminiAdapter
from database import SessionLocal, GenerationHistory, GeneratedQuiz, ContentCache

load_dotenv()

logger = logging.getLogger(__name__)


def get_db_session():
    """Get database session for operations."""
    return SessionLocal()


def _build_prompt_from_sections(sections):
    texts = []
    for s in sections:
        texts.append(f"Section {s['id']}: {s.get('summary')}")
    return "\n\n".join(texts)


def generate_quiz_job(job_id: str, request_payload: dict) -> dict:
    start_time = time.time()

    payload_copy = dict(request_payload or {})
    use_canned = bool(payload_copy.pop("use_canned", False))
    req = GenerateRequest(**payload_copy)

    quiz_id = f"quiz-{uuid.uuid4().hex[:8]}"

    sections = []
    if req.sections:
        sections = [s.model_dump() for s in req.sections]

    n_questions = req.config.n_questions if req.config and req.config.n_questions else 5
    types = (
        req.config.types
        if req.config and req.config.types
        else ["mcq", "tf", "fill_blank"]
    )
    if req.config:
        try:
            n_questions = int(getattr(req.config, "n_questions", n_questions))
        except Exception:
            pass
        cfg_types = getattr(req.config, "types", None)
        if cfg_types:
            types = list(cfg_types)

    prompt = _build_prompt_from_sections(sections)
    example = (
        "[\n"
        '  {"id": "q1", "type": "mcq", "stem": "Đâu là X?", '
        '"options": ["A","B","C"], "answer": "A"},\n'
        '  {"id": "q2", "type": "tf", "stem": "Y có đúng không?", '
        '"options": ["Đúng","Sai"], "answer": "Đúng"},\n'
        '  {"id": "q3", "type": "fill_blank", "stem": "Z là _____.", '
        '"options": null, "answer": "câu trả lời"}\n'
        "]"
    )
    prompt += (
        f"\n\nTạo {n_questions} câu hỏi bằng tiếng Việt. "
        f"Loại câu hỏi ưu tiên: {', '.join(types)}. "
        "Chỉ trả về JSON, chính xác là một mảng như ví dụ này: "
        f"{example} \n\n"
        "Mỗi đối tượng phải có các key: 'id','type','stem','options','answer'. "
        "Với loại 'fill_blank', đặt 'options' thành null và dùng '_____' trong stem ở vị trí cần điền. "
        'Với loại \'tf\', dùng options ["Đúng", "Sai"] và answer phải là một trong số chúng. '
        "Với loại 'mcq', cung cấp 'options' là một mảng và 'answer' phải trùng với một tùy chọn."
    )

    gemini = GeminiAdapter()
    prev_canned = os.environ.get("USE_CANNED_LLM")
    model_name = os.environ.get("GEMINI_MODEL")
    try:
        if use_canned:
            os.environ["USE_CANNED_LLM"] = "1"
        out_text = gemini.generate(prompt, max_tokens=4096, model=model_name)
    except Exception:
        logger.exception("LLM generation failed for job %s", job_id)
        raise
    finally:
        if prev_canned is None:
            os.environ.pop("USE_CANNED_LLM", None)
        else:
            os.environ["USE_CANNED_LLM"] = prev_canned

    def _extract_json_text(s: str) -> Optional[str]:
        import re

        if not s:
            return None
        m = re.search(r"```(?:json)?\s*(.*?)```", s, re.S | re.I)
        if m:
            s = m.group(1)

        start = None
        for i, ch in enumerate(s):
            if ch in "[{":
                start = i
                break
        if start is None:
            return None

        stack = []
        pairs = {"{": "}", "[": "]"}
        for i in range(start, len(s)):
            ch = s[i]
            if ch in pairs:
                stack.append(pairs[ch])
            elif stack and ch == stack[-1]:
                stack.pop()
                if not stack:
                    return s[start : i + 1]
        return None

    questions = []
    parsed = None
    json_text = _extract_json_text(out_text)
    try:
        if json_text:
            parsed = json.loads(json_text)
        else:
            parsed = json.loads(out_text)
        if isinstance(parsed, list):
            for i, q in enumerate(parsed):
                qobj = {
                    "id": q.get("id") or f"q{i+1}",
                    "type": q.get("type", "mcq"),
                    "stem": q.get("stem", ""),
                    "options": q.get("options"),
                    "answer": q.get("answer"),
                    "difficulty": q.get("difficulty"),
                    "source_sections": q.get("source_sections")
                    or [s.get("id") for s in sections],
                }
                questions.append(qobj)
        else:
            questions = [
                {
                    "id": "q1",
                    "type": "fill_blank",
                    "stem": str(parsed) + " _____",
                    "answer": "[đáp án]",
                    "source_sections": [s.get("id") for s in sections],
                }
            ]
    except Exception:
        questions = [
            {
                "id": "q1",
                "type": "fill_blank",
                "stem": out_text[:500] + " _____",
                "answer": "[đáp án]",
                "source_sections": [s.get("id") for s in sections],
            }
        ]

    def _normalize(qs):
        norm = []
        for q in qs:
            t = (q.get("type") or "").lower()
            if t not in ("mcq", "tf", "fill_blank"):
                t = "mcq"
            q["type"] = t

            if t == "fill_blank":
                q["options"] = None
                if q.get("answer") == "" or q.get("answer") is None:
                    q["answer"] = "[đáp án]"
                else:
                    q["answer"] = str(q.get("answer"))
                stem = q.get("stem", "")
                if "_____" not in stem and "___" not in stem:
                    q["stem"] = stem + " _____"

            elif t == "tf":
                q["options"] = ["Đúng", "Sai"]
                ans = q.get("answer")
                if isinstance(ans, str):
                    ans_lower = ans.lower()
                    if ans_lower in ("true", "t", "1", "đúng", "dung"):
                        q["answer"] = "Đúng"
                    elif ans_lower in ("false", "f", "0", "sai"):
                        q["answer"] = "Sai"
                    else:
                        q["answer"] = "Sai"
                else:
                    q["answer"] = "Sai"

            else:  
                opts = q.get("options")
                if not isinstance(opts, list) or len(opts) == 0:
                    q["options"] = ["A", "B", "C", "D"]
                ans = q.get("answer")
                if ans and ans not in q["options"]:
                    q["answer"] = q["options"][0]
            norm.append(q)
        return norm

    questions = _normalize(questions)

    if len(questions) > n_questions:
        questions = questions[:n_questions]

    question_objs = [QuizQuestion(**q) for q in questions]
    quiz = Quiz(
        id=quiz_id, questions=question_objs, meta={"source_count": len(sections)}
    )

    quiz_data = quiz.model_dump()

    try:
        db = get_db_session()

        history = GenerationHistory(
            job_id=job_id,
            quiz_id=quiz_id,
            sections_count=len(sections),
            requested_questions=n_questions,
            question_types=types,
            generated_questions=len(questions),
            generation_time=time.time() - start_time if "start_time" in locals() else 0,
            model_used=(
                getattr(gemini, "current_model", "unknown")
                if "gemini" in locals()
                else "unknown"
            ),
            status="completed",
        )
        db.add(history)

        generated_quiz = GeneratedQuiz(
            quiz_id=quiz_id,
            questions_data=quiz_data,
            quiz_metadata={"generation_time": time.time()},
            source_sections=sections,
            generation_config=request_payload.get("config", {}),
            validation_summary={}, 
        )
        db.add(generated_quiz)

        db.commit()
        logger.info(f"Saved quiz {quiz_id} to database")

    except Exception as e:
        logger.error(f"Failed to save quiz to database: {e}")
        if "db" in locals():
            db.rollback()
    finally:
        if "db" in locals():
            db.close()

    return quiz_data


__all__ = ["generate_quiz_job"]
