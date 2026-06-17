import { Suspense, lazy } from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";

const Overview = lazy(() => import("./pages/Overview"));
const GlobePage = lazy(() => import("./pages/GlobePage"));
const Compare = lazy(() => import("./pages/Compare"));
const Explore = lazy(() => import("./pages/Explore"));
const Insights = lazy(() => import("./pages/Insights"));
const AIAssistant = lazy(() => import("./pages/AIAssistant"));
const DeweyTaxonomy = lazy(() => import("./pages/DeweyTaxonomy"));

export default function App() {
  return (
    <Suspense fallback={<div className="state">Loading...</div>}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<GlobePage />} />
          <Route path="globe" element={<GlobePage />} />
          <Route path="compare" element={<Compare />} />
          <Route path="overview" element={<Overview />} />
          <Route path="explore" element={<Explore />} />
          <Route path="insights" element={<Insights />} />
          <Route path="ai-assistant" element={<AIAssistant />} />
          <Route path="dewey-taxonomy" element={<DeweyTaxonomy />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
