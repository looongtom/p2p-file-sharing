import {Component, OnInit} from '@angular/core';
import {ThemeOptions} from '../../../../../theme-options';
import { AuthRequestServices } from 'src/app/shared/service/request/auth/auth-request.service';
import { ShareService } from 'src/app/shared/service/shareService.service';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: "app-user-box",
  templateUrl: "./user-box.component.html",
  standalone: false,
})
export class UserBoxComponent implements OnInit {
  infoUser: any;
  constructor(
    public globals: ThemeOptions,
    private apiUser: AuthRequestServices,
    public svShare: ShareService,
    private modalService: NgbModal
  ) {}

  ngOnInit() {
    const user = JSON.parse(localStorage.getItem("infoUser") || "{}");
    const userId = user && user.id ? user.id : null;
    if (userId) {
      this.getDetailUser(userId);
    }
  }
  getDetailUser(userId) {
    this.apiUser
      .detail(userId)
      .then((res: any) => {
        if (res && res.body && res.body.code === 200) {
          this.infoUser = {
            ...res.body.result,
            avatar: res.body.result.avatar
              ? "data:image/jpeg;base64," + res.body.result.avatar
              : "../../../../assets/images/user/user.png",
          };
        } else {
          this.infoUser = null;
        }
      })
      .catch(() => {
        this.infoUser = null;
      });
  }
}
