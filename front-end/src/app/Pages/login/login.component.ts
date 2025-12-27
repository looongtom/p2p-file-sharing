import { Component, OnInit } from '@angular/core';
import { FormGroup, NonNullableFormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthRequestServices } from 'src/app/shared/service/request/auth/auth-request.service';
import { SpinnerService } from 'src/app/shared/service/spinner.service';
import { ToastService } from 'src/app/shared/service/toast.service';
import { ResgiterPopupComponent } from './resgiter/resgiter.component';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: "app-login",
  templateUrl: "./login.component.html",
  standalone: false,
  styles: [],
})
export class LoginComponent implements OnInit {
  form: FormGroup;
  constructor(
    private router: Router,
    private fb: NonNullableFormBuilder,
    private apiAuth: AuthRequestServices,
    private spinner: SpinnerService,
    private toast: ToastService,
    private modalService: NgbModal
  ) {
    this.form = this.fb.group({
      username: [
        "",
        {
          validators: [Validators.required],
          updateOn: "change",
        },
      ],
      password: [
        "",
        {
          validators: [Validators.required],
          updateOn: "change",
        },
      ],
    });
  }
  ngOnInit(): void {
    localStorage.clear()
  }
  onSubmit() {
    const payload = {
      ...this.form.value
    }
    this.apiAuth.loginV1(payload).then((res: any) => {
      if(res.ok) {
        const basicAuth = btoa(`${payload.username}:${payload.password}`);
        console.log('res :>> ', res);
        this.toast.success('Login successfull')
        localStorage.setItem("token", basicAuth);
        localStorage.setItem("user", JSON.stringify(this.form.value));
        localStorage.setItem('username', res.username)
        this.router.navigate(["/uploaded-file"]);
      }
    })
  }
  openResgiterPopup() {
    const modal = this.modalService.open(ResgiterPopupComponent, {
      centered: true,
      size: "md",
      backdrop: "static",
      keyboard: false,
    });
  }
}
