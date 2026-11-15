import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ImagePlus, Lock, Trash2, Upload } from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync } from "../../hooks";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import {
  Alert,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Skeleton,
  SkeletonText,
  TagInput,
  Textarea,
} from "../../components/ui";
import { authorOf, errorText } from "./communityUtils";
import "./community.css";

function isHttpUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

export default function ProjectEditor() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const { user, isAdmin } = useAuth();
  const toast = useToast();

  const { data: project, loading, error, reload } = useAsync(
    (signal) => api.get(`/community/projects/${id}/`, { signal }),
    [id],
    { skip: !isEdit }
  );

  const [fields, setFields] = useState({
    title: "",
    description: "",
    technologies: [],
    repo_url: "",
    live_url: "",
    screenshot: "",
  });
  const [errors, setErrors] = useState({});
  const [failure, setFailure] = useState(null);
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (isEdit && project && !initialized) {
      setFields({
        title: project.title ?? "",
        description: project.description ?? "",
        technologies: (project.technologies ?? [])
          .map((tech) => (typeof tech === "string" ? tech : tech?.name))
          .filter(Boolean),
        repo_url: project.repo_url ?? "",
        live_url: project.live_url ?? "",
        screenshot: project.screenshot ?? project.screenshot_url ?? "",
      });
      setInitialized(true);
    }
  }, [isEdit, project, initialized]);

  const owner = authorOf(project);
  const canEdit = !isEdit || Boolean(project) && (isAdmin || (owner?.id != null && owner.id === user?.id));

  const setField = (key) => (event) => {
    const value = event?.target ? event.target.value : event;
    setFields((current) => ({ ...current, [key]: value }));
    setErrors((current) => {
      if (!current[key]) return current;
      const next = { ...current };
      delete next[key];
      return next;
    });
  };

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setUploading(true);
    setUploadError("");
    try {
      const form = new FormData();
      form.append("file", file);
      const result = await api.upload("/uploads/", form);
      const url = result?.url;
      if (!url) {
        setUploadError("The upload service did not return a URL.");
        return;
      }
      setFields((current) => ({ ...current, screenshot: url }));
    } catch (err) {
      setUploadError(errorText(err));
    } finally {
      setUploading(false);
    }
  };

  const submit = async (event) => {
    event.preventDefault();
    const clientErrors = {};
    if (!fields.title.trim()) clientErrors.title = "Give the project a title.";
    else if (fields.title.trim().length < 3) clientErrors.title = "The title is a bit short.";
    if (!fields.description.trim()) clientErrors.description = "Describe what you built and what you learned.";
    for (const key of ["repo_url", "live_url"]) {
      const value = fields[key].trim();
      if (value && !isHttpUrl(value)) clientErrors[key] = "Use a full URL starting with https://";
    }
    if (Object.keys(clientErrors).length) {
      setErrors(clientErrors);
      return;
    }

    setBusy(true);
    setFailure(null);
    const payload = {
      title: fields.title.trim(),
      description: fields.description.trim(),
      technologies: fields.technologies,
      repo_url: fields.repo_url.trim(),
      live_url: fields.live_url.trim(),
      screenshot: fields.screenshot,
    };
    try {
      const saved = isEdit
        ? await api.patch(`/community/projects/${project.id}/`, payload)
        : await api.post(endpoints.projects, payload);
      toast.success(isEdit ? "Project updated." : "Project published — thank you for sharing your work!");
      navigate(`/community/projects/${saved?.id ?? project?.id ?? id}`);
    } catch (err) {
      const fieldErrors = err?.fieldErrors ?? {};
      const mapped = {};
      for (const key of ["title", "description", "technologies", "repo_url", "live_url", "screenshot"]) {
        if (fieldErrors[key]?.[0]) mapped[key] = fieldErrors[key][0];
      }
      setErrors(mapped);
      setFailure(err);
    } finally {
      setBusy(false);
    }
  };

  if (isEdit && error) {
    return (
      <div className="editor-wrap">
        <ErrorState error={error} onRetry={reload} title="We could not load this project" />
      </div>
    );
  }

  if (isEdit && loading && !project) {
    return (
      <div className="editor-wrap" aria-busy="true" aria-live="polite">
        <Skeleton className="skeleton--title" />
        <SkeletonText lines={6} />
      </div>
    );
  }

  // Ownership guard: never render an editable form for somebody else's project.
  if (isEdit && project && !canEdit) {
    return (
      <div className="editor-wrap denied-state">
        <EmptyState
          icon={Lock}
          title="You cannot edit this project"
          description="Only the owner or a CodeHer admin can change a published project. This page will not show an editable form for someone else's work."
          action={
            <Button variant="ghost" to={`/community/projects/${project.id ?? id}`}>
              View the project instead
            </Button>
          }
        />
      </div>
    );
  }

  if (isEdit && !project) return null;

  return (
    <div className="editor-wrap">
      <header className="stack" style={{ gap: "var(--sp-2)" }}>
        <span className="eyebrow">{isEdit ? "Edit project" : "Showcase"}</span>
        <h1>{isEdit ? "Edit your project" : "Publish a project"}</h1>
        <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
          Real work only — this goes into the public gallery exactly as you write it here.
        </p>
      </header>

      <form className="card editor-form" onSubmit={submit} noValidate aria-label="Project details">
        <Field label="Title" required htmlFor="project-title" error={errors.title}>
          <Input
            id="project-title"
            data-autofocus
            maxLength={160}
            value={fields.title}
            onChange={setField("title")}
            placeholder="Study streak tracker for nurses"
            error={errors.title}
          />
        </Field>

        <Field
          label="Description"
          required
          htmlFor="project-description"
          hint="What it does, what you learned, what you would build next."
          error={errors.description}
        >
          <Textarea
            id="project-description"
            rows={6}
            value={fields.description}
            onChange={setField("description")}
            placeholder="I built this after the Django path…"
            error={errors.description}
          />
        </Field>

        <div>
          <TagInput
            label="Technologies"
            value={fields.technologies}
            onChange={(value) => setField("technologies")(value)}
            placeholder="React, Django, MySQL…"
            max={10}
          />
          {errors.technologies && (
            <p className="field__error" role="alert">
              {errors.technologies}
            </p>
          )}
        </div>

        <div className="form-grid form-grid--2">
          <Field label="Repository URL (optional)" htmlFor="project-repo" error={errors.repo_url}>
            <Input
              id="project-repo"
              type="url"
              inputMode="url"
              value={fields.repo_url}
              onChange={setField("repo_url")}
              placeholder="https://github.com/you/project"
              error={errors.repo_url}
            />
          </Field>
          <Field label="Live demo URL (optional)" htmlFor="project-live" error={errors.live_url}>
            <Input
              id="project-live"
              type="url"
              inputMode="url"
              value={fields.live_url}
              onChange={setField("live_url")}
              placeholder="https://my-project.example.com"
              error={errors.live_url}
            />
          </Field>
        </div>

        <div className="field upload-row">
          <span className="field__label" id="screenshot-label">
            Screenshot (optional)
          </span>
          <p className="field__hint">Uploads to the CodeHer media store; you can publish without a picture.</p>
          <input
            className="file-input"
            type="file"
            accept="image/*"
            aria-labelledby="screenshot-label"
            onChange={handleUpload}
            disabled={uploading}
          />
          {uploading && <Alert variant="info">Uploading image…</Alert>}
          {(uploadError || errors.screenshot) && (
            <Alert variant="error" title="Upload failed" onDismiss={uploadError ? () => setUploadError("") : undefined}>
              {uploadError || errors.screenshot}
            </Alert>
          )}
          {fields.screenshot && (
            <>
              <div className="upload-preview">
                <img src={fields.screenshot} alt="Selected project screenshot preview" />
              </div>
              <div className="row">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setFields((current) => ({ ...current, screenshot: "" }))}
                >
                  <Trash2 size={14} aria-hidden="true" /> Remove picture
                </Button>
                <label className="btn btn--ghost btn--sm" style={{ cursor: "pointer" }}>
                  <ImagePlus size={14} aria-hidden="true" /> Replace
                  <input type="file" accept="image/*" style={{ display: "none" }} onChange={handleUpload} disabled={uploading} />
                </label>
              </div>
            </>
          )}
        </div>

        {failure && Object.keys(errors).length === 0 && (
          <Alert variant="error" title="Could not save">{errorText(failure)}</Alert>
        )}

        <div className="row" style={{ justifyContent: "flex-end" }}>
          <Button
            type="button"
            variant="ghost"
            onClick={() => navigate(isEdit ? `/community/projects/${project.id ?? id}` : "/community/projects")}
            disabled={busy}
          >
            Cancel
          </Button>
          <Button type="submit" loading={busy}>
            <Upload size={15} aria-hidden="true" /> {isEdit ? "Save changes" : "Publish project"}
          </Button>
        </div>
      </form>
    </div>
  );
}
