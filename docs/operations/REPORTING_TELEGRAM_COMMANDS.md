# INKA Admin — Executive Reporting Telegram Commands
**System:** INKA Admin Telegram Bot
**Version:** 1.0 | **Updated:** 2026-02-22
**Access:** Admin / Executive roles only

---

## Command Reference

### `/report monthly`

**Purpose:** Generate and deliver the full monthly executive report.

**Behavior:**
- Compiles all 8 report sections for the current or specified month
- Calculates all 8 KPIs from live data sources
- Identifies top 3 risks via AI Risk Predictor
- Renders traffic light status per domain
- Delivers report as a formatted Telegram message + PDF attachment

**Syntax:**
```
/report monthly
/report monthly 2026-01
/report monthly previous
```

**Example Response:**
```
📊 INKA Admin — Monthly Report
Period: February 2026
Generated: 2026-02-22 08:51 UTC

🚦 SYSTEM STATUS
✅ Stability     GREEN  (99.91% uptime)
⚠️  Security     YELLOW (1 High CVE open)
✅ Compliance    GREEN  (90/100)
⚠️  Release      YELLOW (CFR 12.5%)
✅ Engineering   GREEN  (+12% velocity)

📈 KEY METRICS
• Uptime: 99.91%
• CFR: 12.5% ⚠️
• MTTR: 23 min ✅
• Risk Score: 34/100 ✅ (↓ from 41)
• Compliance: 90/100 ✅
• Chaos Resilience: 83.3% ✅
• Self-Healing: 83.3% ✅
• Critical Defects: 0 ✅

📄 Full report attached.
Use /report executive summary for condensed view.
```

---

### `/report executive summary`

**Purpose:** Deliver a condensed, board-ready summary (fits in a single Telegram message).

**Behavior:**
- 5 key metrics only (uptime, CFR, MTTR, risk score, compliance)
- Traffic light status per domain (5 lines)
- 1-paragraph narrative
- Call to action if any YELLOW/RED domains exist

**Syntax:**
```
/report executive summary
/report exec summary
/report exec
```

**Example Response:**
```
🏢 INKA Admin — Executive Summary
Period: February 2026

🚦 STATUS BOARD
✅ Stability      GREEN
⚠️  Security      YELLOW
✅ Compliance     GREEN
⚠️  Release Health YELLOW
✅ Engineering    GREEN

📊 KPIs AT A GLANCE
Uptime: 99.91% | CFR: 12.5% | MTTR: 23min
Risk: 34/100 | Compliance: 90/100

📝 NARRATIVE
Platform delivered stable performance this month with
zero critical incidents (6th consecutive month). Watch
items: CFR at 12.5% (target <10%) and 1 open High CVE
— both under active remediation, ETA <1 week.

✅ No board action required.
```

---

### `/report risk overview`

**Purpose:** Deliver the top 3 risk narrative with mitigation status and next-month prediction.

**Behavior:**
- Pulls top 3 risks from AI Risk Predictor
- Shows current score, mitigation status, owner, and ETA
- Includes next-month risk prediction for each
- Flags if any risk requires board-level decision

**Syntax:**
```
/report risk overview
/report risks
/risk status
```

**Example Response:**
```
⚠️ INKA Admin — Risk Overview
Period: February 2026

🔴 RISK-01: Change Failure Rate (61/100)
Category: Release Health
Status: 🟡 IN PROGRESS
Driver: CFR at 12.5% vs 10% target
Fix: Tightening pre-deploy smoke tests
ETA: 2 weeks
Next month: Expected GREEN if gates enforced

🟡 RISK-02: High CVE in Container Image (52/100)
Category: Security
Status: 🟠 SCHEDULED
Driver: 1 High CVE (non-exploitable in current config)
Fix: Base image upgrade in next release
ETA: 3 days
Next month: Expected GREEN post-upgrade

🟡 RISK-03: API Uptime Below SLA (44/100)
Category: Stability
Status: 🟡 IN PROGRESS
Driver: 99.87% vs 99.9% SLA target
Fix: Redis HA review + self-healing tuning
ETA: 10 days
Next month: Expected GREEN

📊 Overall Risk Score: 34/100 (↓ improving)
✅ No board escalation required.
```

---

## Additional Reporting Commands

### `/report kpi [metric]`

Fetch a single KPI value on demand.

```
/report kpi uptime
/report kpi cfr
/report kpi mttr
/report kpi risk
/report kpi compliance
/report kpi chaos
/report kpi selfheal
/report kpi defects
```

**Example:**
```
/report kpi uptime

📈 Uptime — Current Period
API Service:    99.87% ⚠️
Telegram Bot:   99.94% ✅
Admin Panel:    99.91% ✅
Database:       99.99% ✅
Redis:          99.97% ✅
──────────────────────────
Aggregate:      99.91% ✅
SLA Target:     99.9%
Status:         🟡 YELLOW (API marginally below)
```

---

### `/report compare [month1] [month2]`

Compare KPIs between two reporting periods.

```
/report compare 2026-01 2026-02
```

**Example:**
```
📊 KPI Comparison: Jan → Feb 2026

Uptime:      99.88% → 99.91% ▲ +0.03%
CFR:         8.3%   → 12.5%  ▼ -4.2pp ⚠️
MTTR:        41min  → 23min  ▲ -18min
Risk Score:  41     → 34     ▲ -7 pts
Compliance:  87     → 90     ▲ +3 pts
Chaos:       75%    → 83.3%  ▲ +8.3%
Self-Heal:   77.8%  → 83.3%  ▲ +5.5%
Defects:     1      → 0      ▲ Cleared
```

---

### `/report schedule`

Check when the next automated report will be generated.

```
/report schedule

📅 Report Schedule
Next Monthly Report:  2026-03-01 06:00 UTC
Next Weekly Digest:   2026-02-23 07:00 UTC
Last Generated:       2026-02-22 08:51 UTC
Recipients:           CTO, Board Distribution List
Format:               Telegram + PDF
```

---

## Access Control

| Command | Minimum Role | Telegram Access |
|---------|-------------|----------------|
| `/report monthly` | ADMIN / EXECUTIVE | ✅ |
| `/report executive summary` | ADMIN / EXECUTIVE / MANAGER | ✅ |
| `/report risk overview` | ADMIN / EXECUTIVE | ✅ |
| `/report kpi` | ADMIN / MANAGER / DEVOPS | ✅ |
| `/report compare` | ADMIN | ✅ |
| `/report schedule` | ADMIN | ✅ |

---

## Bot Handler Implementation Reference

```python
# apps/bot/src/handlers/reporting.py

REPORT_COMMANDS = {
    "/report monthly": handle_report_monthly,
    "/report executive summary": handle_report_exec_summary,
    "/report exec summary": handle_report_exec_summary,
    "/report exec": handle_report_exec_summary,
    "/report risk overview": handle_report_risk_overview,
    "/report risks": handle_report_risk_overview,
    "/risk status": handle_report_risk_overview,
    "/report kpi": handle_report_kpi,
    "/report compare": handle_report_compare,
    "/report schedule": handle_report_schedule,
}

# Role gate decorator
@require_role(["ADMIN", "EXECUTIVE"])
async def handle_report_monthly(update, context):
    report = await executive_reporting_agent.generate_monthly()
    await update.message.reply_text(report.telegram_format)
    await update.message.reply_document(report.pdf_bytes, filename=report.filename)
```

---

*Maintained by: Platform Engineering | Telegram Bot v1.0+*
