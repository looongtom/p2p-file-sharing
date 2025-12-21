import { Component, OnInit } from "@angular/core";
import { NgbModal } from "@ng-bootstrap/ng-bootstrap";
import { FileRequestServices } from "src/app/shared/service/request/file/file-request.service";
import { ShareService } from "src/app/shared/service/shareService.service";
import { SpinnerService } from "src/app/shared/service/spinner.service";
import { ToastService } from "src/app/shared/service/toast.service";

@Component({
  selector: 'thiet-bi-cua-toi',
  templateUrl: './thiet-bi-cua-toi.component.html',
  standalone: false,
})
export class ThietBiCuaToiComponent implements OnInit {
  page = 1
  size = 10
  totalItems = 0
  name: any
  taxCode: any
  address: any
  phone: any
  headers: any[] = [
    {
      name: "Index",
      key: "index",
      class: "",
      style: "width: 50px",
    },
    {
      name: "File Name",
      key: "index",
      class: "",
      style: "width: 300px",
    },
    {
      name: "Size",
      key: "phone",
      class: "",
      style: "width: 150px; max-width: 200px",
    },
    {
      name: "Number of Seeds",
      key: "companyName",
      class: "",
      style: "width: 100px",
    },
  ];
  listDatas: any[] = [
  ];
  constructor(
    private modalService: NgbModal,
    public svShare: ShareService,
    private spinner: SpinnerService,
    private toast: ToastService,
    private fileRequestService: FileRequestServices
  ) {
    
  }
  ngOnInit(): void {
    this.getListFile()
  }
  getListFile() {
    this.spinner.show()
    this.fileRequestService.get().then((res: any) => {
      if(res.status === 200) {
        this.listDatas = res.body.items
      }
    })
    .finally(() => {
      this.spinner.hide()
    })
  }
  uploadFile() {
    const input = document.createElement('input')
    input.type = 'file'
    input.onchange = async (event: any) => {
      const file = event.target.files[0]
      if(!file) return
      const formData = new FormData()
      formData.append('file', file)
      this.spinner.show()
      this.fileRequestService.upload(formData).then((res: any) => {
        if(res.status === 200) {
          console.log('res :>> ', res);
          this.toast.success(res.body.message || 'Upload file successfully')
          this.getListFile()
        } else {
          this.toast.error('Upload file failed')
        }
      })
      .finally(() => {
        this.spinner.hide()
      })
    }
    input.click()
  }
}