// Insights — merges Wow-Factor and AI Insights into one tabbed page.

import { useState } from "react";
import Wow from "./Wow";
import AIInsights from "./AIInsights";

export default function Insights() {
  const [tab, setTab] = useState<"wow" | "ai">("wow");
  return (
    <div>
      <div className="controls" role="tablist">
        <button className={tab === "wow" ? "primary" : ""} onClick={() => setTab("wow")}>Wow-Factor</button>
        <button className={tab === "ai" ? "primary" : ""} onClick={() => setTab("ai")}>AI Insights</button>
      </div>
      {tab === "wow" ? <Wow /> : <AIInsights />}
    </div>
  );
}
