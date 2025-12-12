import { Upload, File, CheckCircle, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { useState } from "react";
import { Textarea } from "./ui/textarea";
import { processDocument, ProcessedDocument } from "../api/fileUtils";
import { quizAPI } from "../api/quizAPI";

interface QuickStartProps {
  onDocumentProcessed: (document: any) => void;
}

export function QuickStart({ onDocumentProcessed }: QuickStartProps) {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processedDoc, setProcessedDoc] = useState<ProcessedDocument | null>(
    null
  );
  const [summary, setSummary] = useState("");
  const [isProcessed, setIsProcessed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      setIsProcessed(false);
      setSummary("");
      setError(null);
      setSuccess(null);
      setProcessedDoc(null);

      setIsProcessing(true);
      try {
        const result = await processDocument(file);
        setProcessedDoc(result);
        setSummary(result.summary);
        setIsProcessed(true);
      } catch (error) {
        console.error("Error processing document:", error);
        setError(
          error instanceof Error ? error.message : "Không thể xử lý tài liệu"
        );
        setIsProcessed(false);
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const handleCreateQuiz = async () => {
    if (uploadedFile && processedDoc) {
      setIsSaving(true);
      setError(null);
      setSuccess(null);

      try {
        const result = await quizAPI.saveDocument({
          fileName: processedDoc.fileName,
          fileSize: processedDoc.fileSize,
          fileType: processedDoc.fileType,
          extractedText: processedDoc.extractedText,
          summary: summary,
          documentId: processedDoc.documentId,
          processingTime: processedDoc.processingTime,
          ocrConfidence: processedDoc.ocrConfidence,
          summaryConfidence: processedDoc.summaryConfidence,
        });

        if (result.success) {
          const savedDocument = {
            ...processedDoc,
            summary,
            documentId: result.document_id || processedDoc.documentId,
            savedAt: result.saved_at,
          };

          setSuccess(
            `Đã lưu tài liệu "${uploadedFile.name}" vào thư viện thành công!`
          );

          onDocumentProcessed(savedDocument);
        } else {
          throw new Error("Save failed");
        }
      } catch (error) {
        console.error("Error saving document:", error);
        setError(
          error instanceof Error ? error.message : "Không thể lưu tài liệu"
        );
      } finally {
        setIsSaving(false);
      }
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-slate-900 mb-2">Bắt đầu nhanh</h1>
        <p className="text-slate-600">
          Tải lên tài liệu của bạn để tạo bài quiz tự động
        </p>
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
                Hỗ trợ PDF, DOCX, TXT, PPT và ảnh JPG, PNG, BMP, TIFF (Tối đa
                10MB)
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
                accept=".pdf,.docx,.txt,.ppt,.pptx,.jpg,.jpeg,.png,.bmp,.tiff"
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

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg mb-4">
                  <p className="text-red-600 text-sm">{error}</p>
                </div>
              )}

              {success && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg mb-4 animate-fade-in">
                  <div className="flex items-center gap-2">
                    <svg
                      className="size-4 text-green-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <p className="text-green-700 text-sm font-medium">
                      {success}
                    </p>
                  </div>
                </div>
              )}

              {!isProcessed && !isProcessing && (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    setUploadedFile(null);
                    setSummary("");
                    setError(null);
                    setSuccess(null);
                    setProcessedDoc(null);
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
              <p className="text-slate-500">
                Hệ thống đang trích xuất và tóm tắt nội dung
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Summary Editor */}
      {isProcessed && summary && (
        <Card className="p-6 mb-6">
          <div className="mb-4">
            <h3 className="text-slate-900 mb-2">Bản tóm tắt tài liệu</h3>
            <p className="text-slate-500">
              Bạn có thể chỉnh sửa nội dung tóm tắt bên dưới
            </p>
          </div>

          <Textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            className="min-h-[300px] mb-4"
            placeholder="Nội dung tóm tắt..."
          />

          <div className="flex gap-3">
            <Button
              onClick={handleCreateQuiz}
              className="flex-1"
              disabled={isSaving}
            >
              {isSaving && <Loader2 className="size-4 mr-2 animate-spin" />}
              {isSaving ? "Đang lưu..." : "Lưu và tạo Quiz"}
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setUploadedFile(null);
                setSummary("");
                setIsProcessed(false);
                setError(null);
                setSuccess(null);
                setProcessedDoc(null);
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
