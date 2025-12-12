import google.genai as genai


def Summaries_Knowledge(ocr_text: str, api_key: str):
    """
    Hàm tóm tắt kiến thức quan trọng từ đoạn OCR được Gemini trích xuất.

    - Tóm tắt lại các khái niệm chính
    - Trình bày lại dưới dạng gọn, có cấu trúc
    - Không thêm kiến thức mới ngoài nội dung đã cung cấp
    """

    client = genai.Client(api_key=api_key)
    # ======================================
    # BẮT ĐẦU TÓM TẮT
    # ======================================
    # """

    summary_prompt = f"""
    Bạn là Gemini, một mô hình chuyên tóm tắt tài liệu học thuật và kỹ thuật ở nhiều lĩnh vực khác nhau.

    ========================================
    NHIỆM VỤ CỦA BẠN
    ========================================
    Hãy tạo một bản tóm tắt kiến thức duy nhất từ nội dung OCR sau đây.  
    Nội dung OCR được lấy từ nhiều ảnh/trang khác nhau, nhưng:
    - Một số ảnh có thể liên quan hoặc nối tiếp nhau.
    - Một số ảnh có thể thuộc chủ đề khác.

    Yêu cầu của bản tóm tắt:
    - Gộp toàn bộ nội dung OCR thành **một bản tóm tắt duy nhất**.
    - Các phần có cùng chủ đề → tóm tắt liền mạch.
    - Các phần khác chủ đề → vẫn nằm trong cùng bản tóm tắt nhưng cần có **từ nối nhẹ** để người đọc cảm thấy mạch lạc.
    - Khi tóm tắt bất kỳ ý nào, nếu có thể xác định nguồn (Ảnh/Page) → hãy thêm chú thích nhỏ dạng:
    [Nguồn: Ảnh số X] hoặc [Nguồn: Page số Y]

    Dưới đây là nội dung OCR:
    ------------------------------------
    {ocr_text}
    ------------------------------------

    ========================================
    QUY TẮC BẮT BUỘC
    ========================================
    1. Chỉ sử dụng thông tin xuất hiện trong OCR.
    2. KHÔNG thêm kiến thức mới, không mở rộng, không suy luận.
    3. KHÔNG diễn giải ngoài nội dung cho sẵn.
    4. Chỉ được rút gọn, hệ thống hóa và làm rõ ý.
    5. Lựa chọn cấu trúc phù hợp với nội dung:
    - Nếu lý thuyết → tóm khái niệm chính.
    - Nếu kỹ thuật → tóm quy trình, nguyên lý, công thức.
    - Nếu bảng → chỉ nêu insight quan trọng, không mô tả chi tiết.
    - Nếu biểu đồ → mô tả xu hướng chính.
    - Nếu bài tập → tóm mục tiêu và phương pháp.
    - Nếu văn bản học thuật → tóm theo luận điểm.
    6. Giữ nguyên ký hiệu, công thức quan trọng.
    7. Khi chuyển sang đoạn có chủ đề khác → dùng từ nối nhẹ (ví dụ: “Tiếp theo”, “Ngoài ra”, “Một nội dung khác đề cập đến…”).

    ========================================
    KẾT CẤU ĐẦU RA (BẮT BUỘC)
    ========================================
    Trả về JSON duy nhất chứa 2 trường sau:
        - title: dựa trên toàn bộ nội dung OCR để tạo tiêu đề chung, ngắn gọn và chính xác
        - summary: bản tóm tắt kiến thức quan trọng, có các từ nối nhẹ giữa những phần thuộc chủ đề khác nhau và kèm chú thích nguồn ảnh/page khi cần thiết

    ========================================
    Hãy bắt đầu tạo bản tóm tắt.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=summary_prompt
    )

    return response.text
