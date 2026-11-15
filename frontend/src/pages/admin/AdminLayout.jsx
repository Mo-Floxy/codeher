import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import {
  ClipboardList,
  Code2,
  LayoutDashboard,
  Megaphone,
  Route as RouteIcon,
  ShieldAlert,
  Sparkles,
  Users,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { Button, Card, EmptyState } from "../../components/ui";
import AdminOverview from "./AdminOverview";
import AdminUsers from "./AdminUsers";
import AdminCurriculum from "./AdminCurriculum";
import AdminChallenges from "./AdminChallenges";
import AdminMentors from "./AdminMentors";
import AdminModeration from "./AdminModeration";
import AdminAnnouncements from "./AdminAnnouncements";
import "./admin.css";

const NAV = [
  { to: "/admin", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/admin/users", label: "Users", icon: Users },
  { to: "/admin/curriculum", label: "Curriculum", icon: RouteIcon },
  { to: "/admin/challenges", label: "Challenges", icon: Code2 },
  { to: "/admin/mentors", label: "Mentors", icon: Sparkles },
  { to: "/admin/moderation", label: "Moderation", icon: ClipboardList },
  { to: "/admin/announcements", label: "Announcements", icon: Megaphone },
];

export default function AdminLayout() {
  const { isAdmin, isAuthenticated, isBooting } = useAuth();

  if (isBooting) return null;

  // App.jsx already gates /admin to admins; this is a clean fallback for the
  // rare case of a stale session so the console never renders in a broken state.
  if (!isAuthenticated) return <Navigate to="/signin" state={{ from: "/admin" }} replace />;
  if (!isAdmin) {
    return (
      <div className="admin-shell">
        <EmptyState
          icon={ShieldAlert}
          title="Admins only"
          description="This console is restricted to staff accounts. Sign in with an administrator account to manage the platform."
          action={<Button to="/dashboard">Back to dashboard</Button>}
        />
      </div>
    );
  }

  return (
    <div className="admin-shell">
      <header className="admin-head">
        <h1 className="admin-head__title">Admin console</h1>
        <p className="app-page__sub">Manage members, curriculum, challenges, moderation and broadcasts. Read-only views are labelled.</p>
      </header>

      <nav className="admin-nav" aria-label="Admin sections">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => `admin-nav__link ${isActive ? "admin-nav__link--active" : ""}`.trim()}
          >
            <item.icon size={16} aria-hidden="true" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <Card flush style={{ padding: "var(--sp-6)" }}>
        <Routes>
          <Route index element={<AdminOverview />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="curriculum" element={<AdminCurriculum />} />
          <Route path="challenges" element={<AdminChallenges />} />
          <Route path="mentors" element={<AdminMentors />} />
          <Route path="moderation" element={<AdminModeration />} />
          <Route path="announcements" element={<AdminAnnouncements />} />
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Routes>
      </Card>
    </div>
  );
}
