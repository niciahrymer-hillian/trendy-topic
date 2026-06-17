// Insights — Global Curiosity Index (most-asked questions) and a
// topic×country heatmap.

import { useEffect } from "react";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump, scrollToId } from "../jump";
import { ErrorState, Loading, PageHeader, Section, Table } from "../components/Ui";
import EChart from "../components/EChart";
import { heatmapOption, useChartTheme } from "../charts";

export default function Wow() {
  const curiosity = useFetch(() => api.curiosity(15), []);
  const heat = useFetch(() => api.heatmap(), []);
  const { set } = useJump();
  const chartTheme = useChartTheme();

  useEffect(() => {
    set("On this page", [
      { label: "Curiosity Index", onClick: () => scrollToId("curiosity") },
      { label: "Question heatmap", onClick: () => scrollToId("heat") },
    ]);
  }, [set]);

  if (curiosity.loading || heat.loading) return <Loading />;
  if (curiosity.error || !curiosity.data) return <ErrorState message={curiosity.error ?? "no data"} />;
  if (!heat.data) return <ErrorState message="missing data" />;

  return (
    <div>
      <PageHeader title="Insights" subtitle="What the world asks most, and where." />
      <Section id="curiosity" title="Global Curiosity Index — most-asked questions">
        <Table
          columns={["rank", "conversations", "topic_label", "sample_user_prompt_cleaned"]}
          rows={curiosity.data as unknown as Record<string, string | number>[]}
        />
      </Section>
      <Section id="heat" title="Global Question Heatmap — topic intensity by country">
        <EChart option={heatmapOption(heat.data as unknown as Record<string, string | number>[], "country", "topic_label", "conversations", chartTheme)} height={460} />
      </Section>
    </div>
  );
}
