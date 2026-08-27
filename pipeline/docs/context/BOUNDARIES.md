# BOUNDARIES
# Giới hạn quyền hạn — Những gì AI được và không được làm

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-26

---

## 1. Phạm vi File (File Scope)

### AI được phép đọc và sửa:
```
✅ app/**
✅ tests/**
✅ pipeline/docs/context/**
✅ pipeline/docs/runtime/**
```

### AI KHÔNG được chạm vào:
```
❌ .env
❌ pipeline/docs/core/** — Bộ quy chuẩn cố định
❌ to_do.md (File này dành cho Human User cập nhật/duyệt)
```

---

## 2. Quyền Kiến trúc & Thao tác

### AI có thể tự quyết định:
```
✅ Cấu trúc module bên trong app/core/ và app/data/
✅ Thuật toán Heuristic Check & Hybrid RAG Retrieval
✅ Prompt engineering 3 tầng
```

### Phải hỏi human trước:
```
❓ Thay đổi lớn đến API Endpoints hiện tại của FastAPI
❓ Thêm thư viện nặng ngoài chuẩn Python/FastAPI
```


---

## 3. Real-Time Streaming & Latency Boundaries (Phase 4)

### AI được phép quyết định:
```
✅ Chuyển đổi giữa streaming chunk và full buffer trong TTS
✅ Cấu trúc prompt cho Micro-LLM Rewriter và Fast Voice Track
✅ Phân luồng giữa Synchronous Response và FastAPI BackgroundTasks
```

### Quy tắc bất di bất dịch:
```
🔒 Phải giữ chất lượng câu văn tự nhiên khi hạ cấp level (dùng Micro-LLM, không thay thế từ đồng nghĩa máy móc).
🔒 Toàn bộ chỉ số chấm điểm (Fluency, Grammar, Native Phrasing) phải tiếp tục hoạt động đầy đủ qua BackgroundTasks.
```
