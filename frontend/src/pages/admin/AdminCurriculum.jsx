import { useState } from "react";
import { Pencil, Plus, Trash2, UploadCloud, EyeOff } from "lucide-react";
import { api } from "../../services/api";
import { useAsync, useDebouncedValue } from "../../hooks";
import { useToast } from "../../context/ToastContext";
import {
  Badge,
  Button,
  ConfirmDialog,
  EmptyState,
  ErrorState,
  Field,
  IconButton,
  Input,
  Modal,
  Pagination,
  SearchInput,
  Select,
  Skeleton,
  Tabs,
  Textarea,
} from "../../components/ui";
import { asList, num } from "../app/helpers";
import "./admin.css";

const LEVELS = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];
const KINDS = [
  { value: "text", label: "Text" },
  { value: "code", label: "Code" },
  { value: "quiz", label: "Quiz" },
];

function fieldValue(row, key) {
  const value = row?.[key];
  if (value && typeof value === "object") return value.id ?? value.slug ?? "";
  return value ?? "";
}

// Generic CRUD table + modal driven by a field/column config. Server validation
// surfaces through fieldErrors so the form never claims success it didn't get.
function CrudPanel({ entity, singular, titleField, fields, columns, defaultValues, showStatus }) {
  const toast = useToast();
  const base = `/admin/${entity}/`;
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const debounced = useDebouncedValue(search, 300);

  const { data, loading, error, reload } = useAsync(
    (signal) => api.get(base, { signal, params: { search: debounced || undefined, page, page_size: 10 } }),
    [base, debounced, page]
  );

  const rows = asList(data);
  const count = data?.count ?? rows.length;
  const pageSize = data?.page_size ?? 10;

  const [modal, setModal] = useState({ open: false, mode: "create", row: null });
  const [form, setForm] = useState({});
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [toDelete, setToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const set = (key) => (eventOrValue) => {
    const value = typeof eventOrValue === "object" && eventOrValue?.target ? eventOrValue.target.value : eventOrValue;
    setForm((current) => ({ ...current, [key]: value }));
  };

  const openNew = () => {
    setForm({ ...defaultValues });
    setErrors({});
    setModal({ open: true, mode: "create", row: null });
  };
  const openEdit = (row) => {
    const next = {};
    fields.forEach((field) => {
      const raw = fieldValue(row, field.key);
      next[field.key] = raw === "" ? field.default ?? "" : raw;
    });
    setForm(next);
    setErrors({});
    setModal({ open: true, mode: "edit", row });
  };
  const closeModal = () => setModal({ open: false, mode: "create", row: null });

  const validate = () => {
    const next = {};
    fields.forEach((field) => {
      const value = form[field.key];
      if (field.required && (value === undefined || value === null || String(value).trim() === "")) {
        next[field.key] = `${field.label} is required.`;
      } else if (field.type === "number" && String(value).trim() !== "" && Number.isNaN(Number(value))) {
        next[field.key] = `${field.label} must be a number.`;
      } else if (field.validate && String(value).trim() !== "") {
        const message = field.validate(value);
        if (message) next[field.key] = message;
      }
    });
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const buildPayload = () => {
    const payload = {};
    fields.forEach((field) => {
      const value = form[field.key];
      if (field.type === "number") {
        if (String(value).trim() === "") return;
        payload[field.key] = Number(value);
      } else {
        payload[field.key] = typeof value === "string" ? value : value;
      }
    });
    return payload;
  };

  const submit = async () => {
    if (!validate()) return;
    setSaving(true);
    try {
      const payload = buildPayload();
      if (modal.mode === "edit" && modal.row?.id != null) {
        await api.patch(`${base}${modal.row.id}/`, payload);
        toast.success(`${singular} updated.`);
      } else {
        await api.post(base, payload);
        toast.success(`${singular} created.`);
      }
      closeModal();
      reload();
    } catch (err) {
      setErrors(err?.fieldErrors ?? {});
      toast.error(err?.detail || `Could not save this ${singular.toLowerCase()}.`);
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!toDelete) return;
    setDeleting(true);
    try {
      await api.del(`${base}${toDelete.id}/`);
      toast.success(`${singular} deleted.`);
      setToDelete(null);
      reload();
    } catch (err) {
      toast.error(err?.detail || "Could not delete this row.");
    } finally {
      setDeleting(false);
    }
  };

  const toggleStatus = async (row) => {
    const next = !row.is_published;
    try {
      await api.patch(`${base}${row.id}/`, { is_published: next });
      toast.success(next ? "Published." : "Moved to draft.");
      reload();
    } catch (err) {
      toast.error(err?.detail || "Status change failed.");
    }
  };

  return (
    <div className="admin-panel">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
        <h2 style={{ fontSize: "var(--fs-lg)" }}>{entity}</h2>
        <Button size="sm" onClick={openNew}>
          <Plus size={15} aria-hidden="true" /> New {singular.toLowerCase()}
        </Button>
      </div>

      <div className="admin-toolbar">
        <div className="admin-toolbar__grow">
          <SearchInput label={`Search ${entity}`} value={search} onChange={(value) => { setSearch(value); setPage(1); }} placeholder={`Search ${entity}…`} />
        </div>
      </div>

      {loading ? <Skeleton style={{ height: 240 }} /> : null}
      {!loading && error ? <ErrorState error={error} onRetry={reload} title={`Could not load ${entity}`} /> : null}
      {!loading && !error && rows.length === 0 ? (
        <EmptyState icon={Plus} title={`No ${entity} yet`} description={`Create your first ${singular.toLowerCase()} to populate the catalogue.`} action={<Button onClick={openNew}>New {singular.toLowerCase()}</Button>} />
      ) : null}

      {!loading && !error && rows.length > 0 ? (
        <>
          <div className="table-wrap">
            <table className="table">
              <caption className="sr-only">{`${entity} management table`}</caption>
              <thead>
                <tr>
                  {columns.map((column) => (
                    <th key={column.header} scope="col">{column.header}</th>
                  ))}
                  {showStatus ? <th scope="col">Status</th> : null}
                  <th scope="col">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={row.id ?? index}>
                    {columns.map((column) => (
                      <td key={column.header}>{column.cell ? column.cell(row) : String(row[column.key] ?? "—")}</td>
                    ))}
                    {showStatus ? (
                      <td>
                        <span className={`status-pill ${row.is_published ? "status-pill--ok" : "status-pill--off"}`}>
                          {row.is_published ? "Published" : "Draft"}
                        </span>
                      </td>
                    ) : null}
                    <td>
                      <div className="admin-cell__actions">
                        {showStatus ? (
                          <IconButton label={row.is_published ? "Move to draft" : "Publish"} variant="ghost" onClick={() => toggleStatus(row)}>
                            {row.is_published ? <EyeOff size={15} /> : <UploadCloud size={15} />}
                          </IconButton>
                        ) : null}
                        <IconButton label={`Edit ${row[titleField] ?? singular}`} variant="ghost" onClick={() => openEdit(row)}>
                          <Pencil size={15} />
                        </IconButton>
                        <IconButton label={`Delete ${row[titleField] ?? singular}`} variant="ghost" onClick={() => setToDelete(row)}>
                          <Trash2 size={15} />
                        </IconButton>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination count={count} page={page} pageSize={pageSize} onPageChange={setPage} />
        </>
      ) : null}

      <Modal
        open={modal.open}
        onClose={closeModal}
        title={`${modal.mode === "edit" ? "Edit" : "New"} ${singular.toLowerCase()}`}
        footer={
          <>
            <Button variant="ghost" onClick={closeModal} disabled={saving}>Cancel</Button>
            <Button onClick={submit} loading={saving}>{modal.mode === "edit" ? "Save changes" : "Create"}</Button>
          </>
        }
      >
        <div className="admin-modal-form">
          {fields.map((field) => {
            const controlId = `${entity}-${field.key}`;
            return (
              <Field key={field.key} label={field.label} hint={field.hint} error={errors[field.key]?.[0]} required={field.required} htmlFor={controlId}>
                {field.type === "textarea" ? (
                  <Textarea id={controlId} value={form[field.key] ?? ""} onChange={set(field.key)} rows={field.rows ?? 4} error={errors[field.key]?.[0]} data-autofocus={field.first ? "" : undefined} />
                ) : field.type === "select" ? (
                  <Select id={controlId} options={field.options} value={form[field.key] ?? ""} onChange={set(field.key)} error={errors[field.key]?.[0]} />
                ) : (
                  <Input
                    id={controlId}
                    type={field.type === "number" ? "number" : field.type === "color" ? "color" : "text"}
                    inputMode={field.type === "number" ? "numeric" : undefined}
                    value={form[field.key] ?? ""}
                    onChange={set(field.key)}
                    error={errors[field.key]?.[0]}
                    data-autofocus={field.first ? "" : undefined}
                  />
                )}
              </Field>
            );
          })}
        </div>
      </Modal>

      <ConfirmDialog
        open={Boolean(toDelete)}
        onClose={() => setToDelete(null)}
        onConfirm={remove}
        busy={deleting}
        variant="danger"
        confirmLabel="Delete"
        title={`Delete this ${singular.toLowerCase()}?`}
        message={`“${toDelete ? toDelete[titleField] : ""}” will be removed. This cannot be undone.`}
      />
    </div>
  );
}

export default function AdminCurriculum() {
  const [tab, setTab] = useState("paths");

  // Related-entity options are fetched once so course/path selectors are real.
  const paths = useAsync((signal) => api.get("/admin/paths/", { signal, params: { page_size: 50 } }), []);
  const courses = useAsync((signal) => api.get("/admin/courses/", { signal, params: { page_size: 50 } }), []);

  const pathOptions = [
    { value: "", label: "No path" },
    ...asList(paths.data).map((item) => ({ value: item.id, label: item.title ?? `#${item.id}` })),
  ];
  const courseOptions = asList(courses.data).map((item) => ({ value: item.id, label: item.title ?? `#${item.id}` }));

  const configs = {
    paths: {
      entity: "paths",
      singular: "Path",
      titleField: "title",
      showStatus: true,
      defaultValues: { title: "", slug: "", description: "", level: "beginner", color: "#8b5cf6" },
      fields: [
        { key: "title", label: "Title", type: "text", required: true, first: true },
        { key: "slug", label: "Slug", type: "text", hint: "URL-safe id. Leave blank to auto-generate." },
        { key: "level", label: "Level", type: "select", options: LEVELS },
        { key: "color", label: "Accent colour", type: "color" },
        { key: "description", label: "Description", type: "textarea" },
      ],
      columns: [
        { header: "Title", key: "title" },
        { header: "Level", cell: (row) => <Badge variant="neutral">{row.level ?? "—"}</Badge> },
      ],
    },
    courses: {
      entity: "courses",
      singular: "Course",
      titleField: "title",
      showStatus: true,
      defaultValues: { title: "", slug: "", subtitle: "", description: "", level: "beginner", category: "", duration_hours: "", path: "" },
      fields: [
        { key: "title", label: "Title", type: "text", required: true, first: true },
        { key: "slug", label: "Slug", type: "text" },
        { key: "subtitle", label: "Subtitle", type: "text" },
        { key: "level", label: "Level", type: "select", options: LEVELS },
        { key: "category", label: "Category", type: "text" },
        { key: "duration_hours", label: "Duration (hours)", type: "number" },
        { key: "path", label: "Learning path", type: "select", options: pathOptions, hint: paths.loading ? "Loading paths…" : undefined },
        { key: "description", label: "Description", type: "textarea" },
      ],
      columns: [
        { header: "Title", key: "title" },
        { header: "Level", cell: (row) => <Badge variant="neutral">{row.level ?? "—"}</Badge> },
        { header: "Category", key: "category" },
      ],
    },
    lessons: {
      entity: "lessons",
      singular: "Lesson",
      titleField: "title",
      showStatus: false,
      defaultValues: { title: "", course: "", kind: "text", position: "", estimated_minutes: "", xp: "" },
      fields: [
        { key: "title", label: "Title", type: "text", required: true, first: true },
        { key: "course", label: "Course", type: "select", options: courseOptions, required: true, hint: courses.loading ? "Loading courses…" : undefined },
        { key: "kind", label: "Type", type: "select", options: KINDS },
        { key: "position", label: "Position", type: "number" },
        { key: "estimated_minutes", label: "Estimated minutes", type: "number" },
        { key: "xp", label: "XP awarded", type: "number" },
      ],
      columns: [
        { header: "Title", key: "title" },
        { header: "Type", cell: (row) => <Badge variant="info">{row.kind ?? "text"}</Badge> },
        { header: "Position", cell: (row) => num(row.position) },
        { header: "Course", cell: (row) => (row.course && typeof row.course === "object" ? row.course.title : `#${row.course ?? "—"}`) },
      ],
    },
  };

  const active = configs[tab];

  return (
    <div className="admin-panel">
      <Tabs
        items={[
          { value: "paths", label: "Paths" },
          { value: "courses", label: "Courses" },
          { value: "lessons", label: "Lessons" },
        ]}
        value={tab}
        onChange={setTab}
        ariaLabel="Curriculum sections"
      />
      {/* key remounts the panel so per-entity search + pagination reset on tab switch */}
      <CrudPanel key={tab} {...active} />
    </div>
  );
}
