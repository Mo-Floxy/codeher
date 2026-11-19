import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useReducedMotion } from "framer-motion";
import { Award, BadgeCheck, BookOpen, CalendarDays, GraduationCap, Printer, RefreshCw, ShieldCheck, X } from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync } from "../../hooks";
import { useAuth } from "../../context/AuthContext";
import {
  Alert,
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  IconButton,
  LevelBadge,
  Loading,
  Skeleton,
} from "../../components/ui";
import { Reveal } from "../../components/motion";
import "./learning.css";

function unwrap(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.results ?? [];
}

function formatDate(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
}

function readCourseTitle(record) {
  return record?.course?.title ?? record?.course_title ?? record?.title ?? "CodeHer course";
}

function readSerial(record) {
  return record?.certificate_id ?? record?.serial ?? record?.serial_number ?? record?.certificate_number ?? null;
}

function readIssuedAt(record) {
  return record?.issued_at ?? record?.issued_date ?? record?.completed_at ?? record?.created_at ?? null;
}

function readLearnerName(record, fallback) {
  return (
    record?.learner_name ??
    record?.student_name ??
    record?.recipient_name ??
    record?.learner?.display_name ??
    fallback
  );
}

// `course` is a bare id in this payload and the course facts arrive flat next to it,
// so the nested lookups are the fallback rather than the first choice.
function readCourseLevel(record) {
  return record?.course_level ?? record?.course?.level ?? null;
}

function readCourseHours(record) {
  return record?.duration_hours ?? record?.course?.duration_hours ?? null;
}

function CertificateSheet({ record, learnerName }) {
  const courseLevel = readCourseLevel(record);
  const courseHours = readCourseHours(record);
  return (
    <article className="cert-sheet" aria-label={`Certificate for ${learnerName}`}>
      <div className="cert-sheet__frame">
        <header className="cert-sheet__head">
          <span className="cert-sheet__mark" aria-hidden="true">
            <GraduationCap size={26} />
          </span>
          <span className="cert-sheet__issuer">CodeHer</span>
          <h2 className="cert-sheet__kind">Certificate of Completion</h2>
          <p className="cert-sheet__eyebrow">Technology learning record · codeher.dev</p>
        </header>

        <div className="cert-sheet__body">
          <p className="cert-sheet__lead">This certifies that</p>
          <p className="cert-sheet__name">{learnerName}</p>
          <p className="cert-sheet__lead">has completed every lesson and assessment of the course</p>
          <p className="cert-sheet__course">{readCourseTitle(record)}</p>
          {courseLevel ? (
            <p className="cert-sheet__level">
              <LevelBadge level={courseLevel} /> {courseHours ? `· ${courseHours} hours` : ""}
            </p>
          ) : null}
        </div>

        <footer className="cert-sheet__foot">
          <div className="cert-sheet__cell">
            <span className="cert-sheet__cell-label">Issued</span>
            <strong className="cert-sheet__cell-value">{formatDate(readIssuedAt(record)) ?? "—"}</strong>
          </div>
          <div className="cert-sheet__cell">
            <span className="cert-sheet__cell-label">Certificate ID</span>
            <strong className="cert-sheet__cell-value cert-sheet__serial">{readSerial(record) ?? `CH-${record?.id}`}</strong>
          </div>
          <div className="cert-sheet__cell">
            <span className="cert-sheet__cell-label">Issued by</span>
            <strong className="cert-sheet__cell-value">{record?.issuer ?? "CodeHer Learning Platform"}</strong>
          </div>
          <div className="cert-sheet__cell">
            <span className="cert-sheet__cell-label">Instructor</span>
            <strong className="cert-sheet__cell-value">
              {record?.instructor_name ?? record?.course?.instructor?.display_name ?? "—"}
            </strong>
          </div>
        </footer>

        <p className="cert-sheet__verify">
          <ShieldCheck size={13} aria-hidden="true" /> Verification: progress and completion for this record are
          stored against the learner account on the CodeHer platform.
        </p>
      </div>
    </article>
  );
}

function PrintPanel({ open, record, learnerName, loading, error, onClose }) {
  const panelRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    document.documentElement.classList.add("ch-printing");
    const onKeyDown = (event) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    panelRef.current?.focus();
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.documentElement.classList.remove("ch-printing");
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  const serial = readSerial(record);

  return createPortal(
    <div className="cert-print-root" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <div className="cert-print" role="dialog" aria-modal="true" aria-label="Certificate preview" tabIndex={-1} ref={panelRef}>
        <div className="cert-print__bar no-print">
          <strong className="cert-print__title">
            <Award size={17} aria-hidden="true" /> {readCourseTitle(record)}
          </strong>
          <div className="row" style={{ gap: "var(--sp-2)" }}>
            <Button size="sm" onClick={() => window.print()} disabled={loading}>
              <Printer size={15} /> Print / save as PDF
            </Button>
            <IconButton size="sm" variant="ghost" label="Close certificate preview" onClick={onClose}>
              <X size={17} />
            </IconButton>
          </div>
        </div>

        <p className="cert-print__hint no-print">
          In the print dialog choose “Save as PDF” and A4 landscape for a shareable copy. The page is formatted
          for one landscape sheet.
        </p>

        {loading ? (
          <div className="cert-print__loading">
            <Loading label="Loading the certificate" />
          </div>
        ) : error ? (
          <div className="cert-print__error">
            <Alert variant="error" title="The full certificate could not be fetched">
              {error.detail || error.message} The summary below uses the data already on your certificates page.
            </Alert>
            <CertificateSheet record={record} learnerName={learnerName} />
          </div>
        ) : (
          <CertificateSheet record={record} learnerName={learnerName} />
        )}

        <p className="cert-print__serial no-print">
          {serial ? `Certificate ID ${serial}` : "No serial number published for this record."}
        </p>
      </div>
    </div>,
    document.body
  );
}

export default function Certificates() {
  const { user } = useAuth();
  const reduce = useReducedMotion();
  const [selected, setSelected] = useState(null);

  const list = useAsync((signal) => api.get(endpoints.certificates, { signal, params: { page_size: 50 } }), []);
  const rows = useMemo(() => unwrap(list.data), [list.data]);

  const detail = useAsync(
    (signal) => api.get(`/learning/me/certificates/${selected.id}/`, { signal }),
    [selected?.id],
    { skip: !selected?.id }
  );

  const merged = detail.data ? { ...selected, ...detail.data } : selected;
  const learnerName = readLearnerName(merged, user?.display_name || user?.username || "CodeHer learner");

  return (
    <div className="container cert">
      <header className="section-head">
        <span className="eyebrow">Achievements</span>
        <h1>Your certificates</h1>
        <p className="lead">
          One certificate is issued per completed course, with a serial you can quote on a CV or LinkedIn.
          Open one to preview it and save it as a PDF.
        </p>
        <div className="row">
          <Button variant="ghost" size="sm" onClick={list.reload} disabled={list.loading}>
            <RefreshCw size={15} /> Refresh
          </Button>
          <Button variant="link" size="sm" to="/learning">
            <BookOpen size={15} /> Finish another course
          </Button>
        </div>
      </header>

      {list.loading && !list.data ? (
        <div className="grid-auto">
          {[0, 1, 2].map((key) => (
            <Skeleton key={key} className="skeleton--card" style={{ height: 210 }} />
          ))}
        </div>
      ) : list.error ? (
        <ErrorState error={list.error} onRetry={list.reload} title="Your certificates could not be loaded" />
      ) : rows.length === 0 ? (
        <EmptyState
          icon={Award}
          title="No certificates yet"
          description="Complete every lesson in a course and CodeHer issues its certificate automatically. Your first one will show up here."
          action={
            <Button to="/learning">
              Browse the catalog <BookOpen size={16} />
            </Button>
          }
        />
      ) : (
        <>
          <p className="muted cert__count" aria-live="polite">
            {rows.length} certificate{rows.length === 1 ? "" : "s"} issued to {learnerName}
          </p>
          <div className="grid-auto cert__grid">
            {rows.map((record, index) => (
              <Reveal key={record.id ?? index} className="cert-cell" delay={index * 0.05} y={reduce ? 0 : 18}>
                <Card className="cert-card">
                  <div className="cert-card__seal">
                    <BadgeCheck size={22} aria-hidden="true" />
                  </div>
                  <h2 className="cert-card__course">{readCourseTitle(record)}</h2>
                  <div className="cert-card__meta">
                    <LevelBadge level={readCourseLevel(record)} />
                    <span className="muted">
                      <CalendarDays size={13} aria-hidden="true" /> {formatDate(readIssuedAt(record)) ?? "Date pending"}
                    </span>
                  </div>
                  <dl className="cert-card__serial">
                    <dt>Certificate ID</dt>
                    <dd>
                      <code>{readSerial(record) ?? `CH-${record.id}`}</code>
                    </dd>
                  </dl>
                  <Button
                    size="sm"
                    onClick={() => setSelected(record)}
                    aria-haspopup="dialog"
                    disabled={record.is_revoked}
                  >
                    <Printer size={15} /> View / print
                  </Button>
                  {record.is_revoked && <Badge variant="danger">Revoked</Badge>}
                </Card>
              </Reveal>
            ))}
          </div>
        </>
      )}

      <PrintPanel
        open={Boolean(selected)}
        record={merged ?? selected}
        learnerName={learnerName}
        loading={detail.loading && !detail.data}
        error={detail.error}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}
