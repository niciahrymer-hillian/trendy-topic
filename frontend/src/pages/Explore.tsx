// Explore — merges Topic Explorer, Language Analysis, and Sentiment into one tabbed
// page (reuses the existing chart components, so nothing is lost).

import { useState } from "react";
import Topics from "./Topics";
import Languages from "./Languages";
import Sentiment from "./Sentiment";

type Tab = "topics" | "languages" | "sentiment";

export default function Explore() {
  const [tab, setTab] = useState<Tab>("topics");
  return (
    <div>
      <div className="controls" role="tablist">
        <button className={tab === "topics" ? "primary" : ""} onClick={() => setTab("topics")}>Topics</button>
        <button className={tab === "languages" ? "primary" : ""} onClick={() => setTab("languages")}>Languages</button>
        <button className={tab === "sentiment" ? "primary" : ""} onClick={() => setTab("sentiment")}>Sentiment</button>
      </div>
      {tab === "topics" && <Topics />}
      {tab === "languages" && <Languages />}
      {tab === "sentiment" && <Sentiment />}
    </div>
  );
}
