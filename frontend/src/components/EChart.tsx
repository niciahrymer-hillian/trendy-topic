// Thin wrapper around echarts-for-react so pages pass just an ECharts `option`.
// One charting dependency covers bar/line/pie/heatmap/treemap/scatter consistently.

import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts";
import { applyChartTheme, useChartTheme } from "../charts";

export default function EChart({
  option,
  height = 360,
}: {
  option: EChartsOption;
  height?: number;
}) {
  const chartTheme = useChartTheme();
  return (
    <ReactECharts
      option={applyChartTheme(option, chartTheme)}
      style={{ height, width: "100%" }}
      notMerge
      lazyUpdate
    />
  );
}
