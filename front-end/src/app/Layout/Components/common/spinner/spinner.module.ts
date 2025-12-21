import { CommonModule } from "@angular/common";
import { NgModule } from "@angular/core";
import { SharedModule } from "src/app/shared.module";
import { SpinnerComponent } from "./spinner.component";

@NgModule({
  declarations: [SpinnerComponent],
  imports: [SharedModule, CommonModule],
  exports: [SpinnerComponent],
})
export class SpinnerModule {}
