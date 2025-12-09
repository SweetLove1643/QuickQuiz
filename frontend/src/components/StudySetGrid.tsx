import { StudySetCard } from "./StudySetCard";

type PageType =
  | "home"
  | "library"
  | "quick-start"
  | "upload-document"
  | "create-quiz-standalone"
  | "create-quiz"
  | "take-quiz"
  | "quiz-result"
  | "view-document"
  | "chatbot";

const studySets = [
  {
    id: 1,
    title: "Từ vựng Tiếng Anh cơ bản",
    termCount: 50,
    author: "Nguyễn Văn A",
    avatarColor: "bg-blue-500",
    lastStudied: "2 giờ trước",
    type: "quiz" as const,
    documentName: "Từ vựng Tiếng Anh cơ bản",
    questions: [
      {
        id: "1",
        question: "What does 'beautiful' mean in Vietnamese?",
        options: ["Đẹp", "Xấu", "Tốt", "Dễ thương"],
        correctAnswer: 0,
      },
      {
        id: "2",
        question: "What is the past tense of 'go'?",
        options: ["Goed", "Went", "Gone", "Going"],
        correctAnswer: 1,
      },
      {
        id: "3",
        question: "What does 'happy' mean?",
        options: ["Buồn", "Vui", "Giận", "Sợ"],
        correctAnswer: 1,
      },
    ],
  },
  {
    id: 2,
    title: "Sinh học lớp 10 - Chương 1",
    termCount: 35,
    author: "Trần Thị B",
    avatarColor: "bg-green-500",
    lastStudied: "5 giờ trước",
    type: "document" as const,
    status: "Riêng tư",
    summary:
      "Tài liệu tổng hợp kiến thức sinh học lớp 10 chương 1, bao gồm các khái niệm cơ bản về tế bào, cấu trúc và chức năng của tế bào thực vật và động vật.",
    content: `# Sinh học lớp 10 - Chương 1: Tế bào

## Khái niệm tế bào
Tế bào là đơn vị cấu tạo cơ bản của mọi sinh vật sống.

## Cấu trúc tế bào

### Tế bào thực vật
- Thành tế bào
- Màng tế bào
- Tế bào chất
- Nhân tế bào
- Lục lạp
- Không bào

### Tế bào động vật
- Màng tế bào
- Tế bào chất
- Nhân tế bào
- Ti thể
- Bộ máy Golgi

## Chức năng
Các bào quan khác nhau đảm nhiệm các chức năng sinh học khác nhau trong tế bào.`,
  },
  {
    id: 3,
    title: "Lịch sử Việt Nam",
    termCount: 42,
    author: "Lê Văn C",
    avatarColor: "bg-purple-500",
    lastStudied: "1 ngày trước",
    type: "quiz" as const,
    documentName: "Lịch sử Việt Nam",
    questions: [
      {
        id: "1",
        question: "Triều đại phong kiến đầu tiên của Việt Nam là gì?",
        options: ["Nhà Đinh", "Nhà Lý", "Nhà Trần", "Nhà Ngô"],
        correctAnswer: 0,
      },
      {
        id: "2",
        question: "Ai là người lập ra nhà Lý?",
        options: ["Lý Thái Tổ", "Lý Công Uẩn", "Lý Thánh Tông", "Cả A và B"],
        correctAnswer: 3,
      },
    ],
  },
  {
    id: 4,
    title: "Toán học - Phương trình bậc 2",
    termCount: 28,
    author: "Phạm Thị D",
    avatarColor: "bg-orange-500",
    lastStudied: "2 ngày trước",
    type: "document" as const,
    status: "Công khai",
    summary:
      "Tài liệu về phương trình bậc 2, bao gồm công thức nghiệm, định lý Vi-ét và các bài tập áp dụng.",
    content: `# Toán học - Phương trình bậc 2

## Định nghĩa
Phương trình bậc 2 có dạng: ax² + bx + c = 0 (a ≠ 0)

## Công thức nghiệm

### Delta (Δ)
Δ = b² - 4ac

### Các trường hợp
- Nếu Δ > 0: Phương trình có 2 nghiệm phân biệt
  x₁ = (-b + √Δ) / 2a
  x₂ = (-b - √Δ) / 2a

- Nếu Δ = 0: Phương trình có nghiệm kép
  x = -b / 2a

- Nếu Δ < 0: Phương trình vô nghiệm

## Định lý Vi-ét
Với phương trình ax² + bx + c = 0 có 2 nghiệm x₁, x₂:
- Tổng: x₁ + x₂ = -b/a
- Tích: x₁ · x₂ = c/a

## Bài tập mẫu
1. Giải phương trình: x² - 5x + 6 = 0
2. Tìm m để phương trình có 2 nghiệm phân biệt`,
  },
  {
    id: 5,
    title: "Hóa học hữu cơ",
    termCount: 60,
    author: "Hoàng Văn E",
    avatarColor: "bg-red-500",
    lastStudied: "3 ngày trước",
    type: "quiz" as const,
    documentName: "Hóa học hữu cơ",
    questions: [
      {
        id: "1",
        question: "Công thức phân tử của Methane là gì?",
        options: ["CH4", "C2H6", "C3H8", "CH3OH"],
        correctAnswer: 0,
      },
      {
        id: "2",
        question: "Hợp chất hữu cơ chứa nhóm chức nào?",
        options: [
          "Chỉ Carbon",
          "Carbon và Hydrogen",
          "Carbon, Hydrogen và có thể có các nguyên tố khác",
          "Chỉ Hydrogen",
        ],
        correctAnswer: 2,
      },
    ],
  },
  {
    id: 6,
    title: "Vật lý - Điện học",
    termCount: 38,
    author: "Đỗ Thị F",
    avatarColor: "bg-indigo-500",
    lastStudied: "1 tuần trước",
    type: "document" as const,
    status: "Công khai",
    summary:
      "Tài liệu điện học cơ bản bao gồm định luật Ohm, mạch điện, công suất điện và năng lượng điện.",
    content: `# Vật lý - Điện học

## Định luật Ohm
Cường độ dòng điện qua dây dẫn tỉ lệ thuận với hiệu điện thế giữa hai đầu dây dẫn.

### Công thức
I = U / R

Trong đó:
- I: Cường độ dòng điện (A)
- U: Hiệu điện thế (V)
- R: Điện trở (Ω)

## Công suất điện
P = U · I = I² · R = U² / R

## Năng lượng điện
A = P · t = U · I · t

## Định luật Joule-Lenz
Nhiệt lượng tỏa ra trên dây dẫn:
Q = I² · R · t

## Mạch điện
- Mắc nối tiếp: I = I₁ = I₂, U = U₁ + U₂
- Mắc song song: U = U₁ = U₂, I = I₁ + I₂`,
  },
];

interface StudySetGridProps {
  onNavigate?: (page: PageType, isFromQuickStart?: boolean) => void;
  onQuizSelected?: (quiz: any) => void;
  onDocumentSelected?: (document: any) => void;
}

export function StudySetGrid({
  onNavigate,
  onQuizSelected,
  onDocumentSelected,
}: StudySetGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {studySets.map((set) => (
        <StudySetCard
          key={set.id}
          studySet={set}
          onNavigate={onNavigate}
          onQuizSelected={onQuizSelected}
          onDocumentSelected={onDocumentSelected}
        />
      ))}
    </div>
  );
}
