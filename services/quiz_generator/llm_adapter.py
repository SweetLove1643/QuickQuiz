import os
import logging
from typing import Optional
from dotenv import load_dotenv

import requests
import json

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class GeminiAdapter:
    """Adapter for Google Gemini API.

    Expects environment variables:
    - GEMINI_API_KEY (required)
    - GEMINI_MODEL (optional, defaults to gemini-pro)
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.base_url = "https://generativelanguage.googleapis.com/v1/models"

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 256,
        temperature: float = 0.2,
    ) -> str:
        # Allow an offline canned response for UI/dev testing
        use_canned = os.environ.get("USE_CANNED_LLM", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        if use_canned:
            logger.info(
                "Using canned LLM response (USE_CANNED_LLM=%s)",
                os.environ.get("USE_CANNED_LLM"),
            )
            # Return a small, valid JSON array of questions so downstream parsing works
            canned = [
                {
                    "id": "q1",
                    "type": "mcq",
                    "stem": "Thủ đô của Pháp là gì?",
                    "options": ["Paris", "London", "Berlin", "Madrid"],
                    "answer": "Paris",
                },
                {
                    "id": "q2",
                    "type": "tf",
                    "stem": "Bầu trời có màu xanh.",
                    "options": ["Đúng", "Sai"],
                    "answer": "Đúng",
                },
                {
                    "id": "q3",
                    "type": "fill_blank",
                    "stem": "Việt Nam có _____ tỉnh thành.",
                    "options": None,
                    "answer": "63",
                },
            ]
            return json.dumps(canned, ensure_ascii=False)

        # Try different model names if default fails
        model_names = [
            model or self.model,
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ]

        # Remove duplicates while preserving order
        seen = set()
        model_names = [x for x in model_names if not (x in seen or seen.add(x))]

        headers = {"Content-Type": "application/json"}

        # Construct the request payload for Gemini API
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max(max_tokens, 1000),  # Ensure minimum 1000 tokens
                "candidateCount": 1,
            },
        }

        last_error = None

        for model_name in model_names:
            url = f"{self.base_url}/{model_name}:generateContent"
            params = {"key": self.api_key}

            try:
                logger.info(f"Trying Gemini model: {model_name}")
                resp = requests.post(
                    url, json=payload, headers=headers, params=params, timeout=60
                )
                resp.raise_for_status()

                data = resp.json()

                # Extract text from Gemini response
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]

                    # Check for text content in parts (older format)
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if len(parts) > 0 and "text" in parts[0]:
                            logger.info(f"Successfully used model: {model_name}")
                            return parts[0]["text"]

                    # Check for text directly in content (newer format)
                    elif "content" in candidate and "text" in candidate["content"]:
                        logger.info(f"Successfully used model: {model_name}")
                        return candidate["content"]["text"]

                    # Check finish reason - if MAX_TOKENS, try next model with higher token limit
                    elif candidate.get("finishReason") == "MAX_TOKENS":
                        logger.warning(
                            f"Model {model_name} hit MAX_TOKENS, trying next model"
                        )
                        last_error = f"Model {model_name} hit MAX_TOKENS limit"
                        continue

                    # Check if content is empty or missing
                    else:
                        logger.warning(
                            f"No text content in response from model {model_name}: {candidate}"
                        )
                        last_error = (
                            f"No text content in response from model {model_name}"
                        )
                        continue

                # If no candidates, try next model
                logger.warning(f"No candidates in response from model {model_name}")
                last_error = f"No candidates in response from model {model_name}"
                continue

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.warning(
                        f"Model {model_name} not found (404), trying next model"
                    )
                    last_error = f"Model {model_name} not found: {e}"
                    continue
                else:
                    logger.error(f"HTTP error with model {model_name}: {e}")
                    last_error = f"HTTP error with model {model_name}: {e}"
                    continue
            except Exception as e:
                logger.error(f"Unexpected error with model {model_name}: {e}")
                last_error = f"Unexpected error with model {model_name}: {e}"
                continue

        # If all models failed, raise the last error
        error_msg = f"All Gemini models failed. Last error: {last_error}"
        logger.exception(error_msg)
        raise RuntimeError(error_msg)


class OllamaAdapter:
    """Simple HTTP adapter for an Ollama inference server.

    Expects environment variables:
    - OLLAMA_URL (e.g. http://localhost:11434)
    - OLLAMA_API_KEY (optional)
    """

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or os.environ.get(
            "OLLAMA_URL", "http://localhost:11434"
        )
        self.api_key = api_key or os.environ.get("OLLAMA_API_KEY")

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 256,
        temperature: float = 0.2,
    ) -> str:
        # Allow an offline canned response for UI/dev testing
        use_canned = os.environ.get("USE_CANNED_LLM", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        if use_canned:
            logger.info(
                "Using canned LLM response (USE_CANNED_LLM=%s)",
                os.environ.get("USE_CANNED_LLM"),
            )
            # Return a small, valid JSON array of questions so downstream parsing works
            canned = [
                {
                    "id": "q1",
                    "type": "mcq",
                    "stem": "What is the capital of France?",
                    "options": ["Paris", "London", "Berlin", "Madrid"],
                    "answer": "Paris",
                },
                {
                    "id": "q2",
                    "type": "tf",
                    "stem": "The sky is blue.",
                    "options": ["True", "False"],
                    "answer": "True",
                },
            ]
            return json.dumps(canned, ensure_ascii=False)

        # Try a few possible Ollama-compatible endpoints in case the server uses a different path
        endpoints = [
            "/api/generate",
            "/api/completions",
            "/v1/completions",
            "/completions",
        ]

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        last_exc = None
        for ep in endpoints:
            url = f"{self.base_url.rstrip('/')}{ep}"
            payload = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if model:
                payload["model"] = model

            try:
                # Use streaming request to support Ollama's NDJSON streaming responses
                resp = requests.post(
                    url, json=payload, headers=headers, timeout=60, stream=True
                )
                # raise_for_status will raise if non-2xx
                resp.raise_for_status()
                # success
                logger.debug("Ollama responded from endpoint %s", ep)
                break
            except requests.exceptions.HTTPError as e:
                # If 404, try the next endpoint; otherwise keep the error but continue trying
                logger.warning(
                    "Ollama endpoint %s returned HTTP %s, trying next endpoint",
                    ep,
                    getattr(e.response, "status_code", None),
                )
                last_exc = e
                resp = None
                continue
            except Exception as e:
                logger.exception("Ollama request to %s failed", url)
                last_exc = e
                resp = None
                continue

        if resp is None:
            logger.exception("All Ollama endpoints failed; last error: %s", last_exc)
            # raise the last exception to signal failure to caller
            if last_exc:
                raise last_exc
            raise RuntimeError("Ollama request failed: no response from server")

        # Try to extract text from common response shapes
        # First, handle NDJSON / streaming lines (Ollama /api/generate returns many JSON objects)
        try:
            lines = []
            combined = []
            for raw in resp.iter_lines(decode_unicode=True):
                if not raw:
                    continue
                lines.append(raw)
                try:
                    obj = json.loads(raw)
                except Exception:
                    # not a JSON line, skip
                    continue
                # Ollama incremental responses often have a 'response' field and a 'done' flag
                if isinstance(obj, dict) and "response" in obj:
                    combined.append(str(obj.get("response", "")))
                    if obj.get("done"):
                        # finished streaming
                        return "".join(combined)
                # Some lines may contain the full final payload; try to extract text if present
                if isinstance(obj, dict) and "text" in obj and not combined:
                    combined.append(obj.get("text"))

            # If we collected streaming parts, return them
            if combined:
                return "".join(combined)

            # If no streaming parts, try to parse the full response as JSON
            data = json.loads("\n".join(lines)) if lines else resp.json()
            # Ollama may return {'text': '...'} or {'output': [{'type':'text','content':'...'}]}
            if isinstance(data, dict) and "text" in data:
                return data["text"]
            if isinstance(data, dict) and "content" in data:
                # some endpoints return {'content': '...'}
                return data["content"]
            if (
                isinstance(data, dict)
                and "output" in data
                and isinstance(data["output"], list)
            ):
                parts = [
                    p.get("content") or p.get("text")
                    for p in data["output"]
                    if isinstance(p, dict)
                ]
                return "".join([p for p in parts if p])
            # If response includes 'choices' as in OpenAI-like responses
            if (
                isinstance(data, dict)
                and "choices" in data
                and isinstance(data["choices"], list)
            ):
                texts = []
                for c in data["choices"]:
                    if isinstance(c, dict):
                        if "text" in c:
                            texts.append(c["text"])
                        elif (
                            "message" in c
                            and isinstance(c["message"], dict)
                            and "content" in c["message"]
                        ):
                            texts.append(c["message"]["content"])
                return "\n".join(texts)
            # fallback: stringify
            return str(data)
        except ValueError:
            return resp.text


__all__ = ["GeminiAdapter", "OllamaAdapter"]
