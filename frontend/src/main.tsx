import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { JumpProvider } from "./jump";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <JumpProvider>
        <App />
      </JumpProvider>
    </BrowserRouter>
  </React.StrictMode>
);
