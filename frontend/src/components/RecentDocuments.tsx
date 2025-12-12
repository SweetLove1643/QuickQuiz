import { FileText, Eye, Loader2 } from "lucide-react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { quizAPI } from "../api/quizAPI";

interface RecentDocumentsProps {
  onDocumentSelected?: (document: any) => void;
}

export function RecentDocuments({ onDocumentSelected }: RecentDocumentsProps) {
  const { user } = useAuth();
  const [recentDocuments, setRecentDocuments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadRecentDocuments = async () => {
      if (!user?.id) {
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        const response = await quizAPI.getDocuments();
        if (response.success) {
          // Get documents, sort by created_at desc, and take top 10
          const sortedDocs = (response.documents || [])
            .sort((a: any, b: any) => {
              const dateA = new Date(a.created_at || 0).getTime();
              const dateB = new Date(b.created_at || 0).getTime();
              return dateB - dateA;
            })
            .slice(0, 10);
          setRecentDocuments(sortedDocs);
        }
      } catch (err) {
        console.error("Failed to load recent documents:", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadRecentDocuments();
  }, [user?.id]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="size-8 animate-spin text-blue-600" />
        <span className="ml-3 text-slate-600">Đang tải tài liệu...</span>
      </div>
    );
  }

  if (recentDocuments.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="size-16 mx-auto text-slate-300 mb-4" />
        <h3 className="text-lg font-medium text-slate-900 mb-2">
          Chưa có tài liệu nào
        </h3>
        <p className="text-slate-600">Upload tài liệu đầu tiên để bắt đầu</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-slate-900 mb-1">Tài liệu gần đây</h2>
        <p className="text-slate-600 text-sm">
          {recentDocuments.length} tài liệu gần nhất
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {recentDocuments.map((doc) => (
          <Card
            key={doc.document_id}
            className="p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => onDocumentSelected?.(doc)}
          >
            <div className="flex items-start gap-3">
              {/* Icon */}
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center shrink-0">
                <FileText className="size-6 text-blue-600" />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <h3 className="text-slate-900 font-medium mb-1 truncate">
                  {doc.file_name || doc.title}
                </h3>
                <div className="flex items-center gap-2 text-xs text-slate-600 mb-2">
                  <span>{doc.file_type || "Document"}</span>
                  <span>•</span>
                  <span>
                    {doc.created_at
                      ? new Date(doc.created_at).toLocaleDateString("vi-VN")
                      : "Không rõ"}
                  </span>
                </div>
                {doc.summary && (
                  <p className="text-xs text-slate-600 line-clamp-2">
                    {doc.summary}
                  </p>
                )}
              </div>
            </div>

            {/* Action button */}
            <div className="mt-3">
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={(e: React.MouseEvent) => {
                  e.stopPropagation();
                  onDocumentSelected?.(doc);
                }}
              >
                <Eye className="size-4 mr-2" />
                Xem chi tiết
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
