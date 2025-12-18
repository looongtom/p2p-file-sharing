import { Component, OnInit } from '@angular/core';
import { FormGroup, NonNullableFormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthRequestServices } from 'src/app/shared/service/request/auth/auth-request.service';
import { SpinnerService } from 'src/app/shared/service/spinner.service';
import { ToastService } from 'src/app/shared/service/toast.service';

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
    private toast: ToastService
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
    this.router.navigate(["/"]);
  }
}
