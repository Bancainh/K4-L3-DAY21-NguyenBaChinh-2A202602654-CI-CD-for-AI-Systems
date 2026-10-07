# Báo Cáo Lab Day 21 - CI/CD cho AI Systems

| | |
|---|---|
| Họ và tên | Nguyễn Bá Chính |
| MSSV | 2A202602654 |
| Lớp / Khóa | AI20k K4 |
| Repo GitHub | https://github.com/Bancainh/K4-L3-DAY21-NguyenBaChinh-2A202602654-CI-CD-for-AI-Systems |
| Ngày nộp | 07/10/2026 |

---

## 1. Bộ Siêu Tham Số Đã Chọn và Lý Do

| Lần chạy | n_estimators | learning_rate | max_depth | f1_score | accuracy |
|---|---:|---:|---:|---:|---:|
| 1 | 100 | 0.1 | 3 | 0.7109 | 0.878 |
| 2 | 150 | 0.1 | 5 | 0.7091 | 0.872 |
| 3 | 200 | 0.2 | 3 | 0.7032 | 0.870 |

**Bộ siêu tham số đã chọn:** `n_estimators=100`, `learning_rate=0.1`, `max_depth=3`.

**Lý do:** Trong các thí nghiệm đã chạy bằng MLflow, bộ `100 / 0.1 / 3` đạt `f1_score=0.7109`, cao nhất trong các cấu hình thử nghiệm, đồng thời đạt accuracy 0.878. Vì mục tiêu chính của bài là phát hiện đúng lớp thu nhập cao, tôi ưu tiên F1 thay vì chỉ nhìn accuracy. Trong các lần chạy trên, cấu hình có F1 cao nhất cũng đồng thời có accuracy cao nhất. Việc tăng `n_estimators`, tăng `max_depth` hoặc dùng `learning_rate` lớn hơn không làm kết quả tốt hơn; mô hình phức tạp hơn có thể không cải thiện khả năng tổng quát hóa trên tập holdout. Do đó tôi chọn cấu hình đơn giản hơn nhưng có F1 tốt nhất.

---

## 2. Vì Sao Ngưỡng Chất Lượng Đặt Trên F1 Chứ Không Phải Accuracy

Dữ liệu Adult Income bị mất cân bằng lớp, trong đó lớp thu nhập trên 50K chỉ chiếm khoảng 24,8%, còn lớp thu nhập thấp chiếm khoảng 75,2%. Vì vậy một mô hình luôn dự đoán mọi mẫu là thu nhập thấp vẫn có thể đạt accuracy khoảng 0,752 dù hoàn toàn không phát hiện được trường hợp thu nhập cao. Accuracy vì thế có thể tạo cảm giác mô hình tốt trong khi lớp quan trọng bị bỏ sót. F1 của lớp dương kết hợp precision và recall, nên phản ánh đồng thời khả năng dự đoán đúng người thu nhập cao và hạn chế bỏ sót nhóm này. Tôi sử dụng `f1_score` cho lớp dương thay vì `average="weighted"` vì weighted F1 có thể bị lớp đa số chi phối; macro F1 lại đánh trọng số hai lớp như nhau, không tập trung trực tiếp vào lớp thu nhập cao mà bài toán yêu cầu kiểm soát.

---

## 3. Khó Khăn Gặp Phải và Cách Giải Quyết

| Khó khăn | Nguyên nhân | Cách giải quyết |
|---|---|---|
| EC2 không tải được model từ S3 và trả lỗi 403 | IAM Role chưa có policy S3 phù hợp cho đường dẫn artifact | Cập nhật policy để cho phép `ListBucket` và `GetObject` đối với bucket và `artifacts/*` |
| Job Train ban đầu thất bại | `STORAGE_CREDENTIALS` trong GitHub Secrets không đúng định dạng JSON | Lưu Access Key ID và Secret Access Key trong một JSON đúng cấu trúc mà workflow yêu cầu |
| Job Release không SSH được vào EC2 | `SERVER_SSH_KEY` không chứa đúng private key nhiều dòng | Copy toàn bộ nội dung file `.pem` vào GitHub Secret, giữ nguyên header, footer và xuống dòng |

---

## 4. So Sánh Bước 2 và Bước 3

| | f1_score | accuracy |
|---|---:|---:|
| Bước 2 (chỉ `train_batch1`) | 0.710900 | 0.878 |
| Bước 3 (thêm `train_batch2`) | 0.701422 | 0.874 |

**Nhận xét:** Sau khi bổ sung `train_batch2`, F1 giảm nhẹ từ 0.7109 xuống 0.7014 và accuracy giảm từ 0.878 xuống 0.874. Điều này không bất thường vì batch mới được lấy từ cùng phân phối dữ liệu, nên thêm dữ liệu không đảm bảo chỉ số trên holdout luôn tăng. Quan trọng hơn, mô hình mới vẫn vượt Quality Gate `F1 >= 0.65` và toàn bộ quy trình từ cập nhật dữ liệu, huấn luyện, kiểm tra chất lượng đến triển khai đã chạy tự động thành công.