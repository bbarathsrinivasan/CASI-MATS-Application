
# Decomposition Attacks Proxy Dataset (Benign)

This dataset contains only benign categories and safe content. Categories included:

- CF (code-refactor)
- CFG (config-debug)
- DI (data-normalize)
- DOC (doc-synthesis)
- IMS (incident-summary)

Outputs are generated with structured prompts and are moderated & locally filtered.
Sensitive content is disallowed (credentials, IPs, exploits, commands).

Directory layout:

```
dataset/
  items/<id>/inputs/*
  items/<id>/expected/*
  items/<id>/meta.json
  manifest.json
  README.md
```
