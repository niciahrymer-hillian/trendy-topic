import { Suspense, lazy } from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";

const Overview = lazy(() => import("./pages/Overview"));
const GlobePage = lazy(() => import("./pages/GlobePage"));
const Country = lazy(() => import("./pages/Country"));
const Topics = lazy(() => import("./pages/Topics"));
const Languages = lazy(() => import("./pages/Languages"));
const Sentiment = lazy(() => import("./pages/Sentiment"));
const Wow = lazy(() => import("./pages/Wow"));
const Ask = lazy(() => import("./pages/Ask"));
const Translations = lazy(() => import("./pages/Translations"));
const AIInsights = lazy(() => import("./pages/AIInsights"));
const VoiceStudio = lazy(() => import("./pages/VoiceStudio"));
const LibrarySearch = lazy(() => import("./pages/LibrarySearch"));
const DeweyPrompts = lazy(() => import("./pages/DeweyPrompts"));
const DeweyTaxonomy = lazy(() => import("./pages/DeweyTaxonomy"));

export default function App() {
  return (
    <Suspense fallback={<div className="state">Loading...</div>}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<GlobePage />} />
          <Route path="globe" element={<GlobePage />} />
          <Route path="overview" element={<Overview />} />
          <Route path="library" element={<LibrarySearch />} />
          <Route path="countries" element={<Country />} />
          <Route path="topics" element={<Topics />} />
          <Route path="languages" element={<Languages />} />
          <Route path="sentiment" element={<Sentiment />} />
          <Route path="wow" element={<Wow />} />
          <Route path="ask" element={<Ask />} />
          <Route path="translations" element={<Translations />} />
          <Route path="ai-insights" element={<AIInsights />} />
          <Route path="voice" element={<VoiceStudio />} />
          <Route path="dewey-prompts" element={<DeweyPrompts />} />
          <Route path="dewey-taxonomy" element={<DeweyTaxonomy />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
