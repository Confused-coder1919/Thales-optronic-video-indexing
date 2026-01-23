import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Home" },
  { to: "/library", label: "Videos Library" },
  { to: "/upload", label: "Upload" },
  { to: "/search", label: "Unified Entity Search" },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-ei-panel border-r border-ei-border min-h-screen p-6">
      <div className="mb-8">
        <div className="text-lg font-semibold">Entity Indexing</div>
        <div className="text-xs text-ei-muted">Video intelligence workspace</div>
      </div>
      <nav className="flex flex-col gap-2">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              isActive ? "sidebar-link active" : "sidebar-link"
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-10 text-xs text-ei-muted">
        <div className="uppercase tracking-widest">Status</div>
        <div className="mt-2">Backend API connected</div>
      </div>
    </aside>
  );
}
