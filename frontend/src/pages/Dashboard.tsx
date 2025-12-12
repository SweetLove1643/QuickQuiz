import { Sidebar } from "../components/Sidebar";
import { TopBar } from "../components/TopBar";
import { RecentDocuments } from "../components/RecentDocuments";
import { RecentQuizzes } from "../components/RecentQuizzes";
import { Library } from "../components/Library";
import { QuickStart } from "../components/QuickStart";
import { UploadDocumentOnly } from "../components/UploadDocumentOnly";
import { CreateQuiz } from "../components/CreateQuiz";
import { CreateQuizStandalone } from "../components/CreateQuizStandalone";
import { TakeQuiz } from "../components/TakeQuiz";
import { QuizResult } from "../components/QuizResult";
import { ViewDocument } from "../components/ViewDocument";
import { Chatbot } from "../components/Chatbot";
import { useState } from "react";

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

export const Dashboard = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [currentPage, setCurrentPage] = useState<PageType>("home");
  const [currentDocument, setCurrentDocument] = useState<any>(null);
  const [currentQuiz, setCurrentQuiz] = useState<any>(null);
  const [quizResult, setQuizResult] = useState<any>(null);
  const [isInQuickStartFlow, setIsInQuickStartFlow] = useState(false);

  // Helper function to navigate and manage quick-start flow
  const navigateToPage = (
    page: PageType,
    isFromQuickStart: boolean = false
  ) => {
    setCurrentPage(page);

    // Set quick-start flow flag
    if (page === "quick-start") {
      setIsInQuickStartFlow(true);
    } else if (isFromQuickStart) {
      // Keep the flag true if navigating within quick-start flow
      setIsInQuickStartFlow(true);
    } else {
      // Reset flag for other navigations
      setIsInQuickStartFlow(false);
    }
  };

  const renderPage = () => {
    switch (currentPage) {
      case "home":
        return (
          <div className="space-y-12">
            <div>
              <div className="mb-8">
                <h1 className="text-slate-900 mb-2">Trang chủ</h1>
                <p className="text-slate-600">
                  Các tài liệu và quiz gần đây của bạn
                </p>
              </div>
            </div>

            <RecentDocuments
              onDocumentSelected={(doc) => {
                setCurrentDocument(doc);
                setCurrentPage("view-document");
              }}
            />

            <RecentQuizzes
              onNavigate={navigateToPage}
              onQuizSelected={setCurrentQuiz}
            />
          </div>
        );
      case "library":
        return (
          <Library
            onNavigate={navigateToPage}
            onQuizSelected={(quiz) => setCurrentQuiz(quiz)}
            onDocumentSelected={(doc) => {
              setCurrentDocument(doc);
              setCurrentPage("view-document");
            }}
          />
        );
      case "quick-start":
        return (
          <QuickStart
            onDocumentProcessed={(doc) => {
              setCurrentDocument(doc);
              navigateToPage("create-quiz", true);
            }}
          />
        );
      case "upload-document":
        return <UploadDocumentOnly />;
      case "create-quiz-standalone":
        return (
          <CreateQuizStandalone
            editingQuiz={currentQuiz}
            onQuizCreated={(quiz) => {
              setCurrentQuiz(quiz);
              setCurrentPage("take-quiz");
            }}
          />
        );
      case "create-quiz":
        return (
          <CreateQuiz
            document={currentDocument}
            onQuizCreated={(quiz) => {
              setCurrentQuiz(quiz);
              // Keep quick-start flow flag if we're in that flow
              if (isInQuickStartFlow) {
                navigateToPage("take-quiz", true);
              } else {
                navigateToPage("take-quiz", false);
              }
            }}
          />
        );
      case "take-quiz":
        return (
          <TakeQuiz
            quiz={currentQuiz}
            onQuizCompleted={(result) => {
              setQuizResult(result);
              setCurrentPage("quiz-result");
            }}
          />
        );
      case "quiz-result":
        return (
          <QuizResult
            result={quizResult}
            onBackToHome={() => setCurrentPage("home")}
            onRetakeQuiz={() => {
              // Go back to take-quiz page with the same quiz
              if (isInQuickStartFlow) {
                navigateToPage("take-quiz", true);
              } else {
                navigateToPage("take-quiz", false);
              }
            }}
          />
        );
      case "view-document":
        return (
          <ViewDocument
            document={currentDocument}
            onBack={() => setCurrentPage("library")}
            onSave={async (updatedDocument) => {
              try {
                // Call API to update document in database
                const response = await quizAPI.updateDocument(
                  currentDocument.document_id,
                  {
                    title: updatedDocument.title,
                    summary: updatedDocument.summary,
                    content: updatedDocument.content,
                  }
                );

                if (response.success) {
                  // Update local state
                  setCurrentDocument(updatedDocument);
                  console.log("Document updated successfully:", response);
                  alert("Đã lưu thay đổi thành công!");
                } else {
                  console.error("Update failed:", response);
                  alert("Không thể lưu thay đổi. Vui lòng thử lại.");
                }
              } catch (error) {
                console.error("Error updating document:", error);
                alert("Đã xảy ra lỗi khi lưu. Vui lòng thử lại.");
              }
            }}
          />
        );
      case "chatbot":
        return (
          <div className="space-y-6">
            <div className="mb-8">
              <h1 className="text-slate-900 mb-2">RAG Chatbot</h1>
              <p className="text-slate-600">
                Tương tác với AI để học tập hiệu quả hơn
              </p>
            </div>
            <div className="max-w-4xl mx-auto">
              <Chatbot
                documentId={currentDocument?.documentId || "default"}
                documentName={currentDocument?.fileName}
              />
            </div>
          </div>
        );
      default:
        return (
          <div className="space-y-12">
            <div>
              <div className="mb-8">
                <h1 className="text-slate-900 mb-2">Trang chủ</h1>
                <p className="text-slate-600">
                  Các tài liệu và quiz gần đây của bạn
                </p>
              </div>
            </div>

            <RecentDocuments
              onDocumentSelected={(doc) => {
                setCurrentDocument(doc);
                setCurrentPage("view-document");
              }}
            />

            <RecentQuizzes />
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        currentPage={currentPage}
        onNavigate={navigateToPage}
      />

      {/* Main Content */}
      <div
        className={`transition-all duration-300 ${
          isSidebarOpen ? "lg:pl-[280px]" : "pl-0"
        }`}
      >
        <TopBar
          onMenuToggle={() => setIsSidebarOpen(!isSidebarOpen)}
          isSidebarOpen={isSidebarOpen}
          currentPage={currentPage}
          isInQuickStartFlow={isInQuickStartFlow}
        />

        <main className="max-w-7xl mx-auto px-4 py-8">{renderPage()}</main>
      </div>
    </div>
  );
};
