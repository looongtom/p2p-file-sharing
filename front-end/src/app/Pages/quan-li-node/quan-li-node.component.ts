import { Component, OnInit } from "@angular/core";
import { NgbModal } from "@ng-bootstrap/ng-bootstrap";
import { FileRequestServices } from "src/app/shared/service/request/file/file-request.service";
import { NodeRequestService } from "src/app/shared/service/request/node/node-request.service";
import { ShareService } from "src/app/shared/service/shareService.service";
import { SpinnerService } from "src/app/shared/service/spinner.service";
import { ToastService } from "src/app/shared/service/toast.service";

@Component({
  selector: 'quan-li-node',
  templateUrl: './quan-li-node.component.html',
  standalone: false
})
export class QuanLiNodeComponent implements OnInit{
  page = 1
  size = 10
  totalItems = 0
  name: any
  taxCode: any
  address: any
  phone: any
  headers: any[] = [
    {
      name: "Node ID",
      key: "index",
      class: "",
      style: "width: 50px",
    },
    {
      name: "Host",
      key: "index",
      class: "",
      style: "width: 300px",
    },
    {
      name: "Port",
      key: "phone",
      class: "",
      style: "width: 150px; max-width: 200px",
    },
  ];
  listDatas: any[] = [
  ];
  constructor(
    private modalService: NgbModal,
    public svShare: ShareService,
    private spinner: SpinnerService,
    private toast: ToastService,
    private nodeApi: NodeRequestService
  ) {
    
  }
  ngOnInit(): void {
    this.getListFile()
  }
  getListFile() {
    this.spinner.show()
    this.nodeApi.get().then((res: any) => {
      if(res.body.ok) {
        this.listDatas = res.body.connected_nodes
      }
    })
    .finally(() => this.spinner.hide())
  }
}