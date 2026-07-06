# Hướng Dẫn Nộp Bài - Lab #28: Full Platform Integration Sprint

## Yêu Cầu Nộp Bài

**Full AI infrastructure platform demo** - từ data ingestion đến model serving với full observability.

## Các Artifacts Cần Nộp

### 1. Source Code
- Folder `lab28/` hoàn chỉnh với tất cả files
- Tất cả integration scripts hoạt động
- Prefect flows đã deploy và schedule

### 2. Screenshots Demo
Chụp màn hình các bước:
- Prefect UI: http://localhost:4200 (flow đang chạy)
- API Gateway call: `curl http://localhost:8000/health`
- Grafana dashboard: http://localhost:3000

### 3. Kết Quả Smoke Tests
Chạy và chụp màn hình kết quả:
```bash
cd lab28
pytest smoke-tests/ -v
```
Kỳ vọng: 5/5 tests passing

### 4. Production Readiness Score
```bash
python scripts/production_readiness_check.py
```
Kỳ vọng: Score >80%

### 5. Documentation
- `README.md` giải thích cách:
  - Start platform: `docker compose up -d`
  - Deploy Prefect flows
  - Run smoke tests
  - Access dashboards (Grafana:3000, Prometheus:9090, Prefect:4200)

## Định Dạng Nộp Bài

Tạo Repo GitHub chứa:
```
lab28_submission_[student_id]
├── lab28/                    # Source code hoàn chỉnh
│   ├── docker-compose.yml
│   ├── prefect/flows/
│   ├── scripts/
│   ├── api-gateway/
│   └── monitoring/
├── screenshots/              # Screenshots demo
│   ├── prefect_ui.png
│   ├── api_gateway.png
│   └── grafana_dashboard.png
├── smoke_tests_results.png   # Screenshot kết quả pytest
├── production_readiness.png  # Screenshot readiness score
└── README.md                # Hướng dẫn setup
```

## Địa Điểm Nộp
Nộp link repo GitHub qua LMS

## Tiêu Chí Chấm Điểm

| Tiêu Chí | Trọng Số | Mô Tả |
|----------|----------|-------|
| Integration Completeness | 40% | Tất cả 10 integration points hoạt động, data flow end-to-end |
| Observability | 25% | Logs, metrics, traces hiển thị; alerts configured |
| Performance | 20% | Latency trong SLO; load tested; không có memory leaks |
| Architecture Quality | 15% | Clean separation, GitOps config, documented decisions |

## Các Vấn Đề Cần Tránh

- Config drift giữa các environments
- Thiếu error handling tại integration points
- Monitoring coverage không hoàn chỉnh
- Không có rollback strategy
- Demo không test trước khi nộp

## 5 Câu Hỏi Cần Trả Lời Khi Nộp

1. **Phân tích các trade-offs trong thiết kế kiến trúc AI platform của bạn. Bạn đã cân bằng giữa performance, reliability, và maintainability như thế nào?**
   * **Performance vs Cost (Tài nguyên):** Chạy LLM Serving (vLLM) và Embedding Model trên Kaggle GPU (miễn phí) giúp giảm tải hoàn toàn cho phần cứng local. Tuy nhiên, trade-off là độ trễ mạng (network latency) tăng lên khoảng 3-5 giây do truyền tải gói tin qua Cloudflare Tunnel.
   * **Reliability vs Complexity:** Sử dụng Kafka làm Message Broker trung gian giúp đảm bảo dữ liệu không bị mất mát khi có sự cố (reliability cao), nhưng đánh đổi lại là độ phức tạp hệ thống tăng lên (phải vận hành Zookeeper, Kafka cluster).
   * **Maintainability (Khả năng bảo trì):** Kiến trúc được chia nhỏ thành các container độc lập (Microservices) thông qua Docker Compose (API Gateway, Qdrant, Feast/Redis, Prometheus, Grafana). Điều này giúp dễ dàng cô lập lỗi, nâng cấp hoặc thay thế từng thành phần mà không ảnh hưởng đến toàn bộ hệ thống.

2. **Trong kiến trúc hybrid (Local + Kaggle), bạn xử lý ngắt kết nối giữa local và Kaggle như thế nào? Có cơ chế fallback không?**
   * Sự kết nối giữa local và Kaggle được duy trì qua Cloudflare Tunnels (trycloudflare).
   * **Cơ chế Fallback:** Trong mã nguồn của [api-gateway/main.py](file:///c:/Users/admin/Day28-Lab-Assignment/lab28/api-gateway/main.py), tôi đã bọc các block gọi API ngoài bằng cấu trúc `try/except`. Nếu kết nối tới Kaggle (Embedding/vLLM) bị ngắt hoặc timeout (30s), Gateway sẽ bắt lỗi một cách chủ động và trả về HTTP Status phù hợp (502 Bad Gateway hoặc 504 Gateway Timeout) thay vì bị sập hoàn toàn. Đối với Qdrant, nếu không truy vấn được RAG context, hệ thống sẽ tự động hạ cấp tính năng (Graceful Degradation), chuyển tiếp câu hỏi gốc trực tiếp đến LLM mà không kèm context để đảm bảo người dùng vẫn nhận được câu trả lời.

3. **Giải thích cách event-driven architecture với Kafka giúp decouple các components trong AI platform của bạn.**
   * Kafka đóng vai trò hàng đợi đệm (Buffer queue) cắt đứt liên kết trực tiếp (decouple) giữa luồng thu thập dữ liệu (Ingestion) và luồng xử lý ETL (Prefect).
   * **Decouple về mặt thời gian (Temporal Decoupling):** Client đẩy log/tài liệu vào Kafka mà không cần biết Prefect worker có đang bận hay đang bị sập hay không. Ngược lại, Prefect worker kéo dữ liệu về xử lý theo lô (batching) khi tài nguyên cho phép mà không bị ràng buộc bởi tốc độ đẩy dữ liệu của client.
   * **Decouple về mặt giao diện (Interface Decoupling):** Các thành phần chỉ giao tiếp qua schema của Kafka topic `data.raw`, giúp dễ dàng thay đổi logic backend của Prefect/Delta Lake mà không cần cấu hình lại phía Client Ingestion.

4. **Bạn đã implement observability như thế nào? Logs, metrics, và traces được thu thập và visualized ra sao?**
   * **Metrics (Chỉ số):** API Gateway sử dụng `prometheus-fastapi-instrumentator` để đo đạc metrics. Prometheus định kỳ scrape các chỉ số này thông qua cổng `8000/metrics`. Grafana được cấu hình provisioning tự động kết nối Prometheus làm nguồn dữ liệu để hiển thị biểu đồ trực quan (như số lượng requests, trạng thái up/down của service) trên dashboard mặc định.
   * **Logs (Nhật ký):** Các containers ghi log trực tiếp ra stdout/stderr và được Docker Engine thu thập tập trung, cho phép kiểm tra thời gian thực bằng lệnh `docker compose logs`.
   * **Traces (Vết chạy):** Tích hợp LangSmith SDK bằng cách truyền biến môi trường `LANGCHAIN_API_KEY` vào ứng dụng, giúp giám sát chính xác từng bước xử lý của LLM prompt và RAG retrieval.

5. **Nếu một service trong stack (ví dụ: Qdrant hoặc Kafka) bị crash, hệ thống của bạn sẽ xử lý như thế nào? Có graceful degradation không?**
   * **Nếu Kafka crash:** Luồng thu thập dữ liệu bị gián đoạn, dữ liệu mới tạm thời không thể nạp vào Delta Lake. Tuy nhiên, luồng suy luận (inference chat) trên API Gateway vẫn hoạt động bình thường vì các tài liệu cũ đã được nhúng và lưu trữ sẵn trong Qdrant.
   * **Nếu Qdrant crash:** API Gateway được lập trình cơ chế **Graceful Degradation** (Giảm cấp tính năng an toàn): Khi bắt được ngoại lệ không thể kết nối hoặc tìm kiếm trên Qdrant, hệ thống sẽ bỏ qua bước tìm kiếm ngữ cảnh (context = `[]`) và gửi câu hỏi trực tiếp đến LLM trên Kaggle. Người dùng vẫn nhận được câu trả lời thô từ LLM thay vì nhận thông báo lỗi hệ thống bị sập.

## Câu Hỏi Thêm?
Liên hệ giảng viên qua LMS hoặc office hours.
