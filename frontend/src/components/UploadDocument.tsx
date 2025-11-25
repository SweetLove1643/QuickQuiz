import { Upload, File, CheckCircle, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { useState } from "react";
import { Textarea } from "./ui/textarea";

interface UploadDocumentProps {
  onDocumentProcessed: (document: any) => void;
}

export function UploadDocument({ onDocumentProcessed }: UploadDocumentProps) {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [summary, setSummary] = useState("");
  const [isProcessed, setIsProcessed] = useState(false);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      setIsProcessed(false);
      setSummary("");
      
      // Simulate API call to backend for processing
      setIsProcessing(true);
      setTimeout(() => {
        // Mock summary from backend
        const mockSummary = `Tóm tắt tài liệu "${file.name}":\n\n• Chương 1: Giới thiệu về chủ đề chính\n• Chương 2: Các khái niệm cơ bản và định nghĩa\n• Chương 3: Ứng dụng thực tế\n• Chương 4: Bài tập và câu hỏi ôn tập\n\nNội dung tài liệu bao gồm các kiến thức quan trọng về chủ đề, với nhiều ví dụ minh họa và bài tập thực hành.`;
        setSummary(mockSummary);
        setIsProcessing(false);
        setIsProcessed(true);
      }, 2000);
    }
  };

  const handleCreateQuiz = () => {
    if (uploadedFile && summary) {
      onDocumentProcessed({
        fileName: uploadedFile.name,
        summary: summary,
        uploadDate: new Date().toISOString(),
      });
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-slate-900 mb-2">Tạo bài kiểm tra</h1>
        <p className="text-slate-600">Tải lên tài liệu của bạn để tạo bài quiz tự động</p>
      </div>

      {/* Upload Area */}
      <Card className="p-8 mb-6">
        <div className="flex flex-col items-center justify-center">
          {!uploadedFile ? (
            <>
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <Upload className="size-10 text-blue-600" />
              </div>
              <h3 className="text-slate-900 mb-2">Chọn tài liệu để upload</h3>
              <p className="text-slate-500 mb-6 text-center">
                Hỗ trợ PDF, DOCX, TXT, PPT (Tối đa 10MB)
              </p>
              <label htmlFor="file-upload">
                <Button asChild>
                  <span className="cursor-pointer">Chọn file</span>
                </Button>
              </label>
              <input
                id="file-upload"
                type="file"
                className="hidden"
                accept=".pdf,.docx,.txt,.ppt,.pptx"
                onChange={handleFileUpload}
              />
            </>
          ) : (
            <div className="w-full">
              <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-lg mb-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <File className="size-6 text-blue-600" />
                </div>
                <div className="flex-1">
                  <p className="text-slate-900">{uploadedFile.name}</p>
                  <p className="text-slate-500">
                    {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                {isProcessed && (
                  <CheckCircle className="size-6 text-green-600" />
                )}
                {isProcessing && (
                  <Loader2 className="size-6 text-blue-600 animate-spin" />
                )}
              </div>
              
              {!isProcessed && !isProcessing && (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    setUploadedFile(null);
                    setSummary("");
                  }}
                >
                  Chọn file khác
                </Button>
              )}
            </div>
          )}
        </div>
      </Card>

      {/* Processing Status */}
      {isProcessing && (
        <Card className="p-6 mb-6">
          <div className="flex items-center gap-3">
            <Loader2 className="size-6 text-blue-600 animate-spin" />
            <div>
              <h3 className="text-slate-900">Đang xử lý tài liệu...</h3>
              <p className="text-slate-500">Hệ thống đang trích xuất và tóm tắt nội dung</p>
            </div>
          </div>
        </Card>
      )}

      {/* Summary Editor */}
      {isProcessed && summary && (
        <Card className="p-6 mb-6">
          <div className="mb-4">
            <h3 className="text-slate-900 mb-2">Bản tóm tắt tài liệu</h3>
            <p className="text-slate-500">Bạn có thể chỉnh sửa nội dung tóm tắt bên dưới</p>
          </div>
          
          <Textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            className="min-h-[300px] mb-4"
            placeholder="Nội dung tóm tắt..."
          />

          <div className="flex gap-3">
            <Button onClick={handleCreateQuiz} className="flex-1">
              Tạo bài Quiz
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setUploadedFile(null);
                setSummary("");
                setIsProcessed(false);
              }}
            >
              Upload lại
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}