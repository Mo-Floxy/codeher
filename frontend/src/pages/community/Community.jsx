import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Bookmark, Heart, MessageSquare, Plus, Users, X } from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync, useDebouncedValue } from "../../hooks";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import {
  Alert,
  Badge,
  Button,
  Chip,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Modal,
  Pagination,
  SearchInput,
  Select,
  SkeletonList,
  Tabs,
  TagInput,
  Textarea,
  UserCell,
} from "../../components/ui";
import {
  PAGE_SIZE,
  authorOf,
  commentsCount,
  errorText,
  excerpt,
  isBookmarked,
  isLiked,
  itemsFrom,
  likesCount,
  timeAgo,
  topTags,
  useEngagement,
} from "./communityUtils";
import "./community.css";

const TYPE_TABS = [
  { value: "", label: "All" },
  { value: "question", label: "Questions" },
  { value: "discussion", label: "Discussions" },
  { value: "showcase", label: "Showcase" },
];

const TYPE_OPTIONS = [
  { value: "question", label: "Question — I need help" },
  { value: "discussion", label: "Discussion — start a conversation" },
  { value: "showcase", label: "Showcase — look what I built" },
];

const TYPE_VARIANTS = { question: "info", discussion: "brand", showcase: "success" };

const ORDERING_OPTIONS = [
  { value: "recent", label: "Most recent" },
  { value: "most_commented", label: "Most commented" },
  { value: "most_liked", label: "Most liked" },
];

function PostCard({ post, isAuthenticated, liked, bookmarked, busyLike, busyBookmark, onToggle, activeTag, onTagClick }) {
  const author = authorOf(post);
  const tags = (post.tags ?? []).map((tag) => (typeof tag === "string" ? tag : tag?.name)).filter(Boolean);
  const type = post.type ?? "discussion";

  const LikeControl = isAuthenticated
    ? (
        <Button
          variant="ghost"
          size="sm"
          className={`comm-toggle comm-toggle--like ${liked ? "comm-toggle--on" : ""}`.trim()}
          onClick={() => onToggle(post, "like")}
          disabled={busyLike}
          aria-pressed={liked}
          aria-label={liked ? "Unlike this post" : "Like this post"}
        >
          <Heart size={15} aria-hidden="true" /> {likesCount(post)}
        </Button>
      )
    : (
        <Button variant="ghost" size="sm" to="/signin" aria-label="Sign in to like posts">
          <Heart size={15} aria-hidden="true" /> {likesCount(post)}
        </Button>
      );

  const BookmarkControl = isAuthenticated
    ? (
        <Button
          variant="ghost"
          size="sm"
          className={`comm-toggle comm-toggle--bookmark ${bookmarked ? "comm-toggle--on" : ""}`.trim()}
          onClick={() => onToggle(post, "bookmark")}
          disabled={busyBookmark}
          aria-pressed={bookmarked}
          aria-label={bookmarked ? "Remove bookmark" : "Bookmark this post"}
        >
          <Bookmark size={15} aria-hidden="true" />
          {bookmarked ? "Saved" : "Save"}
        </Button>
      )
    : (
        <Button variant="ghost" size="sm" to="/signin" aria-label="Sign in to bookmark posts">
          <Bookmark size={15} aria-hidden="true" /> Save
        </Button>
      );

  return (
    <article className="card comm-card post-card">
      <header className="post-card__head">
        <UserCell
          user={author}
          to={author?.id != null ? `/members/${author.id}` : undefined}
          subtitle={timeAgo(post.created_at)}
        />
        <Badge variant={TYPE_VARIANTS[type] ?? "neutral"}>{type}</Badge>
      </header>

      <h2 className="post-card__title">
        <Link className="stretched" to={`/community/posts/${post.id}`}>
          {post.title || "Untitled post"}
        </Link>
      </h2>

      <p className="post-card__excerpt muted">{excerpt(post.body)}</p>

      {tags.length > 0 && (
        <div className="comm-card__actions" style={{ display: "flex", gap: "var(--sp-2)", flexWrap: "wrap" }}>
          {tags.slice(0, 5).map((tag) => (
            <Chip key={tag} selected={activeTag === tag} onClick={() => onTagClick(tag)}>
              {tag}
            </Chip>
          ))}
        </div>
      )}

      <footer className="comm-card__actions post-card__foot">
        {LikeControl}
        <span className="post-card__stat" title={`${commentsCount(post)} comments`}>
          <MessageSquare size={15} aria-hidden="true" /> {commentsCount(post)}
        </span>
        {BookmarkControl}
      </footer>
    </article>
  );
}

function ComposeModal({ open, onClose, courses, coursesLoading, onCreated }) {
  const toast = useToast();
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [type, setType] = useState("discussion");
  const [tags, setTags] = useState([]);
  const [course, setCourse] = useState("");
  const [errors, setErrors] = useState({});
  const [failure, setFailure] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    const clientErrors = {};
    if (!title.trim()) clientErrors.title = "Add a title so members know what you need.";
    if (!body.trim()) clientErrors.body = "Write something to share.";
    if (Object.keys(clientErrors).length) {
      setErrors(clientErrors);
      return;
    }
    setBusy(true);
    setFailure(null);
    try {
      await api.post(endpoints.posts, {
        title: title.trim(),
        body: body.trim(),
        type,
        tags,
        course: course === "" ? undefined : course,
      });
      toast.success("Post published to the community.");
      setTitle("");
      setBody("");
      setTags([]);
      setCourse("");
      setErrors({});
      onClose();
      onCreated();
    } catch (err) {
      const fieldErrors = err?.fieldErrors ?? {};
      const mapped = {};
      for (const key of ["title", "body", "type", "tags", "course"]) {
        if (fieldErrors[key]?.[0]) mapped[key] = fieldErrors[key][0];
      }
      setErrors(mapped);
      setFailure(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="New post"
      description="Ask a question, start a discussion, or show what you built."
      wide
    >
      <form className="stack" onSubmit={submit} noValidate>
        <Field label="Title" required htmlFor="post-title" error={errors.title}>
          <Input
            id="post-title"
            data-autofocus
            maxLength={160}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="How do I debug a failing Django test?"
            error={errors.title}
          />
        </Field>

        <Field label="Body" required htmlFor="post-body" error={errors.body}>
          <Textarea
            id="post-body"
            rows={6}
            value={body}
            onChange={(event) => setBody(event.target.value)}
            placeholder="Share the details — what you tried, what worked, what broke."
            error={errors.body}
          />
        </Field>

        <div className="form-grid form-grid--2">
          <Field label="Type" required htmlFor="post-type" error={errors.type}>
            <Select id="post-type" value={type} onChange={(event) => setType(event.target.value)} options={TYPE_OPTIONS} />
          </Field>
          <Field
            label="Related course (optional)"
            htmlFor="post-course"
            hint={coursesLoading ? "Loading courses…" : "Links the post to a course so learners find it."}
            error={errors.course}
          >
            <Select
              id="post-course"
              value={course}
              onChange={(event) => setCourse(event.target.value)}
              options={[{ value: "", label: "None" }, ...courses.map((item) => ({ value: item.id, label: item.title }))]}
            />
          </Field>
        </div>

        <TagInput label="Tags" value={tags} onChange={setTags} placeholder="Add a tag and press Enter" max={6} />
        {errors.tags && <p className="field__error" role="alert">{errors.tags}</p>}

        {failure && !Object.keys(errors).length && <Alert variant="error">{errorText(failure)}</Alert>}

        <div className="row" style={{ justifyContent: "flex-end" }}>
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button type="submit" loading={busy}>
            Publish post
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default function Community() {
  const [params, setParams] = useSearchParams();
  const { isAuthenticated } = useAuth();
  const toast = useToast();

  const type = params.get("type") ?? "";
  const tag = params.get("tag") ?? "";
  const search = params.get("search") ?? "";
  const ordering = params.get("ordering") ?? "recent";
  const page = Number(params.get("page")) || 1;

  const [searchText, setSearchText] = useState(search);
  const debouncedSearch = useDebouncedValue(searchText);
  const [composeOpen, setComposeOpen] = useState(false);

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

  // Debounced typing pushes the query into the URL, which is the single source of truth for the fetch.
  useEffect(() => {
    if (debouncedSearch !== search) updateParams({ search: debouncedSearch });
  }, [debouncedSearch, search, updateParams]);

  const { data, setData, loading, error, reload } = useAsync(
    (signal) =>
      api.get(endpoints.posts, {
        signal,
        params: {
          type: type || undefined,
          tag: tag || undefined,
          search: search || undefined,
          ordering: ordering !== "recent" ? ordering : undefined,
          page,
          page_size: PAGE_SIZE,
        },
      }),
    [type, tag, search, ordering, page]
  );

  const mutatePost = useCallback(
    (id, updater) => {
      setData((current) => {
        if (!current) return current;
        const results = itemsFrom(current).map((post) => (post.id === id ? updater(post) : post));
        return Array.isArray(current) ? results : { ...current, results };
      });
    },
    [setData]
  );
  const engagement = useEngagement({ mutate: mutatePost, toast, scope: "posts" });

  const coursesState = useAsync(
    (signal) => api.get(endpoints.courses, { signal, params: { page_size: 50 } }),
    [],
    { skip: !isAuthenticated || !composeOpen }
  );

  const posts = itemsFrom(data);
  const count = data?.count ?? posts.length;
  const tagOptions = useMemo(() => topTags(posts), [posts]);
  const hasFilters = Boolean(type || tag || search);

  const clearFilters = () => {
    setSearchText("");
    updateParams({ type: "", tag: "", search: "", ordering: "" });
  };

  const handleTagClick = (value) => updateParams({ tag: tag === value ? "" : value });

  let feed;
  if (error && !posts.length) {
    feed = <ErrorState error={error} onRetry={reload} title="We could not load the feed" />;
  } else if (loading && !posts.length) {
    feed = <SkeletonList count={4} height={190} />;
  } else if (!posts.length) {
    feed = hasFilters ? (
      <EmptyState
        icon={X}
        title="No posts match your filters"
        description="Try a different tab, clear the tag, or search for something broader."
        action={
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            Clear all filters
          </Button>
        }
      />
    ) : (
      <EmptyState
        icon={Users}
        title="The community is quiet so far"
        description="No posts exist in the database yet. Be the first to ask a question or show what you are building."
        action={
          isAuthenticated ? (
            <Button variant="ghost" onClick={() => setComposeOpen(true)}>
              <Plus size={15} /> Write the first post
            </Button>
          ) : (
            <Button variant="ghost" to="/signin">
              Sign in to post first
            </Button>
          )
        }
      />
    );
  } else {
    feed = (
      <div className="comm-feed">
        {posts.map((post) => (
          <PostCard
            key={post.id}
            post={post}
            isAuthenticated={isAuthenticated}
            liked={isLiked(post)}
            bookmarked={isBookmarked(post)}
            busyLike={engagement.isPending(post.id, "like")}
            busyBookmark={engagement.isPending(post.id, "bookmark")}
            onToggle={engagement.run}
            activeTag={tag}
            onTagClick={handleTagClick}
          />
        ))}
      </div>
    );
  }

  return (
    <>
      <header className="container comm-page__header">
        <div className="comm-header-row">
          <div className="stack" style={{ gap: "var(--sp-3)" }}>
            <span className="eyebrow">Community</span>
            <h1>Questions, discussions &amp; showcases</h1>
            <p className="lead">
              Everything here is written by CodeHer members. Read freely — signing in lets you post,
              like, and bookmark what matters to you.
            </p>
          </div>
          {isAuthenticated ? (
            <Button onClick={() => setComposeOpen(true)}>
              <Plus size={16} /> New post
            </Button>
          ) : (
            <Button variant="outline" to="/signin">
              <Plus size={16} /> Sign in to post
            </Button>
          )}
        </div>
      </header>

      <section className="container" style={{ paddingBottom: "var(--sp-9)" }} aria-label="Community feed">
        <div className="comm-toolbar">
          <Tabs
            items={TYPE_TABS}
            value={type}
            onChange={(value) => updateParams({ type: value })}
            ariaLabel="Filter posts by type"
          />
          <div className="comm-toolbar__controls">
            <Select
              aria-label="Sort posts"
              value={ordering}
              onChange={(event) =>
                updateParams({ ordering: event.target.value === "recent" ? "" : event.target.value })
              }
              options={ORDERING_OPTIONS}
            />
            <SearchInput label="Search posts" value={searchText} onChange={setSearchText} placeholder="Search posts…" />
          </div>
        </div>

        {(tag || tagOptions.length > 0) && (
          <div className="comm-filter-chips" role="group" aria-label="Filter by tag">
            {tag && (
              <Button variant="link" size="sm" onClick={() => updateParams({ tag: "" })}>
                <X size={14} aria-hidden="true" /> Clear “{tag}”
              </Button>
            )}
            {!tag && <span className="muted" style={{ fontSize: "var(--fs-xs)", fontWeight: 700 }}>Popular tags:</span>}
            {tagOptions
              .filter((option) => option !== tag)
              .slice(0, 8)
              .map((option) => (
                <Chip key={option} onClick={() => handleTagClick(option)}>
                  {option}
                </Chip>
              ))}
          </div>
        )}

        <div aria-live="polite" aria-busy={loading}>
          {feed}
        </div>

        {posts.length > 0 && (
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

      {isAuthenticated && (
        <ComposeModal
          open={composeOpen}
          onClose={() => setComposeOpen(false)}
          courses={itemsFrom(coursesState.data)}
          coursesLoading={coursesState.loading}
          onCreated={() => {
            updateParams({ page: "" });
            reload();
          }}
        />
      )}
    </>
  );
}
