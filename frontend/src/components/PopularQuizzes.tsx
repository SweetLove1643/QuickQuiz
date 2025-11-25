import { Brain, Users, Clock, Star, Trophy } from "lucide-react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";

const popularQuizzes = [
  {
    id: 1,
    title: "Lịch sử Việt Nam - Các triều đại phong kiến",
    author: "Nguyễn Văn A",
    avatarColor: "bg-purple-500",
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
      {
        id: "3",
        question: "Nhà Trần kéo dài bao nhiêu năm?",
        options: ["175 năm", "200 năm", "150 năm", "100 năm"],
        correctAnswer: 0,
      },
    ],
    participants: 542,
    avgTime: "12 phút",
    avgScore: 78,
    rating: 4.8,
    difficulty: "Trung bình",
    category: "Lịch sử",
    documentName: "Lịch sử Việt Nam - Thời kỳ Đại Việt",
  },
  {
    id: 2,
    title: "Sinh học - Cơ chế di truyền",
    author: "Trần Thị B",
    avatarColor: "bg-green-500",
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
      {
        id: "3",
        question: "Quá trình sao chép DNA diễn ra ở giai đoạn nào?",
        options: ["G1", "S", "G2", "M"],
        correctAnswer: 1,
      },
    ],
    participants: 423,
    avgTime: "15 phút",
    avgScore: 72,
    rating: 4.6,
    difficulty: "Khó",
    category: "Sinh học",
    documentName: "Sinh học phân tử - Chương DNA và RNA",
  },
  {
    id: 3,
    title: "Toán học - Phương trình vi phân",
    author: "Lê Văn C",
    avatarColor: "bg-blue-500",
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
    documentName: "Toán học cao cấp - Giải tích",
  },
  {
    id: 4,
    title: "IELTS Vocabulary - Academic Words",
    author: "Phạm Thị D",
    avatarColor: "bg-orange-500",
    questions: [
      {
        id: "1",
        question: "What does 'sophisticated' mean?",
        options: ["Simple", "Complex and refined", "Old", "Cheap"],
        correctAnswer: 1,
      },
      {
        id: "2",
        question: "What is a synonym for 'prominent'?",
        options: ["Hidden", "Important", "Small", "Weak"],
        correctAnswer: 1,
      },
      {
        id: "3",
        question: "What does 'substantial' mean?",
        options: ["Tiny", "Considerable in size", "Quick", "Light"],
        correctAnswer: 1,
      },
    ],
    participants: 687,
    avgTime: "10 phút",
    avgScore: 85,
    rating: 4.7,
    difficulty: "Dễ",
    category: "Tiếng Anh",
    documentName: "IELTS Academic Vocabulary",
  },
];

interface PopularQuizzesProps {
  onNavigate?: (page: string) => void;
  onQuizSelected?: (quiz: any) => void;
}

export function PopularQuizzes({ onNavigate, onQuizSelected }: PopularQuizzesProps) {
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

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-slate-900 mb-1">Bài Quiz phổ biến</h2>
          <p className="text-slate-600">Các bài quiz được nhiều người làm nhất</p>
        </div>
        <Button variant="ghost">Xem tất cả</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {popularQuizzes.map((quiz) => (
          <Card key={quiz.id} className="p-4 hover:shadow-lg transition-shadow">
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center shrink-0">
                <Brain className="size-6 text-purple-600" />
              </div>
              <Badge className={getDifficultyColor(quiz.difficulty)}>
                {quiz.difficulty}
              </Badge>
            </div>

            {/* Title & Category */}
            <div className="mb-3">
              <Badge variant="outline" className="mb-2">
                {quiz.category}
              </Badge>
              <h3 className="text-slate-900 mb-1 line-clamp-2">
                {quiz.title}
              </h3>
              <p className="text-slate-500">{quiz.questions.length} câu hỏi</p>
            </div>

            {/* Author */}
            <div className="flex items-center gap-2 mb-3">
              <div className={`w-6 h-6 rounded-full ${quiz.avatarColor} flex items-center justify-center`}>
                <span className="text-white text-xs">
                  {quiz.author.charAt(0)}
                </span>
              </div>
              <span className="text-slate-600 text-sm">{quiz.author}</span>
            </div>

            {/* Stats */}
            <div className="space-y-2 mb-3 pb-3 border-b border-slate-100">
              <div className="flex items-center justify-between text-slate-600 text-sm">
                <div className="flex items-center gap-1">
                  <Users className="size-4" />
                  <span>{quiz.participants} người</span>
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="size-4" />
                  <span>{quiz.avgTime}</span>
                </div>
              </div>
              <div className="flex items-center justify-between text-slate-600 text-sm">
                <div className="flex items-center gap-1">
                  <Trophy className="size-4 text-yellow-500" />
                  <span>TB: {quiz.avgScore}%</span>
                </div>
                <div className="flex items-center gap-1">
                  <Star className="size-4 fill-yellow-400 text-yellow-400" />
                  <span>{quiz.rating}</span>
                </div>
              </div>
            </div>

            <Button 
              className="w-full" 
              size="sm" 
              onClick={() => {
                if (onQuizSelected && onNavigate) {
                  onQuizSelected(quiz);
                  onNavigate("take-quiz");
                }
              }}
            >
              Làm bài Quiz
            </Button>
          </Card>
        ))}
      </div>
    </div>
  );
}