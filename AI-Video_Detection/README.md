# CyberEdu Quiz (English)

Student-friendly, local-first quiz web app built from **CyberEdu v1.1 (Feb 2017)** modules 1–4 (questions **1–94**).  
No backend required.

## Features

- **Learn mode**: module selection, concept cards grouped by tags, hints, theory links, explanations.
- **Test mode**: full exam (94) or per-module, optional timer, scoring + breakdown by module and tag, missed questions review.
- **Review queue** (spaced repetition): incorrect questions scheduled at **+10 minutes**, **+1 day**, **+3 days**.
- **Local-first persistence**: progress, attempts, and review queue saved in `localStorage`.
- **Teacher-friendly export**: download attempts/results as JSON.

## Run Locally

```bash
npm install
npm run dev
```

Other useful commands:

```bash
npm run typecheck
npm run lint
npm test
npm run build
```

## Attribution

Original quiz: **CyberEdu v1.1 — February 2017**, provided by **ANSSI**, license **Creative Commons Attribution 3.0 France**.  
This app contains an English translation plus additional explanations and concept cards.
