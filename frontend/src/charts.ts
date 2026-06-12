// Reusable ECharts option builders for the chart shapes that several pages share
// (heatmaps and multi-series line charts). Pages pass tidy record arrays.

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { useTheme } from "./theme";

type Row = Record<string, string | number>;

export interface ChartTheme {
  text: string;
  muted: string;
  accent: string;
  accent2: string;
  border: string;
  grid: string;
  panel: string;
  ok: string;
  danger: string;
  heatLow: string;
  heatMid: string;
  heatHigh: string;
  tooltipBg: string;
  tooltipBorder: string;
  sentiment: string[];
  series: string[];
}

function cssVar(name: string, fallback: string) {
  if (typeof window === "undefined") return fallback;
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
}

export function useChartTheme(): ChartTheme {
  const { theme } = useTheme();
  return useMemo(
    () => ({
      text: cssVar("--text", theme === "dark" ? "#e6edf3" : "#132034"),
      muted: cssVar("--muted", theme === "dark" ? "#93a1b1" : "#5b6e86"),
      accent: cssVar("--accent", theme === "dark" ? "#4aa8ff" : "#1f7bff"),
      accent2: cssVar("--accent-2", theme === "dark" ? "#7c5cff" : "#00a7a0"),
      border: cssVar("--border", theme === "dark" ? "#2b3648" : "#d4deed"),
      grid: theme === "dark" ? "rgba(147, 161, 177, 0.16)" : "rgba(91, 110, 134, 0.18)",
      panel: cssVar("--panel", theme === "dark" ? "#1a2230" : "#ffffff"),
      ok: cssVar("--ok", "#3fb950"),
      danger: cssVar("--danger", theme === "dark" ? "#ff7b72" : "#d73a49"),
      heatLow: theme === "dark" ? "#0f1419" : "#e8f0fb",
      heatMid: theme === "dark" ? "#1d4e7a" : "#5ca3ff",
      heatHigh: theme === "dark" ? "#4aa8ff" : "#0d5fd6",
      tooltipBg: cssVar("--tooltip-bg", theme === "dark" ? "rgba(15, 20, 25, 0.96)" : "rgba(255,255,255,0.97)"),
      tooltipBorder: cssVar("--tooltip-border", theme === "dark" ? "#2b3648" : "#b8cbe6"),
      sentiment: [cssVar("--ok", "#3fb950"), cssVar("--accent", theme === "dark" ? "#4aa8ff" : "#1f7bff"), cssVar("--danger", theme === "dark" ? "#ff7b72" : "#d73a49")],
      series: [
        cssVar("--accent", theme === "dark" ? "#4aa8ff" : "#1f7bff"),
        cssVar("--accent-2", theme === "dark" ? "#7c5cff" : "#00a7a0"),
        cssVar("--ok", "#3fb950"),
        theme === "dark" ? "#f2cc60" : "#c68600",
        theme === "dark" ? "#ff7b72" : "#d73a49",
      ],
    }),
    [theme]
  );
}

function withAxisTheme(axis: EChartsOption["xAxis"] | EChartsOption["yAxis"], chartTheme: ChartTheme) {
  const decorate = (item: object) => {
    const axisItem = item as Record<string, unknown>;
    const axisLabel = (axisItem.axisLabel as Record<string, unknown> | undefined) ?? {};
    const axisLine = (axisItem.axisLine as Record<string, unknown> | undefined) ?? {};
    const splitLine = (axisItem.splitLine as Record<string, unknown> | undefined) ?? {};
    const lineStyle = (axisLine.lineStyle as Record<string, unknown> | undefined) ?? {};
    const splitLineStyle = (splitLine.lineStyle as Record<string, unknown> | undefined) ?? {};
    return {
      ...axisItem,
      axisLabel: { color: chartTheme.muted, ...axisLabel },
      nameTextStyle: { color: chartTheme.muted, ...((axisItem.nameTextStyle as Record<string, unknown> | undefined) ?? {}) },
      axisLine: { ...axisLine, lineStyle: { color: chartTheme.border, ...lineStyle } },
      splitLine: { ...splitLine, lineStyle: { color: chartTheme.grid, ...splitLineStyle } },
    };
  };

  if (Array.isArray(axis)) return axis.map((item) => decorate(item));
  if (!axis) return axis;
  return decorate(axis);
}

export function applyChartTheme(option: EChartsOption, chartTheme: ChartTheme): EChartsOption {
  const legend = option.legend
    ? Array.isArray(option.legend)
      ? option.legend.map((item) => ({
          ...item,
          textStyle: { color: chartTheme.muted, ...(item.textStyle ?? {}) },
        }))
      : { ...option.legend, textStyle: { color: chartTheme.muted, ...(option.legend.textStyle ?? {}) } }
    : option.legend;

  const tooltip = option.tooltip
    ? Array.isArray(option.tooltip)
      ? option.tooltip.map((item) => ({
          ...item,
          backgroundColor: chartTheme.tooltipBg,
          borderColor: chartTheme.tooltipBorder,
          textStyle: { color: chartTheme.text, ...(item.textStyle ?? {}) },
        }))
      : {
          ...option.tooltip,
          backgroundColor: chartTheme.tooltipBg,
          borderColor: chartTheme.tooltipBorder,
          textStyle: { color: chartTheme.text, ...(option.tooltip.textStyle ?? {}) },
        }
    : option.tooltip;

  return {
    ...option,
    backgroundColor: "transparent",
    textStyle: { color: chartTheme.text, ...(option.textStyle ?? {}) },
    color: option.color ?? chartTheme.series,
    legend,
    tooltip,
    xAxis: withAxisTheme(option.xAxis, chartTheme),
    yAxis: withAxisTheme(option.yAxis, chartTheme),
  };
}

/** Heatmap from long-form rows: one cell per (xKey, yKey) colored by valKey. */
export function heatmapOption(rows: Row[], xKey: string, yKey: string, valKey: string, chartTheme: ChartTheme): EChartsOption {
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
      inRange: { color: [chartTheme.heatLow, chartTheme.heatMid, chartTheme.heatHigh] },
      textStyle: { color: chartTheme.muted },
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
export function hBarOption(rows: Row[], labelKey: string, valKey: string, color: string): EChartsOption {
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
