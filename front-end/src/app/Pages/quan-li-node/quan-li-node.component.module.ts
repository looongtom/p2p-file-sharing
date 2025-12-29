import { NgModule } from "@angular/core";
import { SharedModule } from "src/app/shared.module";
import { CommonModule } from "@angular/common";
import { QuanLiNodeComponent } from "./quan-li-node.component";

@NgModule({
  declarations: [
    QuanLiNodeComponent
  ],
  imports: [
    SharedModule,
    CommonModule
  ],
  exports: [
    QuanLiNodeComponent
  ]
})
export class QuanLiNodeModule {}