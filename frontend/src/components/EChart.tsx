// Thin wrapper around echarts-for-react so pages pass just an ECharts `option`.
// One charting dependency covers bar/line/pie/heatmap/treemap/scatter consistently.

import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts";

export default function EChart({
  option,
  height = 360,
}: {
  option: EChartsOption;
  height?: number;
}) {
  return (
    <ReactECharts
      option={option}
      style={{ height, width: "100%" }}
      notMerge
      lazyUpdate
    />
  );
}
