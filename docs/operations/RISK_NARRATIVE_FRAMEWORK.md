# INKA Admin — Risk Narrative Framework
**System:** INKA Admin Executive Reporting
**Version:** 1.0 | **Updated:** 2026-02-22
**Audience:** CTO / Board / Investors

---

## Framework Purpose

The Risk Narrative Framework provides a **structured, repeatable methodology** for translating raw risk signals (AI Risk Predictor scores, incident data, vulnerability counts, compliance gaps) into plain-language executive narratives. Every monthly report must include exactly **three top risks**, each with a defined mitigation status and a forward-looking prediction.

---

## 1. Risk Identification Process

### Risk Signal Sources

```
┌──────────────────────────────────────────────────────┐
│                  RISK SIGNAL INPUTS                  │
├──────────────────────────────────────────────────────┤
│  AI Risk Predictor  ──► Deployment risk signals      │
│  Security Scanner   ──► CVE counts / severity        │
│  Incident Log       ──► P0/P1 incidents, MTTR trend  │
│  Compliance Agent   ──► Policy adherence score       │
│  Chaos Framework    ──► Resilience failure points    │
│  DORA Metrics       ──► CFR, Lead Time trends        │
│  Self-Healing Log   ──► Escalation rate              │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
           Risk Scoring Engine (0–100 per risk)
                       │
                       ▼
          Rank → Select Top 3 → Generate Narrative
```

### Risk Scoring Criteria

Each identified risk is scored **0–100** based on:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Probability | 30% | Likelihood of incident occurring this month |
| Impact | 35% | Potential business / operational impact |
| Velocity | 20% | How fast the situation could worsen if untreated |
| Detectability | 15% | How easily the risk would be detected before impact |

**Composite Score = P×0.3 + I×0.35 + V×0.2 + D×0.15**

### Risk Categories

| Category | Signal Source | Example |
|----------|--------------|---------|
| **Release Health** | CFR, Quality Score | High failure rate, blocked releases |
| **Security** | CVE scanner, IAM drift | Open High/Critical CVEs |
| **Stability** | Uptime, MTTR | SLA breach approaching |
| **Compliance** | Compliance Agent | Framework score declining |
| **Operational** | Self-Healing, Chaos | Resilience gaps, escalation rate |
| **Capacity** | Cloud Monitoring | Resource saturation approaching |

---

## 2. Risk Narrative Template

### Top Risk Entry Format

```markdown
### RISK-{N}: {Risk Title} {Traffic Light Emoji}

| Field | Value |
|-------|-------|
| Category | {Release Health / Security / Stability / Compliance / Operational / Capacity} |
| Score | {X} / 100 ({Low / Medium / Medium-High / High / Critical}) |
| Driver | {1–2 sentence root cause description} |
| Mitigation | {Specific action being taken} |
| Status | {🟢 COMPLETE / 🟡 IN PROGRESS / 🔴 BLOCKED} — ETA: {date} |
| Owner | {Team or person} |
| Next-Month Expectation | {Predicted state if mitigation succeeds} |
```

### Score → Severity Mapping

| Score Range | Severity Label | Board Action |
|-------------|---------------|--------------|
| 0–25 | Low | Monitor only |
| 26–45 | Medium | Track in weekly review |
| 46–65 | Medium-High | Active mitigation required |
| 66–80 | High | Escalate to leadership |
| 81–100 | Critical | Emergency response |

---

## 3. Risk Narrative Writing Guidelines

### Tone and Language Rules

| ✅ DO | ❌ AVOID |
|-------|---------|
| Use plain business language | Technical jargon without explanation |
| Quantify impact (users affected, minutes, %) | Vague "some degradation occurred" |
| State clear ownership | Anonymous "the team will" |
| Give specific ETAs | "soon" or "we plan to" |
| Connect risk to business outcome | Pure technical description |

### Narrative Voice Examples

**Too Technical:**
> "The Redis connection pool hit its ulimit cap under concurrent goroutine pressure."

**Executive-Ready:**
> "Peak booking traffic temporarily exhausted the caching layer's connection limit, causing 23 minutes of elevated API response times. No customer data was lost or exposed."

---

## 4. Mitigation Status Classification

| Status | Criteria | Suggested Board Message |
|--------|----------|------------------------|
| 🟢 **COMPLETE** | Risk fully remediated; evidence confirmed | "Risk cleared — no further action needed" |
| 🟡 **IN PROGRESS** | Active mitigation underway; ETA defined | "Under active remediation — monitor next cycle" |
| 🟠 **SCHEDULED** | Fix identified; not yet started; ETA set | "Planned in upcoming sprint — watch item" |
| 🔴 **BLOCKED** | Mitigation blocked by dependency or decision | "Escalation required — board input may be needed" |
| ⚪ **ACCEPTED** | Risk accepted as within tolerance; no action | "Accepted within risk appetite — documented" |

---

## 5. Expected Next-Month Risk Prediction

For each top risk, provide:

1. **Baseline scenario** (mitigation succeeds on schedule)
2. **Downside scenario** (mitigation delayed or fails)
3. **Probability of improvement** (%)

### Prediction Template

```
Next Month Outlook for {Risk Title}:
→ Baseline (70%): {Expected state if current mitigation succeeds}
→ Downside (30%): {Risk if mitigation is delayed or blocked}
→ Trigger for escalation: {Specific condition that would require board attention}
```

---

## 6. Risk Trend Narrative (6-Month)

Include in every monthly report:

```
Overall Risk Trajectory:
Month -5: {score} — {brief descriptor}
Month -4: {score} — {brief descriptor}
Month -3: {score} — {brief descriptor}
Month -2: {score} — {brief descriptor}
Month -1: {score} — {brief descriptor}
Month 0 (current): {score} — {brief descriptor}

Trend analysis: {1–2 sentence commentary on direction and significance}
```

---

## 7. Board-Level Risk Summary (1-Page Format)

For board pack submissions, use this condensed format:

### One-Page Risk Summary

**Platform: INKA Admin | Period: {{MONTH YEAR}}**

| | Risk | Score | Status | ETA |
|--|------|-------|--------|-----|
| 🔴 | {Highest risk title} | {X}/100 | {Status} | {Date} |
| 🟡 | {Second risk title} | {X}/100 | {Status} | {Date} |
| 🟡 | {Third risk title} | {X}/100 | {Status} | {Date} |

**Overall Risk Score: {X}/100 — {Direction} vs last month**

**In plain terms:**
> {2–3 sentence non-technical summary of the platform's risk posture and what the board should know}

**Board Action Required:** {Yes / No — and if yes, what decision is needed}

---

*Risk Narrative Framework — Maintained by: Platform Engineering*
*Review cycle: Quarterly or after any P0 incident*
