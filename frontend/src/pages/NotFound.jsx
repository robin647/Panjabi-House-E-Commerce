import { Link } from "react-router-dom";
import { SearchX } from "lucide-react";
import { EmptyState } from "../components/ui";
import { useDocumentTitle } from "../lib/hooks";

export default function NotFound() {
  useDocumentTitle("Page not found");
  return (
    <div className="container page">
      <EmptyState icon={SearchX} title="Page not found" action={<Link to="/" className="btn btn-primary">Back to home</Link>}>
        The page you’re looking for doesn’t exist or has moved.
      </EmptyState>
    </div>
  );
}
