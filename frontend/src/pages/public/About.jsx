import { ArrowRight, Compass, HeartHandshake, ShieldCheck, Sparkles, Target, Users } from "lucide-react";
import { GlowOrb, Reveal, Stagger } from "../../components/motion";
import { Button, Card, SectionHeading } from "../../components/ui";
import { useReducedMotion } from "framer-motion";
import { api } from "../../services/api";
import { useAsync } from "../../hooks";
import { TAGLINE } from "../../components/Brand";
import "./home.css";

const VALUES = [
  {
    icon: Compass,
    title: "Access first",
    body: "Cost, confidence and not knowing where to start are the three reasons women leave tech tutorials. Every path is free, sequenced, and starts from a working environment.",
  },
  {
    icon: HeartHandshake,
    title: "Mentorship that scales",
    body: "One mentor conversation can replace months of guessing. Requests, availability and sessions live in the product so matches do not depend on who you happen to know.",
  },
  {
    icon: Target,
    title: "Proof over promises",
    body: "Progress comes from completed lessons, passing quizzes and shipped projects — never from a vanity counter. Certificates record what you actually finished.",
  },
  {
    icon: ShieldCheck,
    title: "A safe room to build in",
    body: "Reporting, moderation and role-scoped permissions are part of the platform, not an afterthought. Learners cannot edit mentor data; mentors cannot edit curricula.",
  },
];

const PRINCIPLES = [
  "Beginner-friendly does not mean shallow — every path ends with a deployed, reviewable project.",
  "Struggle is normal and public. Members post the bugs they fixed, not only the wins.",
  "Gamification rewards verified actions only, so a streak means a day you actually learned.",
  "Your data belongs to you: profile fields are private until you choose to publish them.",
];

export default function About() {
  const reduce = useReducedMotion();
  const { data: stats } = useAsync((signal) => api.get("/site/stats/", { signal }).catch(() => null), []);

  return (
    <>
      <section className="hero" style={{ paddingBottom: "var(--sp-6)" }}>
        {!reduce && <GlowOrb size={380} top={-100} left={-60} color="rgba(139,92,246,0.3)" />}
        <div className="container" style={{ display: "grid", gap: "var(--sp-5)", justifyItems: "start" }}>
          <span className="eyebrow">About CodeHer</span>
          <h1 style={{ maxWidth: "18ch" }}>
            We measure our success in <span className="text-gradient">shipped projects</span>.
          </h1>
          <p className="lead" style={{ maxWidth: "68ch" }}>
            CodeHer exists to give girls and women a direct route into software engineering: a
            structured curriculum, a real code editor, a community that reviews your work, and mentors
            who respond. {TAGLINE} is not a slogan on a landing page — it is the reason every feature
            in this product ends in something you built yourself.
          </p>
          <div className="row">
            <Button to="/signup">
              Join the platform <ArrowRight size={16} />
            </Button>
            <Button variant="ghost" to="/learning">
              See the curriculum
            </Button>
          </div>
          {stats && (
            <p className="muted" style={{ fontSize: "var(--fs-xs)" }}>
              Currently {stats.learners} registered members working through {stats.courses} courses and{" "}
              {stats.lessons} lessons, with {stats.projects} published projects.
            </p>
          )}
        </div>
      </section>

      <section className="section container">
        <div className="grid-auto" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(min(320px,100%),1fr))" }}>
          <Reveal>
            <Card className="stack" glow>
              <Sparkles size={22} style={{ color: "var(--violet)" }} />
              <h2 style={{ fontSize: "var(--fs-xl)" }}>Our mission</h2>
              <p>
                Make professional-quality software education reachable for every girl and woman who
                wants it — regardless of school, country, budget or previous experience — and pair it
                with the community and mentorship that turn learning into a career.
              </p>
            </Card>
          </Reveal>
          <Reveal delay={0.1}>
            <Card className="stack">
              <Users size={22} style={{ color: "var(--pink)" }} />
              <h2 style={{ fontSize: "var(--fs-xl)" }}>Our vision</h2>
              <p>
                A generation where being a woman in engineering is unremarkable. We want the default
                story to be: you had a question, you found an answer and a person, you built something,
                and it shipped.
              </p>
            </Card>
          </Reveal>
        </div>
      </section>

      <section className="section container">
        <SectionHeading eyebrow="What we value" title="Four commitments behind every feature" />
        <Stagger className="grid-auto">
          {VALUES.map((value) => (
            <Stagger.Item key={value.title}>
              <Card hover className="stack" style={{ gap: "var(--sp-3)" }}>
                <span className="empty-state__icon" style={{ width: 44, height: 44 }}>
                  <value.icon size={20} aria-hidden="true" />
                </span>
                <h3 style={{ fontSize: "var(--fs-md)" }}>{value.title}</h3>
                <p style={{ fontSize: "var(--fs-sm)" }}>{value.body}</p>
              </Card>
            </Stagger.Item>
          ))}
        </Stagger>
      </section>

      <section className="section container">
        <div className="mentor-band">
          <div className="stack">
            <span className="eyebrow">Principles</span>
            <h2>How we build this platform</h2>
            <p className="lead">
              CodeHer is a real application, not a mockup: React and Vite on the front, Django REST
              Framework and MySQL behind it, and user code executed only in an isolated runner service.
            </p>
          </div>
          <ul className="stack">
            {PRINCIPLES.map((principle) => (
              <li key={principle} className="row" style={{ alignItems: "flex-start", gap: "var(--sp-3)" }}>
                <span aria-hidden="true" style={{ color: "var(--violet)", fontWeight: 800 }}>
                  —
                </span>
                <span style={{ color: "var(--text-secondary)", fontSize: "var(--fs-sm)" }}>{principle}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="section container">
        <Reveal y={26}>
          <div className="final-cta">
            <h2 className="final-cta__title">Start where you are</h2>
            <p className="lead" style={{ maxWidth: "56ch" }}>
              Pick a path, do the first lesson today, and let the streak and your mentor carry you from
              there.
            </p>
            <div className="hero__cta" style={{ justifyContent: "center" }}>
              <Button size="lg" to="/signup">
                Create your account
              </Button>
              <Button size="lg" variant="ghost" to="/community">
                Read member projects
              </Button>
            </div>
          </div>
        </Reveal>
      </section>
    </>
  );
}
