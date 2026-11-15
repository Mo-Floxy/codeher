import { Link } from "react-router-dom";
import { AtSign, Globe, MessageCircle, Rss, Send } from "lucide-react";
import { Logo, TAGLINE } from "../components/Brand";
import { Button, Input } from "../components/ui";
import { useToast } from "../context/ToastContext";
import { useState } from "react";

const COLUMNS = [
  {
    title: "Learn",
    links: [
      { label: "Learning paths", to: "/learning" },
      { label: "All courses", to: "/learning?level=Beginner" },
      { label: "Coding challenges", to: "/challenges" },
      { label: "Certificates", to: "/certificates" },
    ],
  },
  {
    title: "Community",
    links: [
      { label: "Feed", to: "/community" },
      { label: "Project showcase", to: "/community/projects" },
      { label: "Mentors", to: "/mentorship" },
      { label: "Leaderboard", to: "/achievements" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About CodeHer", to: "/about" },
      { label: "Sign in", to: "/signin" },
      { label: "Create account", to: "/signup" },
      { label: "Admin console", to: "/admin" },
    ],
  },
];

const SOCIAL_KEY = "codeher:digest-signups";

function readSignups() {
  try {
    const parsed = JSON.parse(localStorage.getItem(SOCIAL_KEY) ?? "[]");
    return Array.isArray(parsed) ? parsed.filter((item) => typeof item === "string") : [];
  } catch {
    return [];
  }
}

// Filled in from frontend/.env — an unset profile renders no icon at all,
// because a link to somebody else's brand page is worse than no link.
// Vite only substitutes `import.meta.env.VITE_*` statically, so each key is spelled out.
const SOCIALS = [
  { href: import.meta.env.VITE_SOCIAL_GITHUB_URL, label: "GitHub", icon: Globe },
  { href: import.meta.env.VITE_SOCIAL_LINKEDIN_URL, label: "LinkedIn", icon: AtSign },
  { href: import.meta.env.VITE_SOCIAL_COMMUNITY_URL, label: "Community chat", icon: MessageCircle },
  { href: import.meta.env.VITE_SOCIAL_FEED_URL, label: "Blog feed", icon: Rss },
].filter((entry) => Boolean(entry.href));

export function Footer() {
  const toast = useToast();
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");

  // Newsletter delivery needs an ESP credential, so capture locally and be honest about it.
  const subscribe = (event) => {
    event.preventDefault();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
      setError("Enter a valid email address.");
      return;
    }
    setError("");
    const saved = readSignups();
    if (!saved.includes(email)) saved.push(email);
    try {
      localStorage.setItem(SOCIAL_KEY, JSON.stringify(saved));
      toast.info(`Saved on this device (${saved.length} address${saved.length === 1 ? "" : "es"}). Set EMAIL_HOST in backend/.env to deliver campaigns.`);
    } catch {
      toast.error("This browser blocked local storage, so the address could not be kept.");
    }
    setEmail("");
  };

  return (
    <footer className="site-footer">
      <div className="container">
        <div className="site-footer__top">
          <div className="site-footer__brand">
            <Logo />
            <p style={{ maxWidth: "34ch", fontSize: "var(--fs-sm)" }}>{TAGLINE}</p>
            <p className="muted" style={{ fontSize: "var(--fs-xs)", maxWidth: "36ch" }}>
              A technology learning and community platform for girls and women in software.
            </p>
            {SOCIALS.length > 0 && (
              <ul className="site-footer__socials">
                {SOCIALS.map(({ label, icon: Icon, href }) => (
                  <li key={label}>
                    <a href={href} aria-label={`${label} — opens in a new tab`} target="_blank" rel="noreferrer">
                      <Icon size={17} />
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <nav className="site-footer__cols" aria-label="Footer">
            {COLUMNS.map((column) => (
              <div key={column.title}>
                <h4 style={{ fontSize: "var(--fs-sm)", marginBottom: "var(--sp-3)" }}>{column.title}</h4>
                <ul className="stack" style={{ gap: 9 }}>
                  {column.links.map((link) => (
                    <li key={link.label}>
                      <Link to={link.to} className="footer-link">
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </nav>

          <div className="site-footer__cta">
            <h4 style={{ fontSize: "var(--fs-md)" }}>Weekly build digest</h4>
            <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
              One email a week: a new lesson, a challenge, and a community project.
            </p>
            <form onSubmit={subscribe} className="stack" style={{ gap: "var(--sp-2)" }}>
              <label className="sr-only" htmlFor="footer-email">
                Email address
              </label>
              <div className="input-group">
                <span className="input-group__icon" aria-hidden="true">
                  <Send size={16} />
                </span>
                <Input
                  id="footer-email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  aria-invalid={error ? "true" : undefined}
                  error={error}
                />
              </div>
              {error && (
                <p className="field__error" role="alert">
                  {error}
                </p>
              )}
              <Button type="submit" block>
                Subscribe
              </Button>
            </form>
          </div>
        </div>

        <div className="site-footer__bottom">
          <p className="muted" style={{ fontSize: "var(--fs-xs)" }}>
            © {new Date().getFullYear()} CodeHer. Built for learners, by learners.
          </p>
          <p className="muted" style={{ fontSize: "var(--fs-xs)" }}>
            {SOCIALS.length
              ? "Community links open in a new tab."
              : "No external profiles configured yet — set VITE_SOCIAL_* in frontend/.env to show them."}
          </p>
        </div>
      </div>
    </footer>
  );
}
