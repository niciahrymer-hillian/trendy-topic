// Reusable ECharts option builders for the chart shapes that several pages share
// (heatmaps and multi-series line charts). Pages pass tidy record arrays.

import type { EChartsOption } from "echarts";

type Row = Record<string, string | number>;

/** Heatmap from long-form rows: one cell per (xKey, yKey) colored by valKey. */
export function heatmapOption(rows: Row[], xKey: string, yKey: string, valKey: string): EChartsOption {
  const xs = [...new Set(rows.map((r) => String(r[xKey])))];
  const ys = [...new Set(rows.map((r) => String(r[yKey])))];
  const data = rows.map((r) => [xs.indexOf(String(r[xKey])), ys.indexOf(String(r[yKey])), Number(r[valKey])]);
  const max = Math.max(1, ...rows.map((r) => Number(r[valKey])));
  return {
    tooltip: { position: "top" },
    grid: { left: 150, right: 20, top: 10, bottom: 90 },
    xAxis: { type: "category", data: xs, axisLabel: { rotate: 35 } },
    yAxis: { type: "category", data: ys },
    visualMap: {
      min: 0, max, calculable: true, orient: "horizontal", left: "center", bottom: 0,
      inRange: { color: ["#0f1419", "#1d4e7a", "#4aa8ff"] }, textStyle: { color: "#93a1b1" },
    },
    series: [{ type: "heatmap", data, label: { show: false } }],
  };
}

/** Multi-series line: one line per distinct seriesKey, x = sorted xKey, y = valKey. */
export function multiLineOption(rows: Row[], xKey: string, seriesKey: string, valKey: string): EChartsOption {
  const xs = [...new Set(rows.map((r) => String(r[xKey])))].sort();
  const names = [...new Set(rows.map((r) => String(r[seriesKey])))];
  const series = names.map((name) => ({
    name,
    type: "line" as const,
    showSymbol: false,
    data: xs.map((x) => {
      const m = rows.find((r) => String(r[xKey]) === x && String(r[seriesKey]) === name);
      return m ? Number(m[valKey]) : 0;
    }),
  }));
  return {
    tooltip: { trigger: "axis" },
    legend: { type: "scroll", top: 0, textStyle: { color: "#93a1b1" } },
    grid: { top: 48, left: 44, right: 20, bottom: 40 },
    xAxis: { type: "category", data: xs },
    yAxis: { type: "value" },
    series,
  };
}

/** Horizontal bar from a label/value pair, sorted as given (largest at top). */
export function hBarOption(rows: Row[], labelKey: string, valKey: string, color = "#4aa8ff"): EChartsOption {
  const labels = rows.map((r) => String(r[labelKey])).reverse();
  const values = rows.map((r) => Number(r[valKey])).reverse();
  return {
    tooltip: {},
    grid: { left: 150, right: 20, top: 10, bottom: 30 },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: labels },
    series: [{ type: "bar", data: values, itemStyle: { color } }],
  };
}
