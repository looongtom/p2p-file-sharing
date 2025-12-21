import { NgModule } from '@angular/core';

// User Pages Components

import { LoginComponent } from './login.component';
import { SharedModule } from 'src/app/shared.module';
import { ResgiterPopupComponent } from './resgiter/resgiter.component';

@NgModule({
  declarations: [
    LoginComponent,
    ResgiterPopupComponent
  ],
  imports: [
    SharedModule
  ],
  exports: [
    LoginComponent,
    ResgiterPopupComponent
  ]
})
export class LoginModule { }