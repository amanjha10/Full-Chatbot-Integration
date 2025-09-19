import { Suspense } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import { ErrorBoundary } from "../components/ErrorBoundries";
import { IoChatbubbleEllipsesSharp } from "react-icons/io5";
import { useAuth } from "../store/AuthStore";

export default function AppLayout() {
  const navigate = useNavigate();
  const context = useAuth();
  const { pathname } = useLocation();
  // const isValidPath = pathname == "/app/chat";

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col">
      <div className="sticky top-0 z-50">
 <Navbar />
      </div>
     
      <div className="px-4 xl:px-0 flex-1 pb-8" style={{ background: "linear-gradient(to bottom right, #efefef, #f5f5f5)" }}>
        <div className="max-w-[1020px] xl:max-w-[1300px] mx-auto">
          <ErrorBoundary>
            <Suspense fallback="Loading...">
              <Outlet />
            </Suspense>
          </ErrorBoundary>
        </div>
      </div>

      {context?.role === "AGENT" ? null : (
        <div
          onClick={() => navigate("/app/chat")}
          className="cursor-pointer flex items-center justify-center w-[50px] h-[50px] bg-purple fixed rounded-full bottom-3 right-3"
          style={{ boxShadow: "0px 4px 6px rgba(0,0,0,0.8)" }}
        >
          <IoChatbubbleEllipsesSharp size={35} className="text-white" />
        </div>
      )}
    </div>
  );
}
