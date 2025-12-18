import { MoreVertical, Star, FileText, RotateCcw } from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";

interface StudySet {
  id: number;
  title: string;
  termCount: number;
  author: string;
  avatarColor: string;
  lastStudied: string;
  type: "document" | "quiz"; // Type to differentiate between document and quiz
  questions?: any[]; // Quiz questions data
  documentName?: string;
}

interface StudySetCardProps {
  studySet: StudySet;
  onNavigate?: (page: string) => void;
  onQuizSelected?: (quiz: any) => void;
  onDocumentSelected?: (document: any) => void;
}

export function StudySetCard({ studySet, onNavigate, onQuizSelected, onDocumentSelected }: StudySetCardProps) {
  return (
    <Card className="p-0 overflow-hidden hover:shadow-lg transition-shadow">
      <div className="p-4 space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-slate-900 mb-1 line-clamp-2">
              {studySet.title}
            </h3>
            <p className="text-slate-500">
              {studySet.type === "quiz" ? `${studySet.termCount} câu hỏi` : `${studySet.termCount} trang`}
            </p>
          </div>
          <Button variant="ghost" size="icon" className="shrink-0">
            <MoreVertical className="size-4" />
          </Button>
        </div>

        {/* Author Info */}
        <div className="flex items-center gap-2">
          <div className={`w-6 h-6 rounded-full ${studySet.avatarColor} flex items-center justify-center`}>
            <span className="text-white text-xs">
              {studySet.author.charAt(0)}
            </span>
          </div>
          <span className="text-slate-600">{studySet.author}</span>
        </div>

        {/* Last Studied */}
        <div className="flex items-center justify-between text-slate-500 pt-2 border-t border-slate-100">
          <span>
            {studySet.type === "quiz" ? "Làm lần cuối:" : "Xem lần cuối:"} {studySet.lastStudied}
          </span>
          <Button variant="ghost" size="icon" className="size-8">
            <Star className="size-4" />
          </Button>
        </div>
      </div>

      {/* Action Button */}
      <div className="border-t border-slate-200">
        {studySet.type === "document" ? (
          <Button 
            variant="ghost" 
            className="w-full justify-center gap-2 py-4 rounded-none hover:bg-slate-50" 
            onClick={() => {
              if (onDocumentSelected) {
                onDocumentSelected(studySet);
              }
            }}
          >
            <FileText className="size-5" />
            Xem tài liệu
          </Button>
        ) : (
          <Button 
            variant="ghost" 
            className="w-full justify-center gap-2 py-4 rounded-none hover:bg-slate-50"
            onClick={() => {
              if (studySet.type === "quiz" && onQuizSelected && onNavigate) {
                // Prepare quiz data with proper structure
                const quizData = {
                  title: studySet.title,
                  questions: studySet.questions || [],
                  documentName: studySet.documentName || studySet.title,
                };
                onQuizSelected(quizData);
                onNavigate("take-quiz");
              }
            }}
          >
            <RotateCcw className="size-5" />
            Làm lại
          </Button>
        )}
      </div>
    </Card>
  );
}