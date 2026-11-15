import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Code2, Globe, Heart, MessageSquare, Network, Plus, SearchX, X } from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync, useDebouncedValue } from "../../hooks";
import { useAuth } from "../../context/AuthContext";
import { Button, Chip, EmptyState, ErrorState, Pagination, SearchInput, SkeletonList, Tabs, UserCell } from "../../components/ui";
import { Stagger } from "../../components/motion";
import {
  PAGE_SIZE,
  ProjectThumb,
  authorOf,
  commentsCount,
  excerpt,
  itemsFrom,
  likesCount,
  topTechnologies,
} from "./communityUtils";
import "./community.css";

const ORDERING_TABS = [
  { value: "trending", label: "Trending" },
  { value: "recent", label: "Newest" },
  { value: "most_liked", label: "Most liked" },
];

function ProjectCard({ project, activeTechnology, onTechnologyClick }) {
  const owner = authorOf(project);
  const technologies = (project.technologies ?? [])
    .map((tech) => (typeof tech === "string" ? tech : tech?.name))
    .filter(Boolean);

  return (
    <article className="card comm-card project-card">
      <ProjectThumb project={project} />
      <h2 className="project-card__title">
        <Link className="stretched" to={`/community/projects/${project.id}`}>
          {project.title || "Untitled project"}
        </Link>
      </h2>
      <p className="project-card__desc muted">{excerpt(project.description, 140)}</p>

      {technologies.length > 0 && (
        <div className="comm-card__actions" style={{ display: "flex", gap: "var(--sp-2)", flexWrap: "wrap" }}>
          {technologies.slice(0, 4).map((tech) => (
            <Chip key={tech} selected={activeTechnology === tech} onClick={() => onTechnologyClick(tech)}>
              {tech}
            </Chip>
          ))}
        </div>
      )}

      <footer className="comm-card__actions row project-card__foot">
        <UserCell user={owner} to={owner?.id != null ? `/members/${owner.id}` : undefined} />
        <span className="project-card__stats">
          <span title={`${likesCount(project)} likes`}>
            <Heart size={14} aria-hidden="true" /> {likesCount(project)}
          </span>
          <span title={`${commentsCount(project)} comments`}>
            <MessageSquare size={14} aria-hidden="true" /> {commentsCount(project)}
          </span>
        </span>
        {project.repo_url && (
          <Button variant="ghost" size="sm" href={project.repo_url} aria-label={`${project.title} source code (opens in a new tab)`}>
            <Code2 size={14} aria-hidden="true" /> Code
          </Button>
        )}
        {project.live_url && (
          <Button variant="ghost" size="sm" href={project.live_url} aria-label={`${project.title} live site (opens in a new tab)`}>
            <Globe size={14} aria-hidden="true" /> Live
          </Button>
        )}
      </footer>
    </article>
  );
}

export default function Projects() {
  const [params, setParams] = useSearchParams();
  const { isAuthenticated } = useAuth();

  const technology = params.get("technology") ?? "";
  const search = params.get("search") ?? "";
  const ordering = params.get("ordering") ?? "trending";
  const page = Number(params.get("page")) || 1;

  const [searchText, setSearchText] = useState(search);
  const debouncedSearch = useDebouncedValue(searchText);

  const updateParams = useCallback(
    (changes) => {
      setParams((current) => {
        const next = new URLSearchParams(current);
        for (const [key, value] of Object.entries(changes)) {
          if (value === null || value === undefined || value === "") next.delete(key);
          else next.set(key, String(value));
        }
        if (!("page" in changes)) next.delete("page");
        return next;
      }, { replace: true });
    },
    [setParams]
  );

  useEffect(() => {
    if (debouncedSearch !== search) updateParams({ search: debouncedSearch });
  }, [debouncedSearch, search, updateParams]);

  const { data, loading, error, reload } = useAsync(
    (signal) =>
      api.get(endpoints.projects, {
        signal,
        params: {
          technology: technology || undefined,
          search: search || undefined,
          ordering: ordering !== "trending" ? ordering : "trending",
          page,
          page_size: PAGE_SIZE,
        },
      }),
    [technology, search, ordering, page]
  );

  const projects = itemsFrom(data);
  const count = data?.count ?? projects.length;
  const technologyOptions = useMemo(() => topTechnologies(projects), [projects]);
  const hasFilters = Boolean(technology || search);

  const clearFilters = () => {
    setSearchText("");
    updateParams({ technology: "", search: "" });
  };

  const handleTechnologyClick = (value) => updateParams({ technology: technology === value ? "" : value });

  let gallery;
  if (error && !projects.length) {
    gallery = <ErrorState error={error} onRetry={reload} title="We could not load the gallery" />;
  } else if (loading && !projects.length) {
    gallery = <SkeletonList count={6} height={280} />;
  } else if (!projects.length) {
    gallery = hasFilters ? (
      <EmptyState
        icon={SearchX}
        title="No projects match your filters"
        description="Try another technology or a broader search — the gallery only shows what members really published."
        action={
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            Clear filters
          </Button>
        }
      />
    ) : (
      <EmptyState
        icon={Network}
        title="Nobody has published a project yet"
        description="The project table is empty — CodeHer will not show fake showcases. Publish the first real one from your own work."
        action={
          isAuthenticated ? (
            <Button variant="ghost" to="/projects/new">
              <Plus size={15} /> Publish a project
            </Button>
          ) : (
            <Button variant="ghost" to="/signin">
              Sign in to publish
            </Button>
          )
        }
      />
    );
  } else {
    gallery = (
      <Stagger className="grid-auto">
        {projects.map((project) => (
          <Stagger.Item key={project.id}>
            <ProjectCard project={project} activeTechnology={technology} onTechnologyClick={handleTechnologyClick} />
          </Stagger.Item>
        ))}
      </Stagger>
    );
  }

  return (
    <>
      <header className="container comm-page__header">
        <div className="comm-header-row">
          <div className="stack" style={{ gap: "var(--sp-3)" }}>
            <span className="eyebrow">Project showcase</span>
            <h1>Real builds by CodeHer members</h1>
            <p className="lead">
              Trending is computed from genuine engagement — likes, double-weighted comments and
              bookmarks, decayed by age. Nothing here is simulated.
            </p>
          </div>
          {isAuthenticated ? (
            <Button to="/projects/new">
              <Plus size={16} /> Publish a project
            </Button>
          ) : (
            <Button variant="outline" to="/signin">
              <Plus size={16} /> Sign in to publish
            </Button>
          )}
        </div>
      </header>

      <section className="container" style={{ paddingBottom: "var(--sp-9)" }} aria-label="Project gallery">
        <div className="comm-toolbar">
          <Tabs
            items={ORDERING_TABS}
            value={ordering}
            onChange={(value) => updateParams({ ordering: value === "trending" ? "" : value })}
            ariaLabel="Sort projects"
          />
          <div className="comm-toolbar__controls">
            <SearchInput label="Search projects" value={searchText} onChange={setSearchText} placeholder="Search projects…" />
          </div>
        </div>

        {(technology || technologyOptions.length > 0) && (
          <div className="comm-filter-chips" role="group" aria-label="Filter by technology">
            {technology ? (
              <Button variant="link" size="sm" onClick={() => updateParams({ technology: "" })}>
                <X size={14} aria-hidden="true" /> Clear “{technology}”
              </Button>
            ) : (
              <span className="muted" style={{ fontSize: "var(--fs-xs)", fontWeight: 700 }}>
                Technologies in view:
              </span>
            )}
            {technologyOptions
              .filter((option) => option !== technology)
              .slice(0, 10)
              .map((option) => (
                <Chip key={option} onClick={() => handleTechnologyClick(option)}>
                  {option}
                </Chip>
              ))}
          </div>
        )}

        <div aria-live="polite" aria-busy={loading}>
          {gallery}
        </div>

        {projects.length > 0 && (
          <Pagination
            count={count}
            page={page}
            pageSize={PAGE_SIZE}
            onPageChange={(next) => {
              updateParams({ page: next > 1 ? next : "" });
              window.scrollTo({ top: 0, behavior: "auto" });
            }}
          />
        )}
      </section>
    </>
  );
}
