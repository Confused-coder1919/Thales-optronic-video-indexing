import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="stack">
      <h1 className="h1">Page not found</h1>
      <p className="lead">The page you requested does not exist.</p>
      <div className="row">
        <Link className="btn primary" to="/">
          Go home
        </Link>
      </div>
    </div>
  );
}

