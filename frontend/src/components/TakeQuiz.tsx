import { Clock, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { useState, useEffect } from "react";
import { Progress } from "./ui/progress";

interface TakeQuizProps {
  quiz: any;
  onQuizCompleted: (result: any) => void;
}

export function TakeQuiz({ quiz, onQuizCompleted }: TakeQuizProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState<{ [key: number]: number }>({});
  const [textAnswers, setTextAnswers] = useState<{ [key: number]: string }>({});
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Handle null quiz
  if (!quiz || !quiz.questions || quiz.questions.length === 0) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card className="p-8 text-center">
          <h2 className="text-slate-900 mb-4">Không có dữ liệu quiz</h2>
          <p className="text-slate-600 mb-4">
            Vui lòng chọn một quiz để bắt đầu làm bài.
          </p>
        </Card>
      </div>
    );
  }

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeElapsed((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const currentQuestion = quiz.questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / quiz.questions.length) * 100;

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  };

  const handleAnswerSelect = (optionIndex: number) => {
    setUserAnswers({
      ...userAnswers,
      [currentQuestionIndex]: optionIndex,
    });
  };

  const handleTextAnswerChange = (text: string) => {
    setTextAnswers({
      ...textAnswers,
      [currentQuestionIndex]: text,
    });
  };

  const handleNext = () => {
    if (currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleSubmit = () => {
    setIsSubmitting(true);

    // Calculate results
    let correctCount = 0;
    const detailedAnswers = quiz.questions.map((q: any, idx: number) => {
      let userAnswer;
      let isCorrect = false;

      if (q.type === "fill_blank" || q.type === "fill-blank") {
        // For fill-in-the-blank, compare text answer
        userAnswer = textAnswers[idx] || "";
        const correctAnswer = q.options?.[0] || q.answer || "";
        isCorrect =
          userAnswer.trim().toLowerCase() ===
          correctAnswer.trim().toLowerCase();
      } else {
        // For MCQ and True/False, compare index
        userAnswer = userAnswers[idx];
        isCorrect = userAnswer === q.correctAnswer;
      }

      if (isCorrect) correctCount++;

      return {
        question: q.question || q.stem,
        userAnswer:
          q.type === "fill_blank" || q.type === "fill-blank"
            ? textAnswers[idx] || "Không trả lời"
            : userAnswers[idx] !== undefined
            ? q.options?.[userAnswers[idx]]
            : "Không trả lời",
        correctAnswer:
          q.type === "fill_blank" || q.type === "fill-blank"
            ? q.options?.[0] || q.answer
            : q.options?.[q.correctAnswer],
        isCorrect,
        options: q.options,
        userAnswerIndex: userAnswers[idx],
        correctAnswerIndex: q.correctAnswer,
        type: q.type || "mcq",
        topic: q.topic || "General",
      };
    });

    const score = (correctCount / quiz.questions.length) * 100;

    setTimeout(() => {
      onQuizCompleted({
        quizId: quiz.quiz_id,
        quizTitle: quiz.title,
        documentName: quiz.documentName || quiz.document_id,
        totalQuestions: quiz.questions.length,
        correctAnswers: correctCount,
        score: score.toFixed(1),
        timeElapsed,
        detailedAnswers,
        submittedAt: new Date().toISOString(),
      });
    }, 1000);
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <Card className="p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-slate-900 mb-1">{quiz.title}</h1>
            <p className="text-slate-600">{quiz.documentName}</p>
          </div>
          <div className="flex items-center gap-2 text-slate-700">
            <Clock className="size-5" />
            <span className="text-lg">{formatTime(timeElapsed)}</span>
          </div>
        </div>
        <Progress value={progress} className="h-2" />
        <p className="text-slate-600 mt-2">
          Câu hỏi {currentQuestionIndex + 1} / {quiz.questions.length}
        </p>
      </Card>

      {/* Question Card */}
      <Card className="p-8 mb-6">
        <h2 className="text-slate-900 mb-6">
          {currentQuestion.question || currentQuestion.stem}
        </h2>

        {/* Fill-in-the-blank question */}
        {currentQuestion.type === "fill_blank" ||
        currentQuestion.type === "fill-blank" ? (
          <div className="space-y-4">
            <label className="block text-slate-700 mb-2">
              Nhập câu trả lời của bạn:
            </label>
            <input
              type="text"
              value={textAnswers[currentQuestionIndex] || ""}
              onChange={(e) => handleTextAnswerChange(e.target.value)}
              placeholder="Nhập câu trả lời..."
              className="w-full p-4 rounded-lg border-2 border-slate-200 focus:border-blue-600 focus:outline-none transition-all"
            />
          </div>
        ) : (
          /* Multiple choice or True/False questions */
          <div className="space-y-3">
            {currentQuestion.options && currentQuestion.options.length > 0 ? (
              currentQuestion.options.map((option: string, idx: number) => (
                <button
                  key={idx}
                  onClick={() => handleAnswerSelect(idx)}
                  className={`w-full p-4 text-left rounded-lg border-2 transition-all ${
                    userAnswers[currentQuestionIndex] === idx
                      ? "border-blue-600 bg-blue-50"
                      : "border-slate-200 hover:border-slate-300 bg-white"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                        userAnswers[currentQuestionIndex] === idx
                          ? "border-blue-600 bg-blue-600"
                          : "border-slate-300"
                      }`}
                    >
                      {userAnswers[currentQuestionIndex] === idx && (
                        <div className="w-3 h-3 bg-white rounded-full" />
                      )}
                    </div>
                    <span className="text-slate-900">
                      <span className="mr-2">
                        {String.fromCharCode(65 + idx)}.
                      </span>
                      {option}
                    </span>
                  </div>
                </button>
              ))
            ) : (
              <p className="text-slate-600">Không có đáp án cho câu hỏi này.</p>
            )}
          </div>
        )}
      </Card>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          onClick={handlePrevious}
          disabled={currentQuestionIndex === 0}
        >
          <ChevronLeft className="size-4 mr-2" />
          Câu trước
        </Button>

        <div className="flex gap-2 flex-wrap max-w-2xl">
          {quiz.questions.map((q: any, idx: number) => {
            const isAnswered =
              q.type === "fill_blank" || q.type === "fill-blank"
                ? textAnswers[idx]?.trim() && textAnswers[idx]?.trim() !== ""
                : userAnswers[idx] !== undefined;

            return (
              <button
                key={idx}
                onClick={() => setCurrentQuestionIndex(idx)}
                className={`w-10 h-10 rounded-lg border-2 transition-all ${
                  idx === currentQuestionIndex
                    ? "border-blue-600 bg-blue-600 text-white"
                    : isAnswered
                    ? "border-green-600 bg-green-50 text-green-600"
                    : "border-slate-200 bg-white text-slate-600"
                }`}
              >
                {idx + 1}
              </button>
            );
          })}
        </div>

        {currentQuestionIndex === quiz.questions.length - 1 ? (
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? "Đang nộp bài..." : "Nộp bài"}
          </Button>
        ) : (
          <Button onClick={handleNext}>
            Câu tiếp
            <ChevronRight className="size-4 ml-2" />
          </Button>
        )}
      </div>
    </div>
  );
}
