import { Link } from "react-router-dom";
import { useReducedMotion } from "framer-motion";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";

export function Card({ as = "div", hover, glow, flush, className = "", to, ...rest }) {
  const Tag = to ? Link : as;
  const classes = ["card", hover && "card--hover", glow && "card--glow", flush && "card--flush", className]
    .filter(Boolean)
    .join(" ");
  return <Tag to={to} className={classes} {...rest} />;
}

export function Stat({ label, value, icon: Icon, delta, tone = "brand" }) {
  const reduce = useReducedMotion();
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const tones = { brand: "var(--violet)", pink: "var(--pink)", cyan: "var(--cyan)", success: "var(--success)", warning: "var(--warning)" };

  return (
    <motion.div
      ref={ref}
      className="stat"
      initial={reduce ? false : { opacity: 0, y: 14 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
    >
      <span className="stat__label" style={{ color: tones[tone] }}>
        {Icon && <Icon size={15} aria-hidden="true" />}
        {label}
      </span>
      <span className="stat__value">{value}</span>
      {delta && <span className="stat__delta">{delta}</span>}
    </motion.div>
  );
}
