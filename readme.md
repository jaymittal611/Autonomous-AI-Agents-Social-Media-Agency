Download Ollama
Ollama pull llama3.1:8b
uv venv
.venv/bin/activate
python -m pip install ollama
configured llm model
# 🤖 Autonomous AI-Agents Social Media Agency (Fully Local via Ollama)

An end-to-end multi-agent social media collective operating entirely on open-weights local models via Ollama (Model Name-llama3.1:8b). The system ingests an short & unstructured client campaign brief, coordinates strategic decomposition, draft authoring, compliance audits, simulated distribution on a mock platform, audience comment resolution, and closes the loop by feeding analytical discoveries into subsequent campaign weeks.

---

## 📑 Table of Contents
1. [Architecture Overview](#-architecture-overview)
2. [Hardware & Model Specifications](#-hardware--model-specifications)
3. [The Mock Platform & Ground-Truth Engagement Physics](#-the-mock-platform--ground-truth-engagement-physics)
4. [Signal Discovery Analysis (Observed vs. Missed)](#-signal-discovery-analysis-observed-vs-missed)
5. [Closed-Loop Quantitative Uplift (Week 1 vs. Week 2)](#-closed-loop-quantitative-uplift-week-1-vs-week-2)
6. [Inter-Agent Message Tracing](#-inter-agent-message-tracing)
7. [Quickstart & Setup](#-quickstart--setup)
8. [Failure Modes & Engineering Judgement](#-failure-modes--engineering-judgement)

---

## 🏗️ Architecture Overview

The system rejects monolithic prompting ("act as a team of experts") in favor of an isolated, multi-agent state machine where agents have distinct prompts, strict schemas, verifiable failure modes, and deterministic handoffs:


                             [Client Campaign Brief]
                                      │
                                      ▼
                            ┌───────────────────┐
                ┌───────────│   Strategy Agent  │◄──────────────────────────┐
                │           └───────────────────┘                           │
                │                     │                                     │
                │                     ▼                                     │
                │           ┌───────────────────┐                           │
                │     ┌────►│ Content & Creative│                           │
                │     │     │       Agent       │                           │
                │     │     └───────────────────┘                           │
                │ (Rejection          │                                     │
                │   Feedback)         ▼                                     │
                │     │     ┌───────────────────┐                           │
                │     └─────│ Compliance Agent  │                           │
                │           │ (Max 3 Revisions) │                           │
                │           └───────────────────┘                           │
                │                     │ (Approved)                          │
                │                     ▼                                     │
                │           ┌───────────────────┐                           │
                │           │ Human Approval    │                           │
                │           │     Gate          │                           │
                │           └───────────────────┘                           │
                │                     │ (Approved)                          │
                │                     ▼                                     │
                │           ┌───────────────────┐                           │
                │           │ Mock Platform API │                           │
                │           │   (SQLite DB)     │                           │
                │           └───────────────────┘                           │
                │                     │                                     │
                │                     ▼                                     │
                │           ┌───────────────────┐                           │
                │           │ Engagement        |                           | 
                |           | Simulator         │                           │
                │           └───────────────────┘                           │
                │                     │                                     │
                │          ┌──────────┴──────────┐                          │
                │          ▼                     ▼                          │
                │   ┌──────────────┐      ┌──────────────┐                  │
                │   │  Community   │      │  Analytics   │                  │
                │   │    Agent     │      │    Agent     │                  │
                │   └──────────────┘      └──────────────┘                  │
                │                                │ (Directives)             │
                └────────────────────────────────┴──────────────────────────┘


### Agent Roles & Responsibilities

| Agent | Responsibility | Core Schema In/Out |
| :--- | :--- | :--- |
| **Strategy Agent** | Parses human brief into target persona, content pillars, channel mix, and target KPIs. | `str` ➔ `StrategyPlan` |
| **Content & Creative Agent** | Generates tailored copy, hooks, CTAs, hashtag sets, and visual asset briefs per channel. | `StrategyPlan` ➔ `CampaignDrafts` |
| **Compliance Agent** | Audits tone, absolute/unsubstantiated claims, and channel word bounds. Rejects work back to writer. | `str`, `channel` ➔ `ComplianceReview` |
| **Community Agent** | Reads inbound comments from the platform simulation, drafting brand-safe replies. | `list[dict]` ➔ `CommunityAction` |
| **Analytics Agent** | Decodes mock platform telemetry to extract empirical signals and prescriptive changes for next cycle. | `list[dict]` ➔ `WeeklyAnalysisReport` |

---

## 💻 Hardware & Model Specifications

* **Execution Runtime:** Fully local via Ollama (No OpenAI, Anthropic, Gemini, or remote endpoints).
* **Model Selected:** `llama3:8b` .
* **Host Hardware Specs:** 8-core CPU / 16GB Unified Memory (MSI - 12th Gen Intel(R) Core(TM) i5-12450H (2.00 GHz) -NVIDIA GeForce RTX 2050 (4 GB)-Intel(R) UHD Graphics (128 MB)).
* **Local LLM Abstraction (`Local_llm.py`):** Enforces JSON output through Ollama's structured formatting constraints.

---

## 🌐 The Mock Platform & Ground-Truth Behind Engagement Simulator

To prevent hollow analysis, the platform simulation replaces stochastic randomness (`random.randint`) with deterministic mathematical rules with minimal variance ($\pm 4\%$):

$$\text{Impressions} = \text{BaseReach}_{\text{channel}} \times M_{\text{time}} \times M_{\text{length}} \times M_{\text{hashtag}} \times \epsilon$$

### Ground-Truth Rules Planted in `mock_platform.py`

1. **Peak Scheduling Multiplier ($M_{\text{time}}$):** Posts scheduled between `12:00–14:00` or `18:00–20:00` receive a **$1.45\times$** reach multiplier; off-peak hours receive **$0.65\times$**.
2. **Channel Word-Count Bounds ($M_{\text{length}}$):** `Static_image` posts exceeding 120 words suffer a **$60\%$ reach penalty** ($0.40\times$).
3. **Hashtag Sweet Spot ($M_{\text{hashtag}}$):** Posts with 2–4 hashtags receive a **$1.25\times$** boost. Posts with 0 hashtags or $>5$ hashtags suffer a **$30\%$ penalty** ($0.70\times$).
4. **Question Hook on Comments ($M_{\text{question}}$):** Posts whose copy ends with a `?` trigger a **$3.20\times$** surge in comment generation.

---

## 🔍 Signal Discovery Analysis (Observed vs. Missed)

In compliance with the hiring brief, here is a transparent breakdown of what the `Analytics Agent` rediscovered versus what it missed:

### Signals Successfully Discovered
* **Question Mark Driving Comment Volume:** The agent successfully correlated high comment counts with posts ending in questions, issuing the directive: *"End short-form hooks with direct questions to maximize audience response."* 
* **Micro-Copy Word Length Penalty:** The agent detected significant impression drops on short-form channels when posts contained verbose paragraphs, recommending: *"Restrict copy to under 100 words on visual and short-form feeds."* 

### Signals Missed & Engineering Root Cause
* **Non-Linear Hashtag Saturation Curve (2–4 optimal):** The agent failed to extract the hashtag penalty curve .
  * *Root Cause Analysis:* Across a single week with only 3 active channels, the sample size ($N=3$) is statistically insufficient to isolate hashtag density from base channel reach differences without confounding variables .
* **Peak Timing Window Multiplier:** The agent partially noted higher reach on evening posts but failed to formulate a definitive time window rule .
  * *Root Cause Analysis:* Timing interactions were masked by length penalties occurring on the same post instances .

---

## 📈 Closed-Loop Quantitative Uplift (Week 1 vs. Week 2)

By injecting the `WeeklyAnalysisReport` directives into Week 2 generation prompts, the system demonstrated closed-loop adaptation :

| Metric | Week 1 (Baseline) | Week 2 (Analytics Optimized) | Delta |
| :--- | :---: | :---: | :---: |
| **Total Impressions** | ~2,140 | ~3,380 | **+57.94%** |
| **Total Likes** | ~85 | ~138 | **+62.35%** |
| **Total Comments** | ~32 | ~114 | **+256.25%** |
| **Avg Engagement Rate** | 5.60% | 7.45% | **+33.03%** |

---

## 📡 Inter-Agent Message Tracing

Inter-agent communication is decoupled and fully observable via `agent_tracer.py` . Every message, state transition, and compliance rejection is persisted to:
* `agent_trace.json`: Structured machine-readable event log .
* `agent_trace.md`: Formatted human-readable negotiation transcript .



