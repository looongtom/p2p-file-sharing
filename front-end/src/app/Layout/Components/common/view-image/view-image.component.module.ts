import { CommonModule } from "@angular/common";
import { NgModule } from "@angular/core";
import { SharedModule } from "src/app/shared.module";
import { ViewImageModal } from "./view-image.component";

@NgModule({
  declarations: [ViewImageModal],
  imports: [SharedModule, CommonModule],
  exports: [ViewImageModal],
})
export class ViewImageModalModule {}
