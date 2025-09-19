import { Table } from "antd";
import {
  useColumnsPlan,
  type PlanTableRow,
} from "../../../TableColumns/useColumnsPlan";
import { useState } from "react";
import PlanViewModal from "./PlanViewModal";

interface PlanTableProps {
  data: PlanTableRow[];
  loading?: boolean;
  total: number;
  page: number;
  onPageChange: (page: number) => void;
}

export default function PlanTable({
  data,
  loading,
  total,
  page,
  onPageChange,
}: PlanTableProps) {
  const [viewRow, setViewRow] = useState<PlanTableRow | null>(null);
  const pageSize = 10;
  const columns = useColumnsPlan((row) => setViewRow(row), page, pageSize);

  return (
    <>
      <Table
        dataSource={data}
        columns={columns}
        loading={loading}
        pagination={{
          total,
          current: page,
          showSizeChanger: false,
          onChange: onPageChange,
        }}
        rowKey="id"
        scroll={{ x: "max-content" }}
      />
      {viewRow && (
        <PlanViewModal row={viewRow} onClose={() => setViewRow(null)} />
      )}
    </>
  );
}
