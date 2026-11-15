import { useEffect, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Bell, ChevronDown, LayoutDashboard, LogOut, Menu, Settings, Sparkles, X } from "lucide-react";
import { Logo } from "../components/Brand";
import { Avatar, Badge, Button, Dropdown, DropdownItem } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useNotificationCount } from "../hooks/useNotifications";
import { UserCell } from "../components/ui";

const LINKS = [
  { to: "/", label: "Home", end: true },
  { to: "/learning", label: "Learning" },
  { to: "/community", label: "Community" },
  { to: "/mentorship", label: "Mentorship" },
  { to: "/challenges", label: "Challenges" },
  { to: "/about", label: "About" },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { isAuthenticated, user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const reduce = useReducedMotion();
  const { count: unread } = useNotificationCount();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <header className={`site-nav ${scrolled ? "site-nav--solid" : ""}`.trim()}>
      <nav className="container site-nav__inner" aria-label="Main">
        <Logo />

        <ul className="site-nav__links">
          {LINKS.map((link) => (
            <li key={link.to}>
              <NavLink
                to={link.to}
                end={link.end}
                className={({ isActive }) => `nav-link ${isActive ? "nav-link--active" : ""}`.trim()}
              >
                {link.label}
              </NavLink>
            </li>
          ))}
        </ul>

        <div className="site-nav__actions">
          {isAuthenticated ? (
            <>
              <Link to="/notifications" className="nav-icon" aria-label={`Notifications${unread ? `, ${unread} unread` : ""}`}>
                <Bell size={19} />
                {unread > 0 && <span className="nav-icon__dot" aria-hidden="true" />}
              </Link>
              <Dropdown
                trigger={() => (
                  <button type="button" className="nav-user" aria-haspopup="menu">
                    <Avatar user={user} size="sm" />
                    <span className="nav-user__name">{user?.display_name || user?.username}</span>
                    <ChevronDown size={15} />
                  </button>
                )}
              >
                <span style={{ padding: "10px 13px" }}>
                  <UserCell user={user} subtitle={user?.email} size="sm" />
                </span>
                <span className="dropdown__divider" />
                <DropdownItem to="/dashboard" icon={LayoutDashboard}>
                  Dashboard
                </DropdownItem>
                <DropdownItem to="/achievements" icon={Sparkles}>
                  Achievements
                </DropdownItem>
                <DropdownItem to="/profile" icon={Settings}>
                  Profile settings
                </DropdownItem>
                <span className="dropdown__divider" />
                <DropdownItem danger onClick={handleLogout} icon={LogOut}>
                  Sign out
                </DropdownItem>
              </Dropdown>
            </>
          ) : (
            <>
              <Button variant="link" to="/signin">
                Sign In
              </Button>
              <Button to="/signup">Get Started</Button>
            </>
          )}

          <button
            type="button"
            className="nav-burger"
            onClick={() => setMobileOpen((open) => !open)}
            aria-expanded={mobileOpen}
            aria-controls="mobile-nav"
            aria-label={mobileOpen ? "Close menu" : "Open menu"}
          >
            {mobileOpen ? <X size={21} /> : <Menu size={21} />}
          </button>
        </div>
      </nav>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            id="mobile-nav"
            className="mobile-nav"
            role="dialog"
            aria-label="Mobile navigation"
            initial={reduce ? false : { opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.24 }}
          >
            <ul>
              {LINKS.map((link) => (
                <li key={link.to}>
                  <NavLink to={link.to} end={link.end} className={({ isActive }) => `mobile-nav__link ${isActive ? "nav-link--active" : ""}`.trim()}>
                    {link.label}
                  </NavLink>
                </li>
              ))}
            </ul>
            <div className="mobile-nav__footer">
              {isAuthenticated ? (
                <>
                  <Badge variant="brand">{user?.role}</Badge>
                  <Button variant="ghost" block onClick={handleLogout}>
                    Sign out
                  </Button>
                </>
              ) : (
                <>
                  <Button variant="ghost" block to="/signin">
                    Sign In
                  </Button>
                  <Button block to="/signup">
                    Get Started
                  </Button>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
