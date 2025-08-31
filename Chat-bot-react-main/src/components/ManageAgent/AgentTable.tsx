import { Button, Dropdown, Tag, type MenuProps } from "antd";
import type { ColumnsType } from "antd/es/table";
import { BsThreeDotsVertical } from "react-icons/bs";
import { FiPlus } from "react-icons/fi";
import AppTable from "../../share/form/AppTable";
import { IoEyeOutline } from "react-icons/io5";
import { RiResetLeftFill } from "react-icons/ri";
import { MdDeleteOutline } from "react-icons/md";
import useSWR from "swr";
interface AgentTableProps {
  handleOpenModal: () => void;
  handleOpenDeleteModal: () => void;
}

export default function AgentTable({
  handleOpenModal,
  handleOpenDeleteModal,
}: AgentTableProps) {
  const { data, isLoading } = useSWR("/admin-dashboard/list-agents/");
  const getItemMenu = (): MenuProps["items"] => [
    {
      label: "View",
      key: "1",
      icon: <IoEyeOutline size={17} />,
      onClick: () => {
        handleOpenModal();
      },
    },
    {
      label: "Reset Password",
      key: "2",
      icon: <RiResetLeftFill size={17} />,
      onClick: () => console.log("reset"),
    },
    {
      label: "Delete",
      key: "3",
      icon: <MdDeleteOutline size={17} />,
      danger: true,
      onClick: () => {
        handleOpenDeleteModal();
      },
    },
  ];

  const getTagColor = (tagName: string) => {
    switch (tagName) {
      case "AVAILABLE": {
        return "green"; // Green for available/online
      }
      case "BUSY": {
        return "orange"; // Yellow/Orange for busy
      }
      case "OFFLINE": {
        return "red"; // Red for offline
      }
      default:
        return "default";
    }
  };

  const columns: ColumnsType = [
    {
      title: "SN",
      render: ({ sn }) => <p>{sn}</p>,
    },
    {
      title: "Name",
      render: ({ name }) => <p>{name}</p>,
    },
    {
      title: "Email",
      render: ({ email }) => <p>{email}</p>,
    },
    {
      title: "Phone",
      render: ({ phone }) => <p>{phone}</p>,
    },
    {
      title: "Specialization",
      render: ({ specialization }) => <p>{specialization}</p>,
    },
    {
      title: "status",
      render: ({ status }) => <Tag color={getTagColor(status)}>{status}</Tag>,
    },
    {
      title: "Last Active",
      render: ({ formatted_last_active }) => <p>{formatted_last_active}</p>,
    },
    {
      width: 100,
      title: "Action",
      render: () => {
        return (
          <div>
            <Dropdown menu={{ items: getItemMenu() }} trigger={["click"]}>
              <BsThreeDotsVertical className="cursor-pointer" />
            </Dropdown>
          </div>
        );
      },
    },
  ];

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h6 className="font-bold text-xl">Agent Table</h6>
        <Button
          type="primary"
          className="!bg-yellow"
          icon={<FiPlus size={15} />}
          onClick={handleOpenModal}
        >
          Agent
        </Button>
      </div>
      <AppTable
        columns={columns}
        dataSource={data}
        pagination={false}
        loading={isLoading}
        rowKey="id"
      />
    </div>
  );
}
