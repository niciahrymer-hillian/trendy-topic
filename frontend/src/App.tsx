import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Overview from "./pages/Overview";
import GlobePage from "./pages/GlobePage";
import Country from "./pages/Country";
import Topics from "./pages/Topics";
import Languages from "./pages/Languages";
import Sentiment from "./pages/Sentiment";
import Wow from "./pages/Wow";
import Ask from "./pages/Ask";
import Translations from "./pages/Translations";
import AIInsights from "./pages/AIInsights";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Overview />} />
        <Route path="globe" element={<GlobePage />} />
        <Route path="countries" element={<Country />} />
        <Route path="topics" element={<Topics />} />
        <Route path="languages" element={<Languages />} />
        <Route path="sentiment" element={<Sentiment />} />
        <Route path="wow" element={<Wow />} />
        <Route path="ask" element={<Ask />} />
        <Route path="translations" element={<Translations />} />
        <Route path="ai-insights" element={<AIInsights />} />
      </Route>
    </Routes>
  );
}
