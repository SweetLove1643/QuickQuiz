# Quy Tắc Viết Commit Message

## Định Dạng: `<type>: <subject>`

### Types

- `feat` - Thêm tính năng mới
- `fix` - Sửa lỗi
- `docs` - Thay đổi documentation
- `style` - Format code (không ảnh hưởng logic)
- `refactor` - Cải thiện code
- `test` - Thêm/sửa tests
- `chore` - Build process/tools
- `perf` - Cải thiện hiệu suất

### Subject Rules

- Thì hiện tại, dạng mệnh lệnh: "add" không phải "added"
- Không viết hoa chữ cái đầu
- Tối đa 50 ký tự
- Không kết thúc bằng dấu chấm

## Ví Dụ

```
feat: add multiple choice question generation
fix: resolve null pointer exception in validation
docs: update installation instructions
chore: update fastapi to 0.104.0
```

## Quy Tắc

Tiếng Anh hoặc tiếng Việt, tối đa 50 ký tự, một commit một thay đổi
Tránh: "fix bug", "update code", commit nhiều thay đổi

---

> **Tham khảo**: [Conventional Commits](https://www.conventionalcommits.org/)
