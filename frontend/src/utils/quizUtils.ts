/**
 * Normalize quiz questions to uniform format.
 * Backend may return: { stem, options, answer (text), correct_answer, ... }
 * Frontend UI expects: { question, options, correctAnswer (index), ... }
 */
export function normalizeQuestions(questions: any[]): any[] {
  if (!questions || !Array.isArray(questions)) return [];

  return questions.map((q: any) => {
    // Extract text from various possible fields
    const stem = q.stem || q.question || q.text || "";
    const options = q.options || q.choices || [];
    
    // Extract answer text from various possible fields
    const answerText = q.answer ?? q.correct_answer ?? null;
    
    // Determine correct answer index
    let correctIndex: number;

    // Priority 1: If already an index, use it
    if (q.correctAnswer !== undefined && typeof q.correctAnswer === "number") {
      correctIndex = q.correctAnswer;
    }
    // Priority 2: Find index of answer text in options
    else if (answerText && Array.isArray(options) && options.length > 0) {
      const idx = options.indexOf(String(answerText));
      correctIndex = idx >= 0 ? idx : 0;
    }
    // Priority 3: Use first option as fallback
    else {
      correctIndex = options.length > 0 ? 0 : -1;
    }

    return {
      ...q,
      question: stem,
      stem,
      type: q.type || q.question_type || "mcq",
      options,
      correctAnswer: correctIndex,
      answer: answerText,
    };
  });
}

/**
 * Export normalized quiz for safe handling
 */
export function normalizeQuiz(quiz: any): any {
  if (!quiz) return null;
  
  return {
    ...quiz,
    questions: normalizeQuestions(quiz.questions || []),
  };
}