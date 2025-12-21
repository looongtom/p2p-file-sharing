import { Injectable } from "@angular/core";
import { ApiServices } from "../../api.services";
import { HttpClient } from "@angular/common/http";
import { API_V1 } from "src/app/shared/common/constant";

@Injectable({ providedIn: 'root' })
export class FileRequestServices { 
  constructor(
    private apiService: ApiServices,
    private http: HttpClient
  ) {
    
  }
  get() {
    return new Promise((resolve: any, reject: any) => {
      this.apiService.getOption(API_V1 + '/torrent/list', {}, '').subscribe(
        (res: any) => {
          resolve(res)
        },
        (err) => {
          reject(err)
        }
      )
    })
  }
  upload(formData: FormData) {
    return new Promise((resolve: any, reject: any) => {
      this.apiService.uploadFile(API_V1 + '/torrent/send', formData).subscribe(
        (res: any) => {
          resolve(res)
        },
        (err) => {
          reject(err)
        }
      )
    })
  }
  download(params) {
    return new Promise((resolve: any, reject: any) => {
      this.apiService.postOption(API_V1 + '/torrent/download', params, '').subscribe(
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