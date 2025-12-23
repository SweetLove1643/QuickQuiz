import torch
from transformers import (
    Qwen2VLForConditionalGeneration,
    AutoProcessor,
    GenerationConfig,
)
from qwen_vl_utils import process_vision_info
from PIL import Image
from typing import List
import logging
import gc

logger = logging.getLogger(__name__)


class OCRProcessor:
    def __init__(self):
        self.device = self._get_device()
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.model_id = "Qwen/Qwen2-VL-2B-Instruct"

        logger.info("Loading Qwen2-VL model... Please wait.")
        self._load_model()

    def _get_device(self):
        if torch.cuda.is_available():
            logger.info("GPU CUDA detected → using GPU")
            return "cuda"
        logger.info("Running on CPU")
        return "cpu"

    def _load_model(self):
        try:
            # Tối ưu cho GTX 1650 (4GB VRAM): sử dụng 8-bit quantization
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_id,
                torch_dtype=(torch.float16 if self.device == "cuda" else torch.float32),
                device_map="auto",
                load_in_8bit=True,  # Giảm VRAM từ ~6GB xuống ~3GB
                max_memory={0: "3GB"},  # Giới hạn VRAM cho GPU 0
            )
            self.model.eval()

            self.processor = AutoProcessor.from_pretrained(self.model_id)

            # Làm sạch generation config để tránh cảnh báo flags bị bỏ qua
            try:
                gcfg = (
                    self.model.generation_config
                    or GenerationConfig.from_model_config(self.model.config)
                )
                gcfg.do_sample = False
                for k in ("temperature", "top_p", "top_k"):
                    if hasattr(gcfg, k):
                        setattr(gcfg, k, None)
                self.model.generation_config = gcfg
            except Exception as cfg_err:
                logger.warning(f"Generation config sanitize skipped: {cfg_err}")

            logger.info("Qwen2-VL model loaded successfully")

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise e

    def estimate_output_tokens(self, image: Image.Image) -> int:
        width, height = image.size
        print(f"DEBUG: Kích thước hình ảnh đầu vào là: {width}x{height}")
        num_pixels = width * height
        # Giảm max_tokens để tăng tốc độ xử lý
        if num_pixels <= 512 * 512:
            print(f"DEBUG: Max token là: 128")
            return 128
        elif num_pixels <= 720 * 720:
            print(f"DEBUG: Max token là: 256")
            return 256
        elif num_pixels <= 1024 * 1024:
            print(f"DEBUG: Max token là: 512")
            return 512
        else:
            print(f"DEBUG: Max token là: 768")
            return 768

    async def extract_text(self, images: List[Image.Image]) -> str:
        try:
            # Resize ảnh lớn để giảm tải VRAM và tăng tốc độ
            processed_images = []
            for img in images:
                width, height = img.size
                max_size = 1024
                if width > max_size or height > max_size:
                    ratio = min(max_size / width, max_size / height)
                    new_size = (int(width * ratio), int(height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    logger.info(
                        f"Resized image from {width}x{height} to {new_size[0]}x{new_size[1]}"
                    )
                processed_images.append(img)

            PROMPT = """
                Bạn là một hệ thống trích xuất thông tin học thuật có độ chính xác cao.  
                Hãy đọc kỹ nội dung trong ảnh đầu vào, bao gồm mọi dạng dữ liệu: văn bản, công thức, hình ảnh, bảng biểu, chú thích, tiêu đề, số hiệu hình/table, và mối liên kết giữa chúng.

                YÊU CẦU:
                1. Trích xuất lại nguyên vẹn toàn bộ nội dung có trong ảnh.
                2. Không diễn giải, không suy đoán, không thêm thông tin ngoài ảnh.
                3. Giữ đúng cấu trúc logic theo thứ tự xuất hiện: tiêu đề → đoạn văn → hình → chú thích → bảng → ghi chú.
                4. Nếu có hình/figure/table, chỉ mô tả lại bằng những gì hiển thị kèm chú thích (nếu có).
                5. Giữ nguyên cách viết: ký tự, dấu, công thức, số liệu.
                6. Đảm bảo đầu ra là một đoạn văn hoàn chỉnh, rõ ràng và trung thực với nội dung trong ảnh.

                BẮT ĐẦU TRÍCH XUẤT DỮ LIỆU:
                """

            messages = [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": PROMPT}]
                    + [{"type": "image", "image": img} for img in processed_images],
                }
            ]

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

            max_tokens = max(
                self.estimate_output_tokens(img) for img in processed_images
            )

            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    do_sample=False,
                    use_cache=True,  # Bật cache để tăng tốc
                    num_beams=1,  # Greedy decoding cho tốc độ tối đa
                )

            generated_ids_trimmed = [
                out_ids[len(in_ids) :]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]

            output_text = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]

            # Giải phóng VRAM sau mỗi lần xử lý
            if self.device == "cuda":
                torch.cuda.empty_cache()
                gc.collect()

            return output_text.strip()

        except Exception as e:
            logger.error(f"Error in text extraction: {e}")
            raise e
