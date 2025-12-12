# services/ocr_service.py
import google.genai as genai
from google.genai import types
from pdf2image import convert_from_bytes
from PIL import Image
import io

def extract_information(files_bytes_list, mime_types, api_key):
    """
    Hàm OCR hỗ trợ:
    - Ảnh (image/png, image/jpeg, image/webp)
    - PDF nhiều trang (application/pdf)

    Cách hoạt động:
    - Nếu là PDF → convert tất cả trang → gom list ảnh
    - Nếu là ảnh → gom thành list 1 ảnh
    - Sau đó gửi toàn bộ list ảnh vào 1 request duy nhất
    """

    # ---- 1. Khởi tạo client ----
    client = genai.Client(api_key=api_key)

    # ---- 2. Chuẩn bị prompt ----
    prompt = """
    Bạn là Gemini, một mô hình chuyên dụng cho Trích Xuất Tài Liệu Học Thuật từ hình ảnh.

    Bạn sẽ nhận vào một hoặc nhiều ảnh (hoặc trang PDF đã chuyển thành ảnh).

    ========================================
    NHIỆM VỤ CHÍNH
    ========================================
    Bạn phải OCR và ghi lại *100% nội dung xuất hiện trong từng ảnh*, theo đúng thứ tự ảnh được cung cấp.

    Quan trọng:
    - Mỗi ảnh phải được OCR **hoàn toàn độc lập**.
    - Mỗi ảnh bắt buộc phải có phần tiêu đề nhận dạng theo đúng format:

    === ẢNH SỐ X ===
    <nội dung OCR của ảnh X>

    hoặc (đối với PDF):
    === PAGE SỐ X ===
    <nội dung OCR của trang X>

    - KHÔNG được ghép nội dung giữa các ảnh, kể cả nếu nội dung có vẻ liên quan.
    - KHÔNG được suy đoán ảnh nào liên quan hoặc không.
    - KHÔNG được trộn nội dung của các ảnh/page lại với nhau.

    Bước OCR chỉ có mục tiêu duy nhất:  
    **Trích xuất đầy đủ và đánh dấu rõ nguồn của từng ảnh/page để phục vụ cho bước tóm tắt phía sau.**

    ========================================
    NỘI DUNG CẦN TRÍCH XUẤT CHO MỖI ẢNH
    ========================================
    Bạn phải ghi lại:
    - Mọi loại văn bản: tiêu đề, đoạn văn, mục lục, chú thích, ghi chú lề, trích dẫn…
    - Bảng biểu (mô tả bằng lời, không dựng lại bảng)
    - Công thức toán / lý / hoá (giữ nguyên hình thức như mắt thường thấy)
    - Hình minh họa, biểu đồ, đồ thị (mô tả bằng lời)
    - Tham chiếu như “xem hình 2.1”, “tiếp theo”, “bảng 3.2”
    - Ví dụ, bài tập, đề bài, lời giải
    - Ký hiệu đặc biệt, số liệu, đơn vị
    - Bất kỳ nội dung nhỏ hoặc rời rạc nào khác
    - Nếu có số trang, đánh dấu, ký hiệu mục… phải ghi chính xác nguyên văn

    ========================================
    QUY TẮC BẮT BUỘC
    ========================================
    1. KHÔNG tóm tắt.
    2. KHÔNG thêm nội dung mới.
    3. KHÔNG suy luận hoặc đoán nội dung bị thiếu.
    4. KHÔNG bỏ sót chữ, ký tự, ký hiệu, số liệu hoặc đơn vị.
    5. Mỗi ảnh phải được đánh dấu bằng:
    === ẢNH SỐ X ===
    hoặc
    === PAGE SỐ X ===
    6. Trong từng ảnh: đọc từ trên xuống dưới, trái sang phải.
    7. Nếu chữ mờ → ghi đúng những gì thấy, ví dụ: “(mờ, không đọc được)”.
    8. KHÔNG được xác định, phỏng đoán hoặc biểu thị mức độ liên quan giữa các ảnh/page.

    ========================================
    MỤC TIÊU CUỐI
    ========================================
    Tạo ra bản OCR:
    - chính xác tuyệt đối,
    - đầy đủ 100%,
    - được phân tách rõ ràng theo từng ảnh/page,
    - trung thực tuyệt đối với nội dung gốc,
    - không thêm – không bớt – không suy luận.

    Hãy bắt đầu trích xuất ngay bây giờ.
    """


    # ─────────────────────────────────────────────
    # 1) Gom toàn bộ ảnh từ tất cả đầu vào
    # ─────────────────────────────────────────────
    images = []   # danh sách kiểu bytes

    for file_bytes, mime in zip(files_bytes_list, mime_types):

        # Nếu là PDF → convert từng trang → thêm vào images
        if mime == "application/pdf":
            pages = convert_from_bytes(file_bytes)
            for page in pages:
                buffer = io.BytesIO()
                page.save(buffer, format="JPEG")
                images.append(buffer.getvalue())

        # Nếu là ảnh → thêm trực tiếp
        else:
            images.append(file_bytes)

    # ─────────────────────────────────────────────
    # 3) Build contents
    # ─────────────────────────────────────────────
    contents = [prompt]

    for idx, img_bytes in enumerate(images, start=1):
        contents.append(f"=== ẢNH SỐ {idx} ===")
        contents.append(
            types.Part.from_bytes(
                data=img_bytes,
                mime_type="image/jpeg"
            )
        )

    # ─────────────────────────────────────────────
    # 4) Gửi request 1 lần duy nhất
    # ─────────────────────────────────────────────
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
    )

    return response.text