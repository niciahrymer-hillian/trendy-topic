import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { JumpProvider } from "./jump";
import { ThemeProvider } from "./theme";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <BrowserRouter>
        <JumpProvider>
          <App />
        </JumpProvider>
      </BrowserRouter>
    </ThemeProvider>
  </React.StrictMode>
);
