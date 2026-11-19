import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import MemberProfile from "./MemberProfile";

// The payloads below are copied from what the API actually answers, including the
// wrappers that made this page render zeros: `/users/:id/badges/` is an object with a
// `badges` list and a `hidden` flag, and the projects feed is a DRF page.
const state = vi.hoisted(() => ({ badges: {}, projects: {}, profile: {}, calls: [] }));

vi.mock("../../services/api", () => ({
  endpoints: { projects: "/community/projects/" },
  api: {
    get: vi.fn(async (path, options) => {
      state.calls.push({ path, params: options?.params });
      if (path.endsWith("/badges/")) return state.badges;
      if (path === "/community/projects/") return state.projects;
      return state.profile;
    }),
    post: vi.fn(async () => ({ following: true, followers_count: 1 })),
  },
}));

vi.mock("../../context/AuthContext", () => ({
  useAuth: () => ({ user: { id: 1 }, isAuthenticated: true }),
}));

vi.mock("../../context/ToastContext", () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}));

function renderProfile(id = "7") {
  return render(
    <MemoryRouter initialEntries={[`/members/${id}`]}>
      <Routes>
        <Route path="/members/:id" element={<MemberProfile />} />
      </Routes>
    </MemoryRouter>
  );
}

const FIVE_BADGES = {
  badges: [
    { id: 1, title: "First Steps", earned_at: "2026-11-18T09:00:00Z" },
    { id: 2, title: "Quiz Ready", earned_at: "2026-11-18T09:05:00Z" },
    { id: 3, title: "Solved It", earned_at: "2026-11-18T09:10:00Z" },
    { id: 4, title: "Voice Heard", earned_at: "2026-11-18T09:15:00Z" },
    { id: 5, title: "Shipped Something", earned_at: "2026-11-18T09:20:00Z" },
  ],
  count: 5,
  hidden: false,
};

const TWO_PROJECTS = {
  results: [
    { id: 11, title: "Streak Garden", description: "A habit tracker.", technologies: ["React", "Django"] },
    { id: 12, title: "Nurse Roster", description: "Shift planning.", technologies: ["MySQL"] },
  ],
  count: 2,
};

beforeEach(() => {
  state.badges = {};
  state.projects = {};
  state.calls = [];
  state.profile = {
    id: 7,
    user_id: 7,
    display_name: "Ada Lovelace",
    username: "ada",
    badge_count: 5,
    project_count: 2,
    total_xp: 300,
    current_streak: 1,
    followers_count: 0,
    following_count: 0,
  };
});

describe("Member profile", () => {
  it("reads the badge list out of the object the badges endpoint returns", async () => {
    state.badges = FIVE_BADGES;
    state.projects = TWO_PROJECTS;

    const { container } = renderProfile();

    await waitFor(() => expect(container.querySelectorAll(".badge-tile").length).toBe(5));
    expect(screen.getByText("Shipped Something")).toBeInTheDocument();
    expect(screen.getByText("Streak Garden")).toBeInTheDocument();
    expect(screen.getByText("Nurse Roster")).toBeInTheDocument();
  });

  it("asks the projects feed for this member's published work only", async () => {
    state.badges = FIVE_BADGES;
    state.projects = TWO_PROJECTS;

    renderProfile();

    await waitFor(() => expect(state.calls.length).toBeGreaterThan(2));
    const projectsCall = state.calls.find((call) => call.path === "/community/projects/");
    expect(projectsCall.params).toMatchObject({ user: "7", status: "published" });
  });

  it("says Hidden rather than zero when the owner keeps badges private", async () => {
    state.badges = { badges: [], count: 0, hidden: true };
    state.projects = { results: [], count: 0 };
    state.profile = { ...state.profile, badge_count: null };

    renderProfile();

    await waitFor(() => expect(screen.getByText("Hidden")).toBeInTheDocument());
    expect(screen.queryByText("No public badges")).toBeInTheDocument();
  });

  it("names the privacy choice instead of showing an empty project shelf", async () => {
    state.badges = FIVE_BADGES;
    state.projects = { results: [], count: 0 };
    state.profile = { ...state.profile, project_count: null };

    renderProfile();

    await waitFor(() => expect(screen.getByText("Projects kept private")).toBeInTheDocument());
    expect(screen.queryByText("No public projects")).not.toBeInTheDocument();
  });
});
