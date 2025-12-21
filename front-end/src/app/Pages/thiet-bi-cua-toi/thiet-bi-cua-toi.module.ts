import { NgModule } from "@angular/core";
import { ThietBiCuaToiComponent } from "./thiet-bi-cua-toi.component";
import { SharedModule } from "src/app/shared.module";
import { CommonModule } from "@angular/common";

@NgModule({
  declarations: [
    ThietBiCuaToiComponent
  ],
  imports: [
    SharedModule,
    CommonModule
  ],
  exports: [
    ThietBiCuaToiComponent
  ]
})
export class ThietBiCuaToiModule {}