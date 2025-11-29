import { Plus, Trash2, Loader2, Sparkles, Save } from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { useState } from "react";
import {
  quizAPI,
  convertToBackendFormat,
  convertFromBackendFormat,
} from "../api/quizAPI";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "./ui/dialog";
import { Label } from "./ui/label";
import { Checkbox } from "./ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";

interface CreateQuizStandaloneProps {
  onQuizCreated: (quiz: any) => void;
}

interface Question {
  id: string;
  question: string;
  options: string[];
  correctAnswer: number;
  type?: "multiple-choice" | "true-false" | "fill-blank";
}

// Mock documents for selection
const mockDocuments = [
  { id: "1", fileName: "Bài giảng Toán học.pdf", uploadDate: "2024-01-15" },
  { id: "2", fileName: "Lịch sử Việt Nam.docx", uploadDate: "2024-01-10" },
  { id: "3", fileName: "Vật lý đại cương.pdf", uploadDate: "2024-01-05" },
];

export function CreateQuizStandalone({
  onQuizCreated,
}: CreateQuizStandaloneProps) {
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [quizTitle, setQuizTitle] = useState("");
  const [documentContent, setDocumentContent] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [validationInfo, setValidationInfo] = useState<any>(null);
  const [questions, setQuestions] = useState<Question[]>([
    {
      id: "1",
      question: "Chương 1 giới thiệu về nội dung gì?",
      options: ["Chủ đề chính", "Bài tập", "Kết luận", "Tài liệu tham khảo"],
      correctAnswer: 0,
      type: "multiple-choice",
    },
    {
      id: "2",
      question: "Chương 2 bao gồm những nội dung nào?",
      options: [
        "Giới thiệu",
        "Khái niệm cơ bản và định nghĩa",
        "Phụ lục",
        "Mục lục",
      ],
      correctAnswer: 1,
      type: "multiple-choice",
    },
  ]);

  // AI Generation settings
  const [aiDialogOpen, setAiDialogOpen] = useState(false);
  const [aiQuestionCount, setAiQuestionCount] = useState("5");
  const [aiQuestionTypes, setAiQuestionTypes] = useState({
    multipleChoice: true,
    trueFalse: true,
    fillBlank: false,
  });
  const [aiDifficulty, setAiDifficulty] = useState("medium");

  const handleGenerateQuestions = async () => {
    if (!documentContent.trim()) {
      setApiError("Vui lòng nhập nội dung để tạo câu hỏi");
      return;
    }

    setIsGenerating(true);
    setAiDialogOpen(false);
    setApiError(null);

    try {
      // Convert frontend settings to backend format
      const requestData = convertToBackendFormat(documentContent, {
        questionCount: aiQuestionCount,
        questionTypes: aiQuestionTypes,
        difficulty: aiDifficulty,
      });

      // Call real API
      const response = await quizAPI.generateQuiz(requestData);

      // Convert backend format to frontend format
      const newQuestions = convertFromBackendFormat(response.questions);

      // Store validation info
      setValidationInfo(response.validation);

      // Add to existing questions
      setQuestions([...newQuestions, ...questions]);

      console.log("Generated questions with validation:", response.validation);
    } catch (error) {
      console.error("Failed to generate questions:", error);
      setApiError(
        error instanceof Error ? error.message : "Có lỗi xảy ra khi tạo câu hỏi"
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const addQuestion = (
    type: "multiple-choice" | "true-false" | "fill-blank" = "multiple-choice"
  ) => {
    const newQuestion: Question = {
      id: Date.now().toString(),
      question: "",
      options:
        type === "true-false"
          ? ["Đúng", "Sai"]
          : type === "fill-blank"
          ? [""]
          : ["", "", "", ""],
      correctAnswer: 0,
      type,
    };
    setQuestions([newQuestion, ...questions]);
  };

  const updateQuestion = (id: string, field: string, value: any) => {
    setQuestions(
      questions.map((q) => (q.id === id ? { ...q, [field]: value } : q))
    );
  };

  const handleQuestionTypeChange = (
    id: string,
    newType: "multiple-choice" | "true-false" | "fill-blank"
  ) => {
    setQuestions(
      questions.map((q) => {
        if (q.id === id) {
          let newOptions: string[];
          if (newType === "true-false") {
            newOptions = ["Đúng", "Sai"];
          } else if (newType === "fill-blank") {
            newOptions = [""];
          } else {
            newOptions = ["", "", "", ""];
          }
          return {
            ...q,
            type: newType,
            options: newOptions,
            correctAnswer: 0,
          };
        }
        return q;
      })
    );
  };

  const updateOption = (
    questionId: string,
    optionIndex: number,
    value: string
  ) => {
    setQuestions(
      questions.map((q) =>
        q.id === questionId
          ? {
              ...q,
              options: q.options.map((opt, idx) =>
                idx === optionIndex ? value : opt
              ),
            }
          : q
      )
    );
  };

  const deleteQuestion = (id: string) => {
    setQuestions(questions.filter((q) => q.id !== id));
  };

  const handleStartQuiz = () => {
    const selectedDoc = mockDocuments.find(
      (doc) => doc.id === selectedDocumentId
    );

    // Save quiz data
    const quizData = {
      title: quizTitle,
      questions: questions,
      documentName: selectedDoc?.fileName || "Không có tài liệu",
      createdAt: new Date().toISOString(),
    };

    // Here you would typically save to backend/database
    console.log("Quiz saved:", quizData);

    // Show success message (you can use toast here if available)
    alert(`Đã lưu bài quiz "${quizTitle}" với ${questions.length} câu hỏi!`);

    // Optionally reset form or navigate
    // You can uncomment the following to reset:
    // setQuizTitle("");
    // setSelectedDocumentId("");
    // setQuestions([]);
  };

  // Auto-set quiz title when document is selected
  const handleDocumentChange = (docId: string) => {
    setSelectedDocumentId(docId);
    const selectedDoc = mockDocuments.find((doc) => doc.id === docId);
    if (selectedDoc && !quizTitle) {
      setQuizTitle(`Quiz - ${selectedDoc.fileName}`);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-slate-900 mb-2">Tạo bài Quiz</h1>
        <p className="text-slate-600">
          Chọn tài liệu và tạo quiz cho nội dung học tập
        </p>
      </div>

      {/* Document Selection */}
      <Card className="p-6 mb-6">
        <Label htmlFor="document-select" className="mb-2 block">
          Chọn tài liệu
        </Label>
        <Select value={selectedDocumentId} onValueChange={handleDocumentChange}>
          <SelectTrigger id="document-select">
            <SelectValue placeholder="Chọn tài liệu từ thư viện..." />
          </SelectTrigger>
          <SelectContent>
            {mockDocuments.map((doc) => (
              <SelectItem key={doc.id} value={doc.id}>
                {doc.fileName}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </Card>

      {/* Content Input */}
      <Card className="p-6 mb-6">
        <label className="block mb-2 text-slate-700">
          Nội dung để tạo câu hỏi
        </label>
        <Textarea
          value={documentContent}
          onChange={(e) => setDocumentContent(e.target.value)}
          placeholder="Nhập nội dung học liệu để AI tạo câu hỏi..."
          className="min-h-[120px]"
        />
        <p className="text-sm text-slate-500 mt-2">
          Hãy nhập đoạn text bạn muốn tạo câu hỏi. AI sẽ phân tích và tạo ra các
          câu hỏi phù hợp.
        </p>
      </Card>

      {/* Quiz Title */}
      <Card className="p-6 mb-6">
        <label className="block mb-2 text-slate-700">Tên bài Quiz</label>
        <Input
          value={quizTitle}
          onChange={(e) => setQuizTitle(e.target.value)}
          placeholder="Nhập tên bài quiz..."
        />
      </Card>

      {/* API Error Display */}
      {apiError && (
        <Card className="p-4 mb-6 bg-red-50 border-red-200">
          <p className="text-red-600 text-sm">{apiError}</p>
        </Card>
      )}

      {/* Validation Info Display */}
      {validationInfo && (
        <Card className="p-4 mb-6 bg-green-50 border-green-200">
          <h4 className="text-green-800 font-semibold mb-2">
            Thông tin validation AI:
          </h4>
          <div className="text-sm text-green-700 space-y-1">
            <p>
              ✅ Tổng câu hỏi:{" "}
              {validationInfo.summary?.total_questions || "N/A"}
            </p>
            <p>
              ✅ Câu hỏi hợp lệ:{" "}
              {validationInfo.summary?.valid_questions || "N/A"}
            </p>
            <p>
              ✅ Tỷ lệ validation:{" "}
              {validationInfo.summary?.validation_rate || "N/A"}%
            </p>
            <p>
              ✅ Độ tin cậy trung bình:{" "}
              {validationInfo.summary?.average_confidence || "N/A"}
            </p>
            {validationInfo.high_risk_count > 0 && (
              <p className="text-orange-600">
                ⚠️ Phát hiện {validationInfo.high_risk_count} câu hỏi rủi ro cao
              </p>
            )}
          </div>
        </Card>
      )}

      {/* Questions List */}
      <div className="space-y-4 mb-6">
        {questions.map((question, qIndex) => (
          <Card key={question.id} className="p-6">
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-slate-900">Câu hỏi {qIndex + 1}</h3>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => deleteQuestion(question.id)}
              >
                <Trash2 className="size-4 text-red-600" />
              </Button>
            </div>

            <div className="mb-4">
              <Label htmlFor={`type-${question.id}`} className="mb-2 block">
                Loại câu hỏi
              </Label>
              <Select
                value={question.type || "multiple-choice"}
                onValueChange={(value: string) =>
                  handleQuestionTypeChange(
                    question.id,
                    value as "multiple-choice" | "true-false" | "fill-blank"
                  )
                }
              >
                <SelectTrigger id={`type-${question.id}`}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="multiple-choice">
                    Trắc nghiệm (4 đáp án)
                  </SelectItem>
                  <SelectItem value="true-false">
                    Đúng/Sai (2 đáp án)
                  </SelectItem>
                  <SelectItem value="fill-blank">
                    Điền khuyết (tự luận)
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Textarea
              value={question.question}
              onChange={(e) =>
                updateQuestion(question.id, "question", e.target.value)
              }
              placeholder="Nhập câu hỏi..."
              className="mb-4"
            />

            <div className="space-y-2">
              <label className="block text-slate-700 mb-2">
                Các đáp án (chọn đáp án đúng)
              </label>
              {question.options.map((option, optIndex) => (
                <div key={optIndex} className="flex items-center gap-2">
                  <input
                    type="radio"
                    name={`correct-${question.id}`}
                    checked={question.correctAnswer === optIndex}
                    onChange={() =>
                      updateQuestion(question.id, "correctAnswer", optIndex)
                    }
                    className="w-4 h-4"
                  />
                  <Input
                    value={option}
                    onChange={(e) =>
                      updateOption(question.id, optIndex, e.target.value)
                    }
                    placeholder={`Đáp án ${String.fromCharCode(65 + optIndex)}`}
                  />
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>

      {/* Generate Questions Button */}
      <div className="mb-6 flex gap-3">
        <Dialog open={aiDialogOpen} onOpenChange={setAiDialogOpen}>
          <DialogTrigger asChild>
            <Button
              disabled={isGenerating || !selectedDocumentId}
              className="flex-1"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="size-4 mr-2 animate-spin" />
                  Đang tạo câu hỏi...
                </>
              ) : (
                <>
                  <Sparkles className="size-4 mr-2" />
                  Tự động tạo câu hỏi từ tài liệu
                </>
              )}
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Cài đặt tạo câu hỏi tự động</DialogTitle>
              <DialogDescription>
                Cấu hình các tùy chọn để AI tạo câu hỏi từ tài liệu.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="question-count">Số lượng câu hỏi</Label>
                <Select
                  value={aiQuestionCount}
                  onValueChange={setAiQuestionCount}
                >
                  <SelectTrigger id="question-count">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="5">5 câu hỏi</SelectItem>
                    <SelectItem value="10">10 câu hỏi</SelectItem>
                    <SelectItem value="15">15 câu hỏi</SelectItem>
                    <SelectItem value="20">20 câu hỏi</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-3">
                <Label>Loại câu hỏi</Label>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="multiple-choice"
                      checked={aiQuestionTypes.multipleChoice}
                      onCheckedChange={(checked: boolean) =>
                        setAiQuestionTypes({
                          ...aiQuestionTypes,
                          multipleChoice: checked === true,
                        })
                      }
                    />
                    <Label htmlFor="multiple-choice" className="cursor-pointer">
                      Trắc nghiệm nhiều lựa chọn
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="true-false"
                      checked={aiQuestionTypes.trueFalse}
                      onCheckedChange={(checked: boolean) =>
                        setAiQuestionTypes({
                          ...aiQuestionTypes,
                          trueFalse: checked === true,
                        })
                      }
                    />
                    <Label htmlFor="true-false" className="cursor-pointer">
                      Đúng/Sai
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="fill-blank"
                      checked={aiQuestionTypes.fillBlank}
                      onCheckedChange={(checked: boolean) =>
                        setAiQuestionTypes({
                          ...aiQuestionTypes,
                          fillBlank: checked === true,
                        })
                      }
                    />
                    <Label htmlFor="fill-blank" className="cursor-pointer">
                      Điền vào chỗ trống
                    </Label>
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="difficulty">Độ khó</Label>
                <Select value={aiDifficulty} onValueChange={setAiDifficulty}>
                  <SelectTrigger id="difficulty">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="easy">Dễ</SelectItem>
                    <SelectItem value="medium">Trung bình</SelectItem>
                    <SelectItem value="hard">Khó</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                onClick={handleGenerateQuestions}
                disabled={isGenerating}
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="size-4 mr-2 animate-spin" />
                    Đang tạo...
                  </>
                ) : (
                  <>
                    <Sparkles className="size-4 mr-2" />
                    Tạo câu hỏi
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Button variant="outline" onClick={() => addQuestion()}>
          <Plus className="size-4 mr-2" />
          Thêm câu hỏi thủ công
        </Button>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <Button
          onClick={handleStartQuiz}
          className="flex-1"
          disabled={
            questions.length === 0 || !selectedDocumentId || !quizTitle.trim()
          }
        >
          <Save className="size-4 mr-2" />
          Lưu Quiz ({questions.length} câu hỏi)
        </Button>
      </div>
    </div>
  );
}
