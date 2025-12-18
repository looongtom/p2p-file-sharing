import { Component } from "@angular/core";
import { ToastService } from "src/app/shared/service/toast.service";

@Component({
  selector: "toast-container",
  templateUrl: "./toast.component.html",
  styleUrls: ['toast.component.scss'],
  host: { class: 'toast-container position-fixed top-0 end-0 p-3', style: 'z-index: 1200' },
  standalone: false,
})
export class ToastComponent {
  constructor(public toastService: ToastService) {}
}