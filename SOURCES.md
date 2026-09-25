# SOURCES

Every external figure or legal citation used anywhere in AssureLens — in the product UI, the control library, the PRD or the README — is recorded here with its source, access date, and the verbatim wording it rests on.

Rule: **if a claim is not in this file, it does not appear in the product.**

Access date for all entries below: **2026-09-21**.

---

## A. Primary legal sources (authoritative)

### A1. Digital Personal Data Protection Rules, 2025
- **Citation:** G.S.R. 846(E), Ministry of Electronics and Information Technology, New Delhi, dated **13 November 2025**.
- **Official URL:** https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa
- **Gazette PDF (bilingual):** https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf
- **English working copy used for extraction:** https://www.dpdpa.com/DPDP_Rules_2025_English_only.pdf
- **Note on date discrepancy:** the gazette notification itself is dated **13 November 2025**; the MeitY document library lists the publication year/date as **14.11.2025**. Secondary sources cite 13, 14 or 17 November. **The product uses 13 November 2025**, the date on the instrument, and states this note wherever the date is shown.
- **Corrigendum:** **G.S.R. 892(E)**, dated **11 December 2025** — corrects two typographical errors in Rule 1(3) and Rule 1(4) ("of this Gazette" → "in the Official Gazette"). No rule numbering, commencement period, or substantive text changed; the 13 May 2027 date and every other citation in this file are unaffected. **Reviewed 2026-09-25 — see D1, closed.** Confirmed via two independent secondary sources (a legal-industry aggregator and a corrigendum-text mirror); the raw e-Gazette PDF for this specific corrigendum could not be reached directly, so this entry carries the same `source_status: unverified` caveat as any secondary-only citation in this project, not a primary-source guarantee. An earlier draft of this entry recorded the corrigendum's date as 16 December 2025 (MeitY document library indexing), the same instrument-vs-library discrepancy already noted above for the Rules themselves; 11 December 2025 is the gazette's own date on G.S.R. 892(E).

#### A1.1 Commencement schedule — verbatim from Rule 1
> "(2) Rules 1, 2 and 17 to 21 shall come into force on the date of their publication in the Official Gazette.
> (3) Rule 4 shall come into force one year after the date of publication of this Gazette.
> (4) Rules 3, 5 to 16, 22 and 23 shall come into force eighteen months after the date of publication of this Gazette."

Derived dates (arithmetic from 13 November 2025):
| Tranche | Rules | Effective |
|---|---|---|
| Immediate | 1, 2, 17–21 | 13 Nov 2025 |
| +12 months | 4 (Consent Manager registration) | 13 Nov 2026 |
| +18 months | 3, 5–16, 22, 23 (core operating obligations) | **13 May 2027** |

The widely-quoted "13 May 2027" deadline is therefore **confirmed by arithmetic on the instrument itself**, not taken on a vendor blog's word.

#### A1.2 Rule inventory used by the control library
| Rule | Title (verbatim) |
|---|---|
| 3 | Notice given by Data Fiduciary to Data Principal |
| 4 | Registration and obligations of Consent Manager |
| 6 | Reasonable security safeguards |
| 7 | Intimation of personal data breach |
| 8 | Time period for specified purpose to be deemed as no longer being served |
| 9 | Contact information of person to answer questions about processing |
| 10 | Verifiable consent for processing of personal data of child |
| 12 | Exemptions from certain obligations applicable to processing of personal data of child |
| 13 | Additional obligations of Significant Data Fiduciary |
| 14 | Rights of Data Principals |
| 15 | Transfer of personal data outside the territory of India |
| 16 | Exemption from Act for research, archiving or statistical purposes |
| 22 | Appeal to Appellate Tribunal |
| 23 | Calling for information from Data Fiduciary or intermediary |

Schedules referenced: First (Consent Manager conditions Part A / obligations Part B), Second (research/archiving/statistical standards), Third (retention classes and periods), Fourth (children's data — Part A classes, Part B purposes), Seventh (log retention purposes).

#### A1.3 Key operative text relied on
**Rule 6(1) — reasonable security safeguards.** Verbatim, the minimum set:
> "(a) appropriate data security measures, such as securing of personal data through encryption, obfuscation, masking or the use of virtual tokens mapped to that personal data;
> (b) appropriate measures to control access to the computer resources used by such Data Fiduciary or such a Data Processor, wherever applicable;
> (c) visibility on the accessing of such personal data, through appropriate logs, monitoring and review, for enabling detection of unauthorised access, its investigation and remediation to prevent recurrence;
> (d) reasonable measures for continued processing in the event of confidentiality, integrity or availability of such personal data being compromised … such as by way of data-backups;"

This clause is the backbone of controls **DPDP-06-xx** — it is what makes encryption, access control, access logging and backup *legally testable* rather than best-practice.

**Rule 7(1) — breach intimation to Data Principal.** Required content: description of the breach (nature, extent, timing); consequences likely for her; mitigation measures implemented; safety measures she may take; business contact information of a responder. Intimation is "without delay."

**Rule 8 — retention and erasure.**
- 8(1): erase personal data after the Third Schedule period if the Data Principal neither approaches the Fiduciary for the specified purpose nor exercises her rights, unless retention is legally required.
- 8(2): "At least forty-eight hours before completion of the time period for erasure … inform the Data Principal."
- 8(3): retain personal data, associated traffic data and other logs "for a minimum period of one year from the date of such processing" for Seventh Schedule purposes.
- Third Schedule illustrative period seen in text: **three years** from last approach / rights exercise / commencement of the Rules, whichever is latest, for the listed classes.

> **Tension worth surfacing in the product:** Rule 8(1) compels erasure while Rule 8(3) compels a one-year minimum log retention. A naive "delete everything" implementation breaks 8(3). AssureLens tests both directions.

> **CORRECTION (Day 2) — the Third Schedule does not apply to Meridian.**
> Rule 8(1) binds a Data Fiduciary "who is of such class and is processing personal data for such corresponding purposes as are specified in Third Schedule." The Third Schedule names exactly **three** classes:
> 1. e-commerce entity with **≥ 2 crore** registered users in India
> 2. online gaming intermediary with **≥ 50 lakh** registered users in India
> 3. social media intermediary with **≥ 2 crore** registered users in India
>
> A BFSI captive GCC is none of these. The three-year timetable therefore does **not** bind Meridian, and a control that tested it would be testing an inapplicable rule. Rules 8(1) and 8(2) are scoped **NOT_APPLICABLE** for this engagement with a written reason. Rule 8(3) is drafted generally and **does** apply. This closes open item D3.

### A2.1 DPDP Act 2023, s.8(7) and s.8(8) — what actually governs erasure for a bank
- **Source:** https://www.dpdpa.com/dpdpa2023/chapter-2/section8.html (statutory text of Act 22 of 2023). Accessed 2026-09-21.

> "(7) A Data Fiduciary shall, unless retention is necessary for compliance with any law for the time being in force,—
> (a) erase personal data, upon the Data Principal withdrawing her consent or as soon as it is reasonable to assume that the specified purpose is no longer being served, whichever is earlier; and
> (b) cause its Data Processor to erase any personal data that was made available by the Data Fiduciary for processing to such Data Processor."

> "(8) The purpose referred to in clause (a) of sub-section (7) shall be deemed to no longer be served, if the Data Principal does not— (a) approach the Data Fiduciary for the performance of the specified purpose; and (b) exercise any of her rights in relation to such processing, for such time period as may be prescribed."

**Illustration (II) to s.8(7), verbatim — the Act's own banking example:**

> "X, an individual, decides to close her savings account with Y, a bank. Y is required by law applicable to banks to maintain the record of the identity of its clients for a period of ten years beyond closing of accounts. Since retention is necessary for compliance with law, Y shall retain X's personal data for the said period."

> **Why this is the spine of the retention controls.** The Act illustrates its own legal-retention carve-out with a bank. For Meridian the testable question is therefore *not* "is this record older than three years" but **"is this record still held after its purpose ceased, and is there a recorded legal basis for continuing to hold it?"** A record retained without a recorded basis is a finding; a record retained *with* one is compliant however old it is. The `legal_hold` column on `est_data_principals` carries that basis.
>
> s.8(7)(b) extends the same duty to processors, which is what makes the third-party suite a retention control and not only an access one.
>
> *Unverified:* the specific ten-year period comes from the Act's illustration, not from a provision of PMLA or an RBI Master Direction that this project has read. Controls cite the Act's illustration, never a banking-law period. See open item D7.
>
> **D7 partial finding, 2026-09-25 — still open, not closed.** Secondary sources on PMLA s.12 and the RBI KYC Master Direction converge on **five years** post-closure as the actual banking-law retention period, not ten — the Act's own Illustration (II) may be citing a longer period than the specific AML/KYC provision this project could find, possibly a different or superseded requirement, or a period this project has not correctly identified. This is left **unresolved rather than guessed at**: the discrepancy itself, not a resolution, is the honest state to record. Controls continue to cite only the Act's own illustration (ten years), never the PMLA/RBI figure, and `legal_hold`-based justification (not a hardcoded period) remains the actual test — so no control's correctness depends on which number is right. The e-Gazette/RBI primary text has not been read directly; this finding rests on secondary legal-industry sources only.

**Rule 13 — Significant Data Fiduciary.** Verbatim obligations:
- 13(1): "once in every period of twelve months … undertake a Data Protection Impact Assessment and an audit."
- 13(2): furnish to the Board a report containing significant observations from the DPIA and audit.
- 13(3): "observe due diligence to verify that technical measures including algorithmic software adopted by it … are not likely to pose a risk to the rights of Data Principals."

> **This is the hook for the AI module.** Rule 13(3) makes algorithmic due diligence a statutory obligation for SDFs, which is precisely what the fairness / drift / validation tests evidence.

**Rule 14 — rights of Data Principals.** Publish the means to exercise rights and identifying particulars; publish grievance-redressal period "not exceeding ninety days"; implement appropriate technical and organisational measures for effectiveness.

**Rule 15 — cross-border transfer.** Transfer permitted subject to requirements the Central Government may specify by general or special order regarding making data available to a foreign State or entity under its control.

### A2. Digital Personal Data Protection Act, 2023
- Act 22 of 2023, assented **11 August 2023**.
- Penalty ceiling relied on: up to **₹250 crore** per the Schedule to the Act, for breach of section 8(5) — a Data Fiduciary's failure to implement reasonable security safeguards. A separate, lower ceiling of up to ₹200 crore applies to failure to notify the Board or affected Data Principals of a breach (section 8(6)); the two are not the same entry and are not interchangeable. **Reviewed 2026-09-25 — see D2, closed.** Confirmed via multiple converging secondary (legal-industry) sources rather than the Schedule's own gazette text directly, so this remains a secondary-source citation, not a primary-verified one. AssureLens does not currently display this figure against a named breach type anywhere in the product; if a future control cites it, it must cite section 8(5) specifically, not "the Schedule" generically.

---

## B. Market / demand evidence (secondary, EY-published)

### B1. EY India — "India's data privacy shift: Steering the DPDP compliance and readiness"
- **URL:** https://www.ey.com/en_in/insights/cybersecurity/india-s-data-privacy-shift-steering-the-dpdp-compliance-and-readiness
- **Sample:** "over 150 professionals across sectors."
- Figures used:

| Claim | Figure | Verbatim basis |
|---|---|---|
| Have not updated/drafted DPDP-aligned privacy policies or governance frameworks | ~81% | "Nearly 81% have not updated or drafted DPDP-aligned privacy policies or governance frameworks" |
| Have not begun comprehensive implementation | >83% | "More than 83% have not begun comprehensive implementation of the Act's requirements" |
| Not very familiar with the Act and Rules | ~70% | "Close to 70% of respondents are not very familiar with the DPDP Act and Rules" |
| Not equipped to adopt privacy technologies | ~77% | "Approximately 77% are not equipped to adopt privacy technologies such as consent management, data discovery or rights fulfilment tools" |
| Cite limited access to subject-matter expertise | 76.4% | "76.4% cite limited access to subject-matter expertise" |
| Initiated gap assessments | ~48% | "Nearly 48% of organizations have initiated gap assessments" |
| Documented data processing activities | ~44% | "Nearly 44% of organizations have documented data processing activities" |
| Categorised personal data / identified third-party processors | ~38% | "Close to 38% have categorized personal data and identified third-party processors" |
| Interpretation difficulty as an obstacle | 70% | reported as an obstacle |
| Budget constraints as an obstacle | 45.3% | reported as an obstacle |
| Cross-border transfer difficulty | 58.8% | reported as an obstacle |

- **Limitation to state when displaying:** self-reported survey of 150+ professionals, sector mix not disclosed in the page, not a random sample of Indian enterprises. Directional, not a population estimate. AssureLens labels these as an **external reference band**, never as the user's own measured position.

### B2. EY India GCC Pulse Survey 2025
- **Press release URL:** https://www.ey.com/en_in/newsroom/2025/11/58-percent-gccs-in-india-investing-in-agentic-ai-two-third-creating-dedicated-innovation-teams-to-globalize-ideas-ey-gcc-pulse-survey-2025
- **Report PDF:** https://www.ey.com/content/dam/ey-unified-site/ey-com/en-in/insights/consullting/global-capability-centers/documents/ey-global-capability-center-gcc-pulse-survey-november-2025.pdf
- Dateline: **Bengaluru, 23 November 2025.**
- **Reviewed 2026-09-25 — see D6, closed.** Read against the report PDF directly (not only the press release). GenAI (83%) and Agentic AI (58% current / 29% planning) figures, the only two of this table PRD.md currently cites, are confirmed verbatim on the PDF's technology-investment page. One correction found: this table's "Upskilling internal teams on GenAI" was recorded as 81%; the PDF's actual figure for that specific question (approach to building GenAI capability, page 14/15) is **86%** — 81% is a different figure, from a separate EVP-priorities question ("Upskilling" as a retention priority, page 17/18), not GenAI-specific. Corrected above; this row was not displayed anywhere in the product before the fix.

| Claim | Figure |
|---|---|
| GCCs investing in GenAI | 83% |
| GCCs currently investing in Agentic AI | 58% |
| Planning to scale Agentic AI within a year | 29% |
| GenAI pilots (2025 vs 2024) | 43% vs 37% |
| **Fully embedded cybersecurity Centre of Excellence** | **7%** |
| Monitor third-party access to data (2025 vs 2024) | 60% vs 44% |
| Report compliance complexity / data privacy concerns (2025 vs 2024) | 42% vs 32% |
| Upskilling internal teams on GenAI (approach to building GenAI capability) | 86% |
| Attrition (2025 vs 2023) | 9% vs 13% |
| Transfer pricing cited as key regulatory concern | 63% |

- Cities named as GCC hubs: **Bengaluru, Pune, Hyderabad, Delhi NCR, Mumbai, Chennai.**
- EY Intelligent GCC suite, four stated capabilities: design AI-native GCCs; overhaul value chains through autonomous intelligence; build an AI-fluent workforce; **embed governance with responsible AI**.

### B3. EY hiring signals (Bengaluru / Hyderabad / Chennai)
- **Chennai — Risk Consulting, Digital Risk, Manager (Cloud):** https://in.linkedin.com/jobs/view/risk-consulting-digital-risk-manager-cloud-at-ey-4440148829
  - Verbatim requirement: *"Strong audit mindset with the ability to design, execute, and evidence control testing."*
  - Observed absence: no mention of AI, DPDP, or analytics tooling in the posting.
- **Hyderabad — TC-CS-SRCR-Senior, Supply Chain and Third-Party Risk Management** (seen in EY listings index, https://in.linkedin.com/jobs/ey-risk-manager-jobs).
- **Noida — RC Process & Controls, AI Governance, Manager** (same index): AI-governance roles exist in the India network.
- **Reading:** India cloud/tech-risk delivery is control-testing heavy and light on AI/DPDP-specific tooling. That seam is the project's positioning. *This is an inference from a small sample of public postings, and is presented as such — not as a claim about EY's staffing.*

---

## C. Explicitly NOT claimed

The following were searched for and **no credible public source was found**. They must not appear in any deliverable:
- EY-specific attrition, capacity, or delivery-quality problems in Bengaluru, Hyderabad or Chennai.
- Any statement that EY lacks a DPDP or AI-assurance capability. (EY publishes on both; the gap is in the *client population*, not the firm.)
- Any revenue, headcount or pipeline figure for EY India.
- Any figure derived from Thrive Together (T2AI Consultancy) or MerakiPeople engagements. All such data is confidential and excluded by design.

---

## D. Open items to close before publishing

| # | Item | Owner action |
|---|---|---|
| ~~D1~~ | ~~Review the **corrigendum (G.S.R. 892(E), 11 December 2025)** and reconcile against the rule inventory in A1.2~~ | **CLOSED 2026-09-25.** Purely typographical (Rule 1(3)/(4) Gazette wording); no rule numbering or substantive text changed. No control amendment needed. See A1. |
| ~~D2~~ | ~~Confirm the **₹250 crore** penalty entry maps to the breach types AssureLens names~~ | **CLOSED 2026-09-25.** ₹250cr = section 8(5) security safeguards; ₹200cr = section 8(6) breach notification, a separate entry. Not currently displayed against a named breach type in-product. See A2. |
| ~~D3~~ | ~~Extract **Third Schedule** retention classes and periods in full~~ | **CLOSED Day 2.** All three classes extracted. Meridian matches none; Rules 8(1)/8(2) scoped N/A with a written reason. See A1.3. |
| D4 | Extract **First Schedule Part B** Consent Manager obligations in full | **Not extracted — remains genuinely open.** Verified 2026-09-25 that the dependent clause (R4) already carries `source_status: UNVERIFIED` with a `source_note` pointing here, and the Consent Manager control gates on G7 rather than asserting a result — satisfies the acceptance bar ("close, or flag with G7"), but the legal text itself is still unread. |
| ~~D5~~ | ~~Confirm whether any **Rule 15 special order** on cross-border transfer has been issued since notification~~ | **CLOSED 2026-09-25.** As of September 2026, the Central Government has not notified an approved-country list or any general/special order under Rule 15; cross-border restrictions are not yet operative (commence 13 May 2027 with the rest of Rule 15). DPDP-15-01 correctly gates on G7 with nothing yet to test. |
| ~~D6~~ | ~~Verify the GCC Pulse figures against the **report PDF**, not only the press release~~ | **CLOSED 2026-09-25.** Confirmed 83% GenAI / 58% Agentic AI (the two figures PRD.md cites) against the PDF directly. Found and corrected one unrelated table error: "upskilling on GenAI" was 81%, actually 86% (81% was a different, non-GenAI question). See B2. |
| D7 | Confirm the statutory retention period applicable to an Indian bank (PMLA s.12 / RBI KYC Master Direction) | **Still open — a discrepancy found, not resolved.** Secondary sources put PMLA s.12 / RBI KYC retention at five years post-closure, not the Act illustration's ten. Left unresolved rather than guessed at; no control cites a banking-law period, only the Act's own illustration, and none depend on which number is correct. See A1.1. |

Until an open item is closed, any control that depends on it ships with an explicit `source_status: unverified` flag, and the UI renders it as **Insufficient Evidence — source unverified** rather than asserting a result. The product's own honesty rule applies to the product's own claims.
