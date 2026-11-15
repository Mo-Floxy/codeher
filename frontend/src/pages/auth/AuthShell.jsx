import { Navigate, useLocation } from "react-router-dom";
import { useReducedMotion } from "framer-motion";
import { BadgeCheck, Code2, Sparkles, Trophy, Users } from "lucide-react";
import { Logo } from "../../components/Brand";
import { GlowOrb } from "../../components/motion";
import { useAuth } from "../../context/AuthContext";
import "./auth.css";

const HIGHLIGHTS = [
  { icon: Code2, text: "Guided paths from HTML & CSS to Django full-stack" },
  { icon: Sparkles, text: "Sandboxed code editor with scored test cases" },
  { icon: Users, text: "Project showcase with reviews from members and mentors" },
  { icon: Trophy, text: "Streaks, XP and badges earned from verified actions" },
];

export default function AuthShell({ title, subtitle, children, footer, wide }) {
  const reduce = useReducedMotion();
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const target = location.state?.from;

  // Already signed in? No reason to see the form.
  if (isAuthenticated) return <Navigate to={target || "/dashboard"} replace />;

  return (
    <div className="auth-shell">
      <aside className="auth-side">
        {!reduce && (
          <>
            <GlowOrb size={340} top={-60} left={-60} color="rgba(139,92,246,0.35)" />
            <GlowOrb size={300} bottom={-40} right={-40} color="rgba(236,72,153,0.28)" delay={1.5} />
          </>
        )}
        <Logo />
        <div className="auth-side__body">
          <h2 className="text-gradient" style={{ fontSize: "var(--fs-2xl)", maxWidth: "16ch" }}>
            Code Your Future. Own Your Power.
          </h2>
          <ul className="stack" style={{ gap: "var(--sp-4)" }}>
            {HIGHLIGHTS.map(({ icon: Icon, text }) => (
              <li key={text} className="row" style={{ gap: "var(--sp-3)", alignItems: "flex-start" }}>
                <span className="auth-side__icon">
                  <Icon size={16} />
                </span>
                <span style={{ fontSize: "var(--fs-sm)", color: "var(--text-secondary)" }}>{text}</span>
              </li>
            ))}
          </ul>
        </div>
        <p className="muted" style={{ fontSize: "var(--fs-xs)" }}>
          <BadgeCheck size={13} style={{ display: "inline", verticalAlign: "-2px", marginRight: 6 }} />
          Passwords are hashed by Django; your progress is stored in the database behind the API.
        </p>
      </aside>

      <main className="auth-main">
        <div className={`auth-card ${wide ? "auth-card--wide" : ""}`.trim()}>
          <header className="auth-card__head">
            <h1>{title}</h1>
            {subtitle && <p>{subtitle}</p>}
          </header>
          {children}
          {footer && <footer className="auth-card__foot">{footer}</footer>}
        </div>
      </main>
    </div>
  );
}
