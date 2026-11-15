import { useEffect, useRef, useState } from "react";
import { motion, useInView, useReducedMotion } from "framer-motion";

const EASE = [0.22, 1, 0.36, 1];

/** Scroll-triggered reveal. Falls back to an instant render when motion is reduced. */
export function Reveal({ children, delay = 0, y = 22, as = "div", className, once = true, ...rest }) {
  const reduce = useReducedMotion();
  const ref = useRef(null);
  const inView = useInView(ref, { once, margin: "-70px" });
  const Tag = motion[as] ?? motion.div;

  if (reduce) {
    const Plain = as;
    return (
      <Plain ref={ref} className={className} {...rest}>
        {children}
      </Plain>
    );
  }

  return (
    <Tag
      ref={ref}
      className={className}
      initial={{ opacity: 0, y }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.55, delay, ease: EASE }}
      {...rest}
    >
      {children}
    </Tag>
  );
}

/** Staggers direct children — for grids of cards and lists. */
export function Stagger({ children, gap = 0.07, className, as = "div", ...rest }) {
  const reduce = useReducedMotion();
  const Tag = motion[as] ?? motion.div;
  if (reduce) {
    const Plain = as;
    return (
      <Plain className={className} {...rest}>
        {children}
      </Plain>
    );
  }
  return (
    <Tag
      className={className}
      initial="hidden"
      whileInView="shown"
      viewport={{ once: true, margin: "-60px" }}
      transition={{ staggerChildren: gap }}
      {...rest}
    >
      {children}
    </Tag>
  );
}

Stagger.Item = function StaggerItem({ children, className, ...rest }) {
  const reduce = useReducedMotion();
  if (reduce) return <div className={className}>{children}</div>;
  return (
    <motion.div className={className} variants={{ hidden: { opacity: 0, y: 20 }, shown: { opacity: 1, y: 0 } }} transition={{ duration: 0.5, ease: EASE }} {...rest}>
      {children}
    </motion.div>
  );
};

/** Counts from 0 to `value` with easing once visible — used for impact stats. */
export function AnimatedNumber({ value = 0, duration = 1.1, format, prefix = "", suffix = "" }) {
  const reduce = useReducedMotion();
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const [display, setDisplay] = useState(reduce ? value : 0);

  useEffect(() => {
    if (reduce || !inView) {
      if (reduce) setDisplay(value);
      return undefined;
    }
    let frame;
    const start = performance.now();
    const tick = (now) => {
      const progress = Math.min(1, (now - start) / (duration * 1000));
      const eased = 1 - (1 - progress) ** 3;
      setDisplay(value * eased);
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, inView, reduce, duration]);

  const text = format ? format(display) : Math.round(display).toLocaleString();
  return (
    <span ref={ref}>
      {prefix}
      {text}
      {suffix}
    </span>
  );
}

export function GlowOrb({ size = 380, color = "rgba(139, 92, 246, 0.32)", top, left, right, bottom, delay = 0 }) {
  const reduce = useReducedMotion();
  return (
    <motion.span
      aria-hidden="true"
      style={{
        position: "absolute",
        width: size,
        height: size,
        borderRadius: "50%",
        background: `radial-gradient(circle at 50% 50%, ${color}, transparent 68%)`,
        filter: "blur(46px)",
        pointerEvents: "none",
        top,
        left,
        right,
        bottom,
      }}
      animate={reduce ? undefined : { y: [0, -18, 0], opacity: [0.75, 1, 0.75] }}
      transition={{ duration: 9 + delay * 2, repeat: Infinity, ease: "easeInOut" }}
    />
  );
}
