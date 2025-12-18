# Sử dụng base image Nginx gọn nhẹ
FROM nginx:1.25-alpine

# Sao chép file cấu hình Nginx tùy chỉnh cho ứng dụng SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Sao chép thư mục 'www' đã được build sẵn từ máy của bạn vào trong image
# LƯU Ý: Bạn phải chạy 'ionic build --prod' trên máy trước khi build image này.
COPY  ./dist/architectui-angular-free/browser /usr/share/nginx/html
# Mở port 80
EXPOSE 80

# Lệnh để khởi động Nginx
CMD ["nginx", "-g", "daemon off;"]