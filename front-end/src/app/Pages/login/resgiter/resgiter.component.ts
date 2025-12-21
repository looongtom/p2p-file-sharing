import { Component } from "@angular/core";
import { FormBuilder, FormGroup, Validators } from "@angular/forms";
import { NgbActiveModal } from "@ng-bootstrap/ng-bootstrap";
import { AuthRequestServices } from "src/app/shared/service/request/auth/auth-request.service";
import { SpinnerService } from "src/app/shared/service/spinner.service";
import { ToastService } from "src/app/shared/service/toast.service";

@Component({
  selector: 'resgiter-popup',
  templateUrl: './resgiter.component.html',
  standalone: false
})
export class ResgiterPopupComponent {
  form: FormGroup;
  constructor(
    private fb: FormBuilder,
    private modal: NgbActiveModal,
    private toast: ToastService,
    private spinner: SpinnerService,
    private apiAuth: AuthRequestServices
  ) {
    this.form = this.fb.group({
      username: ["", {
        validators: [Validators.required],
        updateOn: 'change'
      }],
      password: ["", {
        validators: [Validators.required],
        updateOn: 'change'
      }],
    })
  }
  closeModal(isReturn = null) {
    this.modal.close(isReturn)
  }
  submitForm() {
    const payload = {
      ...this.form.value
    }
    this.apiAuth.create(payload).then((res: any) => {
      console.log('res :>> ', res);
      this.toast.success('Resgiter successfull')
      this.closeModal(true)
    })
  }
}