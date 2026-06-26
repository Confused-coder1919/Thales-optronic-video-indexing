import { Link, NavLink, Outlet } from "react-router-dom";
import { useMemo } from "react";
import { useAppStore } from "./store/appStore";
import { useNow } from "./lib/useNow";

function useDueCount(): number {
  const reviewQueue = useAppStore((s) => s.reviewQueue);
  const now = useNow({ intervalMs: 30_000 });
  return useMemo(() => {
    return Object.values(reviewQueue).filter((it) => it.nextDue <= now).length;
  }, [reviewQueue, now]);
}

type NavItem = {
  to: string;
  label: string;
  mobileLabel: string;
  badgeDesktop?: string | number;
  badgeMobile?: string | number;
};

export default function App() {
  const dueCount = useDueCount();
  const inProgress = useAppStore((s) => s.inProgressTest);
  const navItems: NavItem[] = [
    { to: "/", label: "Home", mobileLabel: "Home" },
    { to: "/learn", label: "Learn", mobileLabel: "Learn" },
    {
      to: "/test",
      label: "Test",
      mobileLabel: "Test",
      badgeDesktop: inProgress ? "resume" : undefined,
      badgeMobile: inProgress ? "!" : undefined,
    },
    {
      to: "/review",
      label: "Review",
      mobileLabel: "Review",
      badgeDesktop: dueCount ? dueCount : undefined,
      badgeMobile: dueCount ? dueCount : undefined,
    },
    { to: "/attribution", label: "Attribution", mobileLabel: "Credit" },
  ];

  return (
    <>
      <header className="app-header">
        <div className="container header-inner">
          <Link to="/" className="brand" aria-label="CyberEdu Quiz home">
            <div className="brand-title">CyberEdu Quiz</div>
            <div className="brand-sub">English learning + test + review (local-first)</div>
          </Link>

          <nav className="nav nav-desktop" aria-label="Primary navigation">
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.to === "/"}>
                {item.label}{" "}
                {item.badgeDesktop !== undefined ? <span className="badge">{item.badgeDesktop}</span> : null}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="container page">
        <Outlet />
      </main>
      <nav className="mobile-nav" aria-label="Mobile navigation">
        <div className="mobile-nav-inner">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === "/"}>
              <span>{item.mobileLabel}</span>
              {item.badgeMobile !== undefined ? <span className="badge">{item.badgeMobile}</span> : null}
            </NavLink>
          ))}
        </div>
      </nav>
      <footer className="app-footer">
        <div className="container footer-inner">
          <div className="footer-meta">
            <div className="footer-title">CyberEdu Quiz (EN)</div>
            <div className="footer-sub">Local-first learning app (no backend)</div>
          </div>
          <a
            className="footer-powered"
            href="https://linguistic-communication.com/"
            target="_blank"
            rel="noreferrer noopener"
            aria-label="Powered by Linguistic Communication (opens in a new tab)"
            title="Powered by Linguistic Communication"
          >
            <img
              className="footer-logo"
              src="/brand/linguistic-communication.jpg"
              alt="Linguistic Communication"
              loading="lazy"
              decoding="async"
            />
            <span className="footer-powered-text">
              <span className="footer-powered-kicker">Powered by</span>
              <span className="footer-powered-brand">Linguistic Communication</span>
            </span>
          </a>
        </div>
      </footer>
    </>
  );
}
