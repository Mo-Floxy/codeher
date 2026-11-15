import { useState } from "react";
import { Pencil, Plus, Trash2 } from "lucide-react";
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
} from "../../components/ui";
import { asList, num } from "../app/helpers";
import "./admin.css";

const DIFFICULTY = [
  { value: "easy", label: "Easy" },
  { value: "medium", label: "Medium" },
  { value: "hard", label: "Hard" },
];

const DIFFICULTY_VARIANT = { easy: "success", medium: "warning", hard: "danger" };

const DEFAULT_FORM = {
  title: "",
  function_name: "",
  difficulty: "easy",
  category: "",
  points: "10",
  javascript: "",
  python: "",
  tests: "[]",
};

function openFormFor(row) {
  const starter = row.starter_code ?? {};
  const tests = row.test_cases ?? row.tests ?? [];
  return {
    title: row.title ?? "",
    function_name: row.function_name ?? "",
    difficulty: row.difficulty ?? "easy",
    category: row.category ?? "",
    points: String(row.points ?? ""),
    javascript: starter.javascript ?? row.starter_code_javascript ?? "",
    python: starter.python ?? row.starter_code_python ?? "",
    tests: JSON.stringify(Array.isArray(tests) ? tests : [], null, 2),
  };
}

function validateTestCases(text) {
  if (text.trim() === "" || text.trim() === "[]") return "";
  try {
    const parsed = JSON.parse(text);
    if (!Array.isArray(parsed)) return "Test cases must be a JSON array.";
    return "";
  } catch {
    return "Invalid JSON — check commas, quotes and brackets.";
  }
}

export default function AdminChallenges() {
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const debounced = useDebouncedValue(search, 300);

  const { data, loading, error, reload } = useAsync(
    (signal) => api.get("/admin/challenges/", { signal, params: { search: debounced || undefined, page, page_size: 10 } }),
    [debounced, page]
  );

  const rows = asList(data);
  const count = data?.count ?? rows.length;
  const pageSize = data?.page_size ?? 10;

  const [modal, setModal] = useState({ open: false, mode: "create", row: null });
  const [form, setForm] = useState(DEFAULT_FORM);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [toDelete, setToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const set = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));

  const openNew = () => {
    setForm(DEFAULT_FORM);
    setErrors({});
    setModal({ open: true, mode: "create", row: null });
  };
  const openEdit = (row) => {
    setForm(openFormFor(row));
    setErrors({});
    setModal({ open: true, mode: "edit", row });
  };
  const closeModal = () => setModal({ open: false, mode: "create", row: null });

  const validate = () => {
    const next = {};
    if (!form.title.trim()) next.title = "Title is required.";
    if (String(form.points).trim() === "" || Number.isNaN(Number(form.points))) next.points = "Points must be a number.";
    const testsError = validateTestCases(form.tests);
    if (testsError) next.tests = testsError;
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = async () => {
    if (!validate()) return;
    setSaving(true);
    try {
      let parsedTests = [];
      try {
        parsedTests = form.tests.trim() ? JSON.parse(form.tests) : [];
      } catch {
        parsedTests = [];
      }
      const payload = {
        title: form.title.trim(),
        function_name: form.function_name.trim() || undefined,
        difficulty: form.difficulty,
        category: form.category.trim() || undefined,
        points: Number(form.points),
        starter_code: { javascript: form.javascript, python: form.python },
        test_cases: parsedTests,
      };
      if (modal.mode === "edit" && modal.row?.id != null) {
        await api.patch(`/admin/challenges/${modal.row.id}/`, payload);
        toast.success("Challenge updated.");
      } else {
        await api.post("/admin/challenges/", payload);
        toast.success("Challenge created.");
      }
      closeModal();
      reload();
    } catch (err) {
      setErrors(err?.fieldErrors ?? {});
      toast.error(err?.detail || "Could not save this challenge.");
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!toDelete) return;
    setDeleting(true);
    try {
      await api.del(`/admin/challenges/${toDelete.id}/`);
      toast.success("Challenge deleted.");
      setToDelete(null);
      reload();
    } catch (err) {
      toast.error(err?.detail || "Could not delete this challenge.");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="admin-panel">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
        <h2 style={{ fontSize: "var(--fs-lg)" }}>Challenges</h2>
        <Button size="sm" onClick={openNew}>
          <Plus size={15} aria-hidden="true" /> New challenge
        </Button>
      </div>

      <div className="admin-toolbar">
        <div className="admin-toolbar__grow">
          <SearchInput label="Search challenges" value={search} onChange={(value) => { setSearch(value); setPage(1); }} placeholder="Search challenges…" />
        </div>
      </div>

      {loading ? <Skeleton style={{ height: 240 }} /> : null}
      {!loading && error ? <ErrorState error={error} onRetry={reload} title="Could not load challenges" /> : null}
      {!loading && !error && rows.length === 0 ? (
        <EmptyState icon={Plus} title="No challenges yet" description="Add your first coding challenge to the sandbox." action={<Button onClick={openNew}>New challenge</Button>} />
      ) : null}

      {!loading && !error && rows.length > 0 ? (
        <>
          <div className="table-wrap">
            <table className="table">
              <caption className="sr-only">Coding challenges with difficulty, category and points.</caption>
              <thead>
                <tr>
                  <th scope="col">Title</th>
                  <th scope="col">Difficulty</th>
                  <th scope="col">Category</th>
                  <th scope="col">Points</th>
                  <th scope="col"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={row.id ?? index}>
                    <td>{row.title}</td>
                    <td>
                      <Badge variant={DIFFICULTY_VARIANT[row.difficulty] ?? "neutral"}>{row.difficulty ?? "—"}</Badge>
                    </td>
                    <td>{row.category ?? "—"}</td>
                    <td>{num(row.points)}</td>
                    <td>
                      <div className="admin-cell__actions">
                        <IconButton label={`Edit ${row.title}`} variant="ghost" onClick={() => openEdit(row)}>
                          <Pencil size={15} />
                        </IconButton>
                        <IconButton label={`Delete ${row.title}`} variant="ghost" onClick={() => setToDelete(row)}>
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
        wide
        title={`${modal.mode === "edit" ? "Edit" : "New"} challenge`}
        footer={
          <>
            <Button variant="ghost" onClick={closeModal} disabled={saving}>Cancel</Button>
            <Button onClick={submit} loading={saving}>{modal.mode === "edit" ? "Save changes" : "Create"}</Button>
          </>
        }
      >
        <div className="admin-modal-form">
          <div className="form-grid">
            <Field label="Title" error={errors.title?.[0]} required htmlFor="ch-title">
              <Input id="ch-title" value={form.title} onChange={set("title")} data-autofocus error={errors.title?.[0]} />
            </Field>
            <Field label="Function name" error={errors.function_name?.[0]} hint="The entry point the runner calls." htmlFor="ch-fn">
              <Input id="ch-fn" value={form.function_name} onChange={set("function_name")} error={errors.function_name?.[0]} />
            </Field>
            <Field label="Difficulty" error={errors.difficulty?.[0]} htmlFor="ch-diff">
              <Select id="ch-diff" options={DIFFICULTY} value={form.difficulty} onChange={set("difficulty")} />
            </Field>
            <Field label="Category" error={errors.category?.[0]} htmlFor="ch-cat">
              <Input id="ch-cat" value={form.category} onChange={set("category")} error={errors.category?.[0]} />
            </Field>
            <Field label="Points" error={errors.points?.[0]} required htmlFor="ch-points">
              <Input id="ch-points" type="number" inputMode="numeric" value={form.points} onChange={set("points")} error={errors.points?.[0]} />
            </Field>
          </div>

          <Field label="Starter code — JavaScript" hint="Pre-filled in the editor for learners." htmlFor="ch-js">
            <textarea id="ch-js" className="code-input" value={form.javascript} onChange={set("javascript")} spellCheck={false} />
          </Field>
          <Field label="Starter code — Python" htmlFor="ch-py">
            <textarea id="ch-py" className="code-input" value={form.python} onChange={set("python")} spellCheck={false} />
          </Field>
          <Field label="Test cases (JSON)" error={errors.test_cases?.[0] ?? errors.tests?.[0]} hint="An array of { name, input, expected } objects. Validated before saving." htmlFor="ch-tests">
            <textarea id="ch-tests" className="code-input" value={form.tests} onChange={set("tests")} spellCheck={false} />
          </Field>
        </div>
      </Modal>

      <ConfirmDialog
        open={Boolean(toDelete)}
        onClose={() => setToDelete(null)}
        onConfirm={remove}
        busy={deleting}
        variant="danger"
        confirmLabel="Delete"
        title="Delete this challenge?"
        message={`“${toDelete?.title ?? ""}” will be removed. This cannot be undone.`}
      />
    </div>
  );
}
