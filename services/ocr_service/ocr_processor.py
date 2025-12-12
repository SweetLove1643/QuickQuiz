import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image
from typing import List
import logging

logger = logging.getLogger(__name__)


class OCRProcessor:
    def __init__(self):
        self.device = self._get_device()
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.model_id = "Qwen/Qwen2-VL-2B-Instruct"

        logger.info("🔄 Loading Qwen2-VL model... Please wait.")
        self._load_model()

    def _get_device(self):
        if torch.cuda.is_available():
            logger.info("🚀 GPU CUDA detected → using GPU")
            return "cuda"
        logger.info("🖥 Running on CPU")
        return "cpu"

    def _load_model(self):
        try:
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_id, torch_dtype="auto", device_map="auto"
            )
            self.model.eval()

            self.processor = AutoProcessor.from_pretrained(self.model_id)

            logger.info("✅ Qwen2-VL model loaded successfully")

        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            raise e

    async def extract_text(self, images: List[Image.Image]) -> str:
        """Extract text from a list of PIL Images"""
        try:
            # Create messages for the model
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Hãy trích xuất toàn bộ nội dung văn bản có trong tất cả các ảnh được cung cấp.

YÊU CẦU:
- Trích xuất chính xác từng ký tự, từ ngữ
- Giữ nguyên format, xuống dòng như trong ảnh gốc
- Không thêm, bớt, sửa đổi nội dung
- Nếu có nhiều ảnh, gộp nội dung theo thứ tự
- Nếu không đọc được, ghi "Không thể đọc được nội dung"

Chỉ trả về nội dung văn bản đã trích xuất, không cần giải thích thêm.""",
                        }
                    ]
                    + [{"type": "image", "image": img} for img in images],
                }
            ]

            # Prepare inputs
            text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            image_inputs, video_inputs = process_vision_info(messages)

            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )
            inputs = inputs.to(self.device)

            # Generate response
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs, max_new_tokens=2048, temperature=0.1, do_sample=False
                )

            # Decode response
            generated_ids_trimmed = [
                out_ids[len(in_ids) :]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]

            output_text = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]

            return output_text.strip()

        except Exception as e:
            logger.error(f"Error in text extraction: {e}")
            raise e
