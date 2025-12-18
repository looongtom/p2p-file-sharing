import { Injectable } from "@angular/core";
import { ApiServices } from "../../api.services";
import {
  API_V1,
  COMPANY_CONTROLLER,
  DEPARTMENT_CONTROLLER,
  OPERATIONS,
  TEMPLATE_COMTROLLER,
  ZALO_OA,
  ZALO_VER,
  ZALO_VER_03,
} from "src/app/shared/common/constant";
import { HttpBackend, HttpClient, HttpHeaders, HttpResponse } from "@angular/common/http";
import { ApiZaloOAServices } from "../../zalo-api.services";
import { environment } from "src/environments/environment";

@Injectable({ providedIn: "root" })
export class ZaloOARequestServices {
  accessToken: any;
  private http: HttpClient;
  constructor(
    private zaloApiService: ApiZaloOAServices,
    private handler: HttpBackend,
    private apiService: ApiServices
  ) {
    this.http = new HttpClient(handler);
    this.accessToken = localStorage.getItem("zalo_access_token");
  }
  getConversation(userId: string) {
    const data = JSON.stringify({
      user_id: userId,
      offset: 0,
      count: 10,
    });

    const url =
      environment.ZALO_URL_API +
      ZALO_VER +
      ZALO_OA +
      `/conversation?data=${encodeURIComponent(data)}`;
    const headers = new HttpHeaders({
      access_token: this.accessToken,
    });

    return this.http.get(url, { headers }).toPromise();
  }
  messageTemplate(payload: any, type: any) {
    const headers = new HttpHeaders({
      access_token: this.accessToken,
      "Content-Type": "application/json",
    });
    return this.http
      .post(
        environment.ZALO_URL_API + ZALO_VER_03 + ZALO_OA + "/message/" + type,
        payload,
        { headers }
      )
      .toPromise();
  }
  uploadImage(file: any) {
    const formData: FormData = new FormData();
    formData.append("file", file);
    const headers = new HttpHeaders({
      access_token: this.accessToken,
    });
    return this.http
      .post(
        environment.ZALO_URL_API + ZALO_VER + ZALO_OA + "/upload/image",
        formData,
        { headers }
      )
      .toPromise();
  }
  messageText(payload: any) {
    const headers = new HttpHeaders({
      access_token: this.accessToken,
      "Content-Type": "application/json",
    });
    return this.http
      .post(
        environment.ZALO_URL_API + ZALO_VER_03 + ZALO_OA + "/message/cs",
        payload,
        { headers }
      )
      .toPromise();
  }
  search(params: any) {
    return new Promise((resolve: any, reject: any) => {
      this.apiService
        .getOption(API_V1 + TEMPLATE_COMTROLLER, params, "/search")
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
  create(payload: any) {
    return new Promise((resolve: any, reject: any) => {
      this.apiService
        .postOption(API_V1 + TEMPLATE_COMTROLLER, payload, "/create")
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
        .put(API_V1 + TEMPLATE_COMTROLLER, payload, "/update")
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
      this.apiService
        .delete(API_V1 + TEMPLATE_COMTROLLER + OPERATIONS.DELETE, id)
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
  getQuota(payload: any) {
    const headers = new HttpHeaders({
      access_token: this.accessToken,
      "Content-Type": "application/json",
    });
    return this.http
      .post(
        environment.ZALO_URL_API + ZALO_VER_03 + ZALO_OA + "/quota/message",
        payload,
        { headers }
      )
      .toPromise();
  }
  renderTemplate(params: any) {
    const headers = new HttpHeaders({
      access_token: this.accessToken,
      "Content-Type": "application/json",
      "Authorization": 'Bearer ' + localStorage.getItem("token")
    });
    return this.http.get(environment.BASE_API + API_V1 + TEMPLATE_COMTROLLER + "/render?customerId=" + params.customerId + "&templateId=" + params.templateId, { headers }).toPromise();
  }
}