import { useCallback, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Bookmark, Code2, Flag, Globe, Heart, MessageSquare, Pencil, Trash2 } from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync } from "../../hooks";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import {
  Button,
  Chip,
  ChipRow,
  ConfirmDialog,
  ErrorState,
  Skeleton,
  SkeletonText,
  UserCell,
} from "../../components/ui";
import {
  ProjectThumb,
  ReportModal,
  authorOf,
  bookmarksCount,
  commentsCount,
  errorText,
  excerpt,
  isBookmarked,
  isLiked,
  itemsFrom,
  likesCount,
  timeAgo,
  useEngagement,
} from "./communityUtils";
import "./community.css";

function RelatedCard({ project }) {
  const owner = authorOf(project);
  return (
    <article className="card comm-card project-card">
      <ProjectThumb project={project} />
      <h3 className="project-card__title" style={{ fontSize: "var(--fs-base)" }}>
        <Link className="stretched" to={`/community/projects/${project.id}`}>
          {project.title || "Untitled project"}
        </Link>
      </h3>
      <p className="project-card__desc muted">{excerpt(project.description, 90)}</p>
      <footer className="comm-card__actions row">
        <UserCell user={owner} to={owner?.id != null ? `/members/${owner.id}` : undefined} />
        <span className="project-card__stats">
          <Heart size={13} aria-hidden="true" /> {likesCount(project)}
        </span>
      </footer>
    </article>
  );
}

export default function ProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, user, isAdmin } = useAuth();
  const toast = useToast();

  const { data: project, setData, loading, error, reload } = useAsync(
    (signal) => api.get(`/community/projects/${id}/`, { signal }),
    [id]
  );

  const [reportOpen, setReportOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const mutateProject = useCallback(
    (itemId, updater) =>
      setData((current) => (current && String(current.id) === String(itemId) ? updater(current) : current)),
    [setData]
  );
  const engagement = useEngagement({ mutate: mutateProject, toast, scope: "projects" });

  const technologies = useMemo(
    () => (project?.technologies ?? []).map((tech) => (typeof tech === "string" ? tech : tech?.name)).filter(Boolean),
    [project?.technologies]
  );
  const primaryTechnology = technologies[0] ?? "";

  const relatedState = useAsync(
    (signal) =>
      api.get(endpoints.projects, { signal, params: { technology: primaryTechnology, ordering: "most_liked", page_size: 5 } }),
    [primaryTechnology],
    { skip: !primaryTechnology }
  );
  const related = itemsFrom(relatedState.data).filter((item) => String(item.id) !== String(id)).slice(0, 4);

  const owner = authorOf(project);
  const canManage = Boolean(project) && isAuthenticated && (isAdmin || (owner?.id != null && owner.id === user?.id));

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await api.del(`/community/projects/${id}/`);
      toast.success("Project deleted.");
      navigate("/community/projects");
    } catch (err) {
      toast.error(errorText(err));
      setDeleting(false);
      setConfirmOpen(false);
    }
  };

  if (error) {
    return (
      <section className="container section">
        <ErrorState error={error} onRetry={reload} title="We could not load this project" />
      </section>
    );
  }

  if (loading && !project) {
    return (
      <section className="container section" aria-busy="true" aria-live="polite">
        <div className="card stack">
          <Skeleton style={{ height: 220 }} />
          <Skeleton className="skeleton--title" />
          <SkeletonText lines={4} />
        </div>
      </section>
    );
  }

  if (!project) {
    return (
      <section className="container section">
        <div className="empty-state">
          <h4>Project not found</h4>
          <p>It may have been deleted by its owner or a moderator.</p>
          <Button variant="ghost" to="/community/projects">
            Back to the gallery
          </Button>
        </div>
      </section>
    );
  }

  return (
    <section className="container" style={{ paddingBlock: "var(--sp-6) var(--sp-9)" }}>
      <nav aria-label="Breadcrumb" style={{ marginBottom: "var(--sp-4)" }}>
        <Button variant="link" size="sm" to="/community/projects">
          <ArrowLeft size={15} aria-hidden="true" /> Back to projects
        </Button>
      </nav>

      <div className="project-layout">
        <article className="post-main">
          <div className="card project-hero">
            <ProjectThumb project={project} />

            <h1 className="project-hero__title">{project.title || "Untitled project"}</h1>

            <div className="post-meta">
              <UserCell user={owner} to={owner?.id != null ? `/members/${owner.id}` : undefined} />
              {project.created_at && <span className="muted">· published {timeAgo(project.created_at)}</span>}
            </div>

            {technologies.length > 0 && (
              <ChipRow>
                {technologies.map((tech) => (
                  <Chip key={tech}>
                    <Link to={`/community/projects?technology=${encodeURIComponent(tech)}`}>{tech}</Link>
                  </Chip>
                ))}
              </ChipRow>
            )}

            <div className="project-hero__actions">
              {isAuthenticated ? (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    className={`comm-toggle comm-toggle--like ${isLiked(project) ? "comm-toggle--on" : ""}`.trim()}
                    onClick={() => engagement.run(project, "like")}
                    disabled={engagement.isPending(project.id, "like")}
                    aria-pressed={isLiked(project)}
                    aria-label={isLiked(project) ? "Unlike this project" : "Like this project"}
                  >
                    <Heart size={15} aria-hidden="true" /> {likesCount(project)}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className={`comm-toggle comm-toggle--bookmark ${isBookmarked(project) ? "comm-toggle--on" : ""}`.trim()}
                    onClick={() => engagement.run(project, "bookmark")}
                    disabled={engagement.isPending(project.id, "bookmark")}
                    aria-pressed={isBookmarked(project)}
                    aria-label={isBookmarked(project) ? "Remove bookmark" : "Bookmark this project"}
                  >
                    <Bookmark size={15} aria-hidden="true" /> {isBookmarked(project) ? "Saved" : "Save"}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setReportOpen(true)}>
                    <Flag size={15} aria-hidden="true" /> Report
                  </Button>
                </>
              ) : (
                <Button variant="outline" size="sm" to="/signin">
                  <Heart size={15} aria-hidden="true" /> Sign in to like or save
                </Button>
              )}
              {canManage && (
                <>
                  <Button variant="ghost" size="sm" to={`/projects/${project.id}/edit`}>
                    <Pencil size={15} aria-hidden="true" /> Edit
                  </Button>
                  <Button variant="danger" size="sm" onClick={() => setConfirmOpen(true)}>
                    <Trash2 size={15} aria-hidden="true" /> Delete
                  </Button>
                </>
              )}
            </div>
          </div>

          <div className="card stack">
            <h2 style={{ fontSize: "var(--fs-md)" }}>About this project</h2>
            <div className="post-body">{project.description || "The author has not written a description yet."}</div>
          </div>

          {primaryTechnology && (
            <section aria-label={`More projects using ${primaryTechnology}`} aria-live="polite">
              <h2 style={{ fontSize: "var(--fs-md)", margin: "var(--sp-3) 0" }}>More with {primaryTechnology}</h2>
              {related.length > 0 ? (
                <div className="related-grid">
                  {related.map((item) => (
                    <RelatedCard key={item.id} project={item} />
                  ))}
                </div>
              ) : (
                <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
                  No other {primaryTechnology} projects are published yet.
                </p>
              )}
            </section>
          )}
        </article>

        <aside className="stack side-card" aria-label="Project links and stats">
          <div className="card stack">
            <h2 style={{ fontSize: "var(--fs-base)" }}>Links</h2>
            {project.repo_url ? (
              <Button variant="outline" size="sm" href={project.repo_url} block aria-label="Open source code in a new tab">
                <Code2 size={15} aria-hidden="true" /> Source code
              </Button>
            ) : (
              <span className="muted" style={{ fontSize: "var(--fs-sm)" }}>No repository link shared.</span>
            )}
            {project.live_url ? (
              <Button variant="outline" size="sm" href={project.live_url} block aria-label="Open live demo in a new tab">
                <Globe size={15} aria-hidden="true" /> Live demo
              </Button>
            ) : (
              <span className="muted" style={{ fontSize: "var(--fs-sm)" }}>No live demo link shared.</span>
            )}
          </div>

          <div className="card stack">
            <h2 style={{ fontSize: "var(--fs-base)" }}>Engagement</h2>
            <div className="post-meta">
              <span>
                <Heart size={14} aria-hidden="true" /> {likesCount(project)} likes
              </span>
              <span>
                <MessageSquare size={14} aria-hidden="true" /> {commentsCount(project)} comments
              </span>
              {bookmarksCount(project) > 0 && (
                <span>
                  <Bookmark size={14} aria-hidden="true" /> {bookmarksCount(project)} saves
                </span>
              )}
            </div>
          </div>
        </aside>
      </div>

      <ReportModal
        open={reportOpen}
        onClose={() => setReportOpen(false)}
        scope="projects"
        target={project}
        toast={toast}
      />

      <ConfirmDialog
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={handleDelete}
        busy={deleting}
        title="Delete this project?"
        message="The gallery entry, its likes and links will be removed for everyone. This cannot be undone."
        confirmLabel="Delete project"
      />
    </section>
  );
}
