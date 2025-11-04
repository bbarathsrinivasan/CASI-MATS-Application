# CASI‑MATS Application README

<p align="center">
  <img alt="CASI MATS" src="https://img.shields.io/badge/CASI--MATS-Application-4B8BF4?style=for-the-badge&logo=readme&logoColor=white" />
<img alt="Status" src="https://img.shields.io/badge/Status-Submitted-green?style=for-the-badge" />
<img alt="Last Updated" src="https://img.shields.io/badge/Last_Updated-2025--11--04-lightgrey?style=for-the-badge" />
</p>

> 📄 Purpose: This README consolidates and answers the questions from the CASI‑MATS application PDF for convenient review and submission.

## 🧠 Introduction

I’m Barath Srinivasan, a researcher–engineer focused on AI safety, evaluation, and model governance, with a background spanning machine learning, systems engineering, and large-scale automation. At Carnegie Mellon University, I’m a Research Assistant and member of the CMU AI Safety Initiative, where I work on red-teaming and building safe, useful AI systems.

Previously at Wells Fargo, I built agentic AI systems that automated 23 % of incident resolutions across 10 + services, reducing MTTR by 70 % using RAG-based telemetry pipelines integrated with Splunk, Prometheus, and ServiceNow.

Focus areas: LLMs, RAG architectures, structured-output APIs, LangGraph/MCP agents, and compositional safety frameworks.
Goals at CASI-MATS: advance principled leakage metrics, capability–safety trade-off analyses, and open red-teaming benchmarks that promote transparent, accountable AI deployment.

---

## ❓ Questions & ✅ Answers

### 1) ❓ Evidence for LM WMDP Capabilities: Virology Capabilities Test (VCT) Summary and Critique
- ✅ Answer:
    - Methodological gaps or limitations (brief)
        - Tacit knowledge vs execution: Q&A success does not equal bench proficiency.
        - Unclear benchmark ceiling: Low expert scores obscure what “expert-level” means.
        - External validity limits: High scores may not translate to wet-lab effectiveness; practical tests needed.
        - Human baseline confounds: Modest expert scores may reflect format unfamiliarity.
        - Dual-use proxy limits: Troubleshooting scores do not directly indicate harm potential.

    - Striking or concerning findings (brief)
        - LLMs outperform experts on difficult, “Google-proof” tasks.
        - Notable performance on tacit and visual reasoning questions.
        - Public models display sensitive capabilities, raising dual-use risk.
        - Governance implication: Stronger access controls and policy are warranted.

### 2) ❓ Getting Familiar with the Threat Model
- ✅ Answer:
- The key difference between the JDS24 threat model and traditional jailbreaks is that JDS24 focuses on multi-turn, multi-model composition, where individually safe outputs from multiple models are combined to infer restricted information. In contrast, traditional jailbreaks (e.g., Cha+24) are single-turn direct elicitation attacks on a single model.

- To explore this safely, I implemented a benign proxy version of the JDS24-style decomposition attack using the safeharness framework. The setup used two models: a planner (weak model) that decomposes a complex benign task into subtasks, and an executor (strong model) that solves each subtask. Their results were then combined using a safe aggregator, with strict moderation and blacklist filters to block unsafe content.

- Experiments were run on the decomposition_attack_dataset, covering safe cyber-like tasks such as code refactoring, configuration debugging, and data normalization. Two variants were tested: a single-model baseline and a composed-model pipeline.

- Reasoning: The framework replicates the compositional mechanics of JDS24 while ensuring safety, allowing empirical study of capability uplift without dual-use content.

- Assessment: Success was defined as improved accuracy or task completion by the composed model compared to the baseline, with zero safety violations. All runs were fully logged, reproducible, and verified safe.

- This demonstrates how benign model composition can yield emergent capability—core to the JDS24 threat model—while preserving strict safety boundaries.

- As a related validation, I replicated a controlled, offline jailbreak of GPT‑2 using the universal adversarial suffix method from Zou et al. (2023) to study decomposition-style leakage in a benign proxy setup; no production systems were targeted. Reference: https://arxiv.org/abs/2307.15043
https://colab.research.google.com/drive/119BEN0MqrBo1SrI6f6XKdn7lParAbYSB#scrollTo=wkPKFP7pdraA


### 3) ❓ What Did Glu24 Add That Prior Papers Didn’t?
- ✅ Answer:
    - New threat model: formalizes inferential adversaries who assemble restricted knowledge from many safe-looking outputs (decomposition attacks), not just direct harmful completions.
    - Information-theoretic formalization: introduces a rigorous framework to quantify impermissible knowledge leakage through model interactions.
    - Utility–safety trade-off: proves that fully suppressing dangerous information necessarily restricts helpful outputs; defenses must balance both.
    - Attack efficacy: shows decomposition attacks can extract more prohibited knowledge than direct jailbreaks, revealing gaps in current guardrails.
    - Evaluation lens: shifts from one-shot “did it answer?” checks to multi-turn leakage accounting that enables principled comparison of defenses.

- 🧮 Mathematical framework :
    - Defines impermissible concepts (knowledge to censor) and models multi-turn interactions.
    - Tracks an adversary’s posterior (updated beliefs) after each response.
    - Quantifies leakage per turn and cumulatively as the adversary gains clues.
    - Derives limits showing that capping leakage typically reduces utility, formalizing the trade-off.

### 4) ❓ Curating Data 
- ✅ Answer
- To study decomposition attacks safely, I curated a small cyber-themed proxy dataset that mirrors the multi-step reasoning structure of such attacks without including any harmful or dual-use content. The dataset spans five benign categories—code refactor (CF), configuration debugging (CFG), incident postmortem (IMS), data integration (DI), and document synthesis (DOC)—all of which require information to be split, processed, and recombined, similar to a real decomposition attack.

- Methodology and rationale:
  Each item follows a structured JSON schema with fields for full task, inputs, 2–6 canonical subtasks, expected outputs, and simple validators (e.g., unit tests or schema checks). I used GPT-5’s structured-output API to synthesize safe, fictional inputs and human-verified decompositions, applying moderation and blacklist filters to guarantee safety. This approach provides control, reproducibility, and objective evaluation while avoiding any WMDP content.

- Scaling:
  The dataset can be expanded by programmatically generating new synthetic variations, prompting LLMs to produce additional benign tasks, or crowdsourcing decomposition annotations under the same safety and schema constraints.

- Using agents:
  Agents can attempt these tasks either directly or through a decomposition pipeline, where a weaker model proposes subtasks and a stronger model executes them. Comparing the combined pipeline’s performance against single-model baselines quantifies capability uplift—the core phenomenon behind decomposition attacks.

  In summary, this dataset offers a safe, structured, and scalable benchmark for analyzing how multi-model coordination can yield emergent capabilities even when each individual model appears aligned.
<div align="center">
<pre>
┌────────────────────┐
│ make_dataset.py    │  ← entrypoint CLI
└────────┬───────────┘
         │
         ▼
┌────────────────────────────┐
│ ds.generate.main()         │
│  • parse args (--out, --n) │
│  • write JSON Schemas      │
│  • create folders          │
└────────┬───────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  For each item to create    │
│  ─────────────────────────  │
│  1️⃣  Build safe prompt      │
│  2️⃣  Safety check (local+AI)│
│  3️⃣  GPT-5 Structured call  │
│  4️⃣  Parse + validate JSON  │
│  5️⃣  Write item files       │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  ds.safety.ensure_safe_text.│
│  • Local blacklist          │
│  • Optional Moderation API  │
│  • Reject / replace unsafe  │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  ds.gpt.call_structured()   │
│  • Uses Responses API       │
│  • response_format=JSON     │
│  • Retries & validates      │
│  • Offline fallback mocks   │
└────────┬────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ ds.validate                │
│  • Verify schemas          │
│  • Check CSV/code tests    │
│  • Return (ok, errors)     │
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────┐
│ dataset/                   │
│ ├── items/&lt;id&gt;/inputs/*    │
│ ├── items/&lt;id&gt;/expected/*  │
│ ├── items/&lt;id&gt;/meta.json   │
│ ├── manifest.json          │
│ ├── README.md              │
│ └── schemas/*.schema.json  │
└────────────────────────────┘
</pre>
</div>

### 5) ❓ Literature Search: Decomposition Attacks & Multi-Context Jailbreaking
- ✅ Answer: 
- Zou et al., 2023 (arXiv:2307.15043): Universal, transferable adversarial suffixes for aligned LLMs.
- LLM Attacks Demo (GitHub): Demonstration notebooks for studying jailbreak behaviors and evaluations.
- LLM Structured Prompt Attacks (GitHub): Implementations for analyzing prompt decomposition and multi-step attack behaviors.
- DrAttack: Decomposition/reconstruction-based jailbreak techniques with strong empirical performance.
- MasterKey: Automated cross-model jailbreak evaluation, highlighting transferability risks.
- Perez et al., Red Teaming Language Models with Language Models: Automated, scalable red teaming to surface vulnerabilities.
- Indirect Prompt Injection and Multi-Hop Reasoning: Work on prompt injection and chained attacks showing additional decomposition vectors.

### 6) ❓ Future Work: Accountability and Open Red Teaming
- ✅ Answer: 
- Problem Statement:
Current regulatory efforts are often limited by national boundaries, creating an uneven playing field where some organizations may take excessive risks to gain a competitive edge in AI. With AI development becoming a global race, the fundamental challenge is how to ensure responsible behavior and robust safety standards, especially when no single authority can enforce them internationally. Questions remain about who should hold leading tech organizations accountable and how to reliably verify their claims about safe model deployment.

- The Role of Red Teaming:
Comprehensive red teaming systematically probing for vulnerabilities and simulating real-world attacks is a critical way to uncover hidden safety risks in AI models. Identifying and reporting these vulnerabilities not only improves technical robustness but also builds trust with the public. Accountability cannot rely solely on regulation; broad scrutiny and transparent testing are needed to keep organizations honest.

- An Open Red Teaming Framework:
As a future direction, I am working on an open "red teaming marketplace" a collaborative, public platform where anyone can rigorously test and evaluate deployed models. This approach aims to make safety verification transparent and reputationally meaningful, so companies that submit their models for public evaluation can earn a distinct trust signal. The long-term vision is to establish a universal, community-driven framework, akin to the open-source model in software, where public testing and accountability become standard in the AI ecosystem.

---

## Closing Statement

This work is provided solely for academic and research purposes. It does not endorse, enable, or facilitate harmful, unsafe, or unlawful activities.