import { Injectable } from "@angular/core";

export interface Toast {
  header?: string;
  body: string;
  className?: string; // ví dụ: 'bg-success text-white'
  delay?: number; // thời gian hiển thị ms
}

@Injectable({
  providedIn: "root",
})
export class ToastService {
  toasts: Toast[] = [];

  show(toast: Toast) {
    this.toasts.push(toast);
    const delay = toast.delay ?? 2000;
    setTimeout(() => this.remove(toast), delay);
  }

  remove(toast: Toast) {
    this.toasts = this.toasts.filter((t) => t !== toast);
  }

  success(body: string, header = "Thành công") {
    this.show({
      body,
      header,
      className: "bg-success text-white",
      delay: 2000,
    });
  }

  error(body: string, header = "Lỗi") {
    this.show({ body, header, className: "bg-danger text-white", delay: 2000 });
  }

  info(body: string, header = "Thông báo") {
    this.show({ body, header, className: "bg-info text-white", delay: 2000 });
  }

  warning(body: string, header = "Cảnh báo") {
    this.show({ body, header, className: "bg-warning text-dark", delay: 2000 });
  }
}
