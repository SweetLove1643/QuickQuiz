import { ArrowLeft, Edit, Download, FileText, Calendar } from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Textarea } from "./ui/textarea";
import { Input } from "./ui/input";
import { useEffect, useState } from "react";
import { quizAPI } from "../api/quizAPI";

interface ViewDocumentProps {
  document: any;
  onBack: () => void;
  onSave?: (updatedDocument: any) => void;
}

export function ViewDocument({ document, onBack, onSave }: ViewDocumentProps) {
  const [resolvedDoc, setResolvedDoc] = useState(document);
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState(
    document?.title || document?.file_name || ""
  );
  const [editedSummary, setEditedSummary] = useState(
    document?.summary || document?.extracted_text || ""
  );
  const [editedContent, setEditedContent] = useState(
    document?.content || document?.extracted_text || ""
  );
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Sync incoming document and fetch detail if content is missing
  useEffect(() => {
    if (!document) return;

    setResolvedDoc(document);

    const baseTitle =
      document.title || document.file_name || document.document_name || "";
    const baseContent = document.content || document.extracted_text || "";
    const baseSummary = document.summary || baseContent;

    setEditedTitle(baseTitle);
    setEditedSummary(baseSummary || "");
    setEditedContent(baseContent || "");

    if (document.document_id && !document.content && !document.extracted_text) {
      const fetchDetail = async () => {
        setIsLoadingDetail(true);
        setLoadError(null);
        try {
          const res = await quizAPI.getDocumentById(document.document_id);
          if (res.success && res.document) {
            setResolvedDoc(res.document);
            const doc = res.document;
            const title = doc.title || doc.file_name || "";
            const content = doc.content || doc.extracted_text || "";
            const summary = doc.summary || content;
            setEditedTitle(title);
            setEditedSummary(summary || "");
            setEditedContent(content || "");
          } else {
            setLoadError(res.error || "Không thể tải chi tiết tài liệu");
          }
        } catch (err) {
          console.error("Failed to load document detail", err);
          setLoadError("Không thể tải chi tiết tài liệu");
        } finally {
          setIsLoadingDetail(false);
        }
      };

      fetchDetail();
    }
  }, [document]);

  const handleDownload = () => {
    const content = `${editedTitle}\n\n${editedSummary}\n\n${editedContent}`;
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = window.document.createElement("a");
    link.href = url;
    link.download = `${editedTitle}.txt`;
    window.document.body.appendChild(link);
    link.click();
    window.document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleSave = async () => {
    try {
      const updatedDocument = {
        title: editedTitle,
        summary: editedSummary,
        content: editedContent,
      };

      const result = await quizAPI.updateDocument(
        resolvedDoc?.document_id || resolvedDoc?.id,
        updatedDocument
      );

      if (result.success) {
        const merged = {
          ...resolvedDoc,
          ...updatedDocument,
          updated_at: result.updated_at,
        };
        setResolvedDoc(merged);
        onSave?.(merged);
        setIsEditing(false);
      }
    } catch (error) {
      console.error("Save failed:", error);
      alert("Luu that bai. Vui long thu lai.");
    }
  };

  const handleCancel = () => {
    const baseTitle =
      resolvedDoc?.title ||
      resolvedDoc?.file_name ||
      resolvedDoc?.document_name ||
      "";
    const baseContent =
      resolvedDoc?.content || resolvedDoc?.extracted_text || "";
    const baseSummary = resolvedDoc?.summary || baseContent;

    setEditedTitle(baseTitle);
    setEditedSummary(baseSummary || "");
    setEditedContent(baseContent || "");
    setIsEditing(false);
  };

  const handleDelete = async () => {
    if (!window.confirm("Ban chac chan muon xoa tai lieu nay?")) return;

    try {
      const result = await quizAPI.deleteDocument(
        resolvedDoc?.document_id || resolvedDoc?.id
      );
      if (result.success) {
        onBack?.();
      }
    } catch (error) {
      console.error("Delete failed:", error);
      alert("Xoa that bai. Vui long thu lai.");
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <Button variant="ghost" className="mb-4" onClick={onBack}>
          <ArrowLeft className="size-4 mr-2" />
          Quay lại
        </Button>

        <div className="flex items-start justify-between">
          <div className="flex-1">
            {isEditing ? (
              <Input
                value={editedTitle}
                onChange={(e) => setEditedTitle(e.target.value)}
                className="mb-4 text-2xl"
                placeholder="Tiêu đề tài liệu"
              />
            ) : (
              <h1 className="text-slate-900 mb-2">
                {resolvedDoc?.title || resolvedDoc?.file_name || "Tài liệu"}
              </h1>
            )}
            <div className="flex items-center gap-4 text-slate-600">
              <div className="flex items-center gap-2">
                <Calendar className="size-4" />
                <span>
                  {resolvedDoc?.created_at
                    ? new Date(resolvedDoc.created_at).toLocaleDateString(
                        "vi-VN"
                      )
                    : "Hôm nay"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <FileText className="size-4" />
                <span>{resolvedDoc?.file_type || "Tài liệu"}</span>
              </div>
              {isLoadingDetail && (
                <span className="text-xs text-slate-500">
                  Đang tải nội dung...
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 ml-4">
            {isEditing ? (
              <>
                <Button variant="outline" onClick={handleCancel}>
                  Hủy
                </Button>
                <Button onClick={handleSave}>Lưu thay đổi</Button>
              </>
            ) : (
              <>
                <Button variant="outline" onClick={() => setIsEditing(true)}>
                  <Edit className="size-4 mr-2" />
                  Chỉnh sửa
                </Button>
                <Button variant="outline" onClick={handleDownload}>
                  <Download className="size-4 mr-2" />
                  Tải xuống
                </Button>
                <Button
                  variant="outline"
                  onClick={handleDelete}
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  Xoa
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="space-y-6">
        {loadError && <div className="text-sm text-red-600">{loadError}</div>}
        {/* Summary Section */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-slate-900">Tóm tắt</h2>
            {!isEditing && <Badge variant="outline">AI Generated</Badge>}
          </div>
          {isEditing ? (
            <Textarea
              value={editedSummary}
              onChange={(e) => setEditedSummary(e.target.value)}
              rows={4}
              placeholder="Nhập tóm tắt tài liệu..."
              className="resize-none"
            />
          ) : (
            <p className="text-slate-700 leading-relaxed">{editedSummary}</p>
          )}
        </Card>

        {/* Main Content */}
        <Card className="p-6">
          <h2 className="text-slate-900 mb-4">Nội dung chi tiết</h2>
          {isEditing ? (
            <Textarea
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              rows={20}
              placeholder="Nhập nội dung tài liệu..."
              className="resize-none font-mono"
            />
          ) : (
            <div className="prose prose-slate max-w-none">
              <pre className="whitespace-pre-wrap text-slate-700 leading-relaxed">
                {editedContent}
              </pre>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
