# INKA Admin — Visual Summary Plan
**System:** INKA Admin Executive Reporting
**Version:** 1.0 | **Updated:** 2026-02-22
**Purpose:** Define the visual layout, chart types, and data mappings for the executive reporting dashboard and monthly report PDF.

---

## 1. Traffic Light Status Board

### Layout
```
┌─────────────────────────────────────────────┐
│    INKA Admin — System Status at a Glance   │
│    Period: {{MONTH YEAR}}                   │
├───────────────┬────────────┬────────────────┤
│  Domain       │  Status    │  Trend         │
├───────────────┼────────────┼────────────────┤
│  Stability    │  🟢 GREEN  │  ▲ +0.4%       │
│  Security     │  🟡 YELLOW │  → stable      │
│  Compliance   │  🟢 GREEN  │  ▲ improving   │
│  Release      │  🟡 YELLOW │  ▼ CFR up      │
│  Engineering  │  🟢 GREEN  │  ▲ +12% vel.   │
└───────────────┴────────────┴────────────────┘
```

### Traffic Light Rules

| Domain | GREEN Condition | YELLOW Condition | RED Condition |
|--------|----------------|------------------|---------------|
| Stability | Uptime ≥ 99.9%, 0 P0/P1 incidents | Uptime 99.5–99.9% OR 1 P1 | Uptime < 99.5% OR any P0 |
| Security | 0 Critical/High CVEs, IAM clean | 1–2 High CVEs (non-exploitable) | Any Critical CVE OR IAM breach |
| Compliance | Score ≥ 85, 0 policy violations | Score 70–84 OR 1 minor exception | Score < 70 OR audit finding |
| Release Health | CFR < 10%, QS avg ≥ 90 | CFR 10–20% OR QS 80–90 | CFR > 20% OR QS < 80 |
| Engineering | DORA Elite/High, velocity ▲ | Any DORA metric Medium | Multiple DORA metrics Low |

---

## 2. KPI Gauge Charts

### Chart: Uptime Gauge (per service)
- **Type:** Radial gauge / donut chart
- **Range:** 99.0% – 100.0%
- **Color zones:** Red < 99.5% | Yellow 99.5–99.9% | Green ≥ 99.9%
- **Display:** Large center % value + SLA target line

### Chart: Risk Score Trend (6-month)
- **Type:** Line chart with shaded area
- **X-axis:** Last 6 months
- **Y-axis:** 0–100 (inverted — lower is better)
- **Color:** Line color transitions: Green (< 40) → Yellow (40–65) → Red (> 65)
- **Annotations:** Month-over-month delta labels

### Chart: DORA Metrics Radar
- **Type:** Radar / spider chart
- **Axes:** Deployment Frequency | Lead Time | CFR | MTTR
- **Overlays:** Current month vs. last month vs. Elite target
- **Colors:** Current = blue, Previous = grey, Target = green dashed

### Chart: Quality Score Distribution
- **Type:** Horizontal bar chart
- **X-axis:** Quality Score (0–100)
- **Y-axis:** Each release version
- **Color segments:** 0–79 Red | 80–89 Yellow | 90–100 Green
- **Reference lines:** Prod gate (90) and Stage gate (80) as vertical dashed lines

### Chart: Incident Count by Severity (monthly trend)
- **Type:** Stacked bar chart
- **X-axis:** Last 6 months
- **Y-axis:** Count
- **Bars:** P0 (red) | P1 (orange) | P2 (yellow) | P3 (grey)

### Chart: Self-Healing Success vs. Escalation
- **Type:** Donut chart
- **Segments:** Auto-resolved (green) | Escalated (orange) | Agent not triggered (grey)
- **Center label:** Success %

### Chart: Compliance Score by Framework
- **Type:** Grouped horizontal bar chart
- **Bars per group:** ISO 27001 | SOC2 | GDPR | Internal
- **Benchmark line:** 85 (minimum acceptable)

---

## 3. Executive Report PDF Layout

### Page 1 — Cover & Traffic Light
```
┌─────────────────────────────────────────────┐
│  [INKA Logo]   Monthly Executive Report     │
│  Period: {{MONTH YEAR}}                     │
│  Classification: Confidential               │
├─────────────────────────────────────────────┤
│  TRAFFIC LIGHT STATUS BOARD                 │
│  [5-row table with colored status cells]    │
├─────────────────────────────────────────────┤
│  EXECUTIVE NARRATIVE (3–4 paragraphs)       │
└─────────────────────────────────────────────┘
```

### Page 2 — KPI Dashboard
```
┌───────────┬───────────┬───────────┬──────────┐
│  Uptime   │  CFR      │  MTTR     │  Risk    │
│  [gauge]  │  [gauge]  │  [gauge]  │  [line]  │
├───────────┴───────────┴───────────┴──────────┤
│  Compliance Score    │  Self-Healing Donut   │
│  [bar chart]         │  [donut chart]        │
└──────────────────────┴───────────────────────┘
```

### Page 3 — Stability & Release
```
┌─────────────────────┬───────────────────────┐
│  Uptime by Service  │  DORA Radar Chart     │
│  [stacked bars]     │  [radar / spider]     │
├─────────────────────┼───────────────────────┤
│  Incident Trend     │  Quality Score Dist.  │
│  [stacked bars]     │  [horizontal bars]    │
└─────────────────────┴───────────────────────┘
```

### Page 4 — Risk & Security
```
┌──────────────────────────────────────────────┐
│  TOP 3 RISKS                                 │
│  [RISK-01 panel with score, status, ETA]     │
│  [RISK-02 panel with score, status, ETA]     │
│  [RISK-03 panel with score, status, ETA]     │
├──────────────────────────────────────────────┤
│  Risk Score 6-Month Trend [line chart]       │
└──────────────────────────────────────────────┘
```

### Page 5 — Engineering & Cost
```
┌────────────────────┬─────────────────────────┐
│  Velocity Metrics  │  Chaos Resilience       │
│  [KPI table]       │  [pass/fail bar]        │
├────────────────────┼─────────────────────────┤
│  Cost Breakdown    │  Automation Coverage    │
│  [pie chart]       │  [progress bars]        │
└────────────────────┴─────────────────────────┘
```

---

## 4. Telegram Visual Formatting

Since Telegram is text-based, visual elements are represented using **Unicode symbols, emoji, and ASCII tables**:

### Color Encoding
| Visual | Meaning |
|--------|---------|
| ✅ or 🟢 | GREEN — On target |
| ⚠️ or 🟡 | YELLOW — Watch item |
| 🚨 or 🔴 | RED — Action required |
| ▲ | Improving trend |
| ▼ | Declining trend |
| → | Stable trend |

### Progress Bar (for % metrics)
```
Uptime: [████████████████████░░░] 99.91%
CFR:    [███████░░░░░░░░░░░░░░░░] 12.5%
```

Format: `[` + `█` × (value/5) + `░` × (20 − value/5) + `]`

### Spark Line (for trends)
```
Risk Score Trend (6mo): 48 ▬ 45 ▬ 41 ▬ 38 ▬ 36 ▬ 34 📉
```

---

## 5. Admin Panel Dashboard Spec

### Technology Stack
- **Framework:** React + Vite (existing Admin Panel)
- **Charting:** Chart.js or Recharts
- **Data refresh:** Every 5 minutes (live KPIs), monthly snapshots for reports

### Dashboard Sections
1. **Header bar:** Current month, generation timestamp, report status
2. **Traffic Light Grid:** 5 domain cards with color coding
3. **KPI Tiles Row:** 8 KPI values with delta vs. last month
4. **Charts Panel:** Tabbed (Stability | Release | Security | Compliance | Velocity)
5. **Risk Panel:** Top 3 risks with expand-on-click details
6. **Report Actions:** Generate PDF, Send Telegram, Schedule next report

---

*Visual Summary Plan — Maintained by: Platform Engineering*
*Design system: aligned with existing Admin Panel component library*
