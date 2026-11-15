import { useEffect, useRef } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import { Navbar } from "./Navbar";
import { Footer } from "./Footer";
import "./layouts.css";

export default function PublicLayout() {
  const location = useLocation();
  const reduce = useReducedMotion();
  const mainRef = useRef(null);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
  }, [location.pathname, reduce]);

  return (
    <div className="public-shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Navbar />
      <motion.main
        id="main"
        ref={mainRef}
        className="public-shell__main"
        initial={reduce ? false : { opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
        // Every route change replays the entry transition.
        key={location.pathname}
      >
        <Outlet />
      </motion.main>
      <Footer />
    </div>
  );
}

