import { Component } from "@angular/core";
import { SpinnerService } from "src/app/shared/service/spinner.service";

@Component({
  selector: "app-spinner",
  templateUrl: "./spinner.component.html",
  styleUrls: ["./spinner.component.scss"],
  standalone: false
})
export class SpinnerComponent {
  constructor(public spinner: SpinnerService) {}
}
