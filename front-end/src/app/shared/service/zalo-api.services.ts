import { HttpClient, HttpHeaders, HttpResponse } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { Observable } from "rxjs";
import { environment } from "src/environments/environment";
import { createRequestOption } from "../common/request";

@Injectable({ providedIn: "root" })
export class ApiZaloOAServices {
  public base_url = environment.ZALO_URL_API;
  token: any
  constructor(protected http: HttpClient) {
    this.token = localStorage.getItem('token')
  }
  get(requestUrl: any): Observable<HttpResponse<any>> {
    const headers = new HttpHeaders({
      access_token: this.token,
      "Access-Control-Allow-Origin": "*",
      'Skip-Auth': 'true',
    });
    return this.http.get<any>(this.base_url + requestUrl, {
      observe: "response",
      headers,
    });
  }
  getOption(
      requestUrl: any,
      params: any,
      option: any
    ): Observable<HttpResponse<any>> {
      const options = createRequestOption(params);
      return this.http.get<any>(this.base_url + requestUrl + option, {
        params: options,
        observe: 'response',
      });
    }
}