import { Component, OnDestroy, OnInit } from "@angular/core";
import { NgbModal } from "@ng-bootstrap/ng-bootstrap";
import { FileRequestServices } from "src/app/shared/service/request/file/file-request.service";
import { ShareService } from "src/app/shared/service/shareService.service";
import { SpinnerService } from "src/app/shared/service/spinner.service";
import { ToastService } from "src/app/shared/service/toast.service";

@Component({
  selector: 'danh-sach-file',
  templateUrl: './danh-sach-file.component.html',
  standalone: false,
})
export class DanhSachFileComponent implements OnInit, OnDestroy {
  page = 1
  size = 9999
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
  interval: any
  constructor(
    private modalService: NgbModal,
    public svShare: ShareService,
    private spinner: SpinnerService,
    private toast: ToastService,
    private fileRequestService: FileRequestServices
  ) {
    
  }
  ngOnInit(): void {
    this.interval = setInterval(() => {
      this.getListFile()
    }, 5000)
  }
  ngOnDestroy(): void {
    if (this.interval) {
      clearInterval(this.interval)
    }
  }
  getListFile() {
    this.spinner.show()
    this.fileRequestService.get().then((res: any) => {
      if(res.status === 200) {
        this.listDatas = res.body.items
      }
    }).finally(() => {
      this.spinner.hide()
    })
  }
  downloadFile(item: any) {
    const payload = {
      filename: item.filename
    }
    this.spinner.show()
    this.fileRequestService.download(payload).then((res: any) => {
      if(res.status === 200) {
        this.toast.success(res.body.message || 'Download initiated successfully')
      }
    })
    .finally(() => {
      this.spinner.hide()
    })
  }
}