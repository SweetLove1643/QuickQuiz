import { Brain, Play, Loader2 } from "lucide-react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { quizAPI } from "../api/quizAPI";

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

interface RecentQuizzesProps {
  onNavigate?: (page: PageType, isFromQuickStart?: boolean) => void;
  onQuizSelected?: (quiz: any) => void;
}

export function RecentQuizzes({
  onNavigate,
  onQuizSelected,
}: RecentQuizzesProps) {
  const { user } = useAuth();
  const [recentQuizzes, setRecentQuizzes] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadRecentQuizzes = async () => {
      if (!user?.id) {
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        const response = await quizAPI.getUserQuizzes(user.id);
        if (response.success) {
          // Get quizzes, sort by created_at desc, and take top 10
          const sortedQuizzes = (response.quizzes || [])
            .sort((a: any, b: any) => {
              const dateA = new Date(a.created_at || 0).getTime();
              const dateB = new Date(b.created_at || 0).getTime();
              return dateB - dateA;
            })
            .slice(0, 10);
          setRecentQuizzes(sortedQuizzes);
        }
      } catch (err) {
        console.error("Failed to load recent quizzes:", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadRecentQuizzes();
  }, [user?.id]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="size-8 animate-spin text-purple-600" />
        <span className="ml-3 text-slate-600">Đang tải quiz...</span>
      </div>
    );
  }

  if (recentQuizzes.length === 0) {
    return (
      <div className="text-center py-12">
        <Brain className="size-16 mx-auto text-slate-300 mb-4" />
        <h3 className="text-lg font-medium text-slate-900 mb-2">
          Chưa có quiz nào
        </h3>
        <p className="text-slate-600">Tạo quiz đầu tiên để bắt đầu học tập</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-slate-900 mb-1">Quiz gần đây</h2>
        <p className="text-slate-600 text-sm">
          {recentQuizzes.length} quiz gần nhất
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {recentQuizzes.map((quiz) => (
          <Card
            key={quiz.quiz_id}
            className="p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={async () => {
              try {
                // Load full quiz data before navigating
                const fullQuizResponse = await quizAPI.getQuizById(
                  quiz.quiz_id
                );
                if (fullQuizResponse.success && fullQuizResponse.quiz) {
                  // Transform quiz data to ensure compatibility with TakeQuiz component
                  const transformedQuiz = {
                    ...fullQuizResponse.quiz,
                    questions: fullQuizResponse.quiz.questions.map(
                      (q: any) => ({
                        ...q,
                        question: q.stem || q.question,
                        // Convert answer string to correctAnswer index for MCQ
                        correctAnswer:
                          q.options && q.answer
                            ? q.options.findIndex(
                                (opt: string) =>
                                  opt.trim().toLowerCase() ===
                                  q.answer.trim().toLowerCase()
                              )
                            : q.answer,
                      })
                    ),
                  };
                  onQuizSelected?.(transformedQuiz);
                  onNavigate?.("take-quiz");
                } else {
                  console.error("Failed to load quiz");
                  alert("Không thể tải dữ liệu quiz. Vui lòng thử lại.");
                }
              } catch (error) {
                console.error("Error loading quiz:", error);
                alert("Đã xảy ra lỗi khi tải quiz.");
              }
            }}
          >
            <div className="flex items-start gap-3">
              {/* Icon */}
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center shrink-0">
                <Brain className="size-6 text-purple-600" />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <h3 className="text-slate-900 font-medium mb-1 truncate">
                  {quiz.title}
                </h3>
                <div className="flex items-center gap-2 text-xs text-slate-600 mb-2">
                  <span>{quiz.questions_count} câu hỏi</span>
                  <span>•</span>
                  <span>
                    {quiz.created_at
                      ? new Date(quiz.created_at).toLocaleDateString("vi-VN")
                      : "Không rõ"}
                  </span>
                </div>
                {quiz.document_id && (
                  <p className="text-xs text-slate-600">Từ tài liệu</p>
                )}
              </div>
            </div>

            {/* Action button */}
            <div className="mt-3">
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={async (e: React.MouseEvent) => {
                  e.stopPropagation();
                  try {
                    // Load full quiz data before navigating
                    const fullQuizResponse = await quizAPI.getQuizById(
                      quiz.quiz_id
                    );
                    if (fullQuizResponse.success && fullQuizResponse.quiz) {
                      // Transform quiz data to ensure compatibility with TakeQuiz component
                      const transformedQuiz = {
                        ...fullQuizResponse.quiz,
                        questions: fullQuizResponse.quiz.questions.map(
                          (q: any) => ({
                            ...q,
                            question: q.stem || q.question,
                            // Convert answer string to correctAnswer index for MCQ
                            correctAnswer:
                              q.options && q.answer
                                ? q.options.findIndex(
                                    (opt: string) =>
                                      opt.trim().toLowerCase() ===
                                      q.answer.trim().toLowerCase()
                                  )
                                : q.answer,
                          })
                        ),
                      };
                      onQuizSelected?.(transformedQuiz);
                      onNavigate?.("take-quiz");
                    } else {
                      console.error("Failed to load quiz");
                      alert("Không thể tải dữ liệu quiz. Vui lòng thử lại.");
                    }
                  } catch (error) {
                    console.error("Error loading quiz:", error);
                    alert("Đã xảy ra lỗi khi tải quiz.");
                  }
                }}
              >
                <Play className="size-4 mr-2" />
                Làm bài
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
