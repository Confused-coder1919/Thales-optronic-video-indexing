import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Home" },
  { to: "/videos", label: "Videos" },
  { to: "/search", label: "Search" },
  { to: "/upload", label: "Upload" },
];

export default function Sidebar() {
  return (
    <aside className="w-52 bg-ei-surface border-r border-ei-border min-h-screen px-4 py-6">
      <nav className="flex flex-col gap-2">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === "/"}
            className={({ isActive }) =>
              isActive ? "ei-sidebar-link active" : "ei-sidebar-link"
            }
          >
            <span className="w-4 h-4 text-ei-muted">
              <span className="inline-block w-2 h-2 rounded-full border border-ei-border" />
            </span>
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
