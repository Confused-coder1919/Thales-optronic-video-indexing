module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "ei-bg": "#f6f7f9",
        "ei-surface": "#ffffff",
        "ei-border": "#d5d9de",
        "ei-muted": "#6b7280",
        "ei-text": "#1f2937",
        "ei-accent": "#3aa2a4",
        "ei-accent-soft": "#e6f3f3",
        "ei-chip": "#eef4f6",
        "ei-tab": "#f2f4f7",
        "ei-pill-completed": "#2eac69",
        "ei-pill-processing": "#e3a33b",
        "ei-pill-failed": "#e05c4f",
        "ei-blue-soft": "#e9f3ff",
      },
      boxShadow: {
        soft: "0 1px 2px rgba(17, 24, 39, 0.06)",
      },
    },
  },
  plugins: [],
};
