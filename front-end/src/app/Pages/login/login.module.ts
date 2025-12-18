import { NgModule } from '@angular/core';

// User Pages Components

import { LoginComponent } from './login.component';
import { SharedModule } from 'src/app/shared.module';

@NgModule({
  declarations: [
    LoginComponent
  ],
  imports: [
    SharedModule
  ],
  exports: [
    LoginComponent
  ]
})
export class LoginModule { }