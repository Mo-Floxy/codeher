import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  BadgeCheck,
  Flame,
  FolderGit2,
  Sparkles,
  Trophy,
  UserPlus,
  UserX,
  Users,
} from "lucide-react";
import { api } from "../../services/api";
import { useAsync } from "../../hooks";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import {
  Avatar,
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  LevelBadge,
  Skeleton,
  Stat,
} from "../../components/ui";
import { asList, formatDate, num } from "./helpers";
import "./app.css";

export default function MemberProfile() {
  const { id } = useParams();
  const { user, isAuthenticated } = useAuth();
  const toast = useToast();

  const profileQuery = useAsync((signal) => api.get(`/users/${id}/`, { signal }), [id]);
  const badgesQuery = useAsync((signal) => api.get(`/users/${id}/badges/`, { signal }), [id]);

  const profile = profileQuery.data;

  const isSelf = isAuthenticated && String(id) === String(user?.id);

  const [following, setFollowing] = useState(null);
  const [followers, setFollowers] = useState(null);
  const [busy, setBusy] = useState(false);

  // Seed from the response once, then let the toggle own the value.
  const seededFollowing = following ?? Boolean(profile?.following);
  const seededFollowers = followers ?? num(profile?.followers_count);
  const seededFollowingCount = num(profile?.following_count);

  const displayName = useMemo(() => {
    if (!profile) return "Member";
    return profile.display_name ?? profile.user?.display_name ?? profile.username ?? profile.user?.username ?? "Member";
  }, [profile]);

  const avatarUser = { display_name: displayName, avatar: profile?.avatar ?? profile?.user?.avatar };
  const badges = asList(badgesQuery.data);
  const projects = asList(profile?.projects);

  const toggleFollow = async () => {
    setBusy(true);
    try {
      const result = await api.post(`/users/${id}/follow/`);
      setFollowing(Boolean(result?.following));
      if (result?.followers_count != null) setFollowers(num(result.followers_count));
      toast.success(result?.following ? `Now following ${displayName}.` : `Unfollowed ${displayName}.`);
    } catch (err) {
      toast.error(err?.detail || "Could not update your follow.");
    } finally {
      setBusy(false);
    }
  };

  if (profileQuery.loading) {
    return (
      <section className="container section">
        <div className="app-page" aria-busy="true">
          <Skeleton style={{ height: 160 }} />
          <Skeleton style={{ height: 220 }} />
        </div>
      </section>
    );
  }

  if (profileQuery.error) {
    const isMissing = profileQuery.error.status === 404;
    return (
      <section className="container section">
        {isMissing ? (
          <EmptyState
            icon={Users}
            title="Member not found"
            description="We couldn't find a public profile with that identifier. They may have removed their account or set it to private."
            action={<Button to="/">Back to home</Button>}
          />
        ) : (
          <ErrorState error={profileQuery.error} onRetry={profileQuery.reload} title="Could not load this profile" />
        )}
      </section>
    );
  }

  return (
    <section className="container section app-page">
      <Card className="stack" style={{ gap: "var(--sp-5)" }}>
        <div className="member-hero">
          <Avatar user={avatarUser} size="xl" />
          <div style={{ minWidth: 0 }}>
            <h1 style={{ fontSize: "var(--fs-xl)" }}>{displayName}</h1>
            {profile?.headline ? <p className="muted">{profile.headline}</p> : null}
            <div className="row" style={{ gap: "var(--sp-2)", marginTop: "var(--sp-2)" }}>
              <Badge variant="brand">
                <Trophy size={12} aria-hidden="true" /> Level {num(profile?.level)}
              </Badge>
              <Badge variant="neutral">{num(profile?.total_xp).toLocaleString()} XP</Badge>
              <Badge variant="warning">
                <Flame size={12} aria-hidden="true" /> {num(profile?.current_streak)}-day streak
              </Badge>
              {profile?.skill_level ? <LevelBadge level={profile.skill_level} /> : null}
            </div>
          </div>
          {!isSelf ? (
            <Button variant={seededFollowing ? "outline" : "primary"} onClick={toggleFollow} loading={busy}>
              {seededFollowing ? <><UserX size={16} aria-hidden="true" /> Unfollow</> : <><UserPlus size={16} aria-hidden="true" /> Follow</>}
            </Button>
          ) : (
            <Button variant="ghost" to="/profile">
              <Sparkles size={16} aria-hidden="true" /> Edit profile
            </Button>
          )}
        </div>

        <div className="member-stats" role="group" aria-label="Profile summary">
          <span className="member-stats__item">
            <span className="member-stats__value">{num(profile?.current_streak)}</span>
            <span className="member-stats__label">Day streak</span>
          </span>
          <span className="member-stats__item">
            <span className="member-stats__value">{num(profile?.longest_streak)}</span>
            <span className="member-stats__label">Longest streak</span>
          </span>
          <span className="member-stats__item">
            <span className="member-stats__value">{seededFollowers.toLocaleString()}</span>
            <span className="member-stats__label">Followers</span>
          </span>
          <span className="member-stats__item">
            <span className="member-stats__value">{seededFollowingCount.toLocaleString()}</span>
            <span className="member-stats__label">Following</span>
          </span>
          {profile?.joined_at ? (
            <span className="member-stats__item">
              <span className="member-stats__value" style={{ fontSize: "var(--fs-base)" }}>{formatDate(profile.joined_at)}</span>
              <span className="member-stats__label">Joined</span>
            </span>
          ) : null}
        </div>

        {profile?.bio ? <p style={{ maxWidth: "70ch" }}>{profile.bio}</p> : null}

        {asList(profile?.interests).length > 0 ? (
          <div>
            <h2 className="card__title" style={{ marginBottom: "var(--sp-2)" }}>Interests</h2>
            <div className="row" style={{ gap: 6 }}>
              {asList(profile.interests).map((tag) => (
                <Badge key={tag} variant="neutral">{tag}</Badge>
              ))}
            </div>
          </div>
        ) : null}
      </Card>

      <div className="stat-grid">
        <Stat label="Badges earned" value={badgesQuery.loading ? "…" : badges.length} icon={BadgeCheck} tone="brand" />
        <Stat label="Public projects" value={profile?.show_projects === false ? "Hidden" : projects.length} icon={FolderGit2} tone="cyan" />
        <Stat label="Learning XP" value={num(profile?.total_xp).toLocaleString()} icon={Trophy} tone="success" />
      </div>

      <section aria-label="Earned badges">
        <h2 style={{ fontSize: "var(--fs-lg)", marginBottom: "var(--sp-4)" }}>Badges</h2>
        {badgesQuery.loading ? (
          <Skeleton style={{ height: 120 }} />
        ) : badges.length === 0 ? (
          <EmptyState icon={BadgeCheck} title="No public badges" description="This member hasn't earned badges yet, or has chosen to keep them private." />
        ) : (
          <div className="badge-grid">
            {badges.map((badge, index) => (
              <div className="badge-tile" key={badge.badge ?? badge.id ?? index}>
                <span className="badge-tile__icon">
                  <Trophy size={20} aria-hidden="true" />
                </span>
                <span className="badge-tile__title">{badge.title || badge.badge || "Badge"}</span>
                <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>
                  {badge.earned_at ? `Earned ${formatDate(badge.earned_at)}` : "Earned"}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      <section aria-label="Published projects">
        <h2 style={{ fontSize: "var(--fs-lg)", marginBottom: "var(--sp-4)" }}>Projects</h2>
        {projects.length === 0 ? (
          <EmptyState icon={FolderGit2} title="No public projects" description="Published projects appear here when the member shares them and keeps them visible." />
        ) : (
          <div className="grid-auto">
            {projects.map((project, index) => (
              <Card key={project.id ?? index} hover to={`/community/projects/${project.id}`} as="article">
                <h3 style={{ fontSize: "var(--fs-md)" }}>{project.title}</h3>
                <p style={{ fontSize: "var(--fs-sm)" }}>{project.description}</p>
                <div className="row" style={{ gap: 6, marginTop: "var(--sp-3)" }}>
                  {asList(project.technologies).slice(0, 3).map((tech) => (
                    <Badge key={tech} variant="neutral">{tech}</Badge>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      {!isSelf ? (
        <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
          Following is stored on your account. <Link to="/community">Explore the community</Link>.
        </p>
      ) : null}
    </section>
  );
}
