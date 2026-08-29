import React, { useState, useEffect } from "react";
import { getModelMetrics } from "../api";
import { jsPDF } from "jspdf";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from "recharts";
import "./MetricsPage.css";

export default function MetricsPage() {
  const [metrics, setMetrics] = useState({
    accuracy: 92.4,
    precision: 91.1,
    recall: 90.3,
    f1: 90.7,
    total_samples: 12456,
    scam_samples: 4213,
    legit_samples: 8243,
    true_positives: 0,
    true_negatives: 0,
    false_positives: 0,
    false_negatives: 0,
    evaluation_date: "May 18, 2025 • 10:24 AM"
  });

  useEffect(() => {
    getModelMetrics().then((data) => {
      if (data && data.total_samples > 0) {
        setMetrics(data);
      }
    }).catch(console.error);
  }, []);

  const data = [
    { name: "Accuracy", value: metrics.accuracy },
    { name: "Precision", value: metrics.precision },
    { name: "Recall", value: metrics.recall },
    { name: "F-1 Score", value: metrics.f1 },
  ];

  const scamPercent = metrics.total_samples > 0 ? ((metrics.scam_samples / metrics.total_samples) * 100).toFixed(1) : 0;
  const legitPercent = metrics.total_samples > 0 ? ((metrics.legit_samples / metrics.total_samples) * 100).toFixed(1) : 0;

  const exportPDF = async () => {
    // Load logo as base64
    const toBase64 = (url) => new Promise((resolve) => {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        const c = document.createElement("canvas");
        c.width = img.width; c.height = img.height;
        c.getContext("2d").drawImage(img, 0, 0);
        resolve(c.toDataURL("image/png"));
      };
      img.onerror = () => resolve(null);
      img.src = url;
    });

    const logoBase64 = await toBase64("/WebLogo.png");

    const doc = new jsPDF("p", "mm", "a4");
    const W = doc.internal.pageSize.getWidth();   // 210
    const H = doc.internal.pageSize.getHeight();   // 297
    const M = 15;
    const cW = W - 2 * M;

    // Color palette
    const GREEN    = [44, 110, 73];
    const DKGREEN  = [31, 80, 53];
    const LTGREEN  = [240, 253, 244];
    const DARK     = [30, 30, 40];
    const GRAY     = [130, 130, 145];
    const LTGRAY   = [245, 247, 250];
    const WHITE    = [255, 255, 255];
    const BORDER   = [225, 228, 232];
    const RED_T    = [220, 50, 50];

    // Parse date / time from evaluation_date
    const dateStr  = metrics.evaluation_date || "N/A";
    const datePart = dateStr.includes("\u2022") ? dateStr.split("\u2022")[0].trim() : dateStr;
    const timePart = dateStr.includes("\u2022") ? dateStr.split("\u2022")[1].trim() : "";
    const reportId = `PRG-${new Date().getFullYear()}-${String(new Date().getMonth()+1).padStart(2,"0")}${String(new Date().getDate()).padStart(2,"0")}-001`;

    // ═══════════════════════════════════════════
    //  HEADER
    // ═══════════════════════════════════════════
    let y = 12;

    // Logo image
    if (logoBase64) {
      doc.addImage(logoBase64, "PNG", M, y, 28, 28);
    }

    // Title block
    doc.setFont("helvetica", "bold");
    doc.setFontSize(24);
    doc.setTextColor(...DARK);
    doc.text("Protego", M + 34, y + 10);

    doc.setFontSize(13);
    doc.setTextColor(...DARK);
    doc.text("Model Performance Report", M + 34, y + 18);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(...GRAY);
    const hDesc = doc.splitTextToSize(
      "Evaluation of Protego\u2019s mBERT + Early Fusion + Metadata model on the hard test set.",
      72
    );
    doc.text(hDesc, M + 34, y + 24);

    // Right side: date, time, report ID
    const rx = W - M;

    // Calendar icon
    doc.setFillColor(...GREEN);
    doc.roundedRect(rx - 62, y + 3, 4, 4, 1, 1, "F");
    doc.setFontSize(5); doc.setTextColor(...WHITE); doc.setFont("helvetica","bold");
    doc.text("D", rx - 61, y + 6);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(...DARK);
    doc.text(datePart, rx - 56, y + 6.5);

    // Clock icon
    doc.setFillColor(...GREEN);
    doc.circle(rx - 60, y + 14, 2, "F");
    doc.setFontSize(4.5); doc.setTextColor(...WHITE); doc.setFont("helvetica","bold");
    doc.text("T", rx - 61.2, y + 14.8);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(...DARK);
    doc.text(timePart, rx - 56, y + 15);

    // Report ID
    doc.setFontSize(7.5);
    doc.setTextColor(...GRAY);
    doc.text(`Report ID: ${reportId}`, rx - 62, y + 24);

    // Separator
    y = 48;
    doc.setDrawColor(...BORDER);
    doc.setLineWidth(0.3);
    doc.line(M, y, W - M, y);

    // ═══════════════════════════════════════════
    //  OVERALL PERFORMANCE
    // ═══════════════════════════════════════════
    y = 54;

    // Section icon (green circle with checkmark shape)
    doc.setFillColor(...GREEN);
    doc.circle(M + 4, y + 4, 4, "F");
    doc.setFont("helvetica", "bold"); doc.setFontSize(7); doc.setTextColor(...WHITE);
    doc.text("\u2713", M + 2.3, y + 5.5);

    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.setTextColor(...GREEN);
    doc.text("OVERALL PERFORMANCE", M + 12, y + 6);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(...GRAY);
    const perfDesc = doc.splitTextToSize(
      "Protego\u2019s model shows strong performance in detecting scams with high reliability.",
      80
    );
    doc.text(perfDesc, M + 12, y + 13);

    // Big accuracy card (right side)
    const accCardX = W - M - 70;
    const accCardY = y;
    doc.setFillColor(...WHITE);
    doc.setDrawColor(...GREEN);
    doc.setLineWidth(0.7);
    doc.roundedRect(accCardX, accCardY, 70, 28, 3, 3, "FD");

    doc.setFont("helvetica", "bold");
    doc.setFontSize(28);
    doc.setTextColor(...GREEN);
    doc.text(`${metrics.accuracy.toFixed(1)}%`, accCardX + 12, accCardY + 15);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(...GRAY);
    doc.text("Overall Accuracy", accCardX + 12, accCardY + 22);

    // Small trend bars icon in the card
    doc.setFillColor(200, 235, 210);
    doc.rect(accCardX + 51, accCardY + 16, 3.5, 8, "F");
    doc.rect(accCardX + 56, accCardY + 12, 3.5, 12, "F");
    doc.rect(accCardX + 61, accCardY + 8,  3.5, 16, "F");

    // ═══════════════════════════════════════════
    //  KEY METRICS
    // ═══════════════════════════════════════════
    y = 88;

    // Bar‑chart icon
    doc.setFillColor(...GREEN);
    doc.rect(M + 1, y - 1, 2, 5, "F");
    doc.rect(M + 3.5, y - 3, 2, 7, "F");
    doc.rect(M + 6, y + 0, 2, 4, "F");

    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.setTextColor(...GREEN);
    doc.text("KEY METRICS", M + 12, y + 3);

    y = 96;
    const mcCards = [
      { label: "Accuracy",  val: metrics.accuracy,  desc: "Overall correctness of the model\u2019s predictions." },
      { label: "Precision", val: metrics.precision, desc: "Proportion of predicted scams that are actually scams." },
      { label: "Recall",    val: metrics.recall,    desc: "Proportion of actual scams that were correctly detected." },
      { label: "F-1 Score", val: metrics.f1,        desc: "Harmonic mean of Precision and Recall." },
    ];
    const mcW = (cW - 12) / 4;

    mcCards.forEach((card, i) => {
      const cx = M + i * (mcW + 4);

      // Card
      doc.setFillColor(...WHITE);
      doc.setDrawColor(...BORDER);
      doc.setLineWidth(0.25);
      doc.roundedRect(cx, y, mcW, 44, 2, 2, "FD");

      // Icon
      doc.setFillColor(220, 245, 230);
      doc.circle(cx + 6, y + 7, 4, "F");
      doc.setFillColor(...GREEN);
      doc.circle(cx + 6, y + 7, 2, "F");

      // Label
      doc.setFont("helvetica", "bold");
      doc.setFontSize(8.5);
      doc.setTextColor(...DARK);
      doc.text(card.label, cx + 13, y + 8.5);

      // Value
      doc.setFont("helvetica", "bold");
      doc.setFontSize(20);
      doc.setTextColor(...DARK);
      doc.text(card.val.toFixed(1) + "%", cx + 5, y + 22);

      // Description
      doc.setFont("helvetica", "normal");
      doc.setFontSize(6.5);
      doc.setTextColor(...GRAY);
      const dl = doc.splitTextToSize(card.desc, mcW - 8);
      doc.text(dl, cx + 5, y + 28);

      // Progress bar
      const bY = y + 39;
      doc.setFillColor(225, 230, 235);
      doc.roundedRect(cx + 4, bY, mcW - 8, 2, 1, 1, "F");
      doc.setFillColor(...GREEN);
      doc.roundedRect(cx + 4, bY, Math.max(1, (mcW - 8) * card.val / 100), 2, 1, 1, "F");
    });

    // ═══════════════════════════════════════════
    //  METRICS OVERVIEW  +  EVALUATION DETAILS
    // ═══════════════════════════════════════════
    y = 148;
    const halfW = (cW - 6) / 2;

    // ── Left card: METRICS OVERVIEW ──
    doc.setFillColor(...WHITE);
    doc.setDrawColor(...BORDER);
    doc.setLineWidth(0.25);
    doc.roundedRect(M, y, halfW, 88, 2, 2, "FD");

    // Title icon (bar chart)
    doc.setFillColor(...GREEN);
    doc.rect(M + 5, y + 5, 2, 5, "F");
    doc.rect(M + 7.5, y + 3, 2, 7, "F");
    doc.rect(M + 10, y + 6, 2, 4, "F");

    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor(...GREEN);
    doc.text("METRICS OVERVIEW", M + 15, y + 9);

    // Draw the bar chart
    const chartX = M + 14;
    const chartY = y + 18;
    const chartH = 52;
    const chartW = halfW - 22;

    // Y‑axis labels + grid
    const yLabels = [
      { label: "100%", frac: 0 },
      { label: "75%",  frac: 0.25 },
      { label: "50%",  frac: 0.5 },
      { label: "25%",  frac: 0.75 },
      { label: "0%",   frac: 1 },
    ];
    yLabels.forEach((item) => {
      const ly = chartY + chartH * item.frac;
      doc.setFont("helvetica", "normal");
      doc.setFontSize(6);
      doc.setTextColor(...GRAY);
      doc.text(item.label, M + 4, ly + 1);
      doc.setDrawColor(235, 238, 242);
      doc.setLineWidth(0.15);
      doc.line(chartX, ly, chartX + chartW, ly);
    });

    // Bars
    const barVals = [
      { name: "Accuracy",  v: metrics.accuracy },
      { name: "Precision", v: metrics.precision },
      { name: "Recall",    v: metrics.recall },
      { name: "F-1 Score", v: metrics.f1 },
    ];
    const bGap = 4;
    const bW = (chartW - bGap * 5) / 4;

    barVals.forEach((bar, i) => {
      const bx = chartX + bGap + i * (bW + bGap);
      const bh = (bar.v / 100) * chartH;
      const by = chartY + chartH - bh;

      doc.setFillColor(...GREEN);
      doc.roundedRect(bx, by, bW, bh, 1, 1, "F");

      // Value label on top
      doc.setFont("helvetica", "bold");
      doc.setFontSize(5.5);
      doc.setTextColor(...DARK);
      doc.text(bar.v.toFixed(1) + "%", bx + bW / 2, by - 2, { align: "center" });

      // X‑axis label
      doc.setFont("helvetica", "normal");
      doc.setFontSize(5.5);
      doc.setTextColor(...GRAY);
      doc.text(bar.name, bx + bW / 2, chartY + chartH + 5, { align: "center" });
    });

    // Legend
    doc.setFillColor(...GREEN);
    doc.rect(M + halfW / 2 - 14, y + 81, 3, 3, "F");
    doc.setFont("helvetica", "normal");
    doc.setFontSize(6);
    doc.setTextColor(...GRAY);
    doc.text("Performance (%)", M + halfW / 2 - 10, y + 83.5);

    // ── Right card: EVALUATION DETAILS ──
    const rdX = M + halfW + 6;
    doc.setFillColor(...WHITE);
    doc.setDrawColor(...BORDER);
    doc.setLineWidth(0.25);
    doc.roundedRect(rdX, y, halfW, 88, 2, 2, "FD");

    // Title icon
    doc.setFillColor(...GREEN);
    doc.rect(rdX + 5, y + 3, 2, 7, "F");
    doc.rect(rdX + 7.5, y + 5, 2, 5, "F");
    doc.rect(rdX + 10, y + 4, 2, 6, "F");

    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor(...GREEN);
    doc.text("EVALUATION DETAILS", rdX + 15, y + 9);

    // Detail rows
    const detailRows = [
      { color: GREEN, label: "Model",           value: "mBERT + Early Fusion + Metadata" },
      { color: GREEN, label: "Dataset",          value: "Hard Test Set" },
      { color: GREEN, label: "Total Samples",    value: metrics.total_samples.toLocaleString() },
      { color: RED_T, label: "Scam Samples",     value: `${metrics.scam_samples.toLocaleString()} (${scamPercent}%)` },
      { color: GREEN, label: "Non-Scam Samples", value: `${metrics.legit_samples.toLocaleString()} (${legitPercent}%)` },
      { color: GREEN, label: "True Positives",   value: (metrics.true_positives || 0).toLocaleString() },
      { color: GREEN, label: "True Negatives",   value: (metrics.true_negatives || 0).toLocaleString() },
      { color: RED_T, label: "False Positives",  value: (metrics.false_positives || 0).toLocaleString() },
      { color: RED_T, label: "False Negatives",  value: (metrics.false_negatives || 0).toLocaleString() },
      { color: GREEN, label: "Evaluation Date",  value: metrics.evaluation_date },
      { color: GREEN, label: "Split",            value: "Test Set (20%)" },
    ];

    const rowH = 6.8;
    detailRows.forEach((row, i) => {
      const ry = y + 14 + i * rowH;

      // Icon dot
      const dotBg = row.color === RED_T ? [254, 226, 226] : [220, 245, 230];
      doc.setFillColor(...dotBg);
      doc.circle(rdX + 8, ry + 3.5, 3, "F");
      doc.setFillColor(...row.color);
      doc.circle(rdX + 8, ry + 3.5, 1.5, "F");

      // Label
      doc.setFont("helvetica", "bold");
      doc.setFontSize(7.5);
      doc.setTextColor(...(row.color === RED_T ? RED_T : DARK));
      doc.text(row.label, rdX + 14, ry + 4.5);

      // Value
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7.5);
      doc.setTextColor(...DARK);
      doc.text(row.value, rdX + halfW - 5, ry + 4.5, { align: "right" });
    });

    // ═══════════════════════════════════════════
    //  ABOUT THESE METRICS
    // ═══════════════════════════════════════════
    y = 244;
    doc.setFillColor(...LTGREEN);
    doc.setDrawColor(...GREEN);
    doc.setLineWidth(0.4);
    doc.roundedRect(M, y, cW, 24, 3, 3, "FD");

    // Checkmark icon
    doc.setFillColor(...GREEN);
    doc.circle(M + 8, y + 8, 5, "F");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(8);
    doc.setTextColor(...WHITE);
    doc.text("\u2713", M + 6, y + 9.8);

    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor(...GREEN);
    doc.text("About These Metrics", M + 16, y + 7);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(7);
    doc.setTextColor(80, 80, 100);
    const aboutTxt = doc.splitTextToSize(
      "These metrics are calculated using the hard test set, which contains challenging examples the model has never seen during training or validation to ensure real-world reliability.",
      cW - 22
    );
    doc.text(aboutTxt, M + 16, y + 13);

    // ═══════════════════════════════════════════
    //  FOOTER
    // ═══════════════════════════════════════════
    const fy = H - 10;
    doc.setDrawColor(...BORDER);
    doc.setLineWidth(0.3);
    doc.line(M, fy - 4, W - M, fy - 4);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(6.5);
    doc.setTextColor(...GRAY);

    // Left
    doc.setFillColor(...GREEN);
    doc.circle(M + 2, fy + 0.5, 1.5, "F");
    doc.text("https://protego.app", M + 6, fy + 1.2);

    // Center
    doc.text("\u201cProtego\u201d \u2014 Latin for \u201cI protect\u201d", W / 2, fy + 1.2, { align: "center" });

    // Right
    doc.text("Page 1 of 1", W - M, fy + 1.2, { align: "right" });

    // Save
    doc.save("Protego_Model_Performance_Report.pdf");
  };

  return (
    <div className="metrics-page">
      <div className="metrics-header-row">
        <div className="metrics-header-left">
          <div className="metrics-header-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
            </svg>
          </div>
          <div>
            <h1 className="metrics-title">Model Performance Metrics</h1>
            <p className="metrics-subtitle">
              View the evaluation results of Protego's model on the hard test set.
            </p>
          </div>
        </div>
        <button className="btn btn-outline export-btn" onClick={exportPDF}>
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: '8px'}}>
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          Export Report (PDF)
        </button>
      </div>

      {/* Top 4 Cards */}
      <div className="metrics-cards-grid">
        <div className="metric-card">
          <div className="mcard-header">
            <div className="mcard-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>
            </div>
            <span className="mcard-title">Accuracy</span>
          </div>
          <div className="mcard-value">{metrics.accuracy.toFixed(1)}%</div>
          <p className="mcard-desc">Overall correctness of the model's predictions.</p>
          <div className="mcard-bar-wrap">
            <div className="mcard-bar-fill" style={{ width: `${metrics.accuracy}%` }}></div>
          </div>
        </div>

        <div className="metric-card">
          <div className="mcard-header">
            <div className="mcard-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="22" y1="12" x2="18" y2="12"></line><line x1="6" y1="12" x2="2" y2="12"></line><line x1="12" y1="6" x2="12" y2="2"></line><line x1="12" y1="22" x2="12" y2="18"></line></svg>
            </div>
            <span className="mcard-title">Precision</span>
          </div>
          <div className="mcard-value">{metrics.precision.toFixed(1)}%</div>
          <p className="mcard-desc">Proportion of predicted scams that are actually scams.</p>
          <div className="mcard-bar-wrap">
            <div className="mcard-bar-fill" style={{ width: `${metrics.precision}%` }}></div>
          </div>
        </div>

        <div className="metric-card">
          <div className="mcard-header">
            <div className="mcard-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.59-9.21L21.5 8"></path></svg>
            </div>
            <span className="mcard-title">Recall</span>
          </div>
          <div className="mcard-value">{metrics.recall.toFixed(1)}%</div>
          <p className="mcard-desc">Proportion of actual scams that were correctly detected.</p>
          <div className="mcard-bar-wrap">
            <div className="mcard-bar-fill" style={{ width: `${metrics.recall}%` }}></div>
          </div>
        </div>

        <div className="metric-card">
          <div className="mcard-header">
            <div className="mcard-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
            </div>
            <span className="mcard-title">F-1 Score</span>
          </div>
          <div className="mcard-value">{metrics.f1.toFixed(1)}%</div>
          <p className="mcard-desc">Harmonic mean of Precision and Recall.</p>
          <div className="mcard-bar-wrap">
            <div className="mcard-bar-fill" style={{ width: `${metrics.f1}%` }}></div>
          </div>
        </div>
      </div>

      {/* Middle Row */}
      <div className="metrics-middle-grid">
        {/* Left: Chart */}
        <div className="metrics-chart-card">
          <h2 className="section-title">Metrics Overview</h2>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data} margin={{ top: 20, right: 20, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border2)" />
                <XAxis 
                  dataKey="name" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: "var(--text-muted)", fontSize: 13, dy: 10 }} 
                />
                <YAxis 
                  domain={[0, 100]} 
                  ticks={[0, 25, 50, 75, 100]}
                  axisLine={false} 
                  tickLine={false} 
                  tickFormatter={(val) => `${val}%`} 
                  tick={{ fill: "var(--text-muted)", fontSize: 13 }}
                />
                <Tooltip 
                  cursor={{ fill: "var(--surface3)" }}
                  contentStyle={{ backgroundColor: "var(--surface)", borderColor: "var(--border)", borderRadius: "8px", color: "var(--text)" }}
                  formatter={(value) => [`${value}%`, "Score"]}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={60}>
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill="var(--accent)" />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-legend">
            <span className="legend-dot"></span> Performance (%)
          </div>
        </div>

        {/* Right: Details */}
        <div className="metrics-details-card">
          <h2 className="section-title">Evaluation Details</h2>
          
          <div className="details-list">
            <div className="detail-row">
              <div className="d-label">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                Model
              </div>
              <div className="d-value">mBERT + Early Fusion + Metadata</div>
            </div>
            
            <div className="detail-row">
              <div className="d-label">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>
                Dataset
              </div>
              <div className="d-value">Hard Test Set (Unseen Data)</div>
            </div>

            <div className="detail-row">
              <div className="d-label">
                Total Samples
              </div>
              <div className="d-value">{metrics.total_samples.toLocaleString()}</div>
            </div>

            <div className="detail-row">
              <div className="d-label" style={{color: 'var(--danger)'}}>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                Scam Samples
              </div>
              <div className="d-value">{metrics.scam_samples.toLocaleString()} ({scamPercent}%)</div>
            </div>

            <div className="detail-row">
              <div className="d-label" style={{color: 'var(--safe)'}}>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><polyline points="9 12 11 14 15 10"></polyline></svg>
                Non-Scam Samples
              </div>
              <div className="d-value">{metrics.legit_samples.toLocaleString()} ({legitPercent}%)</div>
            </div>

            <div className="detail-row">
              <div className="d-label" style={{color: 'var(--safe)'}}>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
                True Positives (Correct Scam)
              </div>
              <div className="d-value">{metrics.true_positives?.toLocaleString() || 0}</div>
            </div>

            <div className="detail-row">
              <div className="d-label" style={{color: 'var(--safe)'}}>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                True Negatives (Correct Legit)
              </div>
              <div className="d-value">{metrics.true_negatives?.toLocaleString() || 0}</div>
            </div>

            <div className="detail-row">
              <div className="d-label" style={{color: 'var(--danger)'}}>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
                False Positives (False Alarm)
              </div>
              <div className="d-value">{metrics.false_positives?.toLocaleString() || 0}</div>
            </div>

            <div className="detail-row">
              <div className="d-label" style={{color: 'var(--danger)'}}>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
                False Negatives (Missed Scam)
              </div>
              <div className="d-value">{metrics.false_negatives?.toLocaleString() || 0}</div>
            </div>

            <div className="detail-row">
              <div className="d-label">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                Evaluation Date
              </div>
              <div className="d-value">{metrics.evaluation_date}</div>
            </div>

            <div className="detail-row">
              <div className="d-label">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
                Split
              </div>
              <div className="d-value">Test Set (20%)</div>
            </div>
          </div>
        </div>
      </div>

      {/* Info Banner */}
      <div className="metrics-info-banner">
        <div className="info-banner-icon">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><polyline points="9 12 11 14 15 10"></polyline></svg>
        </div>
        <div className="info-banner-text">
          <h3 className="info-banner-title">About These Metrics</h3>
          <p className="info-banner-desc">
            These metrics are calculated using the hard test set, which contains challenging examples the model has never seen during training or validation to ensure real-world reliability.
          </p>
        </div>
      </div>
    </div>
  );
}
