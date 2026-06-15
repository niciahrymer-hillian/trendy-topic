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
<<<<<<< HEAD
import VoiceStudio from "./pages/VoiceStudio";
=======
import LibrarySearch from "./pages/LibrarySearch";
>>>>>>> 1f4c9ef (Implemented Dewey Decimal Library system and search)

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<LibrarySearch />} />
        <Route path="overview" element={<Overview />} />
        <Route path="globe" element={<GlobePage />} />
        <Route path="countries" element={<Country />} />
        <Route path="topics" element={<Topics />} />
        <Route path="languages" element={<Languages />} />
        <Route path="sentiment" element={<Sentiment />} />
        <Route path="wow" element={<Wow />} />
        <Route path="ask" element={<Ask />} />
        <Route path="translations" element={<Translations />} />
        <Route path="ai-insights" element={<AIInsights />} />
        <Route path="voice" element={<VoiceStudio />} />
      </Route>
    </Routes>
  );
}
