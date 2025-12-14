import torch
import logging
from typing import Optional
from transformers import AutoTokenizer, T5ForConditionalGeneration
from peft import PeftModel

logger = logging.getLogger(__name__)


class SummaryProcessor:
    def __init__(
        self,
        checkpoint_path: str,
        base_model_name: str = "VietAI/vit5-base",
        device: Optional[str] = None,
        max_input_length: int = 1024,
        max_new_tokens: int = 256,
    ):
        """
        Summary processor using ViT5 + LoRA checkpoint
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.max_input_length = max_input_length
        self.max_new_tokens = max_new_tokens

        logger.info("Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            checkpoint_path if checkpoint_path else base_model_name
        )

        logger.info("Loading base model...")
        base_model = T5ForConditionalGeneration.from_pretrained(base_model_name)

        logger.info("Loading LoRA adapter...")
        self.model = PeftModel.from_pretrained(base_model, checkpoint_path)

        self.model = self.model.merge_and_unload()

        self.model.to(self.device)
        self.model.eval()

        logger.info(
            f"SummaryProcessor initialized with device={self.device}"
        )

    async def summarize_text(self, text: str) -> str:
        """
        Summarize text using ViT5 + LoRA
        """
        if not text or not text.strip():
            return ""

        try:
            # Nếu lúc train bạn có prefix "summary:"
            input_text = "summary: " + text.strip()

            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                max_length=self.max_input_length,
                truncation=True,
            )

            input_ids = inputs["input_ids"].to(self.device)
            attention_mask = inputs["attention_mask"].to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=self.max_new_tokens,
                    num_beams=4,
                    length_penalty=1.0,
                    early_stopping=True,
                )

            summary = self.tokenizer.decode(
                outputs[0], skip_special_tokens=True
            )

            return summary.strip()

        except Exception as e:
            logger.error(f"Error in text summarization: {e}")
            raise
