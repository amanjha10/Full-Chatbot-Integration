import { Avatar, Button, Dropdown, type MenuProps } from "antd";
import { AiFillDashboard } from "react-icons/ai";
import { FaUsersGear } from "react-icons/fa6";
import { FaQuestionCircle } from "react-icons/fa";
import { MdSupportAgent } from "react-icons/md";
import { IoSettingsSharp } from "react-icons/io5";
import { useNavigate } from "react-router-dom";
import SpellLogo from "../assets/spell-bot.png";
import { useAuth } from "../store/AuthStore";
import { useEffect, useState } from "react";

export default function Navbar() {
  const context = useAuth();
  const navigate = useNavigate();
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    const now = new Date();
    const resetTime = new Date(now);
    resetTime.setHours(24, 0, 0, 0);
    setCountdown(Math.floor((resetTime.getTime() - now.getTime()) / 1000));

    const timer = setInterval(() => {
      setCountdown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatCountdown = (seconds: number) => {
    const h = String(Math.floor(seconds / 3600)).padStart(2, "0");
    const m = String(Math.floor((seconds % 3600) / 60)).padStart(2, "0");
    const s = String(seconds % 60).padStart(2, "0");
    return `${h}:${m}:${s}`;
  };

  const handleLogout = () => {
    localStorage.clear(), navigate("/login");
  };

  const items: MenuProps["items"] = [
    {
      key: "1",
      label: (
        <div className="border-b border-gray-300">
          <p>Profile</p>
        </div>
      ),
    },
    {
      key: "2",
      label: <div className="">Sign Out</div>,
      onClick: () => {
        handleLogout();
      },
    },
  ];

  const roleBaseNavlink = (role: string | null | undefined) => {
    switch (role) {
      case "SUPERADMIN":
        return (
          <div className="flex items-center gap-4">
            <Button
              type="primary"
              onClick={() => navigate("/super-admin/dashboard")}
              className="!bg-yellow !text-base !font-normal !h-10 hover:bg-[#667ee1]"
              icon={<AiFillDashboard size={20} />}
            >
              Dashboard
            </Button>
            <Button
              type="primary"
              onClick={() => navigate("/super-admin/plan")}
              className="!bg-yellow !text-base !font-normal !h-10"
              icon={<FaUsersGear size={20} />}
            >
              Plan
            </Button>
            <Button
              type="primary"
              onClick={() => navigate("/super-admin/company")}
              className="!bg-yellow !text-base !font-normal !h-10"
              icon={<MdSupportAgent size={20} />}
            >
              Company
            </Button>
            <Button
              type="primary"
              onClick={() => navigate("/super-admin/faq")}
              className="!bg-yellow !text-base !font-normal !h-10"
              icon={<FaQuestionCircle size={20} />}
            >
              FAQ
            </Button>
          </div>
        );
      case "ADMIN":
        return (
          <div className="flex items-center gap-4">
            <Button
              type="primary"
              onClick={() => navigate("/app/dashboard")}
              className="!bg-yellow !text-base !font-normal !h-10 hover:bg-[#667ee1]"
              icon={<AiFillDashboard size={20} />}
            >
              Dashboard
            </Button>
            <Button
              type="primary"
              onClick={() => navigate("/app/user-management")}
              className="!bg-yellow !text-base !font-normal !h-10"
              icon={<FaUsersGear size={20} />}
            >
              User Management
            </Button>
            <Button
              type="primary"
              onClick={() => navigate("/app/agent-management")}
              className="!bg-yellow !text-base !font-normal !h-10"
              icon={<MdSupportAgent size={20} />}
            >
              Manage Agent
            </Button>
            <Button
              type="primary"
              onClick={() => navigate("/app/company-faq")}
              className="!bg-yellow !text-base !font-normal !h-10"
              icon={<FaQuestionCircle size={20} />}
            >
              Company FAQ
            </Button>
            <Button
              type="primary"
              onClick={() => navigate("/app/settings")}
              className="!bg-yellow !text-base !font-normal !h-10"
              icon={<IoSettingsSharp size={20} />}
            >
              Chatbot Settings
            </Button>
          </div>
        );
    }
  };

  return (
    <div className="py-4 bg-purple">
      <div className="flex justify-between items-center max-w-[1020px] xl:max-w-[1300px] mx-auto">
        <img src={SpellLogo} alt="logo" className="w-[200px]" />
        {roleBaseNavlink(context?.role)}
        <div>
          <div className="flex items-center gap-3">
            {context?.role == "agent" && (
              <div className="flex items-center space-x-2">
                <div className="text-right">
                  <div className="text-xl font-bold text-white font-mono">
                    {formatCountdown(countdown)}
                  </div>
                  <div className="text-white font-normal text-sm">
                    Next Daily Reset
                  </div>
                </div>
              </div>
            )}
            <Dropdown menu={{ items }} placement="bottomLeft">
              <Avatar
                size={40}
                src="https://img.freepik.com/free-photo/young-bearded-man-with-striped-shirt_273609-5677.jpg"
                className="cursor-pointer"
              />
            </Dropdown>
            <p className="flex items-center gap-2 text-base font-semibold text-white">
              {context?.role == "SUPERADMIN"
                ? "super admin"
                : context?.role == "ADMIN"
                ? "admin"
                : "agent"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
