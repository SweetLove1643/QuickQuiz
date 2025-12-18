import torch
import logging
from typing import Optional
from transformers import AutoTokenizer, T5ForConditionalGeneration
from peft import PeftModel
import re

logger = logging.getLogger(__name__)


class SummaryProcessor:
    def __init__(
        self,
        checkpoint_path: str,
        base_model_name: str = "VietAI/vit5-base",
        device: Optional[str] = None,
        max_input_length: int = 1536,
        max_new_tokens: int = 256,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.max_input_length = max_input_length
        self.max_new_tokens = max_new_tokens

        logger.info("Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            checkpoint_path if checkpoint_path else base_model_name
        )

        logger.info("Loading base model...")
        base_model = T5ForConditionalGeneration.from_pretrained(
            base_model_name,
            torch_dtype=self.dtype,
        )

        logger.info("Loading LoRA adapter...")
        self.model = PeftModel.from_pretrained(base_model, checkpoint_path)

        self.model = self.model.merge_and_unload()

        self.model.to(self.device, dtype=self.dtype)
        self.model.eval()

        logger.info(f"SummaryProcessor initialized with device={self.device}")

    async def summarize_text(self, text: str) -> str:
        if not text or not text.strip():
            return ""

        try:
            # Sử dụng tiền tố chuẩn của ViT5 để tránh mô hình lặp lại câu lệnh
            input_text = "tóm tắt: " + text.strip()

            word_count = len(text.split())
            min_tokens = min(200, int(word_count * 0.3))

            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                max_length=self.max_input_length,
                truncation=True,
            )

            input_ids = inputs["input_ids"].to(self.device)
            attention_mask = inputs["attention_mask"].to(self.device)

            with torch.no_grad():
                with torch.cuda.amp.autocast(
                    enabled=self.device == "cuda", dtype=torch.float16
                ):
                    outputs = self.model.generate(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        max_new_tokens=self.max_new_tokens,
                        min_new_tokens=min_tokens,
                        num_beams=2,
                        length_penalty=1.2,
                        early_stopping=False,
                        no_repeat_ngram_size=3,
                    )

            summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Loại bỏ khả năng mô hình lặp lại câu prompt ở đầu kết quả
            summary = self._clean_summary_output(summary)

            return summary.strip()

        except Exception as e:
            logger.error(f"Error in text summarization: {e}")
            raise

    def _clean_summary_output(self, text: str) -> str:
        s = text.strip()
        # Xóa các cụm thường xuất hiện do lặp lại prompt ở đầu
        s = re.sub(r"^(Nhiệm vụ:\s*[^\n]*\n+)", "", s, flags=re.IGNORECASE)
        s = re.sub(r"^(Tóm\s*tắt[:：]\s*)", "", s, flags=re.IGNORECASE)
        s = re.sub(r"^(Một đoạn văn [^\n]+\n?)", "", s, flags=re.IGNORECASE)
        return s.strip()
