import {
  Plus,
  Trash2,
  Loader2,
  Sparkles,
  Save,
  CheckCircle,
} from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
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

interface Document {
  document_id: string;
  file_name: string;
  file_type: string;
  extracted_text: string;
  summary: string;
  created_at: string;
}

export function CreateQuizStandalone({
  onQuizCreated,
}: CreateQuizStandaloneProps) {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(
    null
  );
  const [quizTitle, setQuizTitle] = useState("");
  const [documentContent, setDocumentContent] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [validationInfo, setValidationInfo] = useState<any>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  // Reset component state for next quiz creation
  const resetComponent = () => {
    setSelectedDocumentId("");
    setSelectedDocument(null);
    setQuizTitle("");
    setDocumentContent("");
    setQuestions([]);
    setApiError(null);
    setValidationInfo(null);
    setSaveSuccess(null);
    setIsSaving(false);
  };

  // AI Generation settings
  const [aiDialogOpen, setAiDialogOpen] = useState(false);
  const [aiQuestionCount, setAiQuestionCount] = useState("5");
  const [aiQuestionTypes, setAiQuestionTypes] = useState({
    multipleChoice: true,
    trueFalse: true,
    fillBlank: false,
  });
  const [aiDifficulty, setAiDifficulty] = useState("medium");

  // Load documents from API
  useEffect(() => {
    const loadDocuments = async () => {
      setIsLoadingDocuments(true);
      try {
        const response = await quizAPI.getDocuments();
        if (response.success) {
          setDocuments(response.documents);
        }
      } catch (error) {
        console.error("Failed to load documents:", error);
        setApiError("Không thể tải danh sách tài liệu");
      } finally {
        setIsLoadingDocuments(false);
      }
    };

    loadDocuments();
  }, []);

  const handleGenerateQuestions = async () => {
    const baseContent =
      selectedDocument?.summary ||
      selectedDocument?.extracted_text ||
      documentContent;
    if (!baseContent.trim()) {
      setApiError("Vui lòng chọn tài liệu hoặc nhập nội dung để tạo câu hỏi");
      return;
    }

    setIsGenerating(true);
    setAiDialogOpen(false);
    setApiError(null);

    const requestedTypes: ("mcq" | "tf" | "fill_blank")[] = [];
    if (aiQuestionTypes.multipleChoice) requestedTypes.push("mcq");
    if (aiQuestionTypes.trueFalse) requestedTypes.push("tf");
    if (aiQuestionTypes.fillBlank) requestedTypes.push("fill_blank");
    if (requestedTypes.length === 0) {
      requestedTypes.push("multiple_choice");
    }

    try {
      const count = parseInt(aiQuestionCount) || 5;
      const payload = {
        sections: [
          {
            id: selectedDocument?.document_id || `section-${Date.now()}`,
            summary: baseContent,
          },
        ],
        config: {
          n_questions: count,
          types: requestedTypes,
        },
      };

      const response = await quizAPI.generateQuiz(payload);
      const generated = convertFromBackendFormat(response.questions).map(
        (q) => ({
          id: q.id,
          question: q.question,
          options: q.options || ["Đúng", "Sai"],
          correctAnswer: q.correctAnswer ?? 0,
          type:
            q.type === "multiple-choice"
              ? "multiple-choice"
              : q.type === "true-false"
              ? "true-false"
              : "fill-blank",
        })
      );

      setQuestions([...generated]);
      setValidationInfo(response.validation);
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

  const handleStartQuiz = async () => {
    if (!quizTitle.trim()) {
      setApiError("Vui lòng nhập tên bài quiz");
      return;
    }

    if (questions.length === 0) {
      setApiError("Vui lòng thêm ít nhất 1 câu hỏi");
      return;
    }

    setIsSaving(true);
    setApiError(null);

    try {
      if (!user?.id) {
        throw new Error("Bạn cần đăng nhập để lưu quiz");
      }

      // Convert questions to backend format
      const quizPayload = {
        user_id: user.id,
        title: quizTitle,
        document_id: selectedDocument?.document_id,
        document_name: selectedDocument?.file_name || "Không có tài liệu",
        questions: questions.map((q) => ({
          id: q.id,
          stem: q.question,
          type:
            q.type === "multiple-choice"
              ? "mcq"
              : q.type === "true-false"
              ? "tf"
              : "fill_blank",
          options: q.options,
          answer:
            q.type === "true-false"
              ? q.correctAnswer === 0
                ? "Đúng"
                : "Sai"
              : q.type === "fill-blank"
              ? q.options[0]
              : q.options[q.correctAnswer],
        })),
        metadata: {
          question_count: questions.length,
          created_at: new Date().toISOString(),
        },
      };

      const response = await quizAPI.saveQuiz(quizPayload);

      if (response.success) {
        // Show success message
        const successMsg = `Đã lưu bài quiz "${quizTitle}" thành công!`;
        setSaveSuccess(successMsg);
        setIsSaving(false);
        // Auto-hide after 3 seconds and reset component
        setTimeout(() => {
          resetComponent();
        }, 3000);
        return;
      }
    } catch (error) {
      console.error("Failed to save quiz:", error);
      setApiError(
        error instanceof Error ? error.message : "Không thể lưu bài quiz"
      );
    } finally {
      setIsSaving(false);
    }
  };

  // Auto-set quiz title when document is selected
  const handleDocumentChange = (docId: string) => {
    setSelectedDocumentId(docId);
    const doc = documents.find((d) => d.document_id === docId);
    if (doc) {
      setSelectedDocument(doc);
      setDocumentContent(doc.summary || doc.extracted_text);
      if (!quizTitle) {
        setQuizTitle(`Quiz - ${doc.file_name}`);
      }
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
          <SelectTrigger id="document-select" disabled={isLoadingDocuments}>
            <SelectValue
              placeholder={
                isLoadingDocuments
                  ? "Đang tải..."
                  : "Chọn tài liệu từ thư viện..."
              }
            />
          </SelectTrigger>
          <SelectContent>
            {documents.map((doc) => (
              <SelectItem key={doc.document_id} value={doc.document_id}>
                {doc.file_name}
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
              {question.type === "fill-blank" ? (
                <Input
                  value={question.options[0] || ""}
                  onChange={(e) => updateOption(question.id, 0, e.target.value)}
                  placeholder="Nhập đáp án cần điền"
                />
              ) : (
                question.options.map((option, optIndex) => (
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
                      placeholder={`Đáp án ${String.fromCharCode(
                        65 + optIndex
                      )}`}
                    />
                  </div>
                ))
              )}
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
                disabled={isGenerating || !documentContent.trim()}
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
      <div className="flex gap-3 items-start">
        <div className="flex-1 flex flex-col gap-2">
          <Button
            onClick={handleStartQuiz}
            className="w-full"
            disabled={
              questions.length === 0 || !selectedDocumentId || !quizTitle.trim()
            }
          >
            {isSaving && <Loader2 className="size-4 mr-2 animate-spin" />}
            {!isSaving && <Save className="size-4 mr-2" />}
            {isSaving
              ? "Đang lưu..."
              : `Lưu Quiz (${questions.length} câu hỏi)`}
          </Button>
          {saveSuccess && (
            <div className="flex items-center gap-2 px-3 py-2 bg-green-50 border border-green-200 rounded-md text-sm text-green-700">
              <CheckCircle className="size-4 text-green-600 flex-shrink-0" />
              <span>{saveSuccess}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
