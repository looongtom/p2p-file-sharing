import {NgModule} from '@angular/core';
import {Routes, RouterModule} from '@angular/router';

import {BaseLayoutComponent} from './Layout/base-layout/base-layout.component';
import {PagesLayoutComponent} from './Layout/pages-layout/pages-layout.component';

// Import all components from barrel file
import {
  // Dashboard components
  AnalyticsComponent,
  
  // Elements components
  StandardComponent,
  DropdownsComponent,
  CardsComponent,
  ListGroupsComponent,
  TimelineComponent,
  IconsComponent,
  
  // Components
  AccordionsComponent,
  TabsComponent,
  CarouselComponent,
  ModalsComponent,
  PaginationComponent,
  ProgressBarComponent,
  TooltipsPopoversComponent,
  
  // Form components
  ControlsComponent,
  LayoutComponent,
  
  // Table components
  RegularComponent,
  TablesMainComponent,
  
  // Widget components
  ChartBoxes3Component,
  
  // User pages components
  ForgotPasswordBoxedComponent,
  LoginBoxedComponent,
  RegisterBoxedComponent,

  // Chart components  
  ChartjsComponent,
  LoginComponent,
  DashboardHomeComponent
} from './components.barrel';
import { UserRouteAccessService } from './user-route-access-service';

const routes: Routes = [
  {
    path: "login",
    component: LoginComponent,
  },
  {
    path: "",
    component: BaseLayoutComponent,
    children: [
      { path: "", redirectTo: "/dashboard", pathMatch: "full" },
      {
        path: "dashboard",
        component: DashboardHomeComponent,
        data: { extraParameter: "dashboard" },
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