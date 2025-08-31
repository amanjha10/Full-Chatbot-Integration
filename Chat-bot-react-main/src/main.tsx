import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import AppProvider from "./components/AppProvider.tsx";
import AuthContextProvider from "./store/AuthStore.tsx";
import CompanyProvider from "./context-provider/CompanyProvider.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AuthContextProvider>
      <CompanyProvider>
        <AppProvider>
          <App />
        </AppProvider>
      </CompanyProvider>
    </AuthContextProvider>
  </StrictMode>
);
