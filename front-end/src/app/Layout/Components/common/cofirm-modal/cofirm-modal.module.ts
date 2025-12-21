import { CommonModule } from "@angular/common";
import { NgModule } from "@angular/core";
import { SharedModule } from "src/app/shared.module";
import { ConfirmModal } from "./cofirm-modal.component";

@NgModule({
  declarations: [ConfirmModal],
  imports: [SharedModule, CommonModule],
  exports: [ConfirmModal],
})
export class ConfirmModalModule {}
