// Utility functions for file handling and API integration
// Supports image upload, OCR processing, and document management

import { quizAPI } from "./quizAPI";

export interface ProcessedDocument {
  fileName: string;
  fileSize: number;
  fileType: string;
  extractedText: string;
  summary: string;
  documentId: string;
  ocrConfidence?: number;
  summaryConfidence?: number;
  processingTime: number;
  uploadDate: string;
}

// Convert file to base64 string
export const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // Remove data:image/jpeg;base64, prefix
      const base64 = result.split(",")[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
};

// Check if file is supported image format
export const isImageFile = (file: File): boolean => {
  const supportedTypes = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/bmp",
    "image/tiff",
  ];
  return supportedTypes.includes(file.type.toLowerCase());
};

// Check if file is supported document format
export const isDocumentFile = (file: File): boolean => {
  const supportedTypes = ["application/pdf", "text/plain", "text/markdown"];
  return supportedTypes.includes(file.type.toLowerCase());
};

// Format file size for display
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

// Validate file before upload
export const validateFile = (
  file: File
): { valid: boolean; error?: string } => {
  const maxSize = 10 * 1024 * 1024; // 10MB

  if (!isImageFile(file) && !isDocumentFile(file)) {
    return {
      valid: false,
      error:
        "Định dạng file không được hỗ trợ. Vui lòng chọn file ảnh (JPG, PNG) hoặc tài liệu (PDF, TXT)",
    };
  }

  if (file.size > maxSize) {
    return {
      valid: false,
      error: "File quá lớn. Kích thước tối đa là 10MB",
    };
  }

  return { valid: true };
};

// Extract text from plain text files
export const extractTextFromTextFile = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsText(file);
  });
};

export const processDocument = async (
  file: File
): Promise<ProcessedDocument> => {
  const startTime = Date.now();
  const validation = validateFile(file);

  if (!validation.valid) {
    throw new Error(validation.error);
  }

  let extractedText = "";
  let ocrResponse = null;
  let summaryResponse = null;

  try {
    // Handle different file types
    if (isImageFile(file)) {
      // OCR processing for images
      const base64 = await fileToBase64(file);
      const combined = await quizAPI.ocrAndSummarize(base64, {
        style: "detailed",
        max_length: 500,
      });

      ocrResponse = combined.ocr;
      summaryResponse = combined.summary;
      extractedText = ocrResponse.extracted_text || "";
      
      // ✅ FIX 1: Validate extracted text is not empty
      if (!extractedText || extractedText.trim().length === 0) {
        throw new Error("OCR failed: Không thể trích xuất text từ ảnh. Vui lòng chọn ảnh khác.");
      }
    } else if (file.type === "text/plain") {
      // Direct text extraction for text files
      extractedText = await extractTextFromTextFile(file);

      // ✅ FIX 2: Validate text file is not empty
      if (!extractedText || extractedText.trim().length === 0) {
        throw new Error("Tệp text trống. Vui lòng chọn tệp khác.");
      }

      // Summarize the text content
      summaryResponse = await quizAPI.summarizeText({
        text: extractedText,
        config: { style: "detailed", max_length: 500 },
      });
    } else {
      throw new Error(`Định dạng file ${file.type} chưa được hỗ trợ`);
    }

    const processingTime = Date.now() - startTime;

    // ✅ FIX 3: Validate summary response has actual data
    const finalSummary = summaryResponse?.summary || extractedText;
    if (!finalSummary || finalSummary.trim().length === 0) {
      throw new Error("Không thể tạo summary cho tài liệu. Vui lòng thử lại.");
    }

    return {
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      extractedText: extractedText.trim(),
      summary: finalSummary.trim(),
      documentId: `doc_${Date.now()}_${Math.random()
        .toString(36)
        .substr(2, 9)}`,
      ocrConfidence: ocrResponse?.confidence_score || 0.85,
      summaryConfidence: summaryResponse?.confidence_score || 0.85,
      processingTime,
      uploadDate: new Date().toISOString(),
    };
  } catch (error) {
    console.error("Document processing error:", error);
    throw error;
  }
};