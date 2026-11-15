import { ArrowLeft, Compass } from "lucide-react";
import { Link } from "react-router-dom";
import { Button, Card } from "../components/ui";
import { GlowOrb, Reveal } from "../components/motion";

export default function NotFound() {
  return (
    <section className="section container" style={{ minHeight: "62vh", display: "grid", placeItems: "center", position: "relative" }}>
      <GlowOrb size={320} top={-40} right={-40} color="rgba(236,72,153,0.25)" />
      <Reveal>
        <Card glow className="stack" style={{ maxWidth: 520, textAlign: "center", justifyItems: "center", padding: "var(--sp-8) var(--sp-6)" }}>
          <span className="empty-state__icon" style={{ width: 62, height: 62 }}>
            <Compass size={28} />
          </span>
          <p style={{ fontSize: "var(--fs-3xl)", fontWeight: 800, lineHeight: 1 }} className="text-gradient">
            404
          </p>
          <h1 style={{ fontSize: "var(--fs-xl)" }}>This page does not exist</h1>
          <p>
            The link may be old, or the page you want is behind a sign-in. Try the dashboard, the
            course catalog, or search the community.
          </p>
          <div className="row" style={{ justifyContent: "center" }}>
            <Button to="/dashboard">
              Go to dashboard
            </Button>
            <Button variant="ghost" to="/learning">
              Browse learning
            </Button>
          </div>
          <Link to="/" className="muted" style={{ fontSize: "var(--fs-sm)", display: "inline-flex", gap: 6, alignItems: "center" }}>
            <ArrowLeft size={15} /> Back to home
          </Link>
        </Card>
      </Reveal>
    </section>
  );
}
