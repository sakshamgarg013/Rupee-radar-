# RupeeRadar — Project Context

## 1. Problem Background

Working professionals in India routinely make **hundreds of monthly transactions** across UPI, cards, bank transfers, subscriptions, EMIs, rent, shopping, food delivery, travel, and investments. Although bank statements contain all this information, they are difficult to understand because:

- Transaction descriptions are **messy and inconsistent** (e.g. `UPI/DR/123456/SWIGGY`).
- Manual categorization is tedious and error-prone.
- There is no easy way to extract recurring payments or spending patterns from raw data.

---

## 2. What Is RupeeRadar?

**RupeeRadar** is an **AI-powered personal finance assistant** that helps users understand _where their money is going_ by analyzing their bank statement data.

The application allows a user to:

1. **Upload** bank statement data (CSV, Excel, or PDF).
2. **Extract & clean** transactions into a structured format.
3. **Categorize** expenses into meaningful groups.
4. **Detect** recurring payments (subscriptions, EMIs, SIPs, rent, insurance).
5. **Generate** spending insights with real transaction amounts.
6. **Present** results in a simple dashboard or downloadable report.

---

## 3. Objective

Create an **end-to-end solution** that converts raw financial transaction data into meaningful personal finance insights.

The solution should help users answer questions such as:

- What are my biggest spending categories?
- How much did I spend this month?
- Which transactions are recurring subscriptions or EMIs?
- What was my biggest transaction?
- What are the top insights from my spending behavior?

---

## 4. Core Requirements

| # | Requirement | Details |
|---|-------------|---------|
| 1 | **Accept bank statement data** | Support CSV as primary format; Excel and PDF as stretch goals |
| 2 | **Extract / clean transactions** | Parse raw rows, normalize dates (ISO 8601), amounts (INR), and descriptions |
| 3 | **Categorize transactions** | Assign to: `Food`, `Travel`, `Shopping`, `Bills`, `EMI`, `Subscriptions`, `Salary`, `Rent`, `Investments`, `Other` |
| 4 | **Identify recurring transactions** | Detect subscriptions, EMIs, rent, SIPs, insurance payments via frequency/amount pattern analysis |
| 5 | **Calculate financial metrics** | Total income, total spend, savings, savings rate, top categories, biggest transactions |
| 6 | **Generate human-readable insights** | ≥ 3 personalized insights using actual transaction amounts |
| 7 | **Present via UI / dashboard / report** | Interactive dashboard with charts, tables, and a downloadable/shareable report |

---

## 5. Category Taxonomy

Fixed enum of categories:

| Category        | Typical Direction |
|-----------------|-------------------|
| Food            | Debit             |
| Travel          | Debit             |
| Shopping        | Debit             |
| Bills           | Debit             |
| EMI             | Debit             |
| Subscriptions   | Debit             |
| Salary          | Credit            |
| Rent            | Debit             |
| Investments     | Credit / Debit    |
| Other           | Fallback          |

---

## 6. Expected Deliverables

The final submission must demonstrate:

- [x] Cleaned transaction data
- [x] Categorized expenses
- [x] Recurring payment detection
- [x] Spend summary dashboard
- [x] At least **three personalized financial insights**
- [x] A final report or visual summary that can be shared

---

## 7. Evaluation Criteria

| Criterion | Weight |
|-----------|--------|
| Accuracy of transaction cleaning & categorization | High |
| Quality of financial insights | High |
| Handling of real-world messy transaction descriptions | High |
| Simplicity and usefulness of user experience | Medium |
| Completeness of end-to-end workflow | Medium |
| Privacy-conscious handling of sensitive financial data | Medium |

---

## 8. Scope & Constraints

- **Prototype-first**: Prioritize a working end-to-end prototype over perfect support for every bank format.
- **Bank format support**: Start with 1–2 common Indian bank CSV exports (e.g. HDFC, ICICI, SBI). Generic CSV mapper as fallback.
- **Technology stack**: Participants may choose their own stack; the following is recommended:

| Layer              | Recommendation                          | Alternatives              |
|--------------------|-----------------------------------------|---------------------------|
| Frontend           | React + TypeScript + Tailwind           | Next.js, Vue              |
| Backend            | Python FastAPI                          | Node.js Express, Django   |
| Database           | SQLite (local) → PostgreSQL (deployed)  | —                         |
| File Parsing       | pandas + bank-specific parsers          | openpyxl, pdfplumber      |
| AI Categorization  | LLM API (Groq) with structured output   | Rule engine + LLM fallback|
| Charts             | Recharts or Chart.js                    | D3                        |
| Report Export      | HTML → PDF (weasyprint / browser print) | —                         |
| Deployment         | Docker + single VM / Railway / Render   | Local-only demo           |

> **Note:** The LLM provider used in this project will be **Groq**.

---

## 9. Categorization Strategy

A **hybrid approach** is recommended:

1. **Rule engine** — fast, high precision for known patterns (e.g. `SWIGGY` → Food, `NETFLIX` → Subscriptions).
2. **Merchant dictionary lookup** — matches against a curated list of Indian merchants.
3. **LLM batch categorization** — for unmatched transactions; uses structured JSON output with confidence scores.
4. **Fallback** — anything below confidence threshold (e.g. < 0.6) → `Other`.

---

## 10. Recurring Payment Detection

Heuristic algorithm:

1. Group debits by similar `description_clean` (fuzzy match).
2. Within each group, check:
   - ≥ 2 occurrences
   - Amount within tolerance (±5% or ±₹50)
   - Intervals consistent with expected cadence (~28–32 days for monthly)
3. Label group from merchant name or dominant keyword.
4. Supported frequencies: `weekly`, `monthly`, `quarterly`, `yearly`, `unknown`.

---

## 11. Key Metrics

| Metric             | Definition                                         |
|--------------------|----------------------------------------------------|
| Total Income       | Sum of credits in selected period                  |
| Total Spend        | Sum of debits (absolute value)                     |
| Savings            | Income − Spend                                     |
| Savings Rate       | (Savings / Income) × 100                           |
| Top Categories     | Debit totals grouped by category, sorted descending|
| Biggest Transaction| Single largest debit (and optionally credit)        |
| Monthly Spend      | Debits grouped by calendar month                   |
| Recurring Total    | Sum of typical amounts from recurring groups        |

---

## 12. Insight Generation

**Two-tier approach:**

### Tier 1 — Template Insights (deterministic, always available)
- "You spent ₹X on Food this month — your largest category."
- "Your biggest transaction was ₹Y to {merchant} on {date}."
- "We detected N recurring payments totalling ₹Z/month."

### Tier 2 — LLM-Enhanced Insights (optional)
- Feed metrics + top categories + recurring summary (not raw PII) to LLM.
- Generate 2–3 narrative observations about spending trends and category shifts.

> Insights **must cite actual transaction amounts** per requirements.

---

## 13. Privacy & Security Principles

- **No persistent storage of raw files** — delete after successful parse.
- **Session TTL** — auto-delete sessions after 24–72 hours (configurable).
- **Minimal LLM payload** — send only cleaned descriptions and amounts, never account numbers or full raw statements.
- **No cross-user data** — sessions are anonymous or single-user.
- **No client-side storage** of financial data.
- **HTTPS** for transport; CORS restricted to frontend origin.
- Secrets managed via `.env` (not committed to version control).

---

## 14. User Experience Principles

- Show **cleaned data alongside raw descriptions** for transparency.
- Allow **category override** by the user (improves trust).
- Provide **clear errors** for unsupported formats with sample CSV template.
- **Desktop-first** layout (for tables), but mobile-responsive.
- **Inspectable output** — users see cleaned data, not just a black-box summary.

---

## 15. Final Deliverable

A **deployed or locally runnable application** that takes raw bank statement data and produces a clear personal finance summary showing where the user's money is going.

---

## 16. Project Documentation Structure

```
docs/
├── context.md              ← This file
├── architecture.md         ← Detailed system architecture
├── implementation-plan.md  ← Phase-wise implementation plan
└── edge-cases.md           ← Corner scenarios and potential bugs
```
