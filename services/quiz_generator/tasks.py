import os
import json
import uuid
import logging
from typing import Optional
from dotenv import load_dotenv

from schemas import GenerateRequest, Quiz, QuizQuestion
from llm_adapter import GeminiAdapter

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


def _build_prompt_from_sections(sections):
    # Simple prompt: include all sections concatenated; production should chunk and RAG
    texts = []
    for s in sections:
        texts.append(f"Section {s['id']}: {s.get('summary')}")
    return "\n\n".join(texts)


def generate_quiz_job(job_id: str, request_payload: dict) -> dict:
    """Run the quiz generation pipeline (callable from a Celery task).

    request_payload is the parsed JSON matching GenerateRequest.
    Returns metadata dict including quiz_id and storage path.
    """
    # Support a per-request 'use_canned' flag (coming from the UI) without
    # passing unknown fields into the Pydantic model.
    payload_copy = dict(request_payload or {})
    use_canned = bool(payload_copy.pop("use_canned", False))
    req = GenerateRequest(**payload_copy)

    quiz_id = f"quiz-{uuid.uuid4().hex[:8]}"

    sections = []
    if req.sections:
        # use Pydantic v2 API model_dump
        sections = [s.model_dump() for s in req.sections]

    # Incorporate generation config: number of questions and types (Vietnamese only)
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
    # Provide an explicit example schema and examples for each question type to
    # help the LLM output the correct JSON shape for mcq, tf and short.
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
    # If this request asked for a canned response, temporarily set the
    # environment variable the adapter checks. Use try/finally to restore.
    prev_canned = os.environ.get("USE_CANNED_LLM")
    # Read optional default model from env so we send the model name to Gemini
    model_name = os.environ.get("GEMINI_MODEL")
    try:
        if use_canned:
            os.environ["USE_CANNED_LLM"] = "1"
        out_text = gemini.generate(prompt, max_tokens=4096, model=model_name)
    except Exception:
        logger.exception("LLM generation failed for job %s", job_id)
        # In real task, mark job as failed in DB
        raise
    finally:
        # restore previous env var state
        if prev_canned is None:
            os.environ.pop("USE_CANNED_LLM", None)
        else:
            os.environ["USE_CANNED_LLM"] = prev_canned

    # Try parse output as JSON. LLMs often return JSON wrapped in markdown code fences
    # or with extra text. Try to extract a JSON substring first (balanced braces) before
    # calling json.loads.
    def _extract_json_text(s: str) -> Optional[str]:
        import re

        if not s:
            return None
        # remove common code fences ```json ... ``` or ``` ... ```
        m = re.search(r"```(?:json)?\s*(.*?)```", s, re.S | re.I)
        if m:
            s = m.group(1)

        # find first JSON opening bracket
        start = None
        for i, ch in enumerate(s):
            if ch in "[{":
                start = i
                break
        if start is None:
            return None

        # scan forward to find the matching closing bracket using a stack
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
    # attempt to extract JSON substring
    json_text = _extract_json_text(out_text)
    try:
        if json_text:
            parsed = json.loads(json_text)
        else:
            parsed = json.loads(out_text)
        if isinstance(parsed, list):
            # map to our schema
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
            # If LLM returned a dict or other shape, wrap it
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
        # Fallback: wrap raw text as single fill_blank question
        questions = [
            {
                "id": "q1",
                "type": "fill_blank",
                "stem": out_text[:500] + " _____",
                "answer": "[đáp án]",
                "source_sections": [s.get("id") for s in sections],
            }
        ]

    # Post-process / normalize questions to ensure they match expected shapes
    def _normalize(qs):
        norm = []
        for q in qs:
            t = (q.get("type") or "").lower()
            if t not in ("mcq", "tf", "fill_blank"):
                # fallback to mcq if unknown
                t = "mcq"
            q["type"] = t

            if t == "fill_blank":
                # fill_blank questions should not have options
                q["options"] = None
                # ensure answer is a short text and stem contains blank
                if q.get("answer") == "" or q.get("answer") is None:
                    q["answer"] = "[đáp án]"
                else:
                    q["answer"] = str(q.get("answer"))
                # ensure stem has blank marker
                stem = q.get("stem", "")
                if "_____" not in stem and "___" not in stem:
                    q["stem"] = stem + " _____"

            elif t == "tf":
                # normalize TF options and answer
                q["options"] = ["Đúng", "Sai"]
                ans = q.get("answer")
                if isinstance(ans, str):
                    ans_lower = ans.lower()
                    if ans_lower in ("true", "t", "1", "đúng", "dung"):
                        q["answer"] = "Đúng"
                    elif ans_lower in ("false", "f", "0", "sai"):
                        q["answer"] = "Sai"
                    else:
                        # unknown -> default Sai
                        q["answer"] = "Sai"
                else:
                    q["answer"] = "Sai"

            else:  # mcq
                opts = q.get("options")
                if not isinstance(opts, list) or len(opts) == 0:
                    # create simple distractors if missing
                    q["options"] = ["A", "B", "C", "D"]
                # ensure answer matches one option when possible
                ans = q.get("answer")
                if ans and ans not in q["options"]:
                    # try to find close match or default to first
                    q["answer"] = q["options"][0]
            norm.append(q)
        return norm

    questions = _normalize(questions)

    # Enforce requested number of questions: truncate if too many. If too few,
    # leave as-is (could implement padding later).
    if len(questions) > n_questions:
        questions = questions[:n_questions]

    # Convert question dicts to QuizQuestion objects for schema validation
    question_objs = [QuizQuestion(**q) for q in questions]
    quiz = Quiz(
        id=quiz_id, questions=question_objs, meta={"source_count": len(sections)}
    )

    # Return quiz data directly without saving to file
    return quiz.model_dump()


__all__ = ["generate_quiz_job"]
