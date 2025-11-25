import { ArrowLeft, Edit, Download, Eye, Star, FileText, Calendar } from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Textarea } from "./ui/textarea";
import { Input } from "./ui/input";
import { useState } from "react";

interface ViewDocumentProps {
  document: any;
  onBack: () => void;
  onSave?: (updatedDocument: any) => void;
}

export function ViewDocument({ document, onBack, onSave }: ViewDocumentProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState(document?.title || "");
  const [editedSummary, setEditedSummary] = useState(
    document?.summary || "Đây là bản tóm tắt tài liệu. Bạn có thể chỉnh sửa nội dung này để phù hợp với nhu cầu học tập của mình."
  );
  const [editedContent, setEditedContent] = useState(
    document?.content || `# ${document?.title || "Nội dung tài liệu"}

## Giới thiệu
Đây là nội dung chi tiết của tài liệu. Trong môi trường thực tế, nội dung này sẽ được trích xuất tự động từ file PDF hoặc các định dạng khác mà người dùng upload.

## Nội dung chính

### Phần 1: Khái niệm cơ bản
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

### Phần 2: Phân tích chi tiết
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

### Phần 3: Tổng kết
Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.

## Kết luận
Tài liệu này cung cấp một cái nhìn tổng quan về chủ đề. Người học có thể sử dụng nội dung này làm tài liệu tham khảo cho quá trình học tập của mình.`
  );

  const handleDownload = () => {
    const content = `${editedTitle}\n\n${editedSummary}\n\n${editedContent}`;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = window.document.createElement('a');
    link.href = url;
    link.download = `${editedTitle}.txt`;
    window.document.body.appendChild(link);
    link.click();
    window.document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleSave = () => {
    const updatedDocument = {
      ...document,
      title: editedTitle,
      summary: editedSummary,
      content: editedContent,
    };
    onSave?.(updatedDocument);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditedTitle(document?.title || "");
    setEditedSummary(document?.summary || "");
    setEditedContent(document?.content || "");
    setIsEditing(false);
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="ghost"
          className="mb-4"
          onClick={onBack}
        >
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
              <h1 className="text-slate-900 mb-2">{document?.title || "Tài liệu"}</h1>
            )}
            <div className="flex items-center gap-4 text-slate-600">
              <div className="flex items-center gap-2">
                <Calendar className="size-4" />
                <span>{document?.uploadDate || "Hôm nay"}</span>
              </div>
              <div className="flex items-center gap-2">
                <FileText className="size-4" />
                <span>{document?.pages || "0"} trang</span>
              </div>
              <div className="flex items-center gap-2">
                <Eye className="size-4" />
                <span>{document?.views || "0"} lượt xem</span>
              </div>
              <div className="flex items-center gap-2">
                <Star className="size-4 fill-yellow-400 text-yellow-400" />
                <span>{document?.rating || "0"}</span>
              </div>
              <Badge className={document?.status === "Công khai" ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-700"}>
                {document?.status || "Riêng tư"}
              </Badge>
            </div>
          </div>

          <div className="flex items-center gap-2 ml-4">
            {isEditing ? (
              <>
                <Button variant="outline" onClick={handleCancel}>
                  Hủy
                </Button>
                <Button onClick={handleSave}>
                  Lưu thay đổi
                </Button>
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
              </>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="space-y-6">
        {/* Summary Section */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-slate-900">Tóm tắt</h2>
            {!isEditing && (
              <Badge variant="outline">AI Generated</Badge>
            )}
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
            <p className="text-slate-700 leading-relaxed">
              {editedSummary}
            </p>
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