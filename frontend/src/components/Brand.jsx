import { Link } from "react-router-dom";

/** Wordmark + glyph. `compact` shows only the glyph for the collapsed sidebar. */
export function Logo({ compact = false, size = 26, to = "/" }) {
  const glyph = (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="ch-mark" x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#8B5CF6" />
          <stop offset="0.55" stopColor="#A855F7" />
          <stop offset="1" stopColor="#EC4899" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill="url(#ch-mark)" fillOpacity="0.16" />
      <rect x="0.6" y="0.6" width="30.8" height="30.8" rx="8.6" stroke="url(#ch-mark)" strokeOpacity="0.55" strokeWidth="1.2" />
      <path d="M12.4 10.6 8.6 16l3.8 5.4" stroke="url(#ch-mark)" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M19.6 10.6 23.4 16l-3.8 5.4" stroke="url(#ch-mark)" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="16" cy="16" r="2.05" fill="url(#ch-mark)" />
    </svg>
  );

  if (compact) return <Link to={to} className="brand" aria-label="CodeHer home">{glyph}</Link>;

  return (
    <Link to={to} className="brand" aria-label="CodeHer home">
      {glyph}
      <span className="brand__word">
        Code<span className="text-gradient">Her</span>
      </span>
    </Link>
  );
}

export const TAGLINE = "Code Your Future. Own Your Power.";
