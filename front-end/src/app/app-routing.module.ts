import {NgModule} from '@angular/core';
import {Routes, RouterModule} from '@angular/router';

import {BaseLayoutComponent} from './Layout/base-layout/base-layout.component';
import {PagesLayoutComponent} from './Layout/pages-layout/pages-layout.component';

// Import all components from barrel file
import {
  // Dashboard components
  LoginComponent,
  DashboardHomeComponent
} from './components.barrel';
import { UserRouteAccessService } from './user-route-access-service';
import { DanhSachFileComponent } from './Pages/danh-sach-file/danh-sach-file.component';
import { ThietBiCuaToiComponent } from './Pages/thiet-bi-cua-toi/thiet-bi-cua-toi.component';
import { QuanLiNodeComponent } from './Pages/quan-li-node/quan-li-node.component';

const routes: Routes = [
  {
    path: "login",
    component: LoginComponent,
  },
  {
    path: "",
    component: BaseLayoutComponent,
    canActivate: [UserRouteAccessService],
    children: [
      { path: "", redirectTo: "/available-file-sharing", pathMatch: "full" },
      {
        path: "available-file-sharing",
        component: DanhSachFileComponent,
        data: { extraParameter: "" },
      },
      {
        path: "uploaded-file",
        component: ThietBiCuaToiComponent,
        data: { extraParameter: "" },
      },
      {
        path: "nodes",
        component: QuanLiNodeComponent,
        data: { extraParameter: "" },
      },
    ],
  },
];

@NgModule({
  imports: [RouterModule.forRoot(routes, {
    scrollPositionRestoration: 'enabled',
    anchorScrolling: 'enabled'
  })],
  exports: [RouterModule]
})
export class AppRoutingModule {
}