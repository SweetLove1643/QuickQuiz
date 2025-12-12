import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image
from typing import List

torch.manual_seed(1234)

def get_device():
    if torch.cuda.is_available():
        print("🚀 GPU CUDA detected → using GPU")
        return "cuda"
    print("🖥 Running on CPU")
    return "cpu"

DEVICE = get_device()
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

MODEL_ID = "Qwen/Qwen2-VL-2B-Instruct"
print("🔄 Loading Qwen2-VL model... Please wait.")

try:
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL_ID,
        torch_dtype="auto",
        device_map="auto"
    )

    model.eval()
except Exception as e:
    print("[ERROR] Error while loading model:", repr(e), flush=True)
    raise

try:
    processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)
except Exception as e:
    print("[ERROR] Error while loading processor:", repr(e), flush=True)
    raise

print("✅ Model & Processor loaded successfully!", flush=True)

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

def estimate_output_tokens(image):
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

def extract_information(images: List[Image.Image]) -> str:

    contents = [{"type": "image", "image": img} for img in images]
    contents.append({"type": "text", "text": PROMPT})

    messages = [
        {
            "role": "user",
            "content": contents
        }
    ]

    try:
        text = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    except Exception as e:
        print("[ERROR] Error in apply_chat_template:", repr(e), flush=True)
        raise

    image_inputs, video_inputs = process_vision_info(messages)
       
    try:

        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt"
        )

        inputs = inputs.to(DEVICE)
    except Exception as e:
        print("[ERROR] Error in processor(text, images):", repr(e), flush=True)
        raise

    print("[DEBUG] Calling model.generate...", flush=True)

    max_tokens = max(estimate_output_tokens(img) for img in images)

    try:
        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=max_tokens, 
                use_cache=True,
            )
    except Exception as e:
        print("[ERROR] Error in model.generate:", repr(e), flush=True)
        raise


    try:
        generated_ids_trimmed = [
            out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]
    except Exception as e:
        print("[ERROR] Error in batch_decode:", repr(e), flush=True)
        raise

    return output_text






