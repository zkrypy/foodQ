# FoodQ demo

Bản demo ứng dụng FoodQ: sinh viên đặt món trước ở căn tin, theo dõi số thứ tự; bếp nhận đơn và báo khi món xong.

- App Sinh viên: `index.html` (chỉ có app đặt món, không có đường dẫn hay mã nguồn của bếp)
- App Bếp: `bep.html#kitchen` (chỉ gửi cho căn tin và nhóm; `bep.html` có thêm trang giới thiệu và chế độ xem song song)
- Xem song song: `index.html#both`

Dữ liệu dùng chung qua Firebase Firestore (cấu hình trong `firebase-config.js`). Để `null` thì demo chạy riêng trên từng máy.

Đây là bản demo cho môn Khởi nghiệp đổi mới sáng tạo, không xử lý thanh toán thật.
