import { Component, Input } from "@angular/core";

@Component({
  selector: 'view-image',
  templateUrl: './view-image.component.html',
  standalone: false,
})
export class ViewImageModal {
  @Input() src: any
}