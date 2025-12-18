import { NgModule } from "@angular/core";
import { BaseChartDirective } from "ng2-charts";
import { DashboardHomeComponent } from "./dashboard.component";
import { SharedModule } from "src/app/shared.module";

// Dashboard Components

@NgModule({
  declarations: [DashboardHomeComponent],
  imports: [SharedModule, BaseChartDirective],
  exports: [DashboardHomeComponent],
})
export class DashboardHomeModule {}
