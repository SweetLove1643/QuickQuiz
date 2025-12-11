// API Configuration and Client
// Connects frontend to QuickQuiz backend services

const API_CONFIG = {
  // API Gateway endpoint
  BASE_URL: "http://localhost:8001/api",

  // Individual services (fallback)
  SERVICES: {
    QUIZ_GENERATOR: "http://localhost:8003",
    QUIZ_EVALUATOR: "http://localhost:8003",
    GATEWAY: "http://localhost:8001",
  },

  // Request timeout
  TIMEOUT: 30000,

  // Headers
  DEFAULT_HEADERS: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
};

export interface QuizSection {
  id: string;
  summary: string;
}

export interface QuizConfig {
  n_questions: number;
  types: ("mcq" | "tf" | "fill_blank")[];
}

// OCR Service interfaces
export interface OCRRequest {
  images: string[]; // base64 encoded images
  config?: {
    language?: string;
    output_format?: "text" | "json";
  };
}

export interface OCRResponse {
  extracted_text: string;
  confidence_score: number;
  processing_time: number;
  metadata?: {
    page_count: number;
    language_detected: string;
  };
}

// Summary Service interfaces
export interface SummaryRequest {
  text: string;
  config?: {
    max_length?: number;
    style?: "concise" | "detailed" | "bullet_points";
    language?: string;
  };
}

export interface SummaryResponse {
  summary: string;
  key_points: string[];
  processing_time: number;
  confidence_score: number;
}

export interface GenerateQuizRequest {
  sections: QuizSection[];
  config: QuizConfig;
}

export interface QuizQuestion {
  id: string;
  type: "mcq" | "tf" | "fill_blank";
  stem: string;
  options?: string[];
  answer: string;
}

export interface GenerateQuizResponse {
  quiz_id: string;
  questions: QuizQuestion[];
  validation?: {
    summary: {
      total_questions: number;
      valid_questions: number;
      validation_rate: number;
      average_confidence: number;
    };
    high_risk_count: number;
    validation_timestamp: string;
  };
  metadata?: {
    total_generated: number;
    total_validated: number;
  };
}

export interface EvaluationRequest {
  submission: {
    quiz_id: string;
    questions: Array<{
      id: string;
      type: string;
      stem: string;
      options?: string[];
      correct_answer: string;
      user_answer: string;
      topic?: string;
    }>;
    user_info: {
      user_id: string;
      completion_time: number;
      session_id: string;
    };
  };
  config: {
    include_explanations: boolean;
    include_ai_analysis: boolean;
    save_history: boolean;
  };
}

class QuizAPI {
  private baseUrl: string;
  private timeout: number;

  constructor() {
    this.baseUrl = API_CONFIG.BASE_URL;
    this.timeout = API_CONFIG.TIMEOUT;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    const requestOptions: RequestInit = {
      signal: controller.signal,
      headers: {
        ...API_CONFIG.DEFAULT_HEADERS,
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, requestOptions);
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`API Error ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("Request timeout");
      }
      console.error(`Request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string; services: any }> {
    return this.makeRequest("/health/");
  }

  // Generate quiz from content
  async generateQuiz(
    request: GenerateQuizRequest
  ): Promise<GenerateQuizResponse> {
    return this.makeRequest("/quiz/generate/", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Evaluate quiz submission
  async evaluateQuiz(request: EvaluationRequest): Promise<any> {
    return this.makeRequest("/quiz/evaluate/", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // OCR Service - Extract text from images
  async extractTextFromImages(request: OCRRequest): Promise<OCRResponse> {
    return this.makeRequest("/ocr/extract_text_multi/", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // OCR Service - Single image extraction
  async extractTextSingle(imageBase64: string): Promise<OCRResponse> {
    return this.makeRequest("/ocr/extract_text/", {
      method: "POST",
      body: JSON.stringify({ image: imageBase64 }),
    });
  }

  // Summary Service - Summarize text content
  async summarizeText(request: SummaryRequest): Promise<SummaryResponse> {
    return this.makeRequest("/summary/summarize_text/", {
      method: "POST",
      body: JSON.stringify({ text: request.text }),
    });
  }

  // OCR + Summary combined workflow
  async ocrAndSummarize(
    imageBase64: string,
    summaryConfig?: SummaryRequest["config"]
  ): Promise<{ ocr: OCRResponse; summary: SummaryResponse }> {
    return this.makeRequest("/summary/ocr_and_summarize/", {
      method: "POST",
      body: JSON.stringify({
        image: imageBase64,
        summary_config: summaryConfig || { style: "detailed" },
      }),
    });
  }

  // Get validation metrics
  async getValidationMetrics(): Promise<any> {
    // Try gateway first, fallback to direct service
    try {
      return this.makeRequest("/validation/metrics");
    } catch (error) {
      // Fallback to direct quiz generator service
      const directUrl = `${API_CONFIG.SERVICES.QUIZ_GENERATOR}/validation/metrics`;
      const response = await fetch(directUrl);
      return response.json();
    }
  }

  // Save processed document to database
  async saveDocument(document: {
    fileName: string;
    fileSize: number;
    fileType: string;
    extractedText: string;
    summary: string;
    documentId: string;
    processingTime?: number;
    ocrConfidence?: number;
    summaryConfidence?: number;
  }): Promise<{
    success: boolean;
    message: string;
    document_id: string;
    saved_at: string;
  }> {
    return this.makeRequest("/documents/save/", {
      method: "POST",
      body: JSON.stringify(document),
    });
  }

  // Save generated quiz to database
  async saveQuiz(quiz: {
    user_id: string; // Required: user who creates the quiz
    title: string;
    document_id?: string;
    document_name?: string;
    questions: Array<{
      id?: string;
      stem: string;
      type: "mcq" | "tf" | "fill_blank";
      options?: string[];
      answer: string;
    }>;
    metadata?: Record<string, any>;
  }): Promise<{
    success: boolean;
    quiz_id: string;
    user_id: string;
    saved_at: string;
  }> {
    return this.makeRequest("/quiz/save/", {
      method: "POST",
      body: JSON.stringify(quiz),
    });
  }

  // Get quizzes created by a specific user
  async getUserQuizzes(
    userId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<{
    success: boolean;
    user_id: string;
    quizzes: Array<{
      quiz_id: string;
      title: string;
      document_id: string | null;
      created_at: string | null;
      questions_count: number;
      last_accessed: string | null;
    }>;
    total: number;
  }> {
    return this.makeRequest(
      `/quiz/user/${userId}/?limit=${limit}&offset=${offset}`,
      {
        method: "GET",
      }
    );
  }

  // Get recent quizzes created by a user (for home page)
  async getUserRecentQuizzes(
    userId: string,
    limit: number = 10
  ): Promise<{
    success: boolean;
    user_id: string;
    recent_quizzes: Array<{
      quiz_id: string;
      title: string;
      document_id: string | null;
      created_at: string | null;
      questions_count: number;
    }>;
  }> {
    return this.makeRequest(`/quiz/user/${userId}/recent/?limit=${limit}`, {
      method: "GET",
    });
  }

  // Get quiz results for a specific user
  async getUserResults(
    userId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<{
    success: boolean;
    user_id: string;
    results: Array<{
      submission_id: string;
      quiz_id: string;
      score_percentage: number;
      grade: string;
      total_questions: number;
      correct_count: number;
      completion_time: number;
      submitted_at: string | null;
    }>;
    total: number;
  }> {
    return this.makeRequest(
      `/results/user/${userId}/?limit=${limit}&offset=${offset}`,
      {
        method: "GET",
      }
    );
  }

  // Get recent quiz results for a user (for home page)
  async getUserRecentResults(
    userId: string,
    limit: number = 10
  ): Promise<{
    success: boolean;
    user_id: string;
    recent_results: Array<{
      submission_id: string;
      quiz_id: string;
      score_percentage: number;
      submitted_at: string | null;
    }>;
  }> {
    return this.makeRequest(`/results/user/${userId}/recent/?limit=${limit}`, {
      method: "GET",
    });
  }

  // Get list of documents from database
  async getDocuments(): Promise<{
    success: boolean;
    documents: Array<{
      document_id: string;
      file_name: string;
      file_type: string;
      file_size: number;
      extracted_text: string;
      summary: string;
      created_at: string;
    }>;
  }> {
    return this.makeRequest("/documents/list/", {
      method: "GET",
    });
  }
}

// Export singleton instance
export const quizAPI = new QuizAPI();

// Utility functions
export const convertToBackendFormat = (
  content: string,
  settings: {
    questionCount: string;
    questionTypes: {
      multipleChoice: boolean;
      trueFalse: boolean;
      fillBlank: boolean;
    };
    difficulty: string;
  }
): GenerateQuizRequest => {
  const types: ("mcq" | "tf" | "fill_blank")[] = [];

  if (settings.questionTypes.multipleChoice) types.push("mcq");
  if (settings.questionTypes.trueFalse) types.push("tf");
  if (settings.questionTypes.fillBlank) types.push("fill_blank");

  return {
    sections: [
      {
        id: `section-${Date.now()}`,
        summary: content,
      },
    ],
    config: {
      n_questions: parseInt(settings.questionCount) || 5,
      types: types.length > 0 ? types : ["mcq"],
    },
  };
};

export const convertFromBackendFormat = (backendQuestions: QuizQuestion[]) => {
  return backendQuestions.map((q, index) => ({
    id: q.id || `q-${index}`,
    question: q.stem,
    options:
      q.type === "fill_blank"
        ? [q.answer || ""]
        : q.type === "tf"
        ? ["Đúng", "Sai"]
        : q.options || [],
    correctAnswer:
      q.type === "tf"
        ? typeof q.answer === "string" &&
          ["true", "đúng"].includes(q.answer.toLowerCase())
          ? 0
          : 1
        : q.type === "fill_blank"
        ? 0
        : Math.max((q.options || []).indexOf(q.answer), 0),
    type:
      q.type === "mcq"
        ? ("multiple-choice" as const)
        : q.type === "tf"
        ? ("true-false" as const)
        : ("fill-blank" as const),
  }));
};

export default quizAPI;
