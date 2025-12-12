import { Menu, LogOut } from "lucide-react";
import { Button } from "./ui/button";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";

interface TopBarProps {
  onMenuToggle: () => void;
  isSidebarOpen: boolean;
  currentPage?: string;
  isInQuickStartFlow?: boolean;
}

export function TopBar({
  onMenuToggle,
  isSidebarOpen,
  currentPage,
  isInQuickStartFlow = false,
}: TopBarProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate("/auth/login");
  };

  const steps = [
    { id: "upload", label: "Upload tài liệu", page: "upload" },
    { id: "create-quiz", label: "Tạo Quiz", page: "create-quiz" },
    { id: "take-quiz", label: "Làm bài", page: "take-quiz" },
    { id: "quiz-result", label: "Kết quả", page: "quiz-result" },
  ];

  // Only show progress bar if in quick-start flow
  const pipelinePages = [
    "quick-start",
    "upload",
    "create-quiz",
    "take-quiz",
    "quiz-result",
  ];
  const showProgress =
    isInQuickStartFlow && currentPage && pipelinePages.includes(currentPage);

  // Map quick-start to the first step (upload)
  const currentPageForStep =
    currentPage === "quick-start" ? "upload" : currentPage;
  const currentStepIndex = steps.findIndex(
    (step) => step.page === currentPageForStep
  );

  return (
    <div className="bg-white border-b border-slate-200">
      <div
        className={`flex items-center justify-between px-4 ${
          showProgress ? "h-32" : "h-16"
        }`}
      >
        <div className="flex items-center">
          {!isSidebarOpen && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onMenuToggle}
              className="absolute"
            >
              <Menu className="size-6" />
            </Button>
          )}
        </div>

        {/* User Profile Section */}
        {user && (
          <div className="flex items-center gap-3 ml-auto">
            <div className="text-slate-700 font-medium">
              Xin chào {user?.username || "Khách"}
            </div>
            <button
              onClick={handleLogout}
              className="ml-2 p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
              title="Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        )}

        {showProgress && (
          <div className="flex-1 max-w-4xl mx-auto px-8 py-4">
            <div className="relative flex items-center justify-between">
              {steps.map((step, index) => {
                const isActive = index === currentStepIndex;
                const isCompleted = index < currentStepIndex;
                const isUpcoming = index > currentStepIndex;

                return (
                  <div
                    key={step.id}
                    className="flex flex-col items-center z-10"
                    style={{ flex: "0 0 auto" }}
                  >
                    {/* Step Circle */}
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors shadow-sm ${
                        isActive
                          ? "bg-blue-600 text-white"
                          : isCompleted
                          ? "bg-green-500 text-white"
                          : "bg-slate-200 text-slate-400"
                      }`}
                    >
                      {isCompleted ? (
                        <svg
                          className="w-6 h-6"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      ) : (
                        <span className="text-lg">{index + 1}</span>
                      )}
                    </div>
                    <span
                      className={`mt-3 text-sm whitespace-nowrap font-medium ${
                        isActive
                          ? "text-blue-600"
                          : isCompleted
                          ? "text-green-600"
                          : "text-slate-400"
                      }`}
                    >
                      {step.label}
                    </span>
                  </div>
                );
              })}

              {/* Connector Lines */}
              <div
                className="absolute top-6 left-0 right-0 flex items-center justify-between px-8"
                style={{ transform: "translateY(-50%)" }}
              >
                {steps.map((step, index) => {
                  if (index === steps.length - 1) return null;
                  const isCompleted = index < currentStepIndex;

                  return (
                    <div
                      key={`line-${step.id}`}
                      className="flex items-center"
                      style={{ flex: "1 1 0" }}
                    >
                      <div style={{ width: "48px" }} />
                      <div
                        className={`h-1 flex-1 rounded transition-colors ${
                          isCompleted ? "bg-green-500" : "bg-slate-200"
                        }`}
                      />
                    </div>
                  );
                })}
                <div style={{ width: "48px" }} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
