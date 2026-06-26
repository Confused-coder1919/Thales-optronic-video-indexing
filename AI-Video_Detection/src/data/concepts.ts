import type { ConceptCard } from "../types";

export const conceptCards: ConceptCard[] = [
  {
    id: "cia-triad",
    title_en: "CIA Triad (What To Protect)",
    body_en:
      "In simple words: Confidentiality = keep data secret. Integrity = keep data correct. Availability = keep services working.\nDo this: map each scenario to leak, tampering, or downtime.\nCommon mistake: mixing confidentiality and integrity.",
    tags: ["cia", "basics"],
    questionIds: [3, 4, 38],
  },
  {
    id: "phishing-vs-spear",
    title_en: "Phishing vs. Spear Phishing",
    body_en:
      "In simple words: phishing is broad and generic; spear phishing is targeted and personalized.\nDo this: verify urgent requests on another channel before acting.\nCommon mistake: trusting a known name without verifying the request.",
    tags: ["phishing", "social_engineering"],
    questionIds: [9, 10, 43],
  },
  {
    id: "passwords",
    title_en: "Passwords That Work",
    body_en:
      "In simple words: strong means long and unique, not just complex symbols.\nDo this: use passphrases and a password manager.\nCommon mistake: reusing one strong password everywhere.",
    tags: ["passwords", "authentication"],
    questionIds: [41, 42, 6],
  },
  {
    id: "wifi-basics",
    title_en: "Safer Wi-Fi (Home + Hotspots)",
    body_en:
      "In simple words: public Wi-Fi is convenient but risky.\nDo this: prefer WPA2/WPA3, avoid sensitive actions on unknown hotspots, and keep protections on.\nCommon mistake: assuming a network name means it is legitimate.",
    tags: ["wifi", "hotspot", "mitm"],
    questionIds: [30, 31, 18],
  },
  {
    id: "byod",
    title_en: "BYOD: The Hidden Costs",
    body_en:
      "In simple words: personal devices can carry company risk.\nDo this: separate personal/work data, enforce updates, and lock devices.\nCommon mistake: allowing BYOD without management or segmentation controls.",
    tags: ["byod", "malware", "data_leak"],
    questionIds: [25, 39, 45],
  },
  {
    id: "patching",
    title_en: "Updates Close Known Holes",
    body_en:
      "In simple words: many attacks use old, known vulnerabilities.\nDo this: patch quickly, enable auto-updates where safe, remove unused software.\nCommon mistake: delaying updates on critical internet-facing systems.",
    tags: ["patching", "hardening", "vulnerabilities"],
    questionIds: [37, 39, 57],
  },
  {
    id: "https",
    title_en: "HTTPS: What To Verify",
    body_en:
      "In simple words: HTTPS encrypts traffic, but trust depends on valid certificates.\nDo this: respect browser warnings and verify the real domain.\nCommon mistake: thinking the lock icon alone guarantees a safe site.",
    tags: ["https", "tls", "cert_validation"],
    questionIds: [73, 74, 70],
  },
  {
    id: "sql-injection",
    title_en: "SQL Injection Mental Model",
    body_en:
      "In simple words: SQL injection is when input is treated as command text.\nDo this: use parameterized queries and validate input by type/format.\nCommon mistake: building SQL with string concatenation.",
    tags: ["web_security", "sql_injection"],
    questionIds: [72, 23, 40],
  },
  {
    id: "incident-first-steps",
    title_en: "Incident First Steps",
    body_en:
      "In simple words: fast reporting and controlled response reduce damage.\nDo this: follow policy, alert the right team, preserve evidence.\nCommon mistake: deleting files or disabling tools before investigation.",
    tags: ["incident_response", "policy"],
    questionIds: [45, 46, 11],
  },
  {
    id: "risk-treatment",
    title_en: "Risk Treatment Options",
    body_en:
      "In simple words: options are reduce, transfer, avoid, or accept risk.\nDo this: decide using business impact and realistic likelihood.\nCommon mistake: selecting controls without a clear risk priority.",
    tags: ["risk_analysis", "risk_treatment", "controls"],
    questionIds: [82, 83, 84],
  },
  {
    id: "defense-in-depth",
    title_en: "Defense In Depth",
    body_en:
      "In simple words: never rely on one control.\nDo this: combine identity, network, endpoint, monitoring, and backup controls.\nCommon mistake: believing one product can prevent all incidents.",
    tags: ["defense_in_depth", "security_principles"],
    questionIds: [85, 86, 65],
  },
  {
    id: "cloud-checklist",
    title_en: "Cloud Checklist (Before You Subscribe)",
    body_en:
      "In simple words: cloud choice is also a legal and governance decision.\nDo this: check encryption, logging, identity controls, data location, and exit plan.\nCommon mistake: buying cloud services before security and legal review.",
    tags: ["cloud", "compliance", "data_lifecycle", "shadow_it"],
    questionIds: [87, 90, 76],
  },
] satisfies ConceptCard[];
