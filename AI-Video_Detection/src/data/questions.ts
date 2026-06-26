import type { Question } from "../types";

const SOURCE_REF = "CyberEdu v1.1 Feb 2017, ANSSI";

export const questions = [
  {
    id: 1,
    module: 1,
    prompt_en: "Select the goals of cybersecurity.",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "Increase the risks weighing on the information system." },
      { key: "b", text_en: "Reveal secrets." },
      {
        key: "c",
        text_en:
          "Make users' lives harder by adding constraints such as long and complex passwords.",
      },
      { key: "d", text_en: "Protect the information system." },
    ],
    correct: ["d"],
    explanation_en:
      "Cybersecurity's purpose is to protect the information system (including confidentiality, integrity, and availability). Constraints like strong passwords are a means, not an end.",
    tags: ["basics", "objectives", "cia"],
    source_ref: SOURCE_REF,
  },
  {
    id: 2,
    module: 1,
    prompt_en:
      "If you were the victim of a cybercriminal attack, what could be the consequences (impacts) on your private life (two examples)?",
    type: "free_text",
    rubric: {
      required_points: [
        "I listed at least two distinct privacy impacts (e.g., identity theft, account takeover, doxxing, blackmail, stalking).",
        "My impacts are concrete and tied to private life (accounts, messages, personal info, finances).",
      ],
      sample_answer_en:
        "Example: a data leak could expose my address and phone number (doxxing), and an attacker could take over my email/social accounts and read or publish private messages.",
    },
    explanation_en:
      "Think in terms of what an attacker can do with leaked data or compromised accounts: expose personal information, impersonate you, access private messages/photos, commit fraud, or pressure you (blackmail).",
    tags: ["impacts", "privacy"],
    source_ref: SOURCE_REF,
  },
  {
    id: 3,
    module: 1,
    prompt_en: "Name the three main security needs.",
    type: "free_text",
    rubric: {
      required_points: ["Confidentiality", "Integrity", "Availability"],
      sample_answer_en: "Confidentiality, integrity, availability (the CIA triad).",
    },
    explanation_en:
      "The classic triad is CIA: confidentiality (keep data secret), integrity (keep data correct), availability (keep services/data accessible).",
    tags: ["basics", "cia"],
    source_ref: SOURCE_REF,
  },
  {
    id: 4,
    module: 1,
    prompt_en: "Choose the correct sentence(s).",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Encryption guarantees that data will always be available/accessible." },
      {
        key: "b",
        text_en: "Physical security helps ensure the availability of equipment and data.",
      },
      {
        key: "c",
        text_en: "An electronic signature guarantees the confidentiality of data.",
      },
      { key: "d", text_en: "Distributed Denial of Service (DDoS) attacks harm data availability." },
    ],
    correct: ["b", "d"],
    explanation_en:
      "Encryption is about confidentiality, not availability. Physical security protects equipment from theft/damage (helping availability). DDoS attacks target availability. Digital signatures provide integrity/authenticity, not confidentiality.",
    tags: ["cia", "physical_security", "ddos", "crypto"],
    source_ref: SOURCE_REF,
  },
  {
    id: 5,
    module: 1,
    prompt_en:
      "You are developing a website www.asso-etudiants-touristes.org for a student association that organizes group trips abroad. The site contains information about proposed trips (country, cities, transport price, accommodation conditions, possible dates). These pieces of information have a confidentiality requirement:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "Low" },
      { key: "b", text_en: "High" },
    ],
    correct: ["a"],
    explanation_en:
      "Trip descriptions and prices are typically meant to be shared publicly, so the confidentiality requirement is generally low.",
    tags: ["classification", "confidentiality"],
    source_ref: SOURCE_REF,
  },
  {
    id: 6,
    module: 1,
    prompt_en:
      "You are developing a website www.asso-etudiants-touristes.org for a student association. Information about students registered on the site (login and password, last name, first name, phone number, address) has a confidentiality requirement:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "Low" },
      { key: "b", text_en: "High" },
    ],
    correct: ["b"],
    explanation_en:
      "Credentials and personal information must be protected to prevent account takeover, identity theft, and privacy violations.",
    tags: ["personal_data", "confidentiality", "authentication"],
    source_ref: SOURCE_REF,
  },
  {
    id: 7,
    module: 1,
    prompt_en:
      "I can succeed in an attack on an object that has no exploitable vulnerability (weakness):",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["b"],
    explanation_en:
      "An attack needs a weakness to exploit (technical, human, organizational, or procedural). If there is truly no exploitable weakness, the attacker cannot succeed.",
    tags: ["threats", "vulnerabilities"],
    source_ref: SOURCE_REF,
  },
  {
    id: 8,
    module: 1,
    prompt_en: "All organizations and individuals face the same threats:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["b"],
    explanation_en:
      "Threats depend on context: assets, exposure, attackers, business, and habits. Risk and threat models differ across people and organizations.",
    tags: ["risk", "threat_modeling"],
    source_ref: SOURCE_REF,
  },
  {
    id: 9,
    module: 1,
    prompt_en: "Circle the attacks that are generally targeted:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Phishing" },
      { key: "b", text_en: "Ransomware" },
      { key: "c", text_en: "Social engineering" },
      { key: "d", text_en: "Spear phishing / \"CEO fraud\" (\"president scam\")" },
    ],
    correct: ["c", "d"],
    explanation_en:
      "Spear phishing and many social engineering attacks target a specific person or organization. Generic phishing and many ransomware campaigns are typically broad and opportunistic.",
    tags: ["social_engineering", "phishing", "targeted_attacks"],
    source_ref: SOURCE_REF,
  },
  {
    id: 10,
    module: 1,
    prompt_en: "Circle the attacks that are generally non-targeted:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Computer intrusion" },
      { key: "b", text_en: "Computer virus" },
      { key: "c", text_en: "Distributed Denial of Service" },
      { key: "d", text_en: "Phishing" },
    ],
    correct: ["b", "d"],
    explanation_en:
      "Viruses and generic phishing are commonly spread at scale. Intrusions and DDoS are often aimed at a specific target (even if discovery can be opportunistic).",
    tags: ["malware", "phishing", "ddos"],
    source_ref: SOURCE_REF,
  },
  {
    id: 11,
    module: 1,
    prompt_en: "Circle the factors that make internal fraud easier:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Shared user accounts used by multiple people" },
      { key: "b", text_en: "Existence of internal control procedures" },
      { key: "c", text_en: "Little or no internal monitoring" },
      { key: "d", text_en: "Strict management and review of privileges" },
    ],
    correct: ["a", "c"],
    explanation_en:
      "Shared accounts reduce accountability, and lack of monitoring reduces detection. Internal controls and strict privilege reviews help prevent fraud.",
    tags: ["insider_threat", "access_control", "audit"],
    source_ref: SOURCE_REF,
  },
  {
    id: 12,
    module: 1,
    prompt_en: "Circle the factors that can reduce or prevent internal fraud:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Strict management and review of privileges" },
      { key: "b", text_en: "Separation of user roles (segregation of duties)" },
      { key: "c", text_en: "Little or no internal monitoring" },
      { key: "d", text_en: "Individual user accounts for everyone" },
    ],
    correct: ["a", "b", "d"],
    explanation_en:
      "Privilege reviews, segregation of duties, and individual accounts improve accountability and reduce abuse. Lack of monitoring does the opposite.",
    tags: ["insider_threat", "access_control", "segregation_of_duties"],
    source_ref: SOURCE_REF,
  },
  {
    id: 13,
    module: 1,
    prompt_en:
      "Name two methods (infection vectors) by which computer viruses can be transmitted from a compromised system (or an attacker) to a clean system.",
    type: "free_text",
    rubric: {
      required_points: [
        "I named at least two distinct infection vectors.",
        "My vectors are plausible (e.g., email attachment, malicious link/download, USB drive, infected website).",
      ],
      sample_answer_en:
        "Email attachment and a malicious download (or a compromised website/drive-by download).",
    },
    explanation_en:
      "Common infection vectors include email attachments, malicious links, USB drives, pirated software, compromised websites, and infected network shares.",
    tags: ["malware", "infection_vectors"],
    source_ref: SOURCE_REF,
  },
  {
    id: 14,
    module: 1,
    prompt_en: "What is a botnet?",
    type: "free_text",
    rubric: {
      required_points: [
        "It is made of compromised devices (bots).",
        "It is controlled remotely by an attacker (command-and-control).",
        "It is used to perform malicious actions at scale (e.g., DDoS, spam).",
      ],
      sample_answer_en:
        "A botnet is a network of infected devices remotely controlled by an attacker to run coordinated malicious actions (e.g., DDoS, spam).",
    },
    explanation_en:
      "A botnet is a coordinated group of compromised machines under a single control infrastructure. Attackers use it to amplify attacks and hide their origin.",
    tags: ["botnet", "malware"],
    source_ref: SOURCE_REF,
  },
  {
    id: 15,
    module: 1,
    prompt_en: "You must always give your consent before being part of a botnet:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["b"],
    explanation_en:
      "Devices are typically recruited into botnets without the owner's consent (via malware infection or exploitation).",
    tags: ["botnet", "malware"],
    source_ref: SOURCE_REF,
  },
  {
    id: 16,
    module: 1,
    prompt_en: "In France, cybersecurity concerns only private-sector companies and individuals:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["b"],
    explanation_en:
      "Cybersecurity concerns public and private organizations (including critical infrastructure), as well as individuals.",
    tags: ["governance", "public_sector"],
    source_ref: SOURCE_REF,
  },
  {
    id: 17,
    module: 1,
    prompt_en:
      "Using tools to obtain Wi-Fi keys and access your neighbor's Wi-Fi network is covered by which law?",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "Vigipirate" },
      { key: "b", text_en: "Godfrain" },
      { key: "c", text_en: "Hadopi" },
      { key: "d", text_en: "Patriot Act" },
    ],
    correct: ["b"],
    explanation_en:
      "Unauthorized access to information systems in France is addressed by the Godfrain law framework.",
    tags: ["law", "unauthorized_access", "wifi"],
    source_ref: SOURCE_REF,
  },
  {
    id: 18,
    module: 1,
    prompt_en:
      "My personal Wi-Fi network is poorly secured (e.g., a weak Wi-Fi key like 12345678). An intruder connects to my network and performs malicious actions such as attacking a government website:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "I may face sanctions." },
      { key: "b", text_en: "Only the intruder may face sanctions." },
      { key: "c", text_en: "Both the intruder and I may face sanctions." },
      { key: "d", text_en: "No sanctions are possible." },
    ],
    correct: ["c"],
    explanation_en:
      "The attacker is responsible for the malicious act, but a poorly secured connection can expose you to legal/administrative trouble (at minimum, investigation and the need to demonstrate due diligence).",
    tags: ["wifi", "law", "liability"],
    source_ref: SOURCE_REF,
  },
  {
    id: 19,
    module: 1,
    prompt_en: "Give an example of personal data.",
    type: "free_text",
    rubric: {
      required_points: ["I gave an example of personal data (identifies or relates to a person)."],
      sample_answer_en: "Example: an email address, phone number, or home address.",
    },
    explanation_en:
      "Personal data is any information relating to an identifiable person (name, email, phone, address, student ID, IP address, etc.).",
    tags: ["personal_data", "privacy"],
    source_ref: SOURCE_REF,
  },
  {
    id: 20,
    module: 1,
    prompt_en:
      "When creating our student association website, if you store the following information for each member: last name, first name, address, email address. To which organization must you file a declaration?",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "National gendarmerie" },
      { key: "b", text_en: "University" },
      { key: "c", text_en: "CNIL" },
      { key: "d", text_en: "Hadopi" },
    ],
    correct: ["c"],
    explanation_en:
      "CNIL is France's data protection authority (note: regulatory processes evolved with GDPR, but the intended answer here is CNIL).",
    tags: ["cnil", "privacy", "personal_data"],
    source_ref: SOURCE_REF,
  },

  // Module 2
  {
    id: 21,
    module: 2,
    prompt_en: "Choose 2 examples of sensitive electronic data for a student:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Postal address" },
      { key: "b", text_en: "Name and social security number" },
      { key: "c", text_en: "Bank card number" },
      { key: "d", text_en: "Family name" },
    ],
    correct: ["b", "c"],
    explanation_en:
      "A social security number and bank card number are highly sensitive. A name or address can be personal data, but is typically less sensitive than those identifiers/financial data.",
    tags: ["personal_data", "sensitive_data"],
    source_ref: SOURCE_REF,
  },
  {
    id: 22,
    module: 2,
    prompt_en: "Choose 2 examples of sensitive electronic data for a university/school:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "The name and origin of the university" },
      { key: "b", text_en: "Teachers' names" },
      { key: "c", text_en: "Filed patents" },
      { key: "d", text_en: "Upcoming exam papers (not yet taken)" },
    ],
    correct: ["c", "d"],
    explanation_en:
      "Patents and future exam papers are high-value assets (intellectual property and integrity/fairness of exams).",
    tags: ["sensitive_data", "intellectual_property", "exam_security"],
    source_ref: SOURCE_REF,
  },
  {
    id: 23,
    module: 2,
    prompt_en: 'In a network, what do we mean by a "trusted zone"?',
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "A visitor Wi-Fi hotspot, for example in a train station" },
      {
        key: "b",
        text_en: "The internal network (where user workstations and servers are hosted)",
      },
      { key: "c", text_en: "The Internet" },
      { key: "d", text_en: "A demilitarized zone (DMZ)" },
    ],
    correct: ["b"],
    explanation_en:
      "A trusted zone is a segment assumed to have stronger controls and higher trust, typically the internal network. A DMZ is deliberately less trusted than the internal network.",
    tags: ["network_security", "trust_zone", "segmentation"],
    source_ref: SOURCE_REF,
  },
  {
    id: 24,
    module: 2,
    prompt_en: "When do we talk about mutual authentication between two entities?",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "When both entities are administered by the same person" },
      { key: "b", text_en: "When each entity must authenticate to the other" },
      { key: "c", text_en: "When the communication between the two entities is encrypted" },
      { key: "d", text_en: "When both entities are on the same network" },
    ],
    correct: ["b"],
    explanation_en:
      "Mutual authentication means both sides verify each other's identity (e.g., mutual TLS). Encryption alone does not imply mutual authentication.",
    tags: ["authentication", "mutual_authentication", "tls"],
    source_ref: SOURCE_REF,
  },
  {
    id: 25,
    module: 2,
    prompt_en:
      "In a network, BYOD (Bring Your Own Device) can cause (choose the true proposition(s)):",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "A reduction of the perimeter to secure" },
      { key: "b", text_en: "The spread of malicious code" },
      { key: "c", text_en: "Company data leakage" },
      { key: "d", text_en: "Better information system security" },
    ],
    correct: ["b", "c"],
    explanation_en:
      "BYOD increases heterogeneity and control challenges, which can increase malware propagation and data leakage risks.",
    tags: ["byod", "malware", "data_leak"],
    source_ref: SOURCE_REF,
  },
  {
    id: 26,
    module: 2,
    prompt_en: "What is the famous principle in network traffic (flow) management?",
    type: "free_text",
    rubric: {
      required_points: [
        'I mention a "default deny" / allowlist approach.',
        "I mention allowing only the strictly necessary flows/services.",
      ],
      sample_answer_en:
        'Default deny: block everything by default and explicitly allow only the necessary flows/services.',
    },
    explanation_en:
      'A common best practice is "default deny": start from a blocked baseline, then allow only what is needed (least privilege applied to network flows).',
    tags: ["firewall", "default_deny", "least_privilege"],
    source_ref: SOURCE_REF,
  },
  {
    id: 27,
    module: 2,
    prompt_en: 'A "firewall" can be both hardware (dedicated appliance) and software:',
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["a"],
    explanation_en:
      "Firewalls exist as network appliances, host-based software, cloud firewalls, and combinations of these.",
    tags: ["firewall"],
    source_ref: SOURCE_REF,
  },
  {
    id: 28,
    module: 2,
    prompt_en:
      "Circle the true proposition(s) that can serve as a measure to secure remote access to a network:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Use a centralized authentication server such as TACACS+" },
      { key: "b", text_en: "Use the Internet" },
      { key: "c", text_en: "Use a secure protocol such as telnet or ftp" },
      { key: "d", text_en: "Use a VPN" },
    ],
    correct: ["a", "d"],
    explanation_en:
      "Centralized AAA (e.g., TACACS+/RADIUS) and VPNs are security measures. Telnet/FTP are insecure (plaintext). The Internet is just a transport, not a control.",
    tags: ["remote_access", "vpn", "aaa"],
    source_ref: SOURCE_REF,
  },
  {
    id: 29,
    module: 2,
    prompt_en: "Circle the good measure(s) to secure administration:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Make admin interfaces available to everyone from the Internet" },
      { key: "b", text_en: "All admins must use the same account to connect" },
      { key: "c", text_en: "Use a dedicated network for administration" },
      {
        key: "d",
        text_en: "Mutually authenticate admin workstations and the servers being administered",
      },
    ],
    correct: ["c", "d"],
    explanation_en:
      "Administrative access should be restricted and strongly authenticated (dedicated admin network, mutual auth). Shared admin accounts and Internet-exposed interfaces increase risk.",
    tags: ["admin_security", "segmentation", "authentication"],
    source_ref: SOURCE_REF,
  },
  {
    id: 30,
    module: 2,
    prompt_en: "Which technology is the most appropriate to secure your Wi-Fi access?",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "WEP" },
      { key: "b", text_en: "WPA" },
      { key: "c", text_en: "WPS" },
      { key: "d", text_en: "WPA2" },
    ],
    correct: ["d"],
    explanation_en:
      "WPA2 (and today WPA3) are designed to secure Wi-Fi. WEP is broken, WPA is older, and WPS is a convenience feature that can introduce weaknesses.",
    tags: ["wifi", "encryption"],
    source_ref: SOURCE_REF,
  },
  {
    id: 31,
    module: 2,
    prompt_en: "Circle the true proposition(s) when using a Wi-Fi hotspot:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "It may be a fake access point" },
      { key: "b", text_en: "Other connected people may see my communications" },
      { key: "c", text_en: "I am protected from malicious people" },
      { key: "d", text_en: "I am on a trusted network; I can disable my firewall" },
    ],
    correct: ["a", "b"],
    explanation_en:
      "Public hotspots can be malicious (evil twin) and are generally untrusted. You should assume others can attempt interception and keep protections enabled.",
    tags: ["wifi", "hotspot", "mitm"],
    source_ref: SOURCE_REF,
  },
  {
    id: 32,
    module: 2,
    prompt_en: "Why check the integrity of software?",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "To make sure it contains no viruses" },
      { key: "b", text_en: "To make sure the software I download has not been corrupted" },
      { key: "c", text_en: "To make sure the software works as promised" },
      { key: "d", text_en: "To make sure it is free" },
    ],
    correct: ["b"],
    explanation_en:
      "Integrity checks (hash/signature verification) help detect corruption or tampering during download, but do not guarantee the absence of malware.",
    tags: ["integrity", "software_integrity", "supply_chain"],
    source_ref: SOURCE_REF,
  },
  {
    id: 33,
    module: 2,
    prompt_en: "Which of the following statements can be true for downloadable software?",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Always free" },
      { key: "b", text_en: 'May be "open source"' },
      { key: "c", text_en: "May contain spyware" },
      { key: "d", text_en: "May be malware" },
    ],
    correct: ["b", "c", "d"],
    explanation_en:
      "Downloaded software can be open source or proprietary, and it may contain unwanted or malicious components. It is not necessarily free.",
    tags: ["software_download", "malware", "spyware"],
    source_ref: SOURCE_REF,
  },
  {
    id: 34,
    module: 2,
    prompt_en: "Name a good practice for configuring your antivirus:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Use an antivirus from a well-known vendor" },
      { key: "b", text_en: "Having installed an antivirus at least once" },
      { key: "c", text_en: "Keep the antivirus up to date (signatures and engine)" },
      {
        key: "d",
        text_en: "Prevent antivirus scans on certain folders or external devices",
      },
    ],
    correct: ["a", "c"],
    explanation_en:
      "An antivirus must be up to date and properly configured. Excluding folders/devices from scans can create blind spots.",
    tags: ["antivirus", "updates"],
    source_ref: SOURCE_REF,
  },
  {
    id: 35,
    module: 2,
    prompt_en:
      "Select the true proposition(s). An antivirus:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Can detect all malware, including unknown (undiscovered) ones" },
      { key: "b", text_en: "Protects against all threats" },
      { key: "c", text_en: "Can only detect malware that is known in its signature database" },
      { key: "d", text_en: "Must be active and up to date to be useful" },
    ],
    correct: ["c", "d"],
    explanation_en:
      "Signature-based detection is limited to known patterns, and the product must be active and current. No antivirus covers all threats.",
    tags: ["antivirus", "detection"],
    source_ref: SOURCE_REF,
  },
  {
    id: 36,
    module: 2,
    prompt_en: "Choose the potential symptom(s) of infection by malicious code:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "My antivirus is disabled" },
      { key: "b", text_en: "My computer runs more slowly" },
      { key: "c", text_en: "Many web pages open by themselves" },
      { key: "d", text_en: "Files or folders are created automatically" },
    ],
    correct: ["a", "b", "c", "d"],
    explanation_en:
      "Malware can disable defenses, degrade performance, cause pop-ups/redirects, and create files or persistence mechanisms.",
    tags: ["malware", "symptoms"],
    source_ref: SOURCE_REF,
  },
  {
    id: 37,
    module: 2,
    prompt_en:
      "Software updates are used to improve software and fix security vulnerabilities:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["a"],
    explanation_en:
      "Updates often include security patches that close known vulnerabilities, as well as bug fixes and improvements.",
    tags: ["patching", "vulnerabilities"],
    source_ref: SOURCE_REF,
  },
  {
    id: 38,
    module: 2,
    prompt_en: "How can you protect the confidentiality of your data?",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "By encrypting it" },
      { key: "b", text_en: "By hashing it to verify its integrity" },
      { key: "c", text_en: "By sending it to external media or to the cloud" },
      { key: "d", text_en: "By publishing it on the Internet" },
    ],
    correct: ["a"],
    explanation_en:
      "Encryption protects confidentiality. Hashing protects integrity. Backups help availability. Publishing data removes confidentiality.",
    tags: ["confidentiality", "encryption", "cia"],
    source_ref: SOURCE_REF,
  },
  {
    id: 39,
    module: 2,
    prompt_en: "Select the hardening methods for a configuration:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Change default passwords" },
      { key: "b", text_en: "Uninstall unnecessary software" },
      { key: "c", text_en: 'Enable "USB debugging" mode on phones' },
      { key: "d", text_en: "Secure the BIOS with a password" },
    ],
    correct: ["a", "b", "d"],
    explanation_en:
      "Hardening reduces the attack surface and removes weak defaults (default passwords, unnecessary services). Enabling USB debugging typically weakens security.",
    tags: ["hardening", "attack_surface", "passwords"],
    source_ref: SOURCE_REF,
  },
  {
    id: 40,
    module: 2,
    prompt_en: "Select the principle(s) to consider when granting user privileges:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: '"Everything that is not forbidden is allowed"' },
      { key: "b", text_en: "Least privilege" },
      { key: "c", text_en: "Need to know" },
      { key: "d", text_en: "Administrator rights for everyone" },
    ],
    correct: ["b", "c"],
    explanation_en:
      "Grant the minimum privileges required and limit access to what the user needs to know. Broad permissions and admin-for-all increase risk.",
    tags: ["least_privilege", "need_to_know", "access_control"],
    source_ref: SOURCE_REF,
  },
  {
    id: 41,
    module: 2,
    prompt_en: "Circle the bad practice(s) for passwords:",
    type: "mcq_multi",
    choices: [
      {
        key: "a",
        text_en: "I create a very long and very complex password that I cannot remember.",
      },
      { key: "b", text_en: "My date of birth is my password." },
      { key: "c", text_en: "I store my passwords in plaintext in a text file." },
      { key: "d", text_en: "My password must be at most 7 characters long." },
    ],
    correct: ["a", "b", "c", "d"],
    explanation_en:
      "Short, guessable, reused, or plaintext-stored passwords are risky. If a password is impossible to remember, people tend to write it down insecurely; prefer long passphrases and password managers.",
    tags: ["passwords", "authentication"],
    source_ref: SOURCE_REF,
  },
  {
    id: 42,
    module: 2,
    prompt_en: "Circle the good practice(s) for passwords:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "I save my passwords in each web browser." },
      {
        key: "b",
        text_en: "I create a long and complex password that I can remember easily.",
      },
      { key: "c", text_en: "I write my password on a post-it note hidden under my keyboard/PC." },
      { key: "d", text_en: "I use a password manager." },
    ],
    correct: ["b", "d"],
    explanation_en:
      "Prefer long memorable passphrases and a dedicated password manager. Writing passwords on a post-it is unsafe; browser storage can be acceptable in some contexts but is not the intended best practice here.",
    tags: ["passwords", "password_manager"],
    source_ref: SOURCE_REF,
  },
  {
    id: 43,
    module: 2,
    prompt_en: "Circle the good practice(s) when browsing the Internet:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "If I get hit by ransomware, I pay the ransom." },
      { key: "b", text_en: "I avoid communicating with strangers." },
      { key: "c", text_en: "I accept all requests on social media." },
      { key: "d", text_en: 'I give my email password to the "administrator" when they ask.' },
    ],
    correct: ["b"],
    explanation_en:
      "Be cautious with unknown contacts and requests. Do not share passwords, and paying ransoms is risky and discouraged.",
    tags: ["phishing", "social_engineering", "ransomware"],
    source_ref: SOURCE_REF,
  },
  {
    id: 44,
    module: 2,
    prompt_en: "Name two methods for physically securing assets/equipment:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Put sensitive equipment in a room with no access control" },
      { key: "b", text_en: "Attach sensitive equipment with security cables" },
      { key: "c", text_en: "Give all equipment the same name" },
      { key: "d", text_en: "Use privacy filters for screens" },
    ],
    correct: ["b", "d"],
    explanation_en:
      "Physical protection includes preventing theft and shoulder-surfing: locking devices and using screen privacy filters are good measures.",
    tags: ["physical_security", "privacy"],
    source_ref: SOURCE_REF,
  },
  {
    id: 45,
    module: 2,
    prompt_en: "Select the example(s) of security incident(s):",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Theft of equipment/device" },
      { key: "b", text_en: "Creating a user account for a new student" },
      { key: "c", text_en: "Presence of malicious code on a workstation" },
      {
        key: "d",
        text_en:
          "Disclosure on a forum of students' names, first names, and social security numbers",
      },
    ],
    correct: ["a", "c", "d"],
    explanation_en:
      "Theft, malware infection, and data leakage are incidents. Creating an account is a normal administrative action (unless done maliciously).",
    tags: ["incident_response", "data_breach", "malware", "physical_security"],
    source_ref: SOURCE_REF,
  },
  {
    id: 46,
    module: 2,
    prompt_en: "Choose the good reaction(s) in the face of a security incident:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Disable/uninstall your antivirus" },
      {
        key: "b",
        text_en:
          "Apply the rules/instructions you received (for example in the IT charter/policy)",
      },
      { key: "c", text_en: "Try to identify the cause of the incident" },
      { key: "d", text_en: "Disable your firewall (personal firewall, for example)" },
    ],
    correct: ["b", "c"],
    explanation_en:
      "Follow incident procedures and help with diagnosis. Disabling protections generally makes the situation worse.",
    tags: ["incident_response", "policy"],
    source_ref: SOURCE_REF,
  },
  {
    id: 47,
    module: 2,
    prompt_en: "Select the reason(s) why security audits can be performed:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "To obtain a certification or accreditation" },
      { key: "b", text_en: "To find weaknesses and fix them" },
      { key: "c", text_en: "To assess the security level" },
      { key: "d", text_en: "To cause security incidents" },
    ],
    correct: ["a", "b", "c"],
    explanation_en:
      "Audits support assurance: measuring security, finding weaknesses, and meeting certification requirements. They are not meant to create incidents.",
    tags: ["audit", "certification"],
    source_ref: SOURCE_REF,
  },

  // Module 3
  {
    id: 48,
    module: 3,
    prompt_en: "Security is at the heart of the implementation of the IP protocol family:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["b"],
    explanation_en:
      "The original IP stack was not designed with strong security properties by default; security is typically added via additional protocols and mechanisms (e.g., TLS, IPsec).",
    tags: ["ip", "network_protocols"],
    source_ref: SOURCE_REF,
  },
  {
    id: 49,
    module: 3,
    prompt_en:
      "When using the IP protocol, it is natively possible to authenticate the senders and receivers of an IP datagram:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["b"],
    explanation_en:
      "Basic IP does not provide authentication of endpoints; it can be spoofed without additional security layers.",
    tags: ["ip", "authentication"],
    source_ref: SOURCE_REF,
  },
  {
    id: 50,
    module: 3,
    prompt_en:
      "Encryption of transported data is automatically handled in the IP protocol family at the Transport layer:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["b"],
    explanation_en:
      "Encryption is not automatic; it requires explicit protocols/configurations (e.g., TLS at higher layers, or IPsec).",
    tags: ["encryption", "ip", "transport_layer"],
    source_ref: SOURCE_REF,
  },
  {
    id: 51,
    module: 3,
    prompt_en:
      "When an attacker C can listen to and modify information exchanged between A and B, we talk about eavesdropping:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "Passive" },
      { key: "b", text_en: "Active" },
      { key: "c", text_en: "Hacktivist" },
      { key: "d", text_en: "Discreet" },
    ],
    correct: ["b"],
    explanation_en:
      "If the attacker can modify traffic, it is active interception (man-in-the-middle). Passive eavesdropping only listens without altering messages.",
    tags: ["mitm", "eavesdropping"],
    source_ref: SOURCE_REF,
  },
  {
    id: 52,
    module: 3,
    prompt_en:
      "Choose at least 2 complementary security mechanisms that can be used to secure IP networks:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Using the Internet" },
      { key: "b", text_en: "Encrypting communications" },
      { key: "c", text_en: "Network segmentation" },
      { key: "d", text_en: "Authenticating entities" },
    ],
    correct: ["b", "c", "d"],
    explanation_en:
      "Securing IP networks typically combines encryption, authentication, and segmentation. The Internet is not a security mechanism.",
    tags: ["network_security", "encryption", "segmentation", "authentication"],
    source_ref: SOURCE_REF,
  },
  {
    id: 53,
    module: 3,
    prompt_en: "Name 2 mechanisms/technologies that can be used to secure IP networks:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Flow filtering" },
      { key: "b", text_en: "Monitoring/supervision of equipment" },
      { key: "c", text_en: "Use of wireless networks, such as Wi-Fi" },
      { key: "d", text_en: "BYOD (Bring Your Own Device)" },
    ],
    correct: ["a", "b"],
    explanation_en:
      "Filtering and monitoring are security measures. Wi-Fi and BYOD are technologies/usages that typically require additional security controls.",
    tags: ["firewall", "monitoring", "network_security"],
    source_ref: SOURCE_REF,
  },
  {
    id: 54,
    module: 3,
    prompt_en:
      "Circle a device that can define and control allowed and forbidden flows between two networks:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "A router" },
      { key: "b", text_en: "A firewall" },
      { key: "c", text_en: "A hub" },
      { key: "d", text_en: "A load balancer" },
    ],
    correct: ["b"],
    explanation_en:
      "A firewall enforces network flow policies (allow/deny rules). Routers primarily route, hubs broadcast, and load balancers distribute traffic.",
    tags: ["firewall", "network_security"],
    source_ref: SOURCE_REF,
  },
  {
    id: 55,
    module: 3,
    prompt_en: "What security role can a proxy server play?",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Cache previously requested web pages" },
      { key: "b", text_en: "Allow or block certain application flows" },
      { key: "c", text_en: "Detect malicious elements (content filtering)" },
      { key: "d", text_en: "Encrypt communications" },
    ],
    correct: ["b", "c"],
    explanation_en:
      "From a security perspective, proxies can enforce application-layer policy and filter content. Caching is a performance feature; encryption is typically provided by TLS/VPN mechanisms.",
    tags: ["proxy", "content_filtering", "policy_enforcement"],
    source_ref: SOURCE_REF,
  },
  {
    id: 56,
    module: 3,
    prompt_en: "Which device can help protect against Distributed Denial of Service (DDoS) attacks?",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "An antivirus" },
      { key: "b", text_en: "A router" },
      { key: "c", text_en: "A proxy" },
      { key: "d", text_en: "A load balancer" },
    ],
    correct: ["d"],
    explanation_en:
      "A load balancer can distribute traffic and increase resilience (often combined with upstream filtering and DDoS protection services).",
    tags: ["ddos", "load_balancer", "availability"],
    source_ref: SOURCE_REF,
  },
  {
    id: 57,
    module: 3,
    prompt_en:
      "My antivirus protects me enough. I am safe from all viruses, including new (0-day) ones not yet detected:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["b"],
    explanation_en:
      "Antivirus products reduce risk but do not eliminate it, especially for new or targeted threats.",
    tags: ["antivirus", "zero_day"],
    source_ref: SOURCE_REF,
  },
  {
    id: 58,
    module: 3,
    prompt_en:
      "Which antivirus component allows it to detect known malicious code?",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "The vendor name (Sophos, Trend Micro, McAfee...)" },
      { key: "b", text_en: "The flow matrix" },
      { key: "c", text_en: "The signature database" },
      { key: "d", text_en: "The encryption engine" },
    ],
    correct: ["c"],
    explanation_en:
      "Signature databases contain known patterns used to recognize previously identified malware.",
    tags: ["antivirus", "signatures"],
    source_ref: SOURCE_REF,
  },
  {
    id: 59,
    module: 3,
    prompt_en: "Which network device can be used to detect an intrusion?",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "A firewall" },
      { key: "b", text_en: "An IDS" },
      { key: "c", text_en: "An IPS" },
      { key: "d", text_en: "An antivirus" },
    ],
    correct: ["b", "c"],
    explanation_en:
      "IDS and IPS are designed for intrusion detection (IPS can also block). Firewalls enforce policy; antivirus focuses on endpoints/content.",
    tags: ["ids_ips", "intrusion_detection"],
    source_ref: SOURCE_REF,
  },
  {
    id: 60,
    module: 3,
    prompt_en:
      "Which technology creates a secure communication between two networks over an untrusted network?",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "Internet" },
      { key: "b", text_en: "Wi-Fi" },
      { key: "c", text_en: "VPN" },
      { key: "d", text_en: "4G" },
    ],
    correct: ["c"],
    explanation_en:
      "A VPN creates an authenticated and encrypted tunnel over an untrusted transport network.",
    tags: ["vpn", "encryption", "authentication"],
    source_ref: SOURCE_REF,
  },
  {
    id: 61,
    module: 3,
    prompt_en:
      'Complete the following sentence: "A TLS VPN is a tunnel established at the _____ layer:"',
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "Data" },
      { key: "b", text_en: "IP" },
      { key: "c", text_en: "Transport" },
      { key: "d", text_en: "HTTPS" },
    ],
    correct: ["c"],
    explanation_en:
      "TLS sits above the transport protocol and is commonly treated as operating at/over the transport layer for this kind of question (as opposed to IPsec at the IP layer).",
    tags: ["tls", "vpn", "osi_layers"],
    source_ref: SOURCE_REF,
  },
  {
    id: 62,
    module: 3,
    prompt_en: "Cryptography is the only way to securely create VPNs:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["a"],
    explanation_en:
      "VPN security relies on cryptography (encryption + authentication) to protect traffic over untrusted networks.",
    tags: ["vpn", "crypto"],
    source_ref: SOURCE_REF,
  },
  {
    id: 63,
    module: 3,
    prompt_en: "VLANs are virtual networks implemented on routers:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["b"],
    explanation_en:
      "VLANs are typically implemented on switches (with routing between VLANs performed by a router or Layer-3 switch).",
    tags: ["vlan", "segmentation"],
    source_ref: SOURCE_REF,
  },
  {
    id: 64,
    module: 3,
    prompt_en: "A proxy allows me to hide my internal address from the Internet:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["a"],
    explanation_en:
      "A proxy can act as an intermediary so external services see the proxy's address rather than the internal client's address.",
    tags: ["proxy", "network_security"],
    source_ref: SOURCE_REF,
  },
  {
    id: 65,
    module: 3,
    prompt_en:
      "In best practice rules, equipment that communicates directly with the Internet should be placed in a DMZ:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["a"],
    explanation_en:
      "A DMZ is used to isolate Internet-facing services from the internal network, limiting impact if exposed systems are compromised.",
    tags: ["dmz", "segmentation", "network_architecture"],
    source_ref: SOURCE_REF,
  },
  {
    id: 66,
    module: 3,
    prompt_en:
      "What is the name of the process that transforms plaintext into unreadable text using an algorithm?",
    type: "free_text",
    rubric: {
      required_points: ["Encryption (encipherment) / cryptographic encryption"],
      sample_answer_en: "Encryption (encipherment).",
    },
    explanation_en:
      "The process is encryption: transforming plaintext into ciphertext (typically using an algorithm and a key).",
    tags: ["encryption", "crypto"],
    source_ref: SOURCE_REF,
  },
  {
    id: 67,
    module: 3,
    prompt_en:
      "When the key used to transform plaintext into unreadable text is the same key used to transform unreadable text back into plaintext, this is called:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "Segmentation" },
      { key: "b", text_en: "Asymmetric encryption" },
      { key: "c", text_en: "Symmetric encryption" },
      { key: "d", text_en: "Virtualization" },
    ],
    correct: ["c"],
    explanation_en:
      "Using the same key for encryption and decryption is symmetric cryptography (shared secret).",
    tags: ["symmetric_crypto", "crypto"],
    source_ref: SOURCE_REF,
  },
  {
    id: 68,
    module: 3,
    prompt_en:
      'To send a private message to Bob, Alice uses Bob\'s public key to make the plaintext "unreadable", and Bob uses his private key to turn the "unreadable" text back into plaintext. This is called:',
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "Symmetric encryption" },
      { key: "b", text_en: "Tokenization" },
      { key: "c", text_en: "Private sending" },
      { key: "d", text_en: "Asymmetric encryption" },
    ],
    correct: ["d"],
    explanation_en:
      "Public-key (asymmetric) cryptography uses a public key to encrypt and a private key to decrypt for confidentiality to the key owner.",
    tags: ["asymmetric_crypto", "public_key", "crypto"],
    source_ref: SOURCE_REF,
  },
  {
    id: 69,
    module: 3,
    prompt_en:
      "Considering security needs, circle the need(s) ensured by an electronic signature:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "Availability" },
      { key: "b", text_en: "Integrity" },
      { key: "c", text_en: "Confidentiality" },
      { key: "d", text_en: "Safety" },
    ],
    correct: ["b"],
    explanation_en:
      "Digital signatures primarily ensure integrity and authenticity (and non-repudiation). They do not provide confidentiality or availability.",
    tags: ["digital_signature", "integrity", "crypto"],
    source_ref: SOURCE_REF,
  },
  {
    id: 70,
    module: 3,
    prompt_en: "Circle the elements that can be found in an entity's electronic certificate:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "The entity's names and URL" },
      { key: "b", text_en: "The entity's private key" },
      { key: "c", text_en: "A trusted third-party signature (certificate authority)" },
      { key: "d", text_en: "The certificate validity period" },
    ],
    correct: ["a", "c", "d"],
    explanation_en:
      "Certificates contain subject identification information, validity dates, and the CA's signature. Private keys are secret and are not included in certificates.",
    tags: ["pki", "certificates", "tls"],
    source_ref: SOURCE_REF,
  },
  {
    id: 71,
    module: 3,
    prompt_en:
      "When browsing the Internet, ____________ are temporary files created and managed by web browsers to store user information such as identifiers, themes, and display preferences.",
    type: "free_text",
    rubric: {
      required_points: ['I answered: "cookies".'],
      sample_answer_en: "Cookies.",
    },
    explanation_en:
      "Cookies are small pieces of data stored by the browser and sent back to the site, commonly used for sessions, preferences, and tracking.",
    tags: ["web", "cookies", "privacy"],
    source_ref: SOURCE_REF,
  },
  {
    id: 72,
    module: 3,
    prompt_en:
      "From the Internet, when an attacker bypasses authentication mechanisms and directly queries the database by writing specific commands, this is called:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "Hacking" },
      { key: "b", text_en: "XSS (Cross Site Scripting)" },
      { key: "c", text_en: "SQL injection" },
      { key: "d", text_en: "Malware" },
    ],
    correct: ["c"],
    explanation_en:
      "SQL injection happens when attacker-controlled input is interpreted as SQL commands, allowing unauthorized reads/writes in the database.",
    tags: ["web_security", "sql_injection"],
    source_ref: SOURCE_REF,
  },
  {
    id: 73,
    module: 3,
    prompt_en: "When browsing a website over HTTPS, circle the true proposition(s):",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "The website has an electronic certificate" },
      { key: "b", text_en: "All exchanges between the website and my browser must be encrypted" },
      { key: "c", text_en: "All exchanges are analyzed by my antivirus" },
      { key: "d", text_en: "Internet communications are faster" },
    ],
    correct: ["a", "b"],
    explanation_en:
      "HTTPS uses TLS: the site presents a certificate and traffic is encrypted in transit. Antivirus inspection is not guaranteed, and HTTPS does not inherently increase throughput.",
    tags: ["https", "tls", "certificates"],
    source_ref: SOURCE_REF,
  },
  {
    id: 74,
    module: 3,
    prompt_en: "When browsing a website over HTTPS, you must pay attention to:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Certificate validity (not expired)" },
      {
        key: "b",
        text_en:
          "The certificate authority that issued it (avoid self-signed or unrecognized authorities)",
      },
      { key: "c", text_en: "Your browser's warning that the certificate is not trusted" },
      {
        key: "d",
        text_en:
          'There is no reason to be careful! "https" means I can browse with full trust.',
      },
    ],
    correct: ["a", "b", "c"],
    explanation_en:
      "HTTPS reduces risk, but trust depends on correct certificate validation. Browser warnings, expired certs, and untrusted issuers are red flags.",
    tags: ["https", "tls", "cert_validation"],
    source_ref: SOURCE_REF,
  },

  // Module 4
  {
    id: 75,
    module: 4,
    prompt_en:
      "Which family of international standards can an organization draw on to integrate security within the organization?",
    type: "free_text",
    rubric: {
      required_points: ["ISO/IEC 27000 family (e.g., ISO 27001/27002)"],
      sample_answer_en: "The ISO/IEC 27000 family, especially ISO 27001 and ISO 27002.",
    },
    explanation_en:
      "An Information Security Management System (ISMS) is commonly based on ISO/IEC 27001 (requirements) and ISO/IEC 27002 (controls guidance).",
    tags: ["isms", "iso27001", "governance"],
    source_ref: SOURCE_REF,
  },
  {
    id: 76,
    module: 4,
    prompt_en: "Give a representative example of an organization that needs a security certification.",
    type: "free_text",
    rubric: {
      required_points: [
        "My example handles sensitive or critical data/services (e.g., health, finance, cloud hosting, defense).",
        "I mention a certification need (e.g., ISO 27001, sectoral certification, evaluation).",
      ],
      sample_answer_en:
        "Example: a cloud service provider hosting customer data may pursue ISO 27001 certification to demonstrate an ISMS and security controls.",
    },
    explanation_en:
      "Certification is often required or expected where trust and compliance matter (hosting providers, critical suppliers, regulated sectors, or organizations handling sensitive data).",
    tags: ["certification", "compliance", "governance"],
    source_ref: SOURCE_REF,
  },
  {
    id: 77,
    module: 4,
    prompt_en:
      "Very often in companies, all information has the same confidentiality level: \"all non-confidential\":",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["b"],
    explanation_en:
      "Information typically has different sensitivity levels. Classification helps apply appropriate controls based on impact and confidentiality needs.",
    tags: ["classification", "confidentiality"],
    source_ref: SOURCE_REF,
  },
  {
    id: 78,
    module: 4,
    prompt_en:
      "For good security integration in an organization, staff must be made aware of security according to their roles:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["a"],
    explanation_en:
      "Different roles face different risks. Tailored awareness and training improve security behavior where it matters most.",
    tags: ["security_awareness", "training", "governance"],
    source_ref: SOURCE_REF,
  },
  {
    id: 79,
    module: 4,
    prompt_en: "Name an offboarding (staff departure) management procedure.",
    type: "free_text",
    rubric: {
      required_points: [
        "Access removal: revoke/disable accounts, badges, VPN, and shared secrets.",
        "Asset recovery: collect devices and ensure data transfer/cleanup per policy.",
      ],
      sample_answer_en:
        "Offboarding checklist: disable the user's accounts and VPN access, revoke badges, collect the laptop/phone, and rotate any shared passwords.",
    },
    explanation_en:
      "Offboarding aims to remove access promptly and recover assets to prevent abuse after departure (account disablement, badge return, device collection, key/password rotation).",
    tags: ["offboarding", "access_control", "governance"],
    source_ref: SOURCE_REF,
  },
  {
    id: 80,
    module: 4,
    prompt_en:
      'Security is like "the cherry on the cake": it must be considered at the end of a project:',
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["b"],
    explanation_en:
      "Security should be integrated from the start (security by design). Adding it at the end is costly and often incomplete.",
    tags: ["security_by_design", "sdlc"],
    source_ref: SOURCE_REF,
  },
  {
    id: 81,
    module: 4,
    prompt_en:
      "The goal of a risk analysis is to determine, for a given scope (e.g., a project), the risks that can affect non-sensitive assets:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["b"],
    explanation_en:
      "Risk analysis focuses on protecting valuable assets, often the most sensitive or critical ones, by identifying and treating risks based on impact and likelihood.",
    tags: ["risk_analysis", "governance"],
    source_ref: SOURCE_REF,
  },
  {
    id: 82,
    module: 4,
    prompt_en: "Select the sentence that best summarizes a risk analysis approach:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "Identify threat agents and neutralize them" },
      { key: "b", text_en: "Identify important project stakeholders" },
      { key: "c", text_en: "Inventory assets" },
      { key: "d", text_en: "Determine risks and treat them" },
    ],
    correct: ["d"],
    explanation_en:
      "Risk analysis is about identifying assets and threats, evaluating risks, and deciding how to treat them (reduce, transfer, avoid, accept).",
    tags: ["risk_analysis", "risk_treatment"],
    source_ref: SOURCE_REF,
  },
  {
    id: 83,
    module: 4,
    prompt_en:
      "Must all risks identified in a risk analysis be treated with a risk reduction measure?",
    type: "free_text",
    rubric: {
      required_points: [
        "I say no: not all risks must be reduced.",
        "I mention at least one other option (accept, transfer, avoid) besides reduction.",
      ],
      sample_answer_en:
        "No. Some risks can be accepted (with justification), transferred (e.g., insurance/contract), or avoided; not all require a reduction control.",
    },
    explanation_en:
      "Risk treatment strategies include reduction (controls), acceptance, transfer, and avoidance. The decision depends on impact, likelihood, cost, and business constraints.",
    tags: ["risk_treatment", "risk_analysis"],
    source_ref: SOURCE_REF,
  },
  {
    id: 84,
    module: 4,
    prompt_en:
      "Choose the correct proposition(s). During risk analysis, risk reduction measures can be:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Technical and organizational" },
      { key: "b", text_en: "Technical only" },
      { key: "c", text_en: "Organizational only" },
      { key: "d", text_en: "Derived from defined security objectives" },
    ],
    correct: ["a", "d"],
    explanation_en:
      "Controls can be technical (e.g., encryption) and organizational (e.g., policies). They should be derived from security objectives and risk treatment decisions.",
    tags: ["risk_treatment", "controls", "governance"],
    source_ref: SOURCE_REF,
  },
  {
    id: 85,
    module: 4,
    prompt_en: "Choose the correct proposition(s):",
    type: "mcq_multi",
    choices: [
      {
        key: "a",
        text_en: "It is easier to attack a system than to make it invulnerable.",
      },
      { key: "b", text_en: "It is easy to create a system with no vulnerabilities." },
      {
        key: "c",
        text_en: "To defend a system, it is enough to protect it at the perimeter.",
      },
      { key: "d", text_en: "Defense in depth can be applied to protect a system." },
    ],
    correct: ["a", "d"],
    explanation_en:
      "Perfect security is unrealistic; attackers need only one weakness. Defense in depth uses multiple independent controls to reduce the chance and impact of compromise.",
    tags: ["defense_in_depth", "security_principles"],
    source_ref: SOURCE_REF,
  },
  {
    id: 86,
    module: 4,
    prompt_en:
      "Choose the correct proposition(s). Defense in depth is a military-origin principle that consists of multiple lines of defense forming autonomous barriers to defend a system:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["a"],
    explanation_en:
      "Defense in depth avoids single points of failure by layering controls (network, identity, endpoints, monitoring, backups, processes).",
    tags: ["defense_in_depth", "security_principles"],
    source_ref: SOURCE_REF,
  },
  {
    id: 87,
    module: 4,
    prompt_en:
      "Choose the correct proposition(s). For an organization, using cloud services must take into account:",
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Legal requirements related to hosted data" },
      {
        key: "b",
        text_en:
          "Security mechanisms such as encryption of stored data offered by the provider",
      },
      { key: "c", text_en: "What happens to hosted data at the end of the contract" },
      { key: "d", text_en: "The certifications the cloud provider holds" },
    ],
    correct: ["a", "b", "c", "d"],
    explanation_en:
      "Cloud risk management includes legal/compliance constraints, security features and responsibilities, end-of-contract data handling, and provider assurance (certifications/audits).",
    tags: ["cloud", "compliance", "data_lifecycle"],
    source_ref: SOURCE_REF,
  },
  {
    id: 88,
    module: 4,
    prompt_en:
      "One of the difficulties of integrating security in an organization is making informed choices about trusted products:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["a"],
    explanation_en:
      "Choosing trustworthy products requires expertise, evaluation, and often third-party assurance (certifications, security reviews, supplier risk management).",
    tags: ["procurement", "trusted_products", "governance"],
    source_ref: SOURCE_REF,
  },
  {
    id: 89,
    module: 4,
    prompt_en:
      "In an organization, security is critical. It must be imposed on everyone without consultation:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["b"],
    explanation_en:
      "Security is more effective with clear governance, communication, and user buy-in. Imposing controls without consultation can lead to workarounds (Shadow IT).",
    tags: ["governance", "change_management", "shadow_it"],
    source_ref: SOURCE_REF,
  },
  {
    id: 90,
    module: 4,
    prompt_en:
      '"Shadow IT" or "Shadow Cloud" is the practice where users subscribe directly to cloud services without IT approval and often despite security policy:',
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["a"],
    explanation_en:
      "Shadow IT/Cloud increases risk by bypassing governance, visibility, and security controls (identity, backups, logging, data residency, etc.).",
    tags: ["shadow_it", "cloud", "governance"],
    source_ref: SOURCE_REF,
  },
  {
    id: 91,
    module: 4,
    prompt_en:
      'Choose the correct proposition(s). "Big Data" can be an opportunity for security because it can allow:',
    type: "mcq_multi",
    choices: [
      { key: "a", text_en: "Sending the organization's sensitive data to the cloud in plaintext" },
      {
        key: "b",
        text_en: "Using processing capacity to analyze security events in real time",
      },
      {
        key: "c",
        text_en:
          "Correlating logs from different network devices to detect advanced persistent threats (APT)",
      },
      { key: "d", text_en: "Monitoring network traffic in real time to detect botnets" },
    ],
    correct: ["b", "c", "d"],
    explanation_en:
      "Large-scale data processing can improve detection and response (real-time analytics, correlation). Sending sensitive data in plaintext is not a security benefit.",
    tags: ["big_data", "siem", "apt", "botnet_detection"],
    source_ref: SOURCE_REF,
  },
  {
    id: 92,
    module: 4,
    prompt_en:
      "Name one cybersecurity role involved in each phase of a project lifecycle: requirements, development, validation, operations.",
    type: "free_text",
    rubric: {
      required_points: [
        "Requirements: I named a relevant role (e.g., security architect / risk analyst).",
        "Development: I named a relevant role (e.g., secure developer / AppSec engineer).",
        "Validation: I named a relevant role (e.g., penetration tester / security assessor).",
        "Operations: I named a relevant role (e.g., SOC analyst / security administrator).",
      ],
      sample_answer_en:
        "Requirements: security architect. Development: AppSec engineer. Validation: penetration tester. Operations: SOC analyst.",
    },
    explanation_en:
      "Security work spans the whole lifecycle: threat modeling and requirements, secure implementation, verification/testing, and secure operations/monitoring.",
    tags: ["security_roles", "sdlc", "governance"],
    source_ref: SOURCE_REF,
  },
  {
    id: 93,
    module: 4,
    prompt_en: "Cybersecurity skills sought are only technical:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["b"],
    explanation_en:
      "Cybersecurity also requires governance, risk, legal/compliance, communication, incident management, and business understanding.",
    tags: ["skills", "careers"],
    source_ref: SOURCE_REF,
  },
  {
    id: 94,
    module: 4,
    prompt_en: "Cybersecurity is a sector with few employment prospects:",
    type: "mcq_single",
    choices: [
      { key: "a", text_en: "True" },
      { key: "b", text_en: "False" },
    ],
    correct: ["b"],
    explanation_en:
      "Cybersecurity demand is strong across many industries. There are diverse roles and continued hiring needs.",
    tags: ["careers", "job_market"],
    source_ref: SOURCE_REF,
  },
] satisfies Question[];

export const questionsById = new Map<number, Question>(questions.map((q) => [q.id, q]));

