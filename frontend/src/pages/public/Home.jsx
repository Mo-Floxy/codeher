import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  BadgeCheck,
  BookOpen,
  Code2,
  Sparkles,
  Target,
  Trophy,
  Users,
  Flame,
  Compass,
  MessagesSquare,
} from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync } from "../../hooks";
import { AnimatedNumber, GlowOrb, Reveal, Stagger } from "../../components/motion";
import {
  Avatar,
  Badge,
  Button,
  Card,
  Chip,
  EmptyState,
  LevelBadge,
  ProgressBar,
  SectionHeading,
  Skeleton,
  SkeletonList,
} from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import "./home.css";

const HERO_CODE = [
  { text: "// your first component", cls: "tk-com" },
  { text: "function Developer({ community }) {", parts: [["function ", "tk-key"], ["Developer", "tk-fn"], "({ community }) {"] },
  { text: "  const [skills, setSkills] = useState([]);", parts: [["  const [", "tk-key"], "skills, setSkills", ["] = ", "tk-key"], ["useState", "tk-fn"], "([]);"] },
  { text: "", plain: true },
  { text: '  return "I build with " + community;', parts: [["  return ", "tk-key"], ['"I build with "', "tk-str"], " + community;"] },
];

function HeroPreview() {
  const reduce = useReducedMotion();
  const [lineIndex, setLineIndex] = useState(reduce ? HERO_CODE.length : 0);

  useEffect(() => {
    if (reduce || lineIndex >= HERO_CODE.length) return undefined;
    const timer = setTimeout(() => setLineIndex((index) => index + 1), 420);
    return () => clearTimeout(timer);
  }, [lineIndex, reduce]);

  return (
    <div className="preview">
      <div className="preview__bar">
        <span className="preview__dot" style={{ background: "#fb7185" }} />
        <span className="preview__dot" style={{ background: "#fbbf24" }} />
        <span className="preview__dot" style={{ background: "#34d399" }} />
        <span className="preview__title">developer.jsx — CodeHer Studio</span>
      </div>

      <div className="preview__body">
        <pre className="preview__code" aria-label="Animated code sample" role="img">
          {HERO_CODE.slice(0, Math.max(1, lineIndex)).map((line, index) => (
            <motion.div
              key={index}
              initial={reduce ? false : { opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.25 }}
            >
              {line.parts
                ? line.parts.map((part, partIndex) =>
                    Array.isArray(part) ? (
                      <span key={partIndex} className={part[1]}>
                        {part[0]}
                      </span>
                    ) : (
                      <span key={partIndex}>{typeof part === "string" ? part : part.text}</span>
                    )
                  )
                : line.text}
              {index === lineIndex - 1 && !reduce && <span className="preview__caret" />}
            </motion.div>
          ))}
        </pre>

        <div className="preview__panel">
          <div className="preview__row">
            <span>React Development · lesson 6 of 24</span>
            <span style={{ color: "var(--violet)", fontWeight: 800 }}>75%</span>
          </div>
          <ProgressBar value={75} thin label="Course progress" />
          <div className="preview__row" style={{ marginTop: 4 }}>
            <span className="row" style={{ gap: 8 }}>
              <Flame size={15} style={{ color: "var(--pink)" }} /> 12-day streak
            </span>
            <span className="row" style={{ gap: 8 }}>
              <Trophy size={15} style={{ color: "var(--warning)" }} /> Level 7
            </span>
          </div>
        </div>
      </div>

      <span className="preview__badge preview__badge--xp">
        <Sparkles size={14} /> +120 XP
      </span>
      <span className="preview__badge preview__badge--streak">
        <BadgeCheck size={14} /> Certificate earned
      </span>
    </div>
  );
}

const STATS = [
  { key: "learners", label: "Members", icon: Users },
  { key: "courses", label: "Courses", icon: BookOpen },
  { key: "lessons", label: "Lessons", icon: Code2 },
  { key: "projects", label: "Projects shipped", icon: Target },
  { key: "mentor_matches", label: "Mentor matches", icon: Sparkles },
];

function StatsBand() {
  const { data, loading, error } = useAsync(
    (signal) => api.get("/site/stats/", { signal }),
    []
  );

  if (error) {
    return (
      <Card className="stats-band" style={{ textAlign: "center" }}>
        <p className="muted" style={{ gridColumn: "1 / -1", fontSize: "var(--fs-sm)" }}>
          Live platform stats are unavailable because the API is not reachable yet — start the Django
          backend to populate this band from the database. No numbers are invented here.
        </p>
      </Card>
    );
  }

  return (
    <div className="stats-band">
      {STATS.map((stat, index) => {
        const value = data?.[stat.key];
        return (
          <div className="stats-band__item" key={stat.key}>
            {loading ? (
              <Skeleton style={{ height: 34, width: "60%", margin: "0 auto" }} />
            ) : (
              <span className="stats-band__value">
                <AnimatedNumber value={Number(value ?? 0)} duration={1 + index * 0.08} />
              </span>
            )}
            <span className="stats-band__label">{stat.label}</span>
          </div>
        );
      })}
    </div>
  );
}

const HOW = [
  {
    icon: Compass,
    title: "Pick a path",
    body: "Choose a guided learning path — from HTML & CSS to full-stack Django — and see exactly which lesson comes next.",
  },
  {
    icon: Code2,
    title: "Build for real",
    body: "Lessons ship with runnable code examples and scored quizzes. Challenges run in an isolated sandbox, not in the app server.",
  },
  {
    icon: Users,
    title: "Learn together",
    body: "Publish projects, ask questions, and get answers from members and mentors. Every streak, badge and point comes from your activity.",
  },
];

const SAMPLE_TESTIMONIALS = [
  {
    name: "Amara O.",
    role: "Sample learner · Frontend",
    quote:
      "I had tried three free courses and quit all of them. The streak tracker and a weekly mentor call are what finally got me to ship my first React app.",
  },
  {
    name: "Nina K.",
    role: "Sample learner · Backend",
    quote:
      "The Django path explained migrations like a human. I moved from copying tutorials to designing my own schema.",
  },
  {
    name: "Priya S.",
    role: "Sample learner · Career switch",
    quote:
      "Posting my project to the showcase got me two code reviews and one interview. That was the push I needed.",
  },
];

export default function Home() {
  const { isAuthenticated } = useAuth();
  const reduce = useReducedMotion();

  const paths = useAsync((signal) => api.get(endpoints.paths, { signal, params: { page_size: 4 } }), []);
  const projects = useAsync(
    (signal) => api.get(endpoints.projects, { signal, params: { ordering: "trending", page_size: 3 } }),
    []
  );
  const testimonials = useAsync((signal) => api.get("/site/testimonials/", { signal }), []);

  const pathList = useMemo(() => (paths.data?.results ?? paths.data ?? []).slice(0, 4), [paths.data]);
  const projectList = useMemo(() => (projects.data?.results ?? []).slice(0, 3), [projects.data]);
  const genuine = testimonials.data?.results ?? testimonials.data ?? [];
  const usingSamples = genuine.length === 0;
  const quotes = usingSamples ? SAMPLE_TESTIMONIALS : genuine;

  return (
    <>
      {/* ---------------- Hero ---------------- */}
      <section className="hero" aria-labelledby="hero-title">
        {!reduce && (
          <>
            <GlowOrb size={420} top={-120} left={-80} color="rgba(139,92,246,0.34)" />
            <GlowOrb size={360} top={40} right={-90} color="rgba(236,72,153,0.28)" delay={2} />
          </>
        )}

        <div className="container hero__inner">
          <div className="hero__copy">
            <span className="eyebrow">For girls &amp; women in technology</span>

            <h1 className="hero__title" id="hero-title">
              {["Your Journey", "in Tech", "Starts Here."].map((line, index) => (
                <span className="line" key={line}>
                  <motion.span
                    className={index === 2 ? "text-gradient" : undefined}
                    initial={reduce ? false : { y: "110%" }}
                    animate={{ y: 0 }}
                    transition={{ duration: 0.75, delay: 0.1 + index * 0.12, ease: [0.22, 1, 0.36, 1] }}
                  >
                    {line}
                  </motion.span>
                </span>
              ))}
            </h1>

            <motion.p
              className="lead"
              initial={reduce ? false : { opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.42 }}
            >
              CodeHer is a technology learning and community platform: guided paths in HTML, CSS,
              JavaScript, React, Python, Django and MySQL, a sandboxed code editor for challenges, a
              project showcase that gets real reviews, and mentors who answer.
            </motion.p>

            <motion.div
              className="hero__cta"
              initial={reduce ? false : { opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.54 }}
            >
              <Button size="lg" to={isAuthenticated ? "/dashboard" : "/signup"}>
                Start Learning <ArrowRight size={18} />
              </Button>
              <Button size="lg" variant="ghost" to="/community">
                Explore the Community
              </Button>
            </motion.div>

            <div className="hero__trust">
              <span className="hero__avatars" aria-hidden="true">
                {["A", "M", "S", "K"].map((letter) => (
                  <span className="avatar" key={letter}>
                    {letter}
                  </span>
                ))}
              </span>
              <span>Free to join · Progress stored in your account · No credit card</span>
            </div>
          </div>

          <Reveal delay={0.2} y={30}>
            <HeroPreview />
          </Reveal>
        </div>
      </section>

      {/* ---------------- Impact stats ---------------- */}
      <section className="container" aria-label="Platform impact">
        <Reveal>
          <StatsBand />
        </Reveal>
      </section>

      {/* ---------------- Featured paths ---------------- */}
      <section className="section container" aria-labelledby="paths-title">
        <SectionHeading
          eyebrow="Curriculum"
          title="Featured learning paths"
          description="Nine structured paths, each broken into courses, lessons, quizzes and a completion record."
          action={
            <Button variant="outline" to="/learning">
              Browse all courses <ArrowRight size={16} />
            </Button>
          }
        />

        {paths.loading ? (
          <SkeletonList count={4} height={210} />
        ) : paths.error && pathList.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="Learning paths could not be loaded"
            description="The API did not answer, so this is a connection problem rather than an empty curriculum."
            action={<Button variant="ghost" onClick={paths.reload}>Try again</Button>}
          />
        ) : pathList.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No learning paths yet"
            description="Paths come from the database. Run the backend seed command to load the sample curriculum."
            action={<Button variant="ghost" to="/about">How seeding works</Button>}
          />
        ) : (
          <Stagger className="grid-auto">
            {pathList.map((path) => (
              <Stagger.Item key={path.id}>
                <Card hover to={`/learning?path=${path.slug}`} className="path-card" as="div">
                  <div
                    className="path-card__art"
                    style={{ background: `linear-gradient(130deg, ${path.color ?? "#8b5cf6"}, rgba(236,72,153,0.75))` }}
                  >
                    {path.title}
                  </div>
                  <h3 style={{ fontSize: "var(--fs-md)" }}>{path.title}</h3>
                  <p style={{ fontSize: "var(--fs-sm)" }}>{path.description}</p>
                  <div className="card__meta" style={{ justifyContent: "space-between" }}>
                    <LevelBadge level={path.level} />
                    <span>
                      {path.course_count} course{path.course_count === 1 ? "" : "s"}
                    </span>
                  </div>
                  {path.completed_course_count > 0 && (
                    <ProgressBar value={(path.completed_course_count / path.course_count) * 100} thin label={`${path.completed_course_count} completed by you`} />
                  )}
                </Card>
              </Stagger.Item>
            ))}
          </Stagger>
        )}
      </section>

      {/* ---------------- How it works ---------------- */}
      <section className="section container" aria-labelledby="how-title">
        <SectionHeading center eyebrow="How CodeHer works" title="Three steps, then momentum" />
        <div className="how">
          {HOW.map((step, index) => (
            <Reveal key={step.title} delay={index * 0.1}>
              <Card className="how__card">
                <span className="how__num">{index + 1}</span>
                <step.icon size={22} style={{ color: "var(--violet)", marginBottom: "var(--sp-3)" }} />
                <h3 style={{ fontSize: "var(--fs-md)", marginBottom: 8 }}>{step.title}</h3>
                <p style={{ fontSize: "var(--fs-sm)" }}>{step.body}</p>
              </Card>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ---------------- Featured projects ---------------- */}
      <section className="section container">
        <SectionHeading
          eyebrow="Showcase"
          title="Trending community projects"
          description="Ranked by real engagement — likes, comments and bookmarks from members, decayed over time."
          action={
            <Button variant="outline" to="/community/projects">
              Open the gallery <ArrowRight size={16} />
            </Button>
          }
        />

        {projects.loading ? (
          <SkeletonList count={3} height={180} />
        ) : projects.error && projectList.length === 0 ? (
          <EmptyState
            icon={Target}
            title="The showcase could not be loaded"
            description="The API did not answer, so nothing here says whether members have published projects."
            action={<Button variant="ghost" onClick={projects.reload}>Try again</Button>}
          />
        ) : projectList.length === 0 ? (
          <EmptyState
            icon={Target}
            title="Nothing published yet"
            description="The first showcase entries appear as soon as members publish projects."
            action={
              <Button variant="ghost" to="/projects/new">
                Publish your first project
              </Button>
            }
          />
        ) : (
          <Stagger className="grid-auto">
            {projectList.map((project) => (
              <Stagger.Item key={project.id}>
                <Card hover to={`/community/projects/${project.id}`}>
                  {project.screenshot ? (
                    <img src={project.screenshot} alt={project.title} style={{ borderRadius: "var(--r-md)", marginBottom: "var(--sp-4)", aspectRatio: "16/9", objectFit: "cover", width: "100%" }} />
                  ) : null}
                  <h3 style={{ fontSize: "var(--fs-md)" }}>{project.title}</h3>
                  <p style={{ fontSize: "var(--fs-sm)" }}>{project.description}</p>
                  <div className="row" style={{ gap: 6, marginTop: "var(--sp-3)" }}>
                    {(project.technologies ?? []).slice(0, 3).map((tech) => (
                      <Chip key={tech}>{tech}</Chip>
                    ))}
                  </div>
                  <div className="card__meta" style={{ marginTop: "var(--sp-3)" }}>
                    <Avatar user={project.owner} size="sm" />
                    <span>{project.owner?.display_name}</span>
                    <span style={{ marginLeft: "auto" }}>
                      ♥ {project.likes_count} · 💬 {project.comments_count}
                    </span>
                  </div>
                </Card>
              </Stagger.Item>
            ))}
          </Stagger>
        )}
      </section>

      {/* ---------------- Mentorship ---------------- */}
      <section className="section container">
        <Reveal>
          <div className="mentor-band">
            <div className="stack">
              <span className="eyebrow">Mentorship</span>
              <h2 id="mentorship-title">Never learn alone</h2>
              <p className="lead">
                Browse mentors by expertise, send a request with your goal and availability, and track
                it from pending to scheduled. Mentors control their own profile and session links —
                learners can only request.
              </p>
              <div className="row">
                <Button to="/mentorship">
                  Find a mentor <ArrowRight size={16} />
                </Button>
                <Button variant="ghost" to="/mentorships">
                  Track my requests
                </Button>
              </div>
            </div>
            <div className="mentor-grid">
              {[
                { title: "Request", body: "Pick a mentor, write your goal, choose slots." },
                { title: "Match", body: "They accept or decline — you get a notification." },
                { title: "Meet", body: "Scheduled session with a link and an agenda." },
                { title: "Grow", body: "Follow up on projects and career steps." },
              ].map((step, index) => (
                <Card key={step.title} className="stack" style={{ gap: 6, padding: "var(--sp-4)" }}>
                  <Badge variant="brand">{index + 1}</Badge>
                  <strong style={{ fontSize: "var(--fs-sm)" }}>{step.title}</strong>
                  <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>
                    {step.body}
                  </span>
                </Card>
              ))}
            </div>
          </div>
        </Reveal>
      </section>

      {/* ---------------- Testimonials ---------------- */}
      <section className="section container">
        <SectionHeading
          eyebrow="Voices"
          title="What members say"
          description={usingSamples ? undefined : "Published by CodeHer members."}
          action={
            usingSamples ? (
              <span className="sample-note">
                <BadgeCheck size={15} /> Development sample content — no genuine testimonials are
                published in the database yet.
              </span>
            ) : null
          }
        />
        <div className="testimonial-grid">
          {quotes.map((quote, index) => (
            <Reveal key={quote.name + index} delay={index * 0.08}>
              <Card>
                <div className="quote">
                  <span className="quote__mark" aria-hidden="true">
                    “
                  </span>
                  <p style={{ fontSize: "var(--fs-sm)" }}>{quote.quote}</p>
                  <div className="card__meta">
                    <Avatar user={{ display_name: quote.name }} size="sm" />
                    <span>
                      <strong style={{ color: "var(--text-primary)" }}>{quote.name}</strong>
                      <br />
                      {quote.role}
                    </span>
                  </div>
                </div>
              </Card>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ---------------- Final CTA ---------------- */}
      <section className="section container">
        <Reveal y={26}>
          <div className="final-cta">
            {!reduce && <GlowOrb size={300} top={-60} left="20%" color="rgba(34,211,238,0.22)" />}
            <h2 className="final-cta__title">Code Your Future. Own Your Power.</h2>
            <p className="lead" style={{ maxWidth: "58ch" }}>
              Create a free account, take the skill check, and land in your first lesson in under two
              minutes. Your progress, streak and badges are stored in your own account.
            </p>
            <div className="hero__cta" style={{ justifyContent: "center" }}>
              <Button size="lg" to={isAuthenticated ? "/dashboard" : "/signup"}>
                {isAuthenticated ? "Go to dashboard" : "Create free account"} <ArrowRight size={18} />
              </Button>
              <Button size="lg" variant="ghost" to="/challenges">
                Try a challenge
              </Button>
            </div>
          </div>
        </Reveal>
      </section>
    </>
  );
}
