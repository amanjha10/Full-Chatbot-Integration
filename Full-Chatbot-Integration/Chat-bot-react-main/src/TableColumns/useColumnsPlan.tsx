import type { TableColumnType } from "antd";

export interface PlanTableRow {
  id: number;
  plan_name: string;
  plan_name_display: string;
  price: number;
  max_agents: number;
  company_name: string;
  created_at: string;
  expiry_date?: string;
  notes?: string;
  history?: PlanTableRow[];
}

export function useColumnsPlan(
  onActionClick: (row: PlanTableRow) => void,
  currentPage: number = 1,
  pageSize: number = 10
): TableColumnType<PlanTableRow>[] {
  return [
    {
      title: "S.N",
      dataIndex: "sn",
      key: "sn",
      render: (_: unknown, __: PlanTableRow, idx: number) =>
        (currentPage - 1) * pageSize + idx + 1,
    },
    {
      title: "Plan ID",
      dataIndex: "id",
      key: "id",
    },
    {
      title: "Company Name",
      dataIndex: "company_name",
      key: "company_name",
    },
    {
      title: "Plan",
      dataIndex: "plan_name_display",
      key: "plan_name_display",
    },
    {
      title: "Plan Price",
      dataIndex: "price",
      key: "price",
      render: (price: number) => `$${price}`,
    },
    {
      title: "Max Agent",
      dataIndex: "max_agents",
      key: "max_agents",
    },
    {
      title: "Action",
      key: "action",
      render: (_: unknown, row: PlanTableRow) => (
        <button
          onClick={() => onActionClick(row)}
          style={{ background: "none", border: "none", cursor: "pointer" }}
        >
          <span style={{ fontSize: 20 }}>⋮</span>
        </button>
      ),
    },
  ];
}
