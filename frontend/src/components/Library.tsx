import {
  FileText,
  Brain,
  Eye,
  Download,
  Users,
  Clock,
  Star,
  MoreVertical,
  Edit,
  Trash2,
  Play,
} from "lucide-react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Badge } from "./ui/badge";

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

const myDocuments = [
  {
    id: 1,
    title: "Lịch sử Việt Nam - Thời kỳ Đại Việt",
    views: 1250,
    downloads: 320,
    rating: 4.8,
    pages: 45,
    uploadDate: "2 ngày trước",
    status: "Công khai",
    summary:
      "Tài liệu này tổng hợp các triều đại phong kiến Việt Nam từ thời Đinh - Tiền Lê đến cuối thời Lý. Nội dung tập trung vào các sự kiện lịch sử quan trọng, các vị vua nổi bật và những đóng góp của họ cho đất nước.",
    content: `# Lịch sử Việt Nam - Thời kỳ Đại Việt

## Giới thiệu
Thời kỳ Đại Việt là giai đoạn quan trọng trong lịch sử Việt Nam, đánh dấu sự hình thành và phát triển của các triều đại phong kiến độc lập.

## Các triều đại chính

### 1. Nhà Đinh (968-980)
- Người sáng lập: Đinh Bộ Lĩnh
- Thành tựu: Thống nhất đất nước sau thời Thập Nhị Sứ Quân
- Đặt tên nước là Đại Cồ Việt

### 2. Nhà Tiền Lê (980-1009)
- Người sáng lập: Lê Hoàn
- Chiến thắng quân Tống xâm lược
- Phát triển kinh tế, văn hóa

### 3. Nhà Lý (1009-1225)
- Người sáng lập: Lý Công Uẩn (Lý Thái Tổ)
- Thời kỳ thịnh trị dưới các vua Lý Thánh Tông, Lý Nhân Tông
- Xây dựng Văn Miếu, phát triển Phật giáo

## Kết luận
Thời kỳ Đại Việt đặt nền móng cho sự phát triển lâu dài của dân tộc Việt Nam.`,
  },
  {
    id: 2,
    title: "Sinh học phân tử - Chương DNA và RNA",
    views: 980,
    downloads: 215,
    rating: 4.6,
    pages: 32,
    uploadDate: "1 tuần trước",
    status: "Riêng tư",
    summary:
      "Chương này giải thích cấu trúc và chức năng của DNA và RNA, hai phân tử di truyền quan trọng nhất trong tế bào sống. Nội dung bao gồm cấu trúc xoắn kép, quá trình sao chép và phiên mã.",
    content: `# Sinh học phân tử - DNA và RNA

## Cấu trúc DNA

### Thành phần cơ bản
- Đường deoxyribose
- Nhóm phosphate
- 4 loại base: Adenine (A), Thymine (T), Guanine (G), Cytosine (C)

### Cấu trúc xoắn kép
- Hai chuỗi polynucleotide chạy song song ngược chiều
- Liên kết hydro giữa các base bổ sung: A-T, G-C

## RNA và vai trò

### Các loại RNA
1. mRNA - messenger RNA
2. tRNA - transfer RNA  
3. rRNA - ribosomal RNA

### Sự khác biệt DNA và RNA
- RNA có đường ribose thay vì deoxyribose
- RNA có Uracil (U) thay vì Thymine (T)
- RNA thường là chuỗi đơn

## Quá trình sinh học

### Sao chép DNA
- Diễn ra trong pha S của chu kỳ tế bào
- Enzyme DNA polymerase tham gia

### Phiên mã (Transcription)
- Tổng hợp mRNA từ DNA
- Enzyme RNA polymerase

### Dịch mã (Translation)
- Tổng hợp protein từ mRNA
- Diễn ra tại ribosome`,
  },
  {
    id: 3,
    title: "Toán học cao cấp - Giải tích",
    views: 875,
    downloads: 190,
    rating: 4.9,
    pages: 56,
    uploadDate: "3 ngày trước",
    status: "Công khai",
    summary:
      "Tài liệu giải tích cao cấp bao gồm lý thuyết về giới hạn, đạo hàm, tích phân và phương trình vi phân. Phù hợp cho sinh viên năm đầu đại học và học sinh chuyên toán.",
    content: `# Toán học cao cấp - Giải tích

## Chương 1: Giới hạn và Liên tục

### Định nghĩa giới hạn
- Giới hạn của hàm số khi x tiến tới một giá trị
- Các định lý về giới hạn

### Hàm liên tục
- Định nghĩa tính liên tục tại một điểm
- Tính chất của hàm liên tục

## Chương 2: Đạo hàm

### Định nghĩa đạo hàm
f'(x) = lim[h→0] (f(x+h) - f(x))/h

### Các quy tắc đạo hàm
- Đạo hàm của tổng, hiệu, tích, thương
- Đạo hàm hàm hợp
- Đạo hàm hàm ngược

## Chương 3: Tích phân

### Tích phân bất định
∫f(x)dx = F(x) + C

### Tích phân xác định
∫[a,b] f(x)dx

### Ứng dụng
- Tính diện tích
- Tính thể tích
- Độ dài đường cong

## Chương 4: Phương trình vi phân

### Phương trình vi phân cấp 1
dy/dx = f(x,y)

### Phương trình vi phân cấp 2
d²y/dx² + p(x)dy/dx + q(x)y = r(x)`,
  },
];

const myQuizzes = [
  {
    id: 1,
    title: "Lịch sử Việt Nam - Các triều đại phong kiến",
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
    participants: 542,
    avgTime: "12 phút",
    avgScore: 78,
    rating: 4.8,
    difficulty: "Trung bình",
    category: "Lịch sử",
    createdDate: "5 ngày trước",
    status: "Công khai",
    documentName: "Lịch sử Việt Nam - Thời kỳ Đại Việt",
  },
  {
    id: 2,
    title: "Sinh học - Cơ chế di truyền",
    questions: [
      {
        id: "1",
        question: "DNA viết tắt của gì?",
        options: [
          "Deoxyribonucleic Acid",
          "Deoxyribose Nuclear Acid",
          "Dioxide Nucleic Acid",
          "Deoxygen Nucleic Acid",
        ],
        correctAnswer: 0,
      },
      {
        id: "2",
        question: "Có bao nhiêu loại base trong DNA?",
        options: ["2", "3", "4", "5"],
        correctAnswer: 2,
      },
    ],
    participants: 423,
    avgTime: "15 phút",
    avgScore: 72,
    rating: 4.6,
    difficulty: "Khó",
    category: "Sinh học",
    createdDate: "1 tuần trước",
    status: "Công khai",
    documentName: "Sinh học phân tử - Chương DNA và RNA",
  },
  {
    id: 3,
    title: "Toán học - Phương trình vi phân",
    questions: [
      {
        id: "1",
        question: "Phương trình vi phân là gì?",
        options: [
          "Phương trình chứa đạo hàm",
          "Phương trình đại số",
          "Phương trình bậc hai",
          "Phương trình tích phân",
        ],
        correctAnswer: 0,
      },
      {
        id: "2",
        question: "Nghiệm tổng quát của phương trình dy/dx = ky là gì?",
        options: ["y = Ce^(kx)", "y = Cx + k", "y = kx^2 + C", "y = sin(kx)"],
        correctAnswer: 0,
      },
    ],
    participants: 358,
    avgTime: "18 phút",
    avgScore: 65,
    rating: 4.9,
    difficulty: "Khó",
    category: "Toán học",
    createdDate: "2 tuần trước",
    status: "Riêng tư",
    documentName: "Toán học cao cấp - Giải tích",
  },
];

interface LibraryProps {
  onNavigate?: (page: PageType, isFromQuickStart?: boolean) => void;
  onQuizSelected?: (quiz: any) => void;
  onDocumentSelected?: (document: any) => void;
}

export function Library({
  onNavigate,
  onQuizSelected,
  onDocumentSelected,
}: LibraryProps) {
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "Dễ":
        return "bg-green-100 text-green-700";
      case "Trung bình":
        return "bg-yellow-100 text-yellow-700";
      case "Khó":
        return "bg-red-100 text-red-700";
      default:
        return "bg-slate-100 text-slate-700";
    }
  };

  const getStatusColor = (status: string) => {
    return status === "Công khai"
      ? "bg-green-100 text-green-700"
      : "bg-slate-100 text-slate-700";
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-slate-900 mb-2">Thư viện của tôi</h1>
        <p className="text-slate-600">Quản lý tài liệu và bài quiz của bạn</p>
      </div>

      <Tabs defaultValue="documents" className="w-full">
        <TabsList className="mb-6">
          <TabsTrigger value="documents">
            <FileText className="size-4 mr-2" />
            Tài liệu của tôi ({myDocuments.length})
          </TabsTrigger>
          <TabsTrigger value="quizzes">
            <Brain className="size-4 mr-2" />
            Quiz của tôi ({myQuizzes.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="documents" className="space-y-4">
          {myDocuments.map((doc) => (
            <Card
              key={doc.id}
              className="p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  {/* Icon */}
                  <div className="w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center shrink-0">
                    <FileText className="size-8 text-blue-600" />
                  </div>

                  {/* Content */}
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="text-slate-900 mb-2">{doc.title}</h3>
                        <div className="flex items-center gap-3 text-slate-600">
                          <span>{doc.pages} trang</span>
                          <span>•</span>
                          <span>{doc.uploadDate}</span>
                          <Badge className={getStatusColor(doc.status)}>
                            {doc.status}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="flex items-center gap-6 text-slate-600 mt-4">
                      <div className="flex items-center gap-2">
                        <Eye className="size-4" />
                        <span>{doc.views} lượt xem</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Download className="size-4" />
                        <span>{doc.downloads} lượt tải</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Star className="size-4 fill-yellow-400 text-yellow-400" />
                        <span>{doc.rating}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 ml-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      console.log("Viewing document:", doc.id);
                      onDocumentSelected?.(doc);
                    }}
                  >
                    <Eye className="size-4 mr-2" />
                    Xem
                  </Button>
                  <Button variant="ghost" size="icon">
                    <MoreVertical className="size-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}

          {myDocuments.length === 0 && (
            <div className="text-center py-12">
              <FileText className="size-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-slate-900 mb-2">Chưa có tài liệu nào</h3>
              <p className="text-slate-600 mb-4">
                Bắt đầu upload tài liệu đầu tiên của bạn
              </p>
              <Button>Upload tài liệu</Button>
            </div>
          )}
        </TabsContent>

        <TabsContent value="quizzes" className="space-y-4">
          {myQuizzes.map((quiz) => (
            <Card
              key={quiz.id}
              className="p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  {/* Icon */}
                  <div className="w-16 h-16 bg-purple-100 rounded-lg flex items-center justify-center shrink-0">
                    <Brain className="size-8 text-purple-600" />
                  </div>

                  {/* Content */}
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="text-slate-900">{quiz.title}</h3>
                          <Badge
                            className={getDifficultyColor(quiz.difficulty)}
                          >
                            {quiz.difficulty}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-3 text-slate-600">
                          <Badge variant="outline">{quiz.category}</Badge>
                          <span>{quiz.questions.length} câu hỏi</span>
                          <span>•</span>
                          <span>{quiz.createdDate}</span>
                          <Badge className={getStatusColor(quiz.status)}>
                            {quiz.status}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="flex items-center gap-6 text-slate-600 mt-4">
                      <div className="flex items-center gap-2">
                        <Users className="size-4" />
                        <span>{quiz.participants} người tham gia</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="size-4" />
                        <span>TB: {quiz.avgTime}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Star className="size-4 fill-yellow-400 text-yellow-400" />
                        <span>{quiz.rating}</span>
                      </div>
                      <div className="flex items-center gap-2 text-green-600">
                        <span>Điểm TB: {quiz.avgScore}%</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 ml-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      console.log("Editing quiz:", quiz.id);
                      onNavigate?.("create-quiz-standalone");
                    }}
                  >
                    <Edit className="size-4 mr-2" />
                    Chỉnh sửa
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      console.log("Taking quiz:", quiz.id);
                      onNavigate?.("take-quiz");
                      onQuizSelected?.(quiz);
                    }}
                  >
                    <Play className="size-4 mr-2" />
                    Làm bài
                  </Button>
                  <Button variant="ghost" size="icon">
                    <MoreVertical className="size-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}

          {myQuizzes.length === 0 && (
            <div className="text-center py-12">
              <Brain className="size-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-slate-900 mb-2">Chưa có quiz nào</h3>
              <p className="text-slate-600 mb-4">
                Tạo bài quiz đầu tiên của bạn
              </p>
              <Button>Tạo quiz mới</Button>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
