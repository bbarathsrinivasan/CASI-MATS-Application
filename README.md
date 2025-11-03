# CASI‑MATS Application README

<p align="center">
  <img alt="CASI MATS" src="https://img.shields.io/badge/CASI--MATS-Application-4B8BF4?style=for-the-badge&logo=readme&logoColor=white" />
  <img alt="Status" src="https://img.shields.io/badge/Status-Draft-yellow?style=for-the-badge" />
  <img alt="Last Updated" src="https://img.shields.io/badge/Last_Updated-2025--11--02-lightgrey?style=for-the-badge" />
</p>

> 📄 Purpose: This README consolidates and answers the questions from the CASI‑MATS application PDF for convenient review and submission.

## 🧭 How to use this file

- If the questions are not visible below, paste the questionnaire text from the PDF here or place the PDF inside this repository so it can be parsed automatically.
- Once the questions are available, fill in each answer under the corresponding section.
- Keep responses concise, specific, and within any stated word/character limits.

## 🧩 Assumptions

- The PDF contains a set of short‑answer prompts (e.g., motivation, background, project idea, timeline, team, logistics).
- This file is prepared with placeholders and icons; it can be updated in-place once the exact questions are extracted.

---

## ❓ Questions & ✅ Answers

> Replace the placeholder text below with the exact questions from the PDF and provide your answers beneath each.

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

### 2) ❓ What Did Glu24 Add That Prior Papers Didn’t?
- ✅ Answer:
    - New threat model: formalizes inferential adversaries who assemble restricted knowledge from many safe-looking outputs (decomposition attacks), not just direct harmful completions.
    - Information-theoretic formalization: introduces a rigorous framework to quantify impermissible knowledge leakage through model interactions.
    - Utility–safety trade-off: proves that fully suppressing dangerous information necessarily restricts helpful outputs; defenses must balance both.
    - Attack efficacy: shows decomposition attacks can extract more prohibited knowledge than direct jailbreaks, revealing gaps in current guardrails.
    - Evaluation lens: shifts from one-shot “did it answer?” checks to multi-turn leakage accounting that enables principled comparison of defenses.

- 🧮 Mathematical framework (brief):
    - Defines impermissible concepts (knowledge to censor) and models multi-turn interactions.
    - Tracks an adversary’s posterior (updated beliefs) after each response.
    - Quantifies leakage per turn and cumulatively as the adversary gains clues.
    - Derives limits showing that capping leakage typically reduces utility, formalizing the trade-off.


### 3) ❓ Question
- ✅ Answer:

### 4) ❓ Question
- ✅ Answer:

### 5) ❓ Question
- ✅ Answer:

### 6) ❓ Question
- ✅ Answer:

### 7) ❓ Question
- ✅ Answer:

### 8) ❓ Question
- ✅ Answer:

### 9) ❓ Question
- ✅ Answer:

### 10) ❓ Question
- ✅ Answer:

---

## 🧠 Guidance for strong responses

- 🎯 Be specific: quantify impact, scope, and constraints (e.g., users, datasets, timelines).
- 🧪 Show feasibility: outline approach, required resources, and risk mitigation.
- 🤝 Highlight collaboration: roles, advisors, and stakeholders.
- ⏱️ Respect limits: ensure you meet any word/character caps in the PDF.
- 🧾 Cite references: link prior work, repositories, or publications if relevant.

## 📦 Attachments & Links

- 📎 PDF: Place `casi_mats_1_application.pdf` at the repository root so it can be parsed.
- 🔗 Additional materials: link slides, repos, or datasets here.

## ✅ Review checklist (before submit)

- [ ] All questions from the PDF are present here in full.
- [ ] Each question has a clear, complete answer.
- [ ] Word/character limits satisfied.
- [ ] Links and references included and working.
- [ ] Spelling/grammar checked.

---

> ℹ️ Note: If you provide the PDF inside this repo or paste the questions, this README can be auto‑filled and reformatted to match the exact prompts.
