import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { HttpClient, HttpResponse, HTTP_INTERCEPTORS } from '@angular/common/http';
import { environment } from 'src/environments/environment';
import { OPERATIONS } from '../common/constant';
import { createRequestOption } from '../common/request';

@Injectable({ providedIn: 'root' })
export class ApiServices {
  constructor(protected http: HttpClient) {}
  private get base_url(): string {
    const port = window.location.port;
    switch (port) {
      case '4200':
        return 'http://127.0.0.1:5001/';
      case '4201':
        return 'http://127.0.0.1:5002/';
      case '4202':
        return 'http://127.0.0.1:5003/';
      case '4203':
        return 'http://127.0.0.1:5004/';
      case '4204':
        return 'http://127.0.0.1:5005/';
      case '4205':
        return 'http://127.0.0.1:5006/';
      case '4206':
        return 'http://127.0.0.1:5007/';
      case '4207':
        return 'http://127.0.0.1:5008/';
      case '4208':
        return 'http://127.0.0.1:5009/';
      case '4209':
        return 'http://127.0.0.1:5010/';
      case '4210':
        return 'http://127.0.0.1:5011/';
      case '4211':
        return 'http://127.0.0.1:5012/';
      case '4212':
        return 'http://127.0.0.1:5013/';
      case '4213':
        return 'http://127.0.0.1:5014/';
      case '4214':
        return 'http://127.0.0.1:5015/';
      case '4215':
        return 'http://127.0.0.1:5016/';
      
      default:
        return 'http://127.0.0.1:5001/';
    }
  }
  create(request: any, entity: any): Observable<HttpResponse<any>> {
    return this.http.post<any>(
      this.base_url + request + OPERATIONS.CREATE,
      entity,
      { observe: 'response' }
    );
  }
  update(request: any, entity: any): Observable<HttpResponse<any>> {
    return this.http.put<any>(
      this.base_url + request + OPERATIONS.UPDATE + '?id=' + entity.id,
      entity,
      {
        observe: 'response',
      }
    );
  }
  get(requestUrl: any): Observable<HttpResponse<any>> {
    return this.http.get<any>(this.base_url + requestUrl, {
      observe: 'response',
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

  getOptionWithHeaders(
    requestUrl: any,
    params: any,
    option: any,
    headers : any
  ): Observable<HttpResponse<any>> {
    const options = createRequestOption(params);
    return this.http.get<any>(this.base_url + requestUrl + option, {
      headers: headers,
      params: options,
      observe: 'response',
    });
  }

  put(
    requestUrl: any,
    entity: any,
    option: any
  ): Observable<HttpResponse<any>> {
    return this.http.put<any>(this.base_url + requestUrl + option, entity, {
      observe: 'response',
    });
  }
  post(requestUrl: any, option: any): Observable<HttpResponse<any>> {
    return this.http.post<any>(this.base_url + requestUrl + option, {
      observe: 'response',
    });
  }
  postOptionWithHeaders(
    requestUrl: any,
    entity: any,
    option: any,
    header: any
  ): Observable<HttpResponse<any>> {
    return this.http.post<any>(this.base_url + requestUrl + option, entity, {
      observe: 'response',
      headers: header,
    });
  }

  postOption(
    requestUrl: any,
    entity: any,
    option: any
  ): Observable<HttpResponse<any>> {
    return this.http.post<any>(this.base_url + requestUrl + option, entity, {
      observe: 'response',
    });
  }
  delete(requestUrl: any, id: number): Observable<HttpResponse<{}>> {
    return this.http.delete(`${this.base_url + requestUrl + '?id='}${id}`, {
      observe: 'response',
    });
  }
  deleteOption(requestUrl: any, id: number): Observable<HttpResponse<{}>> {
    return this.http.delete(`${this.base_url + requestUrl + id}`, {
      observe: 'response',
    });
  }
  query(requestUrl: any, req: any): Observable<HttpResponse<any>> {
    const options = createRequestOption(req);
    return this.http.get<any>(this.base_url + requestUrl + OPERATIONS.SEARCH, {
      params: options,
      observe: 'response',
    });
  }
  uploadFile(requestUrl: any, file: any): Observable<HttpResponse<any>> {
    return this.http.post<any>(this.base_url + requestUrl, file, {
      observe: 'response',
    });
  }
}
