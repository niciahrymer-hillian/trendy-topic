// Left navigation + the contextual "Jump to" panel published by the active page.

import { NavLink } from "react-router-dom";
import { useJump } from "../jump";

const NAV = [
  { to: "/", label: "Global Overview", end: true },
  { to: "/globe", label: "Interactive Globe" },
  { to: "/countries", label: "Country Analysis" },
  { to: "/topics", label: "Topic Explorer" },
  { to: "/languages", label: "Language Analysis" },
  { to: "/sentiment", label: "Sentiment" },
  { to: "/wow", label: "Wow-Factor Insights" },
  { to: "/ask", label: "Ask the Dataset" },
];

export default function Sidebar() {
  const { title, items } = useJump();
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-dot" />
        <div>
          <div className="brand-title">Trendy Topic</div>
          <div className="brand-sub">What the World Asks AI</div>
        </div>
      </div>

      <nav className="nav">
        {NAV.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            end={n.end}
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            {n.label}
          </NavLink>
        ))}
      </nav>

      {items.length > 0 && (
        <div className="jump">
          <div className="jump-title">{title || "Jump to"}</div>
          <div className="jump-list">
            {items.map((it, i) => (
              <button
                key={`${it.label}-${i}`}
                className={`jump-item${it.active ? " active" : ""}`}
                onClick={it.onClick}
              >
                {it.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </aside>
  );
}
