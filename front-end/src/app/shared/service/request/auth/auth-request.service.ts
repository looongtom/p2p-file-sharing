import { Injectable } from "@angular/core";
import { ApiServices } from "../../api.services";
import { API_V1, OPERATIONS } from "src/app/shared/common/constant";
import { HttpClient, HttpHeaders, HttpResponse } from "@angular/common/http";
import { environment } from "src/environments/environment";

@Injectable({ providedIn: 'root' })
export class AuthRequestServices { 
  constructor(
    private apiService: ApiServices,
    private http: HttpClient
  ) {
    
  }
  private get base_url(): string {
    const port = window.location.port;

    if (port === '4200') return 'http://127.0.0.1:5001/';
    if (port === '4201') return 'http://127.0.0.1:5002/';
    if (port === '4202') return 'http://127.0.0.1:5003/';

    const url = environment.BASE_API || 'http://127.0.0.1:5001/';
    return url.endsWith('/') ? url : (url + '/');
  }
  login(payload: any) {
    return new Promise((resolve: any, reject: any) => {
      this.apiService.postOption(API_V1 , payload, '/login').subscribe(
        (res: HttpResponse<any>) => {
          resolve(res)
        },
        (err) => {
          reject(err)
        }
      )
    })
  }
  loginV1(payload: any) {
    const basicAuth = btoa(`${payload.username}:${payload.password}`);

    const headers = new HttpHeaders({
      Authorization: `Basic ${basicAuth}`
    });

    return this.http.post(
      this.base_url + API_V1 + '/login',
      {},
      { headers }
    ).toPromise()
  }
  create(payload: any) {
    return new Promise((resolve: any, reject: any) => {
      this.apiService
        .postOption(API_V1 , payload, "/register")
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
        .put(API_V1 , payload, "/update")
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
        .getOption(API_V1 , params, "/search")
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
      this.apiService.delete(API_V1  + OPERATIONS.DELETE , id)
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
        .postOption(API_V1 , payload, "/change-role")
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
        .postOption(API_V1 , payload, "/change-password")
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
      this.apiService.get(API_V1  + "/get-all").subscribe(
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
      this.apiService.get(API_V1  + '/detail?id=' + id).subscribe(
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