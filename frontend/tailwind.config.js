module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"] ,
  theme: {
    extend: {
      colors: {
        "ei-bg": "#0b0f14",
        "ei-panel": "#111825",
        "ei-card": "#182234",
        "ei-border": "#263145",
        "ei-accent": "#4fd1c5",
        "ei-text": "#e5edf5",
        "ei-muted": "#94a3b8"
      },
      boxShadow: {
        "soft": "0 8px 24px rgba(0,0,0,0.25)",
      }
    }
  },
  plugins: []
};
