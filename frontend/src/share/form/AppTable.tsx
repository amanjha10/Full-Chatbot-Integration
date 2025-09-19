import { Table, type TableProps, type TableColumnType } from "antd";
interface AppTableProps<T> extends TableProps<T> {
  total?: number;
  paginationData?: number;
  handlePagination?: (pagination: number) => void;
  dataSource: T[];
  columns: TableColumnType<T>[];
  loading?: boolean;
  rowSelection?: TableProps<T>["rowSelection"];
  rowKey?: string;
}
export default function AppTable<T extends TableProps>({
  dataSource,
  columns,
  loading,
  rowSelection,
  rowKey = "id",
  total,
  paginationData,
  handlePagination,
}: AppTableProps<T>) {
  return (
    <Table
      dataSource={dataSource}
      columns={columns}
      pagination={
        paginationData && total !== null
          ? {
              total,
              current: paginationData,
              showSizeChanger: false,
              onChange: (page) => {
                handlePagination?.(page);
              },
            }
          : false
      }
      loading={loading}
      rowKey={rowKey}
      scroll={{ x: "max-content" }}
      rowSelection={rowSelection}
    />
  );
}
