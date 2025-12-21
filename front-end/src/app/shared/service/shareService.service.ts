import { Injectable } from "@angular/core";
import { LOG_WORK_STATUS, STATUS } from "../common/constant";
import moment from "moment";
@Injectable({ providedIn: "root" })
export class ShareService {
  getColorStatusByCode(statusCode: any) {
    switch (statusCode) {
      case STATUS.COMPLETED:
        return "btn-status-success";
      case STATUS.CANCELED:
        return "btn-status-danger";
      case STATUS.IN_PROGRESS:
        return "btn-status-warning";
      case STATUS.ON_HOLD:
        return "btn-status-primary";
      default:
        return "btn-status-primary";
    }
  }
  getStatusNameByCode(statusCode: any) {
    switch (statusCode) {
      case STATUS.COMPLETED:
        return "Completed";
      case STATUS.CANCELED:
        return "Canceled";
      case STATUS.IN_PROGRESS:
        return "In progress";
      case STATUS.ON_HOLD:
        return "On hold";
      default:
        return "On hold";
    }
  }
  getColorStatusLogWorkByCode(statusCode: any) {
    switch (statusCode) {
      case 1:
        return "btn-status-success";
      case 2:
      case 3:
      case 4:
        return "btn-status-warning";
      case 5:
        return "btn-status-primary";
      default:
        return "btn-status-info";
    }
  }
  getStatusLogWorkNamByCode(statusCode: any) {
    switch (statusCode) {
      case 1:
        return "Hợp lệ";
      case 2:
        return "Đi công tác";
      case 3:
        return "Làm việc tại nhà";
      case 4:
        return "Khác";
      case 5:
        return "Gửi giải trình";
      default:
        return "Chưa xác định";
    }
  }
  getStatusNameCommonByCode(statusCode: any) {
    switch (statusCode) {
      case 1:
        return "Hoạt động";
      case 2:
        return "Không hoạt động";
      default:
        return "Hoạt động";
    }
  }
  getColorStatusCommonByCode(statusCode: any) {
    switch (statusCode) {
      case 1:
        return "btn-status-success";
      case 2:
        return "btn-status-danger";
      default:
        return "btn-status-success";
    }
  }

  getStatusNameIssue(staus: any) {
    switch (staus) {
      case 0:
        return "Đã tạo"; // Đã tạo
      case 1:
        return "Đã giao"; // Đã giao
      case 2:
        return "Đang xử lý"; // Đang xử lý
      case 3:
        return "Đã hoàn thành"; // Đã hoàn thành
      case 4:
        return "Đã đóng"; // Đã đóng
      default:
        return "Đã tạo";
    }
  }

  getColorStatusNameIssue(staus: any) {
    switch (staus) {
      case 0:
        return "btn-secondary-1"; // Đã tạo
      case 1:
        return "btn-primary-2"; // Đã giao
      case 2:
        return "btn-warning-1"; // Đang xử lý
      case 3:
        return "btn-success-1"; // Đã hoàn thành
      case 4:
        return "btn-danger-1"; // Đã đóng
      default:
        return "btn-secondary-1";
    }
  }

  getPriorityIssue(priority: any) {
    switch (priority) {
      case 1:
        return "Thấp"; // Thấp
      case 2:
        return "Trung bình"; // Trung bình
      case 3:
        return "Cao"; // Cao
      default:
        return "Trung bình";
    }
  }

  getColorPriorityIssue(priority: any) {
    switch (priority) {
      case 1:
        return "btn-primary-2"; // Thấp
      case 2:
        return "btn-warning-1"; // Trung bình
      case 3:
        return "btn-danger-1"; // Cao
      default:
        return "btn-warning-1";
    }
  }
  getTemplateTypeNameByCode(type: any) {
    switch (type) {
      case 1:
        return "Tin tư vấn";
      case 2:
        return "Tin giao dịch";
      case 3:
        return "Tin truyền thông";
      default:
        return "Tin tư vấn";
    }
  }
  getRoleByCode(role: any) {
    switch (role) {
      case "admin":
        return "Quản trị viên";
      case "user":
        return "Người dùng";
      default:
        return "";
    }
  }
  getRoleByCodeEn(role: any) {
    switch (role) {
      case "admin":
        return "Admin";
      case "user":
        return "User";
      default:
        return "";
    }
  }
  truncateString(str: string, maxLength: number): string {
    if (!str) return "";
    return str.length > maxLength ? str.slice(0, maxLength) + "..." : str;
  }
  getExpiredTime(endDate: any) {
    if(!endDate) return {
      text: '',
      color: ""
    }
    if (+this.tinhSoNgayConLai(endDate) < 0) {
      return {
        text: "Hết hạn",
        color: "text-danger fw-bold",
      };
    } else if (+this.tinhSoNgayConLai(endDate) === 0) {
      return {
        text: "Hết hạn hôm nay",
        color: "",
      };
    } else {
      return {
        text: "Còn " + this.tinhSoNgayConLai(endDate) + " ngày",
        color: "",
      };
    }
  }
  tinhSoNgayConLai(endDate: any) {
    const start = moment();
    const end = moment(endDate, 'DD/MM/YYYY');
    return end.diff(start, "days");
  }
  removeVietnameseTones(str: string): string {
    return str
      .normalize('NFD') // tách chữ và dấu
      .replace(/[\u0300-\u036f]/g, '') // xóa các ký tự dấu
      .replace(/đ/g, 'd')
      .replace(/Đ/g, 'D')
      .replace(/[^a-zA-Z0-9\s]/g, '') // loại bỏ ký tự đặc biệt (nếu muốn)
      .trim();
  }
}