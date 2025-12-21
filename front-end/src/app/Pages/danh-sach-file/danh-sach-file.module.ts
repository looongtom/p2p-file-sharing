import { NgModule } from "@angular/core";
import { DanhSachFileComponent } from "./danh-sach-file.component";
import { SharedModule } from "src/app/shared.module";
import { CommonModule } from "@angular/common";

@NgModule({
  declarations: [
    DanhSachFileComponent
  ],
  imports: [SharedModule, CommonModule],
  exports: [DanhSachFileComponent]
})
export class DanhSachFileModule {}