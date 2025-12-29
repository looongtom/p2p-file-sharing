import { Injectable } from "@angular/core";
import { ApiServices } from "../../api.services";
import { HttpClient } from "@angular/common/http";
import { API_V1 } from "src/app/shared/common/constant";

@Injectable({ providedIn: 'root' })
export class NodeRequestService { 
  constructor(
    private apiService: ApiServices,
    private http: HttpClient
  ) {
    
  }
  get() {
    return new Promise((resolve: any, reject: any) => {
      this.apiService.get(API_V1 + '/nodes/connected').subscribe(
        (res: any) => {
          resolve(res)
        },
        (err) => {
          reject(err)
        }
      )
    })
  }
}