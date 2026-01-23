export default function TopBar() {
  return (
    <header className="h-14 bg-ei-surface border-b border-ei-border flex items-center justify-between px-6">
      <div className="text-ei-accent font-semibold">Entity Indexing</div>
      <div className="w-8 h-8 rounded-full flex items-center justify-center text-ei-muted">
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      </div>
    </header>
  );
}
