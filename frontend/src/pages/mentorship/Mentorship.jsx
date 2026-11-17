import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Clock, Sparkles, Users, X } from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync, useDebouncedValue } from "../../hooks";
import { useAuth } from "../../context/AuthContext";
import {
  Avatar,
  Button,
  Chip,
  ChipRow,
  EmptyState,
  ErrorState,
  SearchInput,
  SkeletonList,
} from "../../components/ui";
import { Stagger } from "../../components/motion";
import { excerpt, itemsFrom, mentorAvatarUser, mentorName, topExpertise } from "./mentorshipUtils";
import "./mentorship.css";

function MentorCard({ mentor }) {
  const expertise = (mentor.expertise ?? [])
    .map((value) => (typeof value === "string" ? value : value?.name))
    .filter(Boolean);
  const availability = mentor.availability_note ?? mentor.availability ?? "";
  const headline = mentor.headline ?? mentor.user?.headline ?? "";
  const bio = mentor.bio ?? mentor.user?.bio ?? "";

  return (
    <article className="card mentor-card">
      <header className="mentor-card__head">
        <Avatar user={mentorAvatarUser(mentor)} size="lg" />
        <div style={{ minWidth: 0 }}>
          <h2 className="mentor-card__name">
            <Link className="stretched" to={`/mentorship/${mentor.id}`}>
              {mentorName(mentor)}
            </Link>
          </h2>
          {headline && <p className="mentor-card__headline muted">{headline}</p>}
        </div>
      </header>

      {expertise.length > 0 && (
        <ChipRow className="mentor-card__expertise">
          {expertise.slice(0, 5).map((value) => (
            <Chip key={value}>{value}</Chip>
          ))}
        </ChipRow>
      )}

      {availability && (
        <p className="mentor-card__availability">
          <Clock size={14} aria-hidden="true" /> {availability}
        </p>
      )}

      <p className="mentor-card__bio">{bio ? excerpt(bio, 150) : "This mentor has not written a bio yet."}</p>
    </article>
  );
}

export default function Mentorship() {
  const [params, setParams] = useSearchParams();
  const { isAuthenticated } = useAuth();

  const search = params.get("search") ?? "";
  const expertise = params.get("expertise") ?? "";

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
      api.get(endpoints.mentors, {
        signal,
        params: { search: search || undefined, expertise: expertise || undefined },
      }),
    [search, expertise]
  );

  const mentors = itemsFrom(data);
  const expertiseOptions = useMemo(() => topExpertise(mentors), [mentors]);
  const hasFilters = Boolean(search || expertise);

  let content;
  if (error) {
    content = <ErrorState error={error} onRetry={reload} title="We could not load the mentor list" />;
  } else if (loading && !mentors.length) {
    content = <SkeletonList count={6} height={220} />;
  } else if (!mentors.length) {
    content = hasFilters ? (
      <EmptyState
        icon={X}
        title="No mentors match this search"
        description="Only approved mentors appear here. Try a broader expertise term or clear the filters."
        action={
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setSearchText("");
              updateParams({ search: "", expertise: "" });
            }}
          >
            Clear filters
          </Button>
        }
      />
    ) : (
      <EmptyState
        icon={Users}
        title="No mentors are listed yet"
        description="The database has no approved mentor profiles right now, and CodeHer will not invent any. When real mentors join, they appear here instantly."
        action={
          <Button variant="ghost" to="/about">
            How mentorship at CodeHer works
          </Button>
        }
      />
    );
  } else {
    content = (
      <Stagger className="grid-auto">
        {mentors.map((mentor) => (
          <Stagger.Item key={mentor.id}>
            <MentorCard mentor={mentor} />
          </Stagger.Item>
        ))}
      </Stagger>
    );
  }

  return (
    <>
      <header className="container mentorship-header">
        <div className="mentorship-header__row">
          <div className="stack" style={{ gap: "var(--sp-3)" }}>
            <span className="eyebrow">Mentorship</span>
            <h1>Find a mentor who has walked the path</h1>
            <p className="lead">
              Every profile below is a CodeHer member approved for the mentor role — the seed
              ships labelled demonstration accounts, so look for &ldquo;sample&rdquo; in a name
              while developing. Browse by expertise, open a profile, and send a request with your
              goal and availability.
            </p>
          </div>
          {isAuthenticated && (
            <Button variant="outline" to="/mentorships">
              Track my requests
            </Button>
          )}
        </div>
      </header>

      <section className="container" style={{ paddingBottom: "var(--sp-9)" }} aria-label="Mentor directory">
        <div className="mentorship-toolbar">
          <SearchInput label="Search mentors" value={searchText} onChange={setSearchText} placeholder="Search by name or headline…" />
        </div>

        {(expertise || expertiseOptions.length > 0) && (
          <div className="mentorship-filters" role="group" aria-label="Filter by expertise">
            {expertise ? (
              <Button variant="link" size="sm" onClick={() => updateParams({ expertise: "" })}>
                <X size={14} aria-hidden="true" /> Clear “{expertise}”
              </Button>
            ) : (
              <span className="muted" style={{ fontSize: "var(--fs-xs)", fontWeight: 700 }}>
                <Sparkles size={13} aria-hidden="true" /> Expertise areas:
              </span>
            )}
            {expertiseOptions
              .filter((option) => option !== expertise)
              .slice(0, 10)
              .map((option) => (
                <Chip
                  key={option}
                  onClick={() => updateParams({ expertise: expertise === option ? "" : option })}
                >
                  {option}
                </Chip>
              ))}
          </div>
        )}

        <div aria-live="polite" aria-busy={loading}>
          {content}
        </div>
      </section>
    </>
  );
}
