import { render, screen, waitFor } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Certificates from "./Certificates";

// CertificateSerializer sends the course as a bare id and the course facts flat next to
// it (`course_level`, `duration_hours`, `instructor_name`). The page once looked only for
// the nested ones, so printed certificates quietly lost their level and hours line.
const state = vi.hoisted(() => ({ list: {}, detail: null }));

vi.mock("../../services/api", () => ({
  endpoints: { certificates: "/learning/me/certificates/" },
  api: {
    get: vi.fn(async (path) => (path === "/learning/me/certificates/" ? state.list : state.detail)),
  },
}));

vi.mock("../../context/AuthContext", () => ({
  useAuth: () => ({ user: { id: 9, display_name: "UI Sweep Tester", username: "sweeptest" } }),
}));

const RECORD = {
  id: 4,
  course: 1,
  course_title: "Semantic HTML: Pages That Make Sense",
  course_slug: "semantic-html",
  course_level: "beginner",
  duration_hours: 6,
  instructor_name: "Grace Okafor",
  serial: "CH-2026-ABC123",
  learner_name: "UI Sweep Tester",
  issued_at: "2026-11-19T10:00:00Z",
  hours_studied: 6,
  final_percent: 100,
};

beforeEach(() => {
  state.list = { results: [RECORD], count: 1 };
  state.detail = RECORD;
});

function renderPage() {
  return render(
    <MemoryRouter>
      <Certificates />
    </MemoryRouter>
  );
}

describe("Certificates", () => {
  it("shows the course level on the card from the flat payload field", async () => {
    const { container } = renderPage();

    await waitFor(() => expect(container.querySelectorAll(".cert-card").length).toBe(1));
    expect(screen.getByText("Semantic HTML: Pages That Make Sense")).toBeInTheDocument();
    expect(screen.getByText(/beginner/i)).toBeInTheDocument();
    expect(screen.getByText("CH-2026-ABC123")).toBeInTheDocument();
  });

  it("prints the level and hours line on the certificate sheet", async () => {
    const { container } = renderPage();

    await waitFor(() => expect(container.querySelectorAll(".cert-card").length).toBe(1));
    await userEvent.click(screen.getByRole("button", { name: /view \/ print/i }));

    const line = await waitFor(() => {
      const found = document.querySelector(".cert-sheet__level");
      if (!found) throw new Error("no level line");
      return found;
    });
    expect(line.textContent).toContain("beginner");
    expect(line.textContent).toContain("6 hours");
    expect(screen.getByText("Grace Okafor")).toBeInTheDocument();
  });
});
