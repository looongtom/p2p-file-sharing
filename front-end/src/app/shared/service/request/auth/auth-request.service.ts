import { Injectable } from "@angular/core";
import { ApiServices } from "../../api.services";
import { API_V1, OPERATIONS, USER_CONTROLLER } from "src/app/shared/common/constant";
import { HttpResponse } from "@angular/common/http";

@Injectable({ providedIn: 'root' })
export class AuthRequestServices { 
  constructor(
    private apiService: ApiServices
  ) {
    
  }
  login(payload: any) {
    return new Promise((resolve: any, reject: any) => {
      this.apiService.postOption(API_V1 + USER_CONTROLLER, payload, '/login').subscribe(
        (res: HttpResponse<any>) => {
          resolve(res)
        },
        (err) => {
          reject(err)
        }
      )
    })
  }
  create(payload: any) {
    return new Promise((resolve: any, reject: any) => {
      this.apiService
        .postOption(API_V1 + USER_CONTROLLER, payload, "/create")
        .subscribe(
          (res: HttpResponse<any>) => {
            resolve(res);
          },
          (err) => {
            reject(err);
          }
        );
    });
  }
  update(payload: any) {
    return new Promise((resolve: any, reject: any) => {
      this.apiService
        .put(API_V1 + USER_CONTROLLER, payload, "/update")
        .subscribe(
          (res: HttpResponse<any>) => {
            resolve(res);
          },
          (err) => {
            reject(err);
          }
        );
    });
  }
  search(params: any) {
    return new Promise((resolve: any, reject: any) => {
      this.apiService
        .getOption(API_V1 + USER_CONTROLLER, params, "/search")
        .subscribe(
          (res: HttpResponse<any>) => {
            resolve(res);
          },
          (err) => {
            reject(err);
          }
        );
    });
  }
  delete(id: any) {
    return new Promise((resolve: any, reject: any) => {
      this.apiService.delete(API_V1 + USER_CONTROLLER + OPERATIONS.DELETE , id)
      .subscribe(
        (res: HttpResponse<any>) => {
          resolve(res);
        },
        (err) => {
          reject(err);
        }
      );
    });
  }
  changeRole(payload: any) {
    return new Promise((resolve: any, reject: any) => {
      this.apiService
        .postOption(API_V1 + USER_CONTROLLER, payload, "/change-role")
        .subscribe(
          (res: HttpResponse<any>) => {
            resolve(res);
          },
          (err) => {
            reject(err);
          }
        );
    });
  }
  changePassword(payload: any) {
    return new Promise((resolve: any, reject: any) => {
      this.apiService
        .postOption(API_V1 + USER_CONTROLLER, payload, "/change-password")
        .subscribe(
          (res: HttpResponse<any>) => {
            resolve(res);
          },
          (err) => {
            reject(err);
          }
        );
    });
  }
  getAll() {
    return new Promise((resolve: any, reject: any) => {
      this.apiService.get(API_V1 + USER_CONTROLLER + "/get-all").subscribe(
        (res: HttpResponse<any>) => {
          resolve(res);
        },
        (err) => {
          reject(err);
        }
      );
    });
  }
  detail(id: any) {
    return new Promise((resolve: any, reject: any) => {
      this.apiService.get(API_V1 + USER_CONTROLLER + '/detail?id=' + id).subscribe(
        (res: HttpResponse<any>) => {
          resolve(res);
        },
        (err) => {
          reject(err);
        }
      );
    });
  }
}