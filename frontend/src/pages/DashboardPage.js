import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  XAxis,
  YAxis,
  AreaChart,
  Area,
  CartesianGrid,
  Legend,
} from "recharts";
import { getStats, getDetections, clearDetections } from "../api";
import "./DashboardPage.css";

// ── Visibility-aware polling hook ─────────────────────────────────────────────
function useVisibilityPolling(callback, interval) {
  const savedCallback = useRef(callback);
  const timerRef = useRef(null);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    function start() {
      timerRef.current = setInterval(() => savedCallback.current(), interval);
    }
    function stop() {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    function onVisibilityChange() {
      if (document.hidden) {
        stop();
      } else {
        savedCallback.current();
        start();
      }
    }

    savedCallback.current();
    start();

    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      stop();
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [interval]);
}

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reportPeriod, setReportPeriod] = useState("7days");

  const load = useCallback(async () => {
    setLoading((prev) => (prev === true ? true : false));
    try {
      const [s, r] = await Promise.all([getStats(), getDetections(500)]);
      setStats(s);
      setRows(r);
      setError("");
    } catch {
      setError("Cannot reach API. Make sure the server is running.");
    } finally {
      setLoading(false);
    }
  }, []);

  useVisibilityPolling(load, 15000);

  const handleClear = async () => {
    if (!window.confirm("Clear all detection records?")) return;
    await clearDetections();
    load();
  };

  // ── Filter rows based on selected period ────────────────────────────────────
  const getFilteredRows = (rows, period) => {
    if (!rows || rows.length === 0) return rows;
    
    const now = new Date();
    let cutoffDate = new Date();
    
    switch(period) {
      case "24h":
        cutoffDate.setHours(now.getHours() - 24);
        break;
      case "7days":
        cutoffDate.setDate(now.getDate() - 7);
        break;
      case "30days":
        cutoffDate.setDate(now.getDate() - 30);
        break;
      case "all":
      default:
        return rows; // No filtering
    }
    
    return rows.filter(r => {
      if (!r.timestamp) return false;
      const date = new Date(r.timestamp + "Z");
      return date >= cutoffDate;
    });
  };

  // ── Apply period filter to rows ─────────────────────────────────────────────
  const filteredRows = getFilteredRows(rows, reportPeriod);

  // ── Data Processing ──────────────────────────────────────────────────────────
  const pieData = stats
    ? [
        { name: "Legitimate", value: stats.legit_count },
        { name: "Scam", value: stats.scam_count },
      ]
    : [];

  const platData = stats
    ? [
        { name: "Facebook", value: stats.facebook_total, fill: "#2563eb" },
        { name: "X (Twitter)", value: stats.twitter_total, fill: "#60a5fa" },
      ]
    : [];

  // ── Hourly Data (filtered) ──────────────────────────────────────────────────
  const hourlyData = (() => {
    const counts = {};
    filteredRows.forEach((r) => {
      const h = r.timestamp ? new Date(r.timestamp + "Z").getHours() : 0;
      if (!counts[h]) counts[h] = { hour: `${h}:00`, scam: 0, legit: 0 };
      counts[h][r.label === 1 ? "scam" : "legit"]++;
    });
    return Object.values(counts).sort(
      (a, b) => parseInt(a.hour) - parseInt(b.hour),
    );
  })();

  // ── Daily Trend Data (filtered) ─────────────────────────────────────────────
  // For 24h period, we use hourly data instead of daily
  const dailyTrendData = (() => {
    // If 24h period, return hourly data formatted for area chart
    if (reportPeriod === "24h") {
      // Create 24 hour slots
      const hourSlots = {};
      const now = new Date();
      for (let i = 23; i >= 0; i--) {
        const d = new Date(now);
        d.setHours(d.getHours() - i);
        const key = d.toISOString().split("T")[0] + " " + d.getHours().toString().padStart(2, '0') + ":00";
        hourSlots[key] = { date: key, scam: 0, legit: 0, total: 0 };
      }

      filteredRows.forEach((r) => {
        if (r.timestamp) {
          const date = new Date(r.timestamp + "Z");
          const key = date.toISOString().split("T")[0] + " " + date.getHours().toString().padStart(2, '0') + ":00";
          if (hourSlots[key]) {
            hourSlots[key][r.label === 1 ? "scam" : "legit"]++;
            hourSlots[key].total++;
          }
        }
      });

      return Object.values(hourSlots);
    }

    // For other periods, use daily data
    const days = {};
    const now = new Date();
    const numDays = reportPeriod === "7days" ? 7 : reportPeriod === "30days" ? 30 : 7;
    
    for (let i = numDays - 1; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      const key = d.toISOString().split("T")[0];
      days[key] = { date: key, scam: 0, legit: 0, total: 0 };
    }

    filteredRows.forEach((r) => {
      if (r.timestamp) {
        const date = new Date(r.timestamp + "Z").toISOString().split("T")[0];
        if (days[date]) {
          days[date][r.label === 1 ? "scam" : "legit"]++;
          days[date].total++;
        }
      }
    });

    return Object.values(days);
  })();

  // ── Risk Score Distribution (filtered) ──────────────────────────────────────
  const riskDistribution = (() => {
    const ranges = [
      { range: "0-20%", min: 0, max: 20, count: 0 },
      { range: "21-40%", min: 21, max: 40, count: 0 },
      { range: "41-60%", min: 41, max: 60, count: 0 },
      { range: "61-80%", min: 61, max: 80, count: 0 },
      { range: "81-100%", min: 81, max: 100, count: 0 },
    ];

    filteredRows.forEach((r) => {
      const prob = parseFloat(r.scam_prob) || 0;
      for (const range of ranges) {
        if (prob >= range.min && prob <= range.max) {
          range.count++;
          break;
        }
      }
    });

    return ranges;
  })();

  // ── Summary Statistics (filtered) ───────────────────────────────────────────
  const summaryStats = (() => {
    const total = filteredRows.length;
    const scams = filteredRows.filter((r) => r.label === 1).length;
    const legit = total - scams;
    const avgConfidence = total > 0
      ? filteredRows.reduce((sum, r) => sum + (parseFloat(r.confidence) || 0), 0) / total
      : 0;
    const peakHour = (() => {
      const hours = {};
      filteredRows.forEach((r) => {
        if (r.timestamp) {
          const h = new Date(r.timestamp + "Z").getHours();
          hours[h] = (hours[h] || 0) + 1;
        }
      });
      let maxHour = 0;
      let maxCount = 0;
      for (const [h, count] of Object.entries(hours)) {
        if (count > maxCount) {
          maxCount = count;
          maxHour = parseInt(h);
        }
      }
      return maxHour;
    })();

    return {
      total,
      scams,
      legit,
      scamRate: total > 0 ? ((scams / total) * 100).toFixed(1) : "0",
      avgConfidence: avgConfidence.toFixed(1),
      peakHour,
      peakHourLabel: `${peakHour}:00 - ${peakHour + 1}:00`,
    };
  })();

  // ── Period display name ─────────────────────────────────────────────────────
  const getPeriodDisplayName = () => {
    switch(reportPeriod) {
      case "24h": return "Last 24 Hours (Hourly)";
      case "7days": return "Last 7 Days";
      case "30days": return "Last 30 Days";
      case "all": return "All Time";
      default: return "Last 7 Days";
    }
  };

  if (loading && !stats)
    return (
      <div className="dash-loading">
        <div className="big-spinner-dash" />
        <p>Loading dashboard...</p>
      </div>
    );

  if (error)
    return (
      <div className="dash-error card">
        <div style={{ fontSize: 40, marginBottom: 12 }}>⚠️</div>
        <p>{error}</p>
      </div>
    );

  const isDark =
    document.documentElement.getAttribute("data-theme") !== "light";
  const tooltipStyle = {
    contentStyle: {
      background: isDark ? "#111118" : "#ffffff",
      border: `1px solid ${isDark ? "#25252e" : "#dcdce5"}`,
      borderRadius: 6,
      fontSize: 12,
    },
    labelStyle: { color: isDark ? "#f0f0f5" : "#0a0a0f" },
  };
  const tickColor = isDark ? "#9898a8" : "#4a4a5a";
  const textColor = isDark ? "#f0f0f5" : "#0a0a0f";

  const statCards = [
    {
      label: "Total Scanned",
      value: stats?.total_detections ?? "—",
      color: "default",
      sub: `${stats?.detections_today ?? 0} today`,
    },
    {
      label: "Scams Detected",
      value: stats?.scam_count ?? "—",
      color: "danger",
      sub: stats?.scam_rate ?? "—",
    },
    {
      label: "Legitimate Posts",
      value: stats?.legit_count ?? "—",
      color: "safe",
      sub: "non-scam",
    },
    {
      label: "Scam Rate",
      value: stats?.scam_rate ?? "—",
      color: "warn",
      sub: "of all scanned",
    },
  ];

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-sub">
            Live overview · auto-refreshes every 15s (pauses when tab is
            inactive)
            {stats?.mock_mode && (
              <span className="mock-tag"> · Mock Mode</span>
            )}
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button className="btn btn-ghost" onClick={load} style={{ cursor: 'pointer' }}>
            ↻ Refresh
          </button>
          <button className="btn btn-danger" onClick={handleClear}>
            Clear All
          </button>
        </div>
      </div>

      {/* ── STATS ROW ── */}
      <div className="stats-row">
        {statCards.map(({ label, value, color, sub }) => (
          <div key={label} className={`stat-card-d stat-${color}`}>
            <div className="stat-label-d">{label}</div>
            <div className="stat-value-d">{value}</div>
            <div className="stat-sub-d">{sub}</div>
          </div>
        ))}
      </div>

      {/* ── CHARTS ROW ── */}
      <div className="charts-row">
        {/* Pie chart */}
        <div className="chart-card card">
          <div className="chart-title">Scam vs Legit</div>
          {pieData.every((d) => d.value === 0) ? (
            <div className="chart-empty">No data yet</div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={["#22c55e", "#ef4444"][i]} />
                    ))}
                  </Pie>
                  <Tooltip
                    {...tooltipStyle}
                    formatter={(value, name) => [value, name]}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="pie-legend">
                <span
                  className="pie-legend-dot"
                  style={{ background: "#22c55e" }}
                />
                <span className="pie-legend-label">Legitimate</span>
                <span
                  className="pie-legend-dot"
                  style={{ background: "#f05252", marginLeft: 14 }}
                />
                <span className="pie-legend-label">Scam</span>
              </div>
            </>
          )}
        </div>

        {/* By Platform */}
        <div className="chart-card card">
          <div className="chart-title">By Platform</div>
          {platData.every((d) => d.value === 0) ? (
            <div className="chart-empty">No data yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={platData} barSize={40}>
                <XAxis
                  dataKey="name"
                  tick={{ fill: tickColor, fontSize: 12 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: tickColor, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip {...tooltipStyle} cursor={false} />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {platData.map((e, i) => (
                    <Cell key={i} fill={e.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Detections by Hour */}
        <div className="chart-card chart-wide card">
          <div className="chart-title">Detections by Hour</div>
          {hourlyData.length === 0 ? (
            <div className="chart-empty">No data yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={hourlyData} barSize={14}>
                <XAxis
                  dataKey="hour"
                  tick={{ fill: tickColor, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: tickColor, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip {...tooltipStyle} cursor={false} />
                <Bar
                  dataKey="scam"
                  fill="#ef4444"
                  radius={[4, 4, 0, 0]}
                  name="Scam"
                />
                <Bar
                  dataKey="legit"
                  fill="#22c55e"
                  radius={[4, 4, 0, 0]}
                  name="Legit"
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* ── ANALYSIS REPORT SECTION ── */}
      <div className="analysis-report">
        <div className="report-header">
          <h2 className="report-title">Analysis Report</h2>
          <div className="report-controls">
            <span className="report-period-label">Period:</span>
            <select
              className="report-period-select"
              value={reportPeriod}
              onChange={(e) => setReportPeriod(e.target.value)}
            >
              <option value="24h">Last 24 Hours</option>
              <option value="7days">Last 7 Days</option>
              <option value="30days">Last 30 Days</option>
              <option value="all">All Time</option>
            </select>
          </div>
        </div>

        {/* ── SUMMARY STATS CARDS ── */}
        <div className="report-summary-grid">
          <div className="report-summary-card">
            <span className="report-summary-icon">#</span>
            <div>
              <div className="report-summary-value">{summaryStats.total}</div>
              <div className="report-summary-label">Total Detections</div>
            </div>
          </div>
          <div className="report-summary-card">
            <span className="report-summary-icon">!</span>
            <div>
              <div className="report-summary-value" style={{ color: "#ef4444" }}>
                {summaryStats.scams}
              </div>
              <div className="report-summary-label">Scams Detected</div>
            </div>
          </div>
          <div className="report-summary-card">
            <span className="report-summary-icon">✓</span>
            <div>
              <div className="report-summary-value" style={{ color: "#22c55e" }}>
                {summaryStats.legit}
              </div>
              <div className="report-summary-label">Legitimate</div>
            </div>
          </div>
          <div className="report-summary-card">
            <span className="report-summary-icon">%</span>
            <div>
              <div className="report-summary-value" style={{ color: "#f59e0b" }}>
                {summaryStats.scamRate}%
              </div>
              <div className="report-summary-label">Scam Rate</div>
            </div>
          </div>
          <div className="report-summary-card">
            <span className="report-summary-icon">T</span>
            <div>
              <div className="report-summary-value" style={{ color: "#06b6d4" }}>
                {summaryStats.peakHourLabel}
              </div>
              <div className="report-summary-label">Peak Detection Hour</div>
            </div>
          </div>
        </div>

        {/* ── TREND CHART ── */}
        <div className="report-chart-card">
          <div className="report-chart-title">
            Detection Trend ({getPeriodDisplayName()})
          </div>
          {dailyTrendData.every((d) => d.total === 0) ? (
            <div className="chart-empty">No data available</div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={dailyTrendData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke={isDark ? "#25252e" : "#dcdce5"}
                />
                <XAxis
                  dataKey="date"
                  tick={{ fill: tickColor, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  interval={reportPeriod === "24h" ? 2 : undefined}
                />
                <YAxis
                  tick={{ fill: tickColor, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip {...tooltipStyle} />
                <Legend
                  wrapperStyle={{ color: textColor, fontSize: 12 }}
                />
                <Area
                  type="monotone"
                  dataKey="scam"
                  stackId="1"
                  stroke="#ef4444"
                  fill="#ef4444"
                  fillOpacity={0.6}
                  name="Scam"
                />
                <Area
                  type="monotone"
                  dataKey="legit"
                  stackId="1"
                  stroke="#22c55e"
                  fill="#22c55e"
                  fillOpacity={0.6}
                  name="Legit"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* ── RISK DISTRIBUTION ── */}
        <div className="report-chart-card">
          <div className="report-chart-title">
            Risk Score Distribution
          </div>
          {riskDistribution.every((d) => d.count === 0) ? (
            <div className="chart-empty">No data available</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={riskDistribution}>
                <XAxis
                  dataKey="range"
                  tick={{ fill: tickColor, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: tickColor, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip {...tooltipStyle} />
                <Bar
                  dataKey="count"
                  fill="#2563eb"
                  radius={[4, 4, 0, 0]}
                  name="Detections"
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* ── REPORT FOOTER ── */}
        <div className="report-footer">
          <div className="report-footer-text">
            Report generated on {new Date().toLocaleString()}
          </div>
          <div className="report-footer-text">
            • Total detections: {summaryStats.total}
            {summaryStats.total > 0 && (
              <>
                {" "}
                • Scam rate: {summaryStats.scamRate}% • Avg confidence:{" "}
                {summaryStats.avgConfidence}%
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}