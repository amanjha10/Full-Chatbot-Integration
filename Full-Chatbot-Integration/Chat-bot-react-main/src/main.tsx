import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App as AntdApp } from "antd";
import "./index.css";
import App from "./App.tsx";
import AppProvider from "./components/AppProvider.tsx";
import AuthContextProvider from "./store/AuthStore.tsx";
import CompanyProvider from "./context-provider/CompanyProvider.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AntdApp>
      <AuthContextProvider>
        <CompanyProvider>
          <AppProvider>
            <App />
          </AppProvider>
        </CompanyProvider>
      </AuthContextProvider>
    </AntdApp>
  </StrictMode>
);
