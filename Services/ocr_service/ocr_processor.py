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
    
    def estimate_output_tokens(self, image: Image.Image) -> int:
        width, height = image.size
        print(f'DEBUG: Kích thước hình ảnh đầu vào là: {width}x{height}')
        num_pixels = width * height
        if num_pixels <= 512 * 512:
            print(f'DEBUG: Max token là: 256')
            return 256
        elif num_pixels <= 720 * 720:
            print(f'DEBUG: Max token là: 512')
            return 512
        elif num_pixels <= 1024 * 1024:
            print(f'DEBUG: Max token là: 1024')
            return 1024
        elif num_pixels <= 1536 * 1536:
            print(f'DEBUG: Max token là: 1536')
            return 1536
        else:
            print(f'DEBUG: Max token là: 2048')
            return 2048
    

    async def extract_text(self, images: List[Image.Image]) -> str:
        """Extract text from a list of PIL Images"""
        try:
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
            
            # Create messages for the model
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": PROMPT,
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

            max_tokens = max(self.estimate_output_tokens(img) for img in images)

            # Generate response
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs, 
                    max_new_tokens=max_tokens, 
                    temperature=0.1, 
                    do_sample=False,
                    use_cache=True,
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
            # return "Trong bài viết này mình xin giới thiệu đến các bạn những lệnh cơ bản nhất (Cần nhớ và cách ghi nhớ nó) khi sử dụng, làm việc với Git. Đồng thời mô phỏng một quy trình làm việc với Git theo từng giai đoạn. Ở giai đoạn nào thì sử dụng những lệnh nào. Nhằm giúp các bạn mới nắm được bức tranh tổng quan nhất khi làm việc với Git, để sử dụng dòng lệnh cho phù hơp trong quá trình học tập, thực hành cũng như phục vụ công việc sau này.".strip()

        except Exception as e:
            logger.error(f"Error in text extraction: {e}")
            raise e
