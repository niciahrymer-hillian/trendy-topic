// App frame: fixed Sidebar + scrollable content area where routed pages render.

import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import ErrorBoundary from "./ErrorBoundary";

export default function Layout() {
  return (
    <div className="app">
      <Sidebar />
      <main className="content">
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </main>
    </div>
  );
}
