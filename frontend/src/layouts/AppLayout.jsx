import { useEffect, useState } from "react";
import { Link, NavLink, Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  Bell,
  BookOpen,
  ChevronLeft,
  Code2,
  ExternalLink,
  LayoutDashboard,
  LogOut,
  Menu,
  Network,
  Settings,
  Shield,
  Sparkles,
  Users,
  X,
} from "lucide-react";
import { Logo } from "../components/Brand";
import { Avatar, Badge, Button, Dropdown, DropdownItem } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useNotificationCount } from "../hooks/useNotifications";
import "./layouts.css";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/learning", label: "Learning", icon: BookOpen },
  { to: "/challenges", label: "Challenges", icon: Code2 },
  { to: "/community", label: "Community", icon: Users },
  { to: "/community/projects", label: "Projects", icon: Network },
  { to: "/mentorship", label: "Mentorship", icon: Sparkles },
  { to: "/achievements", label: "Achievements", icon: Bell },
];

const COLLAPSE_KEY = "codeher.sidebar.collapsed";

export default function AppLayout() {
  const { isAuthenticated, isBooting, user, profile, isAdmin, isMentor, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const reduce = useReducedMotion();
  const { count: unread } = useNotificationCount();
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(COLLAPSE_KEY) === "1");
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem(COLLAPSE_KEY, collapsed ? "1" : "0");
  }, [collapsed]);

  useEffect(() => {
    setDrawerOpen(false);
  }, [location.pathname]);

  if (isBooting) {
    return <div className="app-boot" role="status">Restoring your session…</div>;
  }
  if (!isAuthenticated) {
    return <Navigate to="/signin" state={{ from: location.pathname }} replace />;
  }

  const items = [
    ...NAV,
    ...(isMentor || isAdmin ? [{ to: "/mentorships", label: "My mentorships", icon: Users }] : []),
    ...(isAdmin ? [{ to: "/admin", label: "Admin", icon: Shield }] : []),
  ];

  const sidebar = (
    <div className={`side ${collapsed ? "side--collapsed" : ""}`.trim()}>
      <div className="side__head">
        <Logo compact={collapsed} />
        <button
          type="button"
          className="side__collapse"
          onClick={() => setCollapsed((value) => !value)}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <ChevronLeft size={16} style={{ transform: collapsed ? "rotate(180deg)" : undefined }} />
        </button>
      </div>

      <nav className="side__nav" aria-label="Workspace">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `side__link ${isActive ? "side__link--active" : ""}`.trim()}
            title={collapsed ? label : undefined}
          >
            <Icon size={18} aria-hidden="true" />
            {!collapsed && <span>{label}</span>}
            {!collapsed && to === "/notifications" && unread > 0 && <Badge variant="brand">{unread}</Badge>}
          </NavLink>
        ))}
      </nav>

      <div className="side__foot">
        {!collapsed && (
          <div className="side__xp">
            <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>
              Level {profile?.level ?? 1} · {profile?.total_xp ?? 0} XP
            </span>
            <div className="progress progress--thin">
              <div className="progress__bar" style={{ width: `${profile?.level_progress_percent ?? 0}%` }} />
            </div>
          </div>
        )}
        <Link to="/" className="side__link" title="Back to the public site">
          <ExternalLink size={18} aria-hidden="true" />
          {!collapsed && <span>Public site</span>}
        </Link>
      </div>
    </div>
  );

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <div className="app-shell">
      <aside className="app-shell__side desktop-only">{sidebar}</aside>

      <div className="app-shell__body">
        <header className="app-topbar">
          <button type="button" className="nav-burger mobile-only" onClick={() => setDrawerOpen(true)} aria-label="Open navigation" aria-expanded={drawerOpen}>
            <Menu size={20} />
          </button>
          <span className="app-topbar__logo mobile-only">
            <Logo />
          </span>

          <div className="app-topbar__spacer" />

          <Link to="/notifications" className="nav-icon" aria-label={`Notifications${unread ? `, ${unread} unread` : ""}`}>
            <Bell size={19} />
            {unread > 0 && <span className="nav-icon__dot" aria-hidden="true" />}
          </Link>
          <Dropdown
            trigger={() => (
              <button type="button" className="nav-user" aria-haspopup="menu">
                <Avatar user={user} size="sm" />
                <span className="nav-user__name">{user?.display_name || user?.username}</span>
              </button>
            )}
          >
            <span style={{ padding: "10px 13px", fontSize: "var(--fs-xs)" }} className="muted">
              Signed in as {user?.email}
            </span>
            <DropdownItem to="/profile" icon={Settings}>
              Profile settings
            </DropdownItem>
            <DropdownItem to="/achievements" icon={Sparkles}>
              Achievements
            </DropdownItem>
            <DropdownItem to="/dashboard" icon={LayoutDashboard}>
              Dashboard
            </DropdownItem>
            <div className="dropdown__divider" />
            <DropdownItem danger onClick={handleLogout} icon={LogOut}>
              Sign out
            </DropdownItem>
          </Dropdown>
        </header>

        <main className="app-shell__main" id="main">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={reduce ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      <AnimatePresence>
        {drawerOpen && (
          <>
            <motion.div
              className="drawer-backdrop mobile-only"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setDrawerOpen(false)}
              aria-hidden="true"
            />
            <motion.aside
              className="drawer mobile-only"
              role="dialog"
              aria-label="Navigation"
              initial={reduce ? false : { x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ duration: 0.26, ease: [0.22, 1, 0.36, 1] }}
            >
              <button type="button" className="drawer__close" onClick={() => setDrawerOpen(false)} aria-label="Close navigation">
                <X size={19} />
              </button>
              {sidebar}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
