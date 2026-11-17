import { Atom, BookOpen, Braces, Code2, Database, FileCode2, GitBranch, Layers, Palette, Rocket, Server, ShieldCheck, Sparkles, Terminal } from "lucide-react";

/** Cover art for a course: the learning path's own accent colour and icon, both of
 * which already live in the database. Names are resolved through this map rather than
 * `lucide-react`'s namespace so the bundle stays tree-shaken and an unexpected value
 * can never become a component lookup. */
const ICONS = { Atom, BookOpen, Braces, Code2, Database, FileCode2, GitBranch, Layers, Palette, Rocket, Server, ShieldCheck, Sparkles, Terminal };

const DEFAULT_COLOR = "#8b5cf6";

function rgba(hex, alpha) {
  const value = parseInt(hex.slice(1), 16);
  return `rgba(${(value >> 16) & 255}, ${(value >> 8) & 255}, ${value & 255}, ${alpha})`;
}

/** The colour is operator-entered, so anything that is not a plain #rrggbb falls back. */
function accent(value) {
  const text = String(value ?? "").trim();
  return /^#[0-9a-fA-F]{6}$/.test(text) ? text : DEFAULT_COLOR;
}

export function CourseCover({ path, className = "" }) {
  const color = accent(path?.color);
  const Icon = ICONS[String(path?.icon ?? "")] ?? BookOpen;

  return (
    <span
      className={`course-cover ${className}`.trim()}
      style={{
        background: `radial-gradient(115% 85% at 80% 12%, ${rgba(color, 0.55)}, ${rgba(color, 0)} 62%), linear-gradient(135deg, ${rgba(color, 0.32)}, rgba(9, 8, 24, 0.78) 70%)`,
        "--cover-glow": rgba(color, 0.5),
      }}
      aria-hidden="true"
    >
      <Icon className="course-cover__icon" strokeWidth={1.2} />
    </span>
  );
}
