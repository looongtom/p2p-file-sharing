export const STATUS_LIST = [
  {
    code: "ON_HOLD",
    name: "On hold",
  },
  {
    code: "IN_PROGRESS",
    name: "In progress",
  },
  {
    code: "COMPLETED",
    name: "Completed",
  },
  {
    code: "CANCELED",
    name: "Canceled",
  },
];
export const STATUS = {
  ON_HOLD: "ON_HOLD",
  IN_PROGRESS: "IN_PROGRESS",
  COMPLETED: "COMPLETED",
  CANCELED: "CANCELED"
};
export const LOG_WORK_STATUS = {
  INVALID: "INVALID",
  VALID: "VALID",
  EXPLANATION: "EXPLANATION"
}
export const OPERATIONS = {
  DELETE: "/delete",
  SEARCH: "/search",
  UPDATE: "/update",
  DETAILS: "/details",
  CREATE: "/create",
  ADD: "/add",
  UPLOAD: "/upload",
  DOWNLOAD: "/download",
  UPDATELOGO: "/updatelogo",
};

export const ROLE = {
  USER: 'USER',
  ADMIN: 'ADMIN'
}

export const TYPE_TEMPLATE_LIST = [
  {
    type: 1,
    code: "text",
    name: "Tin tư vấn"
  },
  {
    type: 2,
    code: "transaction_order",
    name: "Tin giao dịch",
  },
  {
    type: 3,
    code: "promotion",
    name: "Tin truyền thông",
  }
]
export const TYPE_TEMPLATE_LIST_INT = [
  {
    code: 1,
    name: "Tin tư vấn",
  },
  {
    code: 2,
    name: "Tin giao dịch",
  },
  {
    code: 3,
    name: "Tin truyền thông",
  },
];
export const TYPE_TEMPLATE = {
  TEXT: "text",
  TRANSACTION_ORDER: "transaction_order",
  PROMOTION: "promotion"
}
export const TYPE_TEMPLATE_INT = {
  TEXT: 1,
  TRANSACTION_ORDER: 2,
  PROMOTION: 3,
};

export const API_V1 = "api/v1/"
export const ZALO_VER = "v2.0/"
export const ZALO_VER_03 = "v3.0/"
export const ZALO_OA = "oa"
export const USER_CONTROLLER = "user"
export const COMPANY_CONTROLLER = "company"
export const DEPARTMENT_CONTROLLER = "department"
export const CUSTOMER_CONTROLLER = "customer"
export const TEMPLATE_COMTROLLER = "template"
export const WORK_CONTROLLER = "work"
export const ISSUE_CONTROLLER = "issue"
export const COMMENT_CONTROLLER = "comment"
