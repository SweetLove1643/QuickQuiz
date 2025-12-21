import { FileText, Eye, Download, Star } from "lucide-react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";

const popularDocuments = [
  {
    id: 1,
    title: "Lịch sử Việt Nam - Thời kỳ Đại Việt",
    author: "Nguyễn Văn A",
    avatarColor: "bg-purple-500",
    views: 1250,
    downloads: 320,
    rating: 4.8,
    pages: 45,
    uploadDate: "2 ngày trước",
    status: "Công khai",
    summary: "Tài liệu này tổng hợp các triều đại phong kiến Việt Nam từ thời Đinh - Tiền Lê đến cuối thời Lý. Nội dung tập trung vào các sự kiện lịch sử quan trọng, các vị vua nổi bật và những đóng góp của họ cho đất nước.",
    content: `# Lịch sử Việt Nam - Thời kỳ Đại Việt

## Giới thiệu
Thời kỳ Đại Việt là giai đoạn quan trọng trong lịch sử Việt Nam, đánh dấu sự hình thành và phát triển của các triều đại phong kiến độc lập.

## Các triều đại chính

### 1. Nhà Đinh (968-980)
- Người sáng lập: Đinh Bộ Lĩnh
- Thành tựu: Thống nhất đất nước sau thời Thập Nhị Sứ Quân
- Đặt tên nước là Đại Cồ Việt

### 2. Nhà Tiền Lê (980-1009)
- Người sáng lập: Lê Hoàn
- Chiến thắng quân Tống xâm lược
- Phát triển kinh tế, văn hóa

### 3. Nhà Lý (1009-1225)
- Người sáng lập: Lý Công Uẩn (Lý Thái Tổ)
- Thời kỳ thịnh trị dưới các vua Lý Thánh Tông, Lý Nhân Tông
- Xây dựng Văn Miếu, phát triển Phật giáo

## Kết luận
Thời kỳ Đại Việt đặt nền móng cho sự phát triển lâu dài của dân tộc Việt Nam.`,
  },
  {
    id: 2,
    title: "Sinh học phân tử - Chương DNA và RNA",
    author: "Trần Thị B",
    avatarColor: "bg-green-500",
    views: 980,
    downloads: 215,
    rating: 4.6,
    pages: 32,
    uploadDate: "1 tuần trước",
    status: "Công khai",
    summary: "Chương này giải thích cấu trúc và chức năng của DNA và RNA, hai phân tử di truyền quan trọng nhất trong tế bào sống. Nội dung bao gồm cấu trúc xoắn kép, quá trình sao chép và phiên mã.",
    content: `# Sinh học phân tử - DNA và RNA

## Cấu trúc DNA

### Thành phần cơ bản
- Đường deoxyribose
- Nhóm phosphate
- 4 loại base: Adenine (A), Thymine (T), Guanine (G), Cytosine (C)

### Cấu trúc xoắn kép
- Hai chuỗi polynucleotide chạy song song ngược chiều
- Liên kết hydro giữa các base bổ sung: A-T, G-C

## RNA và vai trò

### Các loại RNA
1. mRNA - messenger RNA
2. tRNA - transfer RNA  
3. rRNA - ribosomal RNA

### Sự khác biệt DNA và RNA
- RNA có đường ribose thay vì deoxyribose
- RNA có Uracil (U) thay vì Thymine (T)
- RNA thường là chuỗi đơn

## Quá trình sinh học

### Sao chép DNA
- Diễn ra trong pha S của chu kỳ tế bào
- Enzyme DNA polymerase tham gia

### Phiên mã (Transcription)
- Tổng hợp mRNA từ DNA
- Enzyme RNA polymerase

### Dịch mã (Translation)
- Tổng hợp protein từ mRNA
- Diễn ra tại ribosome`,
  },
  {
    id: 3,
    title: "Toán học cao cấp - Giải tích",
    author: "Lê Văn C",
    avatarColor: "bg-blue-500",
    views: 875,
    downloads: 190,
    rating: 4.9,
    pages: 56,
    uploadDate: "3 ngày trước",
    status: "Công khai",
    summary: "Tài liệu giải tích cao cấp bao gồm lý thuyết về giới hạn, đạo hàm, tích phân và phương trình vi phân. Phù hợp cho sinh viên năm đầu đại học và học sinh chuyên toán.",
    content: `# Toán học cao cấp - Giải tích

## Chương 1: Giới hạn và Liên tục

### Định nghĩa giới hạn
- Giới hạn của hàm số khi x tiến tới một giá trị
- Các định lý về giới hạn

### Hàm liên tục
- Định nghĩa tính liên tục tại một điểm
- Tính chất của hàm liên tục

## Chương 2: Đạo hàm

### Định nghĩa đạo hàm
f'(x) = lim[h→0] (f(x+h) - f(x))/h

### Các quy tắc đạo hàm
- Đạo hàm của tổng, hiệu, tích, thương
- Đạo hàm hàm hợp
- Đạo hàm hàm ngược

## Chương 3: Tích phân

### Tích phân bất định
∫f(x)dx = F(x) + C

### Tích phân xác định
∫[a,b] f(x)dx

### Ứng dụng
- Tính diện tích
- Tính thể tích
- Độ dài đường cong

## Chương 4: Phương trình vi phân

### Phương trình vi phân cấp 1
dy/dx = f(x,y)

### Phương trình vi phân cấp 2
d²y/dx² + p(x)dy/dx + q(x)y = r(x)`,
  },
  {
    id: 4,
    title: "Tiếng Anh IELTS - Từ vựng học thuật",
    author: "Phạm Thị D",
    avatarColor: "bg-orange-500",
    views: 1420,
    downloads: 450,
    rating: 4.7,
    pages: 28,
    uploadDate: "5 ngày trước",
    status: "Công khai",
    summary: "Bộ từ vựng học thuật tiếng Anh cho kỳ thi IELTS, bao gồm các từ vựng quan trọng được phân loại theo chủ đề và kèm theo ví dụ minh họa.",
    content: `# Tiếng Anh IELTS - Từ vựng học thuật

## Academic Vocabulary

### Education
- curriculum (n): chương trình giảng dạy
- pedagogy (n): phương pháp sư phạm
- dissertation (n): luận văn
- seminar (n): hội thảo

### Environment
- sustainability (n): tính bền vững
- biodiversity (n): đa dạng sinh học
- conservation (n): bảo tồn
- ecosystem (n): hệ sinh thái

### Technology
- innovation (n): sự đổi mới
- automation (n): tự động hóa
- artificial intelligence: trí tuệ nhân tạo
- digital transformation: chuyển đổi số

## Collocations
- conduct research: tiến hành nghiên cứu
- reach a conclusion: đi đến kết luận
- raise awareness: nâng cao nhận thức`,
  },
];

interface PopularDocumentsProps {
  onDocumentSelected?: (document: any) => void;
}

export function PopularDocuments({ onDocumentSelected }: PopularDocumentsProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-slate-900 mb-1">Tài liệu phổ biến</h2>
          <p className="text-slate-600">Các tài liệu được nhiều người xem nhất</p>
        </div>
        <Button variant="ghost">Xem tất cả</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {popularDocuments.map((doc) => (
          <Card key={doc.id} className="p-4 hover:shadow-lg transition-shadow">
            <div className="flex items-start gap-3 mb-3">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center shrink-0">
                <FileText className="size-6 text-blue-600" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-slate-900 mb-1 line-clamp-2">
                  {doc.title}
                </h3>
                <p className="text-slate-500">{doc.pages} trang</p>
              </div>
            </div>

            {/* Author */}
            <div className="flex items-center gap-2 mb-3">
              <div className={`w-6 h-6 rounded-full ${doc.avatarColor} flex items-center justify-center`}>
                <span className="text-white text-xs">
                  {doc.author.charAt(0)}
                </span>
              </div>
              <span className="text-slate-600 text-sm">{doc.author}</span>
            </div>

            {/* Stats */}
            <div className="flex items-center justify-between text-slate-500 text-sm mb-3">
              <div className="flex items-center gap-1">
                <Eye className="size-4" />
                <span>{doc.views}</span>
              </div>
              <div className="flex items-center gap-1">
                <Download className="size-4" />
                <span>{doc.downloads}</span>
              </div>
              <div className="flex items-center gap-1">
                <Star className="size-4 fill-yellow-400 text-yellow-400" />
                <span>{doc.rating}</span>
              </div>
            </div>

            {/* Upload Date */}
            <div className="text-slate-500 text-sm mb-3 pt-3 border-t border-slate-100">
              {doc.uploadDate}
            </div>

            <Button className="w-full" size="sm" onClick={() => onDocumentSelected?.(doc)}>
              Xem tài liệu
            </Button>
          </Card>
        ))}
      </div>
    </div>
  );
}