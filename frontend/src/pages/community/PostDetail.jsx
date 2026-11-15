import { useCallback, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  BadgeCheck,
  Bookmark,
  CheckCircle2,
  CornerDownRight,
  Flag,
  Heart,
  MessageSquare,
  Send,
  Trash2,
} from "lucide-react";
import { api } from "../../services/api";
import { useAsync } from "../../hooks";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import {
  Alert,
  Badge,
  Button,
  Chip,
  ChipRow,
  ConfirmDialog,
  EmptyState,
  ErrorState,
  Field,
  Skeleton,
  SkeletonText,
  Textarea,
  UserCell,
} from "../../components/ui";
import {
  ReportModal,
  authorOf,
  commentsCount,
  errorText,
  isBookmarked,
  isLiked,
  likesCount,
  timeAgo,
  useEngagement,
} from "./communityUtils";
import "./community.css";

function parentIdOf(comment) {
  const parent = comment.parent ?? comment.parent_comment;
  if (parent && typeof parent === "object") return parent.id ?? null;
  return parent ?? null;
}

/** One level of nesting: replies (and replies-to-replies) fold under their nearest root. */
function buildThreads(comments) {
  const list = Array.isArray(comments) ? comments : [];
  const ids = new Set(list.map((comment) => String(comment.id)));
  const roots = list.filter((comment) => {
    const parent = parentIdOf(comment);
    return parent == null || !ids.has(String(parent));
  });
  const children = new Map(roots.map((root) => [String(root.id), []]));
  for (const comment of list) {
    const parent = parentIdOf(comment);
    if (parent == null) continue;
    const key = String(parent);
    if (children.has(key)) {
      if (String(comment.id) !== key) children.get(key).push(comment);
      continue;
    }
    const middle = list.find((candidate) => String(candidate.id) === key);
    const grand = middle ? parentIdOf(middle) : null;
    if (grand != null && children.has(String(grand))) children.get(String(grand)).push(comment);
  }
  return roots.map((root) => ({ ...root, threadChildren: children.get(String(root.id)) ?? [] }));
}

function helpfulIdOf(post) {
  const raw = post?.helpful_comment ?? post?.helpful_answer ?? null;
  if (raw && typeof raw === "object") return raw.id;
  return raw;
}

function CommentForm({ parent, onCreated, onCancel, submitLabel = "Post comment", autoFocus = false }) {
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [invalid, setInvalid] = useState(false);
  const [failure, setFailure] = useState(null);
  const fieldId = `comment-body-${parent ?? "root"}`;

  const submit = async (event) => {
    event.preventDefault();
    if (!body.trim()) {
      setInvalid(true);
      return;
    }
    setBusy(true);
    setFailure(null);
    try {
      await onCreated({ body: body.trim(), parent });
      setBody("");
      setInvalid(false);
    } catch (err) {
      setFailure(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form
      className="stack"
      onSubmit={submit}
      style={{ gap: "var(--sp-3)" }}
      aria-label={parent ? "Write a reply" : "Write a comment"}
    >
      <Field
        label={parent ? "Your reply" : "Your comment"}
        required
        htmlFor={fieldId}
        error={invalid ? "Write something first." : undefined}
      >
        <Textarea
          id={fieldId}
          rows={4}
          value={body}
          data-autofocus={autoFocus || undefined}
          onChange={(event) => {
            setBody(event.target.value);
            if (invalid) setInvalid(false);
          }}
          placeholder="Add to the discussion — kindness and specifics welcome."
          error={invalid ? "required" : undefined}
        />
      </Field>
      {failure && <Alert variant="error">{errorText(failure)}</Alert>}
      <div className="row" style={{ justifyContent: "flex-end" }}>
        {onCancel && (
          <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" size="sm" loading={busy}>
          <Send size={14} aria-hidden="true" /> {submitLabel}
        </Button>
      </div>
    </form>
  );
}

/** `thread` carries the shared reply/helpful/delete context so every comment — root or reply — gets its own flags. */
function CommentBlock({ comment, depth, thread }) {
  const author = authorOf(comment);
  const replyOpen = thread.replyTo === comment.id;
  const helpful = thread.isHelpful(comment);
  const canDelete = thread.canDelete(comment);

  return (
    <article className={`comment ${depth > 0 ? "comment--reply" : ""}`.trim()}>
      <header className="comment__head">
        <UserCell
          user={author}
          to={author?.id != null ? `/members/${author.id}` : undefined}
          subtitle={timeAgo(comment.created_at ?? comment.created)}
        />
        {helpful && (
          <Badge variant="success">
            <BadgeCheck size={13} aria-hidden="true" /> Helpful answer
          </Badge>
        )}
      </header>

      <p className="comment__body">{comment.body}</p>

      <div className="comment__actions">
        {thread.canReply && (
          <Button
            variant="link"
            size="sm"
            onClick={() => thread.toggleReply(comment.id)}
            aria-expanded={replyOpen}
            aria-label={`Reply to ${author?.display_name || author?.username || "this comment"}`}
          >
            <CornerDownRight size={14} aria-hidden="true" /> Reply
          </Button>
        )}
        {thread.isQuestion && thread.canModerate && !helpful && (
          <Button variant="ghost" size="sm" onClick={() => thread.markHelpful(comment)} disabled={thread.helpfulBusy}>
            <CheckCircle2 size={14} aria-hidden="true" /> Mark as helpful answer
          </Button>
        )}
        {canDelete && (
          <Button variant="danger" size="sm" onClick={() => thread.requestDelete(comment)}>
            <Trash2 size={14} aria-hidden="true" /> Delete
          </Button>
        )}
      </div>

      {replyOpen && (
        <div className="comment__reply-form">
          <CommentForm
            parent={comment.id}
            onCreated={thread.onCreated}
            onCancel={() => thread.toggleReply(comment.id)}
            submitLabel="Post reply"
            autoFocus
          />
        </div>
      )}

      {comment.threadChildren?.length > 0 && (
        <div className="comment__children">
          {comment.threadChildren.map((child) => (
            <CommentBlock key={child.id} comment={child} depth={Math.min(depth + 1, 1)} thread={thread} />
          ))}
        </div>
      )}
    </article>
  );
}

export default function PostDetail() {
  const { id } = useParams();
  const { isAuthenticated, user, isAdmin } = useAuth();
  const toast = useToast();

  const { data: post, setData, loading, error, reload } = useAsync(
    (signal) => api.get(`/community/posts/${id}/`, { signal }),
    [id]
  );

  const [replyTo, setReplyTo] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [reportOpen, setReportOpen] = useState(false);
  const [helpfulBusy, setHelpfulBusy] = useState(false);

  const mutatePost = useCallback(
    (itemId, updater) =>
      setData((current) => (current && String(current.id) === String(itemId) ? updater(current) : current)),
    [setData]
  );
  const engagement = useEngagement({ mutate: mutatePost, toast, scope: "posts" });

  const threads = useMemo(() => buildThreads(post?.comments), [post?.comments]);

  const isQuestion = (post?.type ?? "") === "question";
  const postAuthor = authorOf(post);
  const canModerate = Boolean(post) && (isAdmin || (isAuthenticated && postAuthor?.id === user?.id));
  const activeHelpfulId = helpfulIdOf(post);

  const addComment = async ({ body, parent }) => {
    const created = await api.post(`/community/posts/${id}/comments/`, parent ? { body, parent } : { body });
    const normalized = { ...created };
    if (!authorOf(normalized)) normalized.author = user;
    setData((current) =>
      current
        ? { ...current, comments: [...(current.comments ?? []), normalized], comments_count: commentsCount(current) + 1 }
        : current
    );
    setReplyTo(null);
    toast.success(parent ? "Reply posted." : "Comment posted.");
  };

  const confirmDeleteComment = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.del(`/community/comments/${deleteTarget.id}/`);
      setData((current) =>
        current
          ? {
              ...current,
              comments: (current.comments ?? []).filter((comment) => comment.id !== deleteTarget.id),
              comments_count: Math.max(0, commentsCount(current) - 1),
            }
          : current
      );
      toast.success("Comment deleted.");
      setDeleteTarget(null);
    } catch (err) {
      toast.error(errorText(err));
    } finally {
      setDeleting(false);
    }
  };

  const markHelpful = async (comment) => {
    setHelpfulBusy(true);
    try {
      await api.post(`/community/posts/${id}/helpful/`, { comment_id: comment.id });
      setData((current) =>
        current
          ? {
              ...current,
              helpful_comment: comment.id,
              comments: (current.comments ?? []).map((item) => ({ ...item, is_helpful: item.id === comment.id })),
            }
          : current
      );
      toast.success("Marked as the helpful answer.");
    } catch (err) {
      toast.error(errorText(err));
    } finally {
      setHelpfulBusy(false);
    }
  };

  if (error) {
    return (
      <section className="container section">
        <ErrorState error={error} onRetry={reload} title="We could not load this post" />
      </section>
    );
  }

  if (loading && !post) {
    return (
      <section className="container section" aria-busy="true" aria-live="polite">
        <div className="card stack">
          <Skeleton className="skeleton--title" />
          <SkeletonText lines={5} />
        </div>
      </section>
    );
  }

  if (!post) {
    return (
      <section className="container section">
        <EmptyState
          icon={MessageSquare}
          title="Post not found"
          description="This post may have been removed by its author or a moderator."
          action={
            <Button variant="ghost" to="/community">
              Back to the community
            </Button>
          }
        />
      </section>
    );
  }

  const tags = (post.tags ?? []).map((tag) => (typeof tag === "string" ? tag : tag?.name)).filter(Boolean);
  const course = post.course && typeof post.course === "object" ? post.course : null;
  const courseLink = course ? `/learning/${course.slug ?? course.id}` : post.course ? `/learning/${post.course}` : null;

  const thread = {
    replyTo,
    toggleReply: (commentId) => setReplyTo((current) => (current === commentId ? null : commentId)),
    canReply: isAuthenticated,
    isQuestion,
    canModerate,
    helpfulBusy,
    markHelpful,
    canDelete: (comment) => {
      if (!isAuthenticated) return false;
      const commentAuthor = authorOf(comment);
      return isAdmin || (commentAuthor?.id != null && commentAuthor.id === user?.id);
    },
    requestDelete: setDeleteTarget,
    onCreated: addComment,
    isHelpful: (comment) =>
      Boolean(comment.is_helpful ?? comment.helpful) ||
      (activeHelpfulId != null && String(activeHelpfulId) === String(comment.id)),
  };

  return (
    <section className="container" style={{ paddingBlock: "var(--sp-6) var(--sp-9)" }}>
      <nav aria-label="Breadcrumb" style={{ marginBottom: "var(--sp-4)" }}>
        <Button variant="link" size="sm" to="/community">
          <ArrowLeft size={15} aria-hidden="true" /> Back to community
        </Button>
      </nav>

      <div className="post-layout">
        <article className="post-main">
          <div className="card stack">
            <div className="post-card__head">
              <Badge variant={isQuestion ? "info" : post.type === "showcase" ? "success" : "brand"}>
                {post.type ?? "discussion"}
              </Badge>
              <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>
                {post.created_at ? new Date(post.created_at).toLocaleString() : ""}
              </span>
            </div>

            <h1 className="post-title">{post.title || "Untitled post"}</h1>

            {tags.length > 0 && (
              <ChipRow>
                {tags.map((tag) => (
                  <Chip key={tag}>
                    <Link to={`/community?tag=${encodeURIComponent(tag)}`}>{tag}</Link>
                  </Chip>
                ))}
              </ChipRow>
            )}

            <div className="post-body">{post.body}</div>

            {courseLink && (
              <p className="post-meta">
                Related course:{" "}
                <Link to={courseLink}>
                  <strong>{course?.title ?? "Course"}</strong>
                </Link>
              </p>
            )}

            <div className="post-actions">
              {isAuthenticated ? (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    className={`comm-toggle comm-toggle--like ${isLiked(post) ? "comm-toggle--on" : ""}`.trim()}
                    onClick={() => engagement.run(post, "like")}
                    disabled={engagement.isPending(post.id, "like")}
                    aria-pressed={isLiked(post)}
                    aria-label={isLiked(post) ? "Unlike this post" : "Like this post"}
                  >
                    <Heart size={15} aria-hidden="true" /> {likesCount(post)}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className={`comm-toggle comm-toggle--bookmark ${isBookmarked(post) ? "comm-toggle--on" : ""}`.trim()}
                    onClick={() => engagement.run(post, "bookmark")}
                    disabled={engagement.isPending(post.id, "bookmark")}
                    aria-pressed={isBookmarked(post)}
                    aria-label={isBookmarked(post) ? "Remove bookmark" : "Bookmark this post"}
                  >
                    <Bookmark size={15} aria-hidden="true" /> {isBookmarked(post) ? "Saved" : "Save"}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setReportOpen(true)}>
                    <Flag size={15} aria-hidden="true" /> Report
                  </Button>
                </>
              ) : (
                <Button variant="outline" size="sm" to="/signin">
                  <Heart size={15} aria-hidden="true" /> Sign in to like, save or report
                </Button>
              )}
              <span className="post-card__stat" style={{ marginLeft: "auto" }}>
                <MessageSquare size={15} aria-hidden="true" /> {commentsCount(post) || threads.length} comments
              </span>
            </div>
          </div>

          <section className="card stack" aria-label="Comments">
            <h2 style={{ fontSize: "var(--fs-md)" }}>Discussion ({commentsCount(post) || threads.length})</h2>

            {isAuthenticated ? (
              <CommentForm onCreated={addComment} />
            ) : (
              <Alert variant="info">
                <Link to="/signin">Sign in</Link> to join the discussion.
              </Alert>
            )}

            <div className="comment-list" aria-live="polite">
              {threads.length === 0 ? (
                <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
                  No comments yet — be the first to reply.
                </p>
              ) : (
                threads.map((comment) => <CommentBlock key={comment.id} comment={comment} depth={0} thread={thread} />)
              )}
            </div>
          </section>
        </article>

        <aside className="stack" aria-label="Post details">
          <div className="card author-aside">
            <span className="muted" style={{ fontSize: "var(--fs-xs)", fontWeight: 800, textTransform: "uppercase", letterSpacing: "var(--tracking-wide)" }}>
              Author
            </span>
            <UserCell
              user={postAuthor}
              to={postAuthor?.id != null ? `/members/${postAuthor.id}` : undefined}
              size="lg"
              subtitle={postAuthor?.headline ? String(postAuthor.headline) : undefined}
            />
            <hr />
            <div className="post-meta">
              <span>
                <Heart size={14} aria-hidden="true" /> {likesCount(post)} likes
              </span>
              <span>
                <MessageSquare size={14} aria-hidden="true" /> {commentsCount(post)} comments
              </span>
            </div>
          </div>
        </aside>
      </div>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        onConfirm={confirmDeleteComment}
        busy={deleting}
        title="Delete this comment?"
        message="It will be removed for everyone. This cannot be undone."
        confirmLabel="Delete comment"
      />

      <ReportModal open={reportOpen} onClose={() => setReportOpen(false)} scope="posts" target={post} toast={toast} />
    </section>
  );
}
