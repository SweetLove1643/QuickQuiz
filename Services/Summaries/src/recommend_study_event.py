import google.genai as genai
from google.genai import types
import json

def RecommendStudyEvent(userEmail,newNote, allEventsInMonth, api_key:str):
    """
    Hàm đề xuất sự kiện học tập liên quan dựa trên ghi chú mới và các sự kiện đã có trong tháng.
    Sử dụng mô hình Gemini 2.5 Flash để phân tích và đề xuất.
    """
    client = genai.Client(api_key=api_key)

    prompt = f"""
        Bạn là hệ thống lập lịch học tối ưu cho con người, sử dụng trí tuệ nhân tạo.

        ===========================================
        NHIỆM VỤ CHÍNH
        ===========================================
        Dựa vào:
        1. "newNote" – chứa nội dung ghi chú học tập mới, mô tả môn học, mức độ, lượng kiến thức.
        2. "allEventsInMonth" – danh sách các sự kiện/lịch học đã có trong tháng.
        3. "userEmail" – email người dùng.

        Hãy lên lịch cho buổi học mới tương ứng với newNote sao cho:
        - Phù hợp với nội dung ghi chú (tiêu đề và content).
        - Không trùng lịch với sự kiện đã có.
        - Phân bố hợp lý để đảm bảo sức khỏe.
        - Nếu tháng hiện tại không còn thời gian phù hợp → tự động tạo trong tháng kế tiếp.
        - Trả về duy nhất một JSON chứa event mới theo đúng format mẫu.

        ===========================================
        PHÂN TÍCH NỘI DUNG newNote
        ===========================================
        Hãy phân tích:
        - Kiến thức lĩnh vực liên quan.
        - Mức độ khó (dễ / trung bình / nặng).
        - Khối lượng kiến thức (ít / vừa / nhiều).
        - Mức độ khẩn cấp (dựa vào content và createdAt).
        - Gợi ý thời lượng học phù hợp (45–120 phút tùy môn).
        - Xác định thời điểm lý tưởng: sáng / chiều / tối.

        ===========================================
        QUY TẮC SẮP XẾP LỊCH
        ===========================================
        1. **Không xếp trùng ngày + giờ** với các event có sẵn.
        2. **Không xếp quá sớm trong ngày**: trước 07:00 không hợp lý.
        3. **Không xếp quá muộn**: sau 21:00 không hợp lý.
        4. **Thời gian nghỉ tối thiểu giữa các buổi học cùng ngày: 2 giờ**.
        5. **Không xếp quá 2 buổi học khó trong cùng một ngày.**
        6. **Nếu newNote liên quan đến bài kiểm tra**:
        - Xếp sớm hơn ngày kiểm tra ít nhất 1–5 ngày (nếu có timeline liên quan).
        7. **Nếu trong tháng không có ngày phù hợp → chuyển sang ngày đầu tiên phù hợp của tháng kế tiếp.**
        8. Ngày xếp lịch phải **sau thời điểm createdAt**.
        9. Giữ nguyên logic con người về sức khỏe: tránh học liên tục nhiều ngày nếu nội dung nặng (ưu tiên cách 1 ngày).

        ===========================================
        CÁCH CHỌN THỜI ĐIỂM PHÙ HỢP
        ===========================================
        Khi quyết định ngày + giờ, hãy:
        1. Duyệt từng ngày trong tháng từ near-future → cuối tháng.
        2. Tìm giờ trống hợp lý:
        - Ưu tiên 08:00–10:00 hoặc 14:00–17:00.
        3. Nếu không phù hợp → tiếp tục ngày tiếp theo.
        4. Nếu hết tháng → chuyển sang tháng kế tiếp với logic tương tự.

        ===========================================
        FORMAT JSON BẮT BUỘC TRẢ VỀ
        ===========================================
        PHẢI trả về đúng dạng sau (không nhiều hơn, không ít hơn):

        {{
        "id": "<tạo một UUID>",
        "title": "<từ newNote hoặc sinh tiêu đề phù hợp>",
        "description": "<mô tả buổi học, dựa trên nội dung newNote>",
        "email": "<email trong input>",
        "date": "YYYY-MM-DD",
        "time": "HH:mm",
        "color": "#33A1FD",
        "eventDateTime": "YYYY-MM-DDTHH:mm:00",
        "notificationSent": false
        }}

        ===========================================
        QUY TẮC BẮT BUỘC VỀ JSON
        ===========================================
        - email = userEmail từ input.
        - id là UUID ngẫu nhiên.
        - color giữ mặc định "#33A1FD" nếu không có yêu cầu khác.
        - notificationSent = false.
        - Không thêm trường mới ngoài mẫu JSON.
        - Không trả về nhiều event, chỉ 1 event mới duy nhất.

        ===========================================
        DỮ LIỆU ĐẦU VÀO
        ===========================================
        userEmail:
        {userEmail}

        newNote:
        {newNote}

        allEventsInMonth:
        {allEventsInMonth}

        ===========================================
        NHIỆM VỤ CUỐI
        ===========================================
        Hãy phân tích dữ liệu và trả về JSON event mới phù hợp nhất theo đúng format quy định.
        KHÔNG trả lời thêm giải thích. Chỉ trả về JSON.

    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    try:
        event_json = json.loads(response.text)
        return event_json
    except:
        return {"error": "Model không trả về JSON hợp lệ", "raw": response.text}
