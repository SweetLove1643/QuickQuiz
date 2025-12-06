import { Plus, Trash2, Loader2, Sparkles } from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "./ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Label } from "./ui/label";
import { Checkbox } from "./ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { quizAPI, convertFromBackendFormat } from "../api/quizAPI";

interface CreateQuizProps {
  document: any;
  onQuizCreated: (quiz: any) => void;
}

interface Question {
  id: string;
  question: string;
  options: string[];
  correctAnswer: number;
  type?: "multiple-choice" | "true-false" | "fill-blank";
}

export function CreateQuiz({ document, onQuizCreated }: CreateQuizProps) {
  const [quizTitle, setQuizTitle] = useState(
    `Quiz - ${document?.fileName || "Tài liệu"}`
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [questions, setQuestions] = useState<Question[]>([]);

  // AI Generation settings
  const [aiDialogOpen, setAiDialogOpen] = useState(false);
  const [aiQuestionCount, setAiQuestionCount] = useState("5");
  const [aiQuestionTypes, setAiQuestionTypes] = useState({
    multipleChoice: true,
    trueFalse: true,
    fillBlank: false,
  });
  const [aiDifficulty, setAiDifficulty] = useState("medium");
  const [error, setError] = useState<string | null>(null);
  const [isSavingQuiz, setIsSavingQuiz] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Manual question type selection
  const [manualDialogOpen, setManualDialogOpen] = useState(false);

  const handleGenerateQuestions = async () => {
    const baseContent = document?.summary || document?.extractedText || "";
    if (!baseContent) {
      setError("Không có nội dung tài liệu để tạo câu hỏi.");
      return;
    }

    setIsGenerating(true);
    setError(null);

    const requestedTypes: ("multiple_choice" | "true_false" | "fill_blank")[] =
      [];
    if (aiQuestionTypes.multipleChoice) requestedTypes.push("multiple_choice");
    if (aiQuestionTypes.trueFalse) requestedTypes.push("true_false");
    if (aiQuestionTypes.fillBlank) requestedTypes.push("fill_blank");
    if (requestedTypes.length === 0) {
      requestedTypes.push("multiple_choice");
    }

    try {
      const count = parseInt(aiQuestionCount) || 5;
      const payload = {
        sections: [
          {
            id: document?.documentId || `section-${Date.now()}`,
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
      setAiDialogOpen(false);
    } catch (err) {
      console.error("Generate quiz failed:", err);
      setError(
        err instanceof Error ? err.message : "Không thể tạo câu hỏi tự động"
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
    setIsSavingQuiz(true);
    setSaveError(null);

    try {
      const payload = {
        title: quizTitle,
        document_id: document?.documentId,
        document_name: document?.fileName,
        questions: questions.map((q) => ({
          id: q.id,
          stem: q.question,
          type:
            q.type === "true-false"
              ? "tf"
              : q.type === "fill-blank"
              ? "fill_blank"
              : "mcq",
          options: q.options,
          answer:
            q.type === "true-false"
              ? q.correctAnswer === 0
                ? "True"
                : "False"
              : q.options[q.correctAnswer] || "",
        })),
        metadata: {
          source: "quick-start",
        },
      };

      const result = await quizAPI.saveQuiz(payload);

      if (!result.success) {
        throw new Error("Không thể lưu quiz");
      }

      onQuizCreated({
        quizId: result.quiz_id,
        title: quizTitle,
        questions,
        documentName: document?.fileName,
        savedAt: result.saved_at,
      });
    } catch (err) {
      console.error("Save quiz failed:", err);
      const message = err instanceof Error ? err.message : "Không thể lưu quiz";
      setSaveError(message);

      // Fallback: if endpoint 404 or not available, proceed without saving
      if (message.includes("404")) {
        onQuizCreated({
          quizId: `local-${Date.now()}`,
          title: quizTitle,
          questions,
          documentName: document?.fileName,
          savedAt: new Date().toISOString(),
        });
      }
    } finally {
      setIsSavingQuiz(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-slate-900 mb-2">Tạo bài Quiz</h1>
        <p className="text-slate-600">
          Tài liệu: <span className="text-slate-900">{document?.fileName}</span>
        </p>
      </div>

      {/* Quiz Title */}
      <Card className="p-6 mb-6">
        <label className="block mb-2 text-slate-700">Tên bài Quiz</label>
        <Input
          value={quizTitle}
          onChange={(e) => setQuizTitle(e.target.value)}
          placeholder="Nhập tên bài quiz..."
        />
      </Card>

      {/* Questions List */}
      {error && (
        <div className="p-3 mb-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {saveError && (
        <div className="p-3 mb-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{saveError}</p>
        </div>
      )}

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
                onValueChange={(value) =>
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
            <Button disabled={isGenerating} className="flex-1">
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
                      onCheckedChange={(checked) =>
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
                      onCheckedChange={(checked) =>
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
                      onCheckedChange={(checked) =>
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
          disabled={questions.length === 0 || isSavingQuiz}
        >
          {isSavingQuiz && <Loader2 className="size-4 mr-2 animate-spin" />}
          {isSavingQuiz
            ? "Đang lưu quiz..."
            : `Bắt đầu làm Quiz (${questions.length} câu hỏi)`}
        </Button>
      </div>
    </div>
  );
}
