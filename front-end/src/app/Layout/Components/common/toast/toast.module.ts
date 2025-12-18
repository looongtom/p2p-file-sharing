import { CommonModule } from "@angular/common";
import { NgModule } from "@angular/core";
import { SharedModule } from "src/app/shared.module";
import { ToastComponent } from "./toast.component";

@NgModule({
  declarations: [ToastComponent],
  imports: [SharedModule, CommonModule],
  exports: [ToastComponent]
})
export class ToastModule {}