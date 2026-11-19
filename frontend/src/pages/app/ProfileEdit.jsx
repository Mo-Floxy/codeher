import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AtSign,
  Eye,
  Globe,
  Lock,
  LogIn,
  Mail,
  Rocket,
  Save,
  Sparkles,
  Upload,
  UserCircle2,
} from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync } from "../../hooks";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import {
  Avatar,
  Badge,
  Button,
  Card,
  ErrorState,
  Field,
  Input,
  Select,
  Skeleton,
  Switch,
  TagInput,
  Textarea,
} from "../../components/ui";
import { asList, formatDate, num } from "./helpers";
import "./app.css";

const SKILL_LEVELS = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

const EMPTY_FORM = {
  display_name: "",
  avatar: "",
  headline: "",
  bio: "",
  interests: [],
  skill_level: "beginner",
  learning_technologies: [],
  is_profile_public: true,
  show_email: false,
  show_projects: true,
  show_badges: true,
};

function buildForm(profile, user) {
  return {
    display_name: user?.display_name ?? "",
    avatar: profile?.avatar ?? "",
    headline: profile?.headline ?? "",
    bio: profile?.bio ?? "",
    interests: profile?.interests ?? [],
    skill_level: profile?.skill_level ?? "beginner",
    learning_technologies: profile?.learning_technologies ?? [],
    is_profile_public: Boolean(profile?.is_profile_public ?? true),
    show_email: Boolean(profile?.show_email),
    show_projects: Boolean(profile?.show_projects ?? true),
    show_badges: Boolean(profile?.show_badges ?? true),
  };
}

export default function ProfileEdit() {
  const { user, updateProfile, updateUser } = useAuth();
  const toast = useToast();
  const { data: profile, loading, error, reload } = useAsync((signal) => api.get(endpoints.myProfile, { signal }), []);
  const userId = user?.id;
  // The profile payload only carries scalar counters, so the badge tiles and the
  // published-project total come from the same endpoints a profile page uses.
  const { data: badgePayload } = useAsync(
    (signal) => api.get(`/users/${userId}/badges/`, { signal }),
    [userId],
    { skip: !userId },
  );
  const { data: projectPayload } = useAsync(
    (signal) => api.get(endpoints.projects, { params: { user: userId, status: "published", page_size: 1 }, signal }),
    [userId],
    { skip: !userId },
  );

  const [form, setForm] = useState(EMPTY_FORM);
  const [initial, setInitial] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (profile) {
      const next = buildForm(profile, user);
      setForm(next);
      setInitial(next);
    }
  }, [profile, user]);

  const dirty = useMemo(() => JSON.stringify(form) !== JSON.stringify(initial), [form, initial]);

  const set = (key) => (value) => setForm((current) => ({ ...current, [key]: value }));
  const setInput = (key) => (event) => set(key)(event.target.value);

  const onAvatarFile = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const result = await api.upload("/uploads/", formData);
      const url = result?.url ?? "";
      if (url) {
        set("avatar")(url);
        toast.success("Avatar uploaded — remember to save.");
      } else {
        toast.error("Upload did not return a URL.");
      }
    } catch (err) {
      // Upload refusals are reported under `file`; `detail` is empty, so the generic
      // message would hide why the image was rejected.
      toast.error(err?.messageFor?.("file") || "Could not upload that image.");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  const save = async (event) => {
    event.preventDefault();
    if (!dirty) return;
    setSaving(true);
    setErrors({});
    try {
      if (form.display_name !== (user?.display_name ?? "")) {
        const nextUser = await api.patch(endpoints.me, { display_name: form.display_name });
        updateUser(nextUser);
      }
      const payload = {
        avatar: form.avatar,
        headline: form.headline,
        bio: form.bio,
        interests: form.interests,
        skill_level: form.skill_level,
        learning_technologies: form.learning_technologies,
        is_profile_public: form.is_profile_public,
        show_email: form.show_email,
        show_projects: form.show_projects,
        show_badges: form.show_badges,
      };
      const updated = await api.patch(endpoints.myProfile, payload);
      updateProfile(updated);
      const next = buildForm(updated ?? profile, updated?.user ?? user);
      setForm(next);
      setInitial(next);
      toast.success("Profile saved.");
    } catch (err) {
      setErrors(err?.fieldErrors ?? {});
      toast.error(err?.messageFor?.("__default__") || err?.detail || "Could not save your profile.");
    } finally {
      setSaving(false);
    }
  };

  // `/users/:id/badges/` answers `{badges, count, hidden}` and the project feed answers
  // `{results, count}`; reading either as a bare array renders nothing at all.
  const earnedBadges = asList(badgePayload?.badges ?? badgePayload);
  const completedCourses = num(profile?.completed_course_count);
  const publishedProjects = num(projectPayload?.count ?? projectPayload?.results?.length);

  return (
    <div className="app-page">
      <header className="app-page__head">
        <h1 className="app-page__title">Profile settings</h1>
        <p className="app-page__sub">
          This is how other members see you.{" "}
          {user?.id ? <Link to={`/members/${user.id}`}>View your public profile</Link> : null}
        </p>
      </header>

      {loading ? <Skeleton style={{ height: 300 }} /> : null}
      {!loading && error ? <ErrorState error={error} onRetry={reload} title="Could not load your profile" /> : null}

      {!loading && profile ? (
        <form className="profile-grid" onSubmit={save} noValidate>
          <div className="dash-stack">
            <Card className="stack" style={{ gap: "var(--sp-4)" }}>
              <h2 className="card__title">Profile picture</h2>
              <div className="avatar-drop">
                <Avatar user={{ display_name: form.display_name, avatar: form.avatar }} size="xl" />
                <div className="stack" style={{ gap: "var(--sp-2)" }}>
                  <label className="btn btn--outline btn--sm" htmlFor="avatar-upload" style={{ cursor: "pointer" }}>
                    <Upload size={15} aria-hidden="true" /> {uploading ? "Uploading…" : "Upload image"}
                  </label>
                  <input id="avatar-upload" type="file" accept="image/*" className="sr-only" onChange={onAvatarFile} disabled={uploading} />
                  <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>PNG or JPG. Stored via the media upload endpoint.</span>
                </div>
              </div>
            </Card>

            <Card className="stack" style={{ gap: "var(--sp-4)" }}>
              <h2 className="card__title">Basics</h2>
              <Field label="Display name" htmlFor="pf-name" error={errors.display_name?.[0]}>
                <Input id="pf-name" value={form.display_name} onChange={setInput("display_name")} maxLength={80} error={errors.display_name?.[0]} placeholder="Your name" />
              </Field>
              <Field label="Headline" htmlFor="pf-headline" error={errors.headline?.[0]} hint="One line about you, e.g. 'Frontend dev learning React'">
                <Input id="pf-headline" value={form.headline} onChange={setInput("headline")} maxLength={120} error={errors.headline?.[0]} placeholder="Frontend developer in training" />
              </Field>
              <Field label="Bio" htmlFor="pf-bio" error={errors.bio?.[0]}>
                <Textarea id="pf-bio" value={form.bio} onChange={setInput("bio")} rows={5} maxLength={600} error={errors.bio?.[0]} placeholder="Tell members about your goals." />
              </Field>
            </Card>

            <Card className="stack" style={{ gap: "var(--sp-4)" }}>
              <h2 className="card__title">Interests &amp; goals</h2>
              <Field error={errors.interests?.[0]}>
                <TagInput label="Interests" value={form.interests} onChange={set("interests")} placeholder="Add an interest and press Enter" />
              </Field>
              <Field label="Skill level" htmlFor="pf-skill" error={errors.skill_level?.[0]}>
                <Select id="pf-skill" options={SKILL_LEVELS} value={form.skill_level} onChange={setInput("skill_level")} error={errors.skill_level?.[0]} />
              </Field>
              <Field error={errors.learning_technologies?.[0]}>
                <TagInput label="Technologies you're learning" value={form.learning_technologies} onChange={set("learning_technologies")} placeholder="React, Python, SQL…" />
              </Field>
            </Card>

            <Card className="stack" style={{ gap: "var(--sp-4)" }}>
              <h2 className="card__title">Profile visibility</h2>
              <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
                Controls exactly what other members can see on your public profile. Private fields are omitted from the API response entirely.
              </p>
              <div className="visibility-group">
                <span className="visibility-group__title">
                  <Globe size={15} aria-hidden="true" /> Who can see your profile
                </span>
                <Switch checked={form.is_profile_public} onChange={set("is_profile_public")} label="Make my profile publicly visible" id="vis-public" />
                <Switch checked={form.show_email} onChange={set("show_email")} label="Show my email address" id="vis-email" />
                <Switch checked={form.show_projects} onChange={set("show_projects")} label="Show my published projects" id="vis-projects" />
                <Switch checked={form.show_badges} onChange={set("show_badges")} label="Show my earned badges" id="vis-badges" />
              </div>
            </Card>

            <div className="form-footbar">
              <span className="muted" style={{ fontSize: "var(--fs-sm)", marginRight: "auto" }} aria-live="polite">
                {dirty ? "You have unsaved changes." : "All changes saved."}
              </span>
              <Button type="submit" loading={saving} disabled={!dirty || saving}>
                <Save size={16} aria-hidden="true" /> Save changes
              </Button>
            </div>
          </div>

          <aside className="profile-aside">
            <PublicProfilePreview form={form} />
            <AccountFacts user={user} profile={profile} />
            <AchievementSummary badges={earnedBadges} courseCount={completedCourses} projectCount={publishedProjects} />
          </aside>
        </form>
      ) : null}
    </div>
  );
}

function PublicProfilePreview({ form }) {
  const visible = form.is_profile_public;
  return (
    <Card className="stack" style={{ gap: "var(--sp-4)" }}>
      <span className="row" style={{ gap: "var(--sp-2)" }}>
        <Eye size={16} style={{ color: "var(--violet)" }} aria-hidden="true" />
        <h2 className="card__title">Public preview</h2>
      </span>
      <div className="stack" style={{ gap: "var(--sp-3)" }}>
        <div className="member-hero" style={{ gridTemplateColumns: "auto 1fr", gap: "var(--sp-3)" }}>
          <Avatar user={{ display_name: form.display_name, avatar: form.avatar }} size="lg" />
          <div style={{ minWidth: 0 }}>
            <strong style={{ fontSize: "var(--fs-md)", display: "block", overflow: "hidden", textOverflow: "ellipsis" }}>
              {form.display_name || "Your name"}
            </strong>
            <span className="muted" style={{ fontSize: "var(--fs-sm)" }}>{form.headline || "Add a headline"}</span>
          </div>
        </div>
        <p style={{ fontSize: "var(--fs-sm)" }}>{form.bio || "Your bio will appear here."}</p>
        {form.interests.length > 0 ? (
          <div className="row" style={{ gap: 6 }}>
            {form.interests.map((tag) => (
              <Badge key={tag} variant="neutral">{tag}</Badge>
            ))}
          </div>
        ) : null}
        <Badge variant={visible ? "success" : "warning"}>
          {visible ? <><Globe size={12} aria-hidden="true" /> Public</> : <><Lock size={12} aria-hidden="true" /> Hidden</>}
        </Badge>
      </div>
    </Card>
  );
}

function AccountFacts({ user, profile }) {
  const facts = [
    { icon: Mail, label: "Email", value: user?.email },
    { icon: UserCircle2, label: "Role", value: user?.role },
    { icon: LogIn, label: "Joined", value: formatDate(user?.date_joined ?? profile?.joined_at) },
    { icon: Sparkles, label: "Total XP", value: num(profile?.total_xp).toLocaleString() },
    { icon: AtSign, label: "Username", value: user?.username },
  ];
  return (
    <Card className="stack" style={{ gap: "var(--sp-3)" }}>
      <h2 className="card__title">Account</h2>
      {facts.map((fact) => (
        <div key={fact.label} className="row" style={{ justifyContent: "space-between" }}>
          <span className="muted" style={{ fontSize: "var(--fs-sm)", display: "flex", alignItems: "center", gap: 6 }}>
            <fact.icon size={14} aria-hidden="true" /> {fact.label}
          </span>
          <span style={{ fontSize: "var(--fs-sm)", fontWeight: 700, textTransform: fact.label === "Role" ? "capitalize" : "none" }}>
            {fact.value || "—"}
          </span>
        </div>
      ))}
    </Card>
  );
}

function AchievementSummary({ badges, courseCount, projectCount }) {
  return (
    <Card className="stack" style={{ gap: "var(--sp-3)" }}>
      <h2 className="card__title">Your record</h2>
      <div className="stack" style={{ gap: "var(--sp-2)" }}>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span className="muted" style={{ fontSize: "var(--fs-sm)" }}>Earned badges</span>
          <span style={{ fontWeight: 800 }}>{badges.length}</span>
        </div>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span className="muted" style={{ fontSize: "var(--fs-sm)" }}>Completed courses</span>
          <span style={{ fontWeight: 800 }}>{courseCount}</span>
        </div>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span className="muted" style={{ fontSize: "var(--fs-sm)" }}>Published projects</span>
          <span style={{ fontWeight: 800 }}>{projectCount}</span>
        </div>
      </div>
      {badges.length > 0 ? (
        <div className="row" style={{ gap: 6 }}>
          {badges.slice(0, 6).map((badge, index) => (
            <Badge key={badge.badge ?? index} variant="brand">{badge.title || badge.badge || "Badge"}</Badge>
          ))}
        </div>
      ) : (
        <p className="muted" style={{ fontSize: "var(--fs-xs)" }}>
          No badges, courses or projects on your profile yet — these numbers come straight from your saved profile data.
        </p>
      )}
      <Button variant="link" to="/achievements">
        <Rocket size={15} aria-hidden="true" /> Browse badge catalogue
      </Button>
    </Card>
  );
}
