import {
  Trophy,
  Clock,
  CheckCircle,
  XCircle,
  Home,
  Loader2,
} from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Separator } from "./ui/separator";
import { useEffect, useState } from "react";
import { quizAPI } from "../api/quizAPI";

interface QuizResultProps {
  result: any;
  onBackToHome: () => void;
  onRetakeQuiz: () => void;
}

export function QuizResult({
  result,
  onBackToHome,
  onRetakeQuiz,
}: QuizResultProps) {
  const [aiEvaluation, setAiEvaluation] = useState<any>(null);
  const [isEvaluating, setIsEvaluating] = useState(true);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);

  useEffect(() => {
    // Call evaluation API on mount
    const evaluateQuizResults = async () => {
      try {
        setIsEvaluating(true);
        setEvaluationError(null);

        // Prepare evaluation request
        const evaluationRequest = {
          submission: {
            quiz_id: result.quizId || `quiz-${Date.now()}`,
            questions: result.detailedAnswers.map(
              (answer: any, idx: number) => ({
                id: `q${idx + 1}`,
                type:
                  answer.type === "multiple-choice"
                    ? "mcq"
                    : answer.type === "true-false"
                    ? "tf"
                    : answer.type === "fill-blank" ||
                      answer.type === "fill_blank"
                    ? "fill_blank"
                    : "mcq",
                stem: answer.question,
                options: answer.options || [],
                correct_answer: answer.correctAnswer,
                user_answer: answer.userAnswer || "",
                topic: answer.topic || "General",
              })
            ),
            user_info: {
              user_id: "anonymous",
              completion_time: result.timeElapsed,
              session_id: `session-${Date.now()}`,
            },
          },
          config: {
            include_explanations: true,
            include_ai_analysis: true,
            save_history: true,
          },
        };

        const evaluation = await quizAPI.evaluateQuiz(evaluationRequest);
        setAiEvaluation(evaluation);
        console.log("Quiz evaluation completed:", evaluation);
      } catch (error) {
        console.error("Failed to evaluate quiz:", error);
        setEvaluationError("Không thể tải nhận xét AI. Vui lòng thử lại sau.");
      } finally {
        setIsEvaluating(false);
      }
    };

    evaluateQuizResults();
  }, [result]);
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins} phút ${secs} giây`;
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return "bg-green-50";
    if (score >= 60) return "bg-yellow-50";
    return "bg-red-50";
  };

  const getFeedback = (score: number) => {
    if (score >= 90) return "Xuất sắc! Bạn đã nắm vững kiến thức.";
    if (score >= 80) return "Tốt lắm! Bạn đã hiểu khá rõ nội dung.";
    if (score >= 60) return "Khá tốt! Hãy ôn lại một số phần để hiểu rõ hơn.";
    if (score >= 40)
      return "Cần cố gắng thêm! Hãy xem lại tài liệu và làm lại bài quiz.";
    return "Bạn cần học lại nội dung. Đừng nản chí, hãy thử lại!";
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-slate-900 mb-2">Kết quả Quiz</h1>
        <p className="text-slate-600">{result.quizTitle}</p>
      </div>

      {/* Overall Results */}
      <Card className={`p-8 mb-6 ${getScoreBgColor(parseFloat(result.score))}`}>
        <div className="flex items-start gap-6">
          <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center">
            <Trophy
              className={`size-10 ${getScoreColor(parseFloat(result.score))}`}
            />
          </div>
          <div className="flex-1">
            <h2 className="text-slate-900 mb-2">Kết quả tổng quát</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div>
                <p className="text-slate-600">Điểm số</p>
                <p
                  className={`text-3xl ${getScoreColor(
                    parseFloat(result.score)
                  )}`}
                >
                  {result.score}%
                </p>
              </div>
              <div>
                <p className="text-slate-600">Đúng/Tổng</p>
                <p className="text-slate-900 text-2xl">
                  {result.correctAnswers}/{result.totalQuestions}
                </p>
              </div>
              <div>
                <p className="text-slate-600">Thời gian</p>
                <p className="text-slate-900 text-2xl">
                  <Clock className="inline size-5 mr-1" />
                  {formatTime(result.timeElapsed)}
                </p>
              </div>
              <div>
                <p className="text-slate-600">Tỷ lệ đúng</p>
                <p className="text-slate-900 text-2xl">
                  {(
                    (result.correctAnswers / result.totalQuestions) *
                    100
                  ).toFixed(0)}
                  %
                </p>
              </div>
            </div>
            <Separator className="my-4" />
            <p className="text-slate-700">
              Bạn đã hoàn thành bài quiz vào lúc{" "}
              {new Date(result.submittedAt).toLocaleString("vi-VN")}
            </p>
          </div>
        </div>
      </Card>

      {/* Detailed Answers */}
      <Card className="p-6 mb-6">
        <h2 className="text-slate-900 mb-4">Chi tiết đáp án</h2>
        <div className="space-y-6">
          {result.detailedAnswers.map((answer: any, idx: number) => (
            <div
              key={idx}
              className="border-l-4 pl-4"
              style={{
                borderColor: answer.isCorrect ? "#10b981" : "#ef4444",
              }}
            >
              <div className="flex items-start gap-3 mb-3">
                {answer.isCorrect ? (
                  <CheckCircle className="size-6 text-green-600 shrink-0 mt-1" />
                ) : (
                  <XCircle className="size-6 text-red-600 shrink-0 mt-1" />
                )}
                <div className="flex-1">
                  <h3 className="text-slate-900 mb-2">
                    Câu {idx + 1}: {answer.question}
                  </h3>

                  <div className="space-y-2">
                    <div
                      className={`p-3 rounded-lg ${
                        answer.isCorrect ? "bg-green-50" : "bg-red-50"
                      }`}
                    >
                      <p className="text-slate-600">Câu trả lời của bạn:</p>
                      <p
                        className={
                          answer.isCorrect ? "text-green-700" : "text-red-700"
                        }
                      >
                        {answer.userAnswer}
                      </p>
                    </div>

                    {!answer.isCorrect && (
                      <div className="p-3 rounded-lg bg-green-50">
                        <p className="text-slate-600">Đáp án đúng:</p>
                        <p className="text-green-700">{answer.correctAnswer}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Feedback */}
      <Card className="p-6 mb-6">
        <h2 className="text-slate-900 mb-4">Nhận xét</h2>

        {isEvaluating && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="size-6 animate-spin text-blue-600 mr-3" />
            <p className="text-slate-600">Đang phân tích kết quả với AI...</p>
          </div>
        )}

        {evaluationError && (
          <div className="p-4 bg-red-50 rounded-lg mb-4">
            <p className="text-red-700">{evaluationError}</p>
          </div>
        )}

        {!isEvaluating && aiEvaluation && (
          <div className="space-y-4">
            {/* Overall AI Feedback */}
            {aiEvaluation.analysis?.overall_feedback && (
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-blue-900">
                  {aiEvaluation.analysis.overall_feedback}
                </p>
              </div>
            )}

            {/* Fallback to simple feedback if no AI feedback */}
            {!aiEvaluation.analysis?.overall_feedback && (
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-blue-900">
                  {getFeedback(parseFloat(result.score))}
                </p>
              </div>
            )}

            {/* Strengths */}
            {aiEvaluation.analysis?.strengths &&
              aiEvaluation.analysis.strengths.length > 0 && (
                <div>
                  <h3 className="text-slate-900 mb-2 flex items-center gap-2">
                    <span className="text-green-600">✓</span> Điểm mạnh:
                  </h3>
                  <ul className="space-y-2 text-slate-700 ml-4">
                    {aiEvaluation.analysis.strengths.map(
                      (strength: string, idx: number) => (
                        <li key={idx}>• {strength}</li>
                      )
                    )}
                  </ul>
                </div>
              )}

            {/* Weaknesses */}
            {aiEvaluation.analysis?.weaknesses &&
              aiEvaluation.analysis.weaknesses.length > 0 && (
                <div>
                  <h3 className="text-slate-900 mb-2 flex items-center gap-2">
                    <span className="text-orange-600">⚠</span> Cần cải thiện:
                  </h3>
                  <ul className="space-y-2 text-slate-700 ml-4">
                    {aiEvaluation.analysis.weaknesses.map(
                      (weakness: string, idx: number) => (
                        <li key={idx}>• {weakness}</li>
                      )
                    )}
                  </ul>
                </div>
              )}

            {/* Basic statistics (fallback) */}
            {(!aiEvaluation.analysis?.strengths ||
              aiEvaluation.analysis.strengths.length === 0) && (
              <div>
                <h3 className="text-slate-900 mb-2">Phân tích chi tiết:</h3>
                <ul className="space-y-2 text-slate-700">
                  <li>
                    • Bạn đã trả lời đúng {result.correctAnswers} câu trên tổng
                    số {result.totalQuestions} câu hỏi
                  </li>
                  <li>
                    • Thời gian làm bài: {formatTime(result.timeElapsed)} (trung
                    bình{" "}
                    {Math.round(result.timeElapsed / result.totalQuestions)}
                    s/câu)
                  </li>
                  <li>
                    •{" "}
                    {result.correctAnswers >= result.totalQuestions * 0.8
                      ? "Bạn đã nắm vững phần lớn kiến thức trong tài liệu."
                      : "Hãy xem lại các câu trả lời sai để củng cố kiến thức."}
                  </li>
                </ul>
              </div>
            )}

            {/* Recommendations and Study Plan */}
            {aiEvaluation.analysis?.recommendations &&
              aiEvaluation.analysis.recommendations.length > 0 && (
                <div className="pt-4">
                  <h3 className="text-slate-900 mb-2">💡 Gợi ý cải thiện:</h3>
                  <ul className="space-y-2 text-slate-700">
                    {aiEvaluation.analysis.recommendations.map(
                      (rec: string, idx: number) => (
                        <li key={idx}>• {rec}</li>
                      )
                    )}
                  </ul>
                </div>
              )}

            {/* Study Plan */}
            {aiEvaluation.analysis?.study_plan &&
              aiEvaluation.analysis.study_plan.length > 0 && (
                <div className="pt-4">
                  <h3 className="text-slate-900 mb-2">📚 Kế hoạch học tập:</h3>
                  <ul className="space-y-2 text-slate-700">
                    {aiEvaluation.analysis.study_plan.map(
                      (plan: string, idx: number) => (
                        <li key={idx}>• {plan}</li>
                      )
                    )}
                  </ul>
                </div>
              )}

            {/* Fallback suggestions */}
            {(!aiEvaluation.analysis?.recommendations ||
              aiEvaluation.analysis.recommendations.length === 0) && (
              <div className="pt-4">
                <h3 className="text-slate-900 mb-2">Gợi ý tiếp theo:</h3>
                <ul className="space-y-2 text-slate-700">
                  {parseFloat(result.score) < 80 && (
                    <>
                      <li>
                        • Đọc lại tài liệu gốc để hiểu rõ hơn các phần còn yếu
                      </li>
                      <li>• Làm lại bài quiz để cải thiện điểm số</li>
                    </>
                  )}
                  <li>• Tạo thêm các bài quiz khác từ tài liệu để ôn tập</li>
                  <li>• Chia sẻ bài quiz với bạn bè để cùng học tập</li>
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Show fallback feedback if evaluation failed or is still loading */}
        {!isEvaluating && !aiEvaluation && (
          <div className="space-y-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-blue-900">
                {getFeedback(parseFloat(result.score))}
              </p>
            </div>

            <div>
              <h3 className="text-slate-900 mb-2">Phân tích chi tiết:</h3>
              <ul className="space-y-2 text-slate-700">
                <li>
                  • Bạn đã trả lời đúng {result.correctAnswers} câu trên tổng số{" "}
                  {result.totalQuestions} câu hỏi
                </li>
                <li>
                  • Thời gian làm bài: {formatTime(result.timeElapsed)} (trung
                  bình {Math.round(result.timeElapsed / result.totalQuestions)}
                  s/câu)
                </li>
                <li>
                  •{" "}
                  {result.correctAnswers >= result.totalQuestions * 0.8
                    ? "Bạn đã nắm vững phần lớn kiến thức trong tài liệu."
                    : "Hãy xem lại các câu trả lời sai để củng cố kiến thức."}
                </li>
              </ul>
            </div>

            <div className="pt-4">
              <h3 className="text-slate-900 mb-2">Gợi ý tiếp theo:</h3>
              <ul className="space-y-2 text-slate-700">
                {parseFloat(result.score) < 80 && (
                  <>
                    <li>
                      • Đọc lại tài liệu gốc để hiểu rõ hơn các phần còn yếu
                    </li>
                    <li>• Làm lại bài quiz để cải thiện điểm số</li>
                  </>
                )}
                <li>• Tạo thêm các bài quiz khác từ tài liệu để ôn tập</li>
                <li>• Chia sẻ bài quiz với bạn bè để cùng học tập</li>
              </ul>
            </div>
          </div>
        )}
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <Button onClick={onBackToHome} variant="outline" className="flex-1">
          <Home className="size-4 mr-2" />
          Về trang chủ
        </Button>
        <Button onClick={onRetakeQuiz} className="flex-1">
          Làm lại bài Quiz
        </Button>
      </div>
    </div>
  );
}
