import { CommonModule } from "@angular/common";
import { NgModule } from "@angular/core";
import { SharedModule } from "src/app/shared.module";
import { DeleteConfirmModal } from "./delete-cofirm-modal.component";

@NgModule({
  declarations: [DeleteConfirmModal],
  imports: [SharedModule, CommonModule],
  exports: [DeleteConfirmModal],
})
export class DeleteConfirmModalModule {}
