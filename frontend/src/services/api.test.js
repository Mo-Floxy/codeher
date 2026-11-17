import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import { API_BASE, ApiError, api, onUnauthorized, tokenStore } from "./api";

function jsonResponse(status, payload) {
  return {
    status,
    ok: status >= 200 && status < 300,
    headers: new Headers({ "content-type": "application/json" }),
    json: async () => payload,
  };
}

describe("tokenStore", () => {
  it("round-trips a session and clears it", () => {
    tokenStore.set({ access: "a", refresh: "r" });
    expect(tokenStore.access).toBe("a");
    expect(tokenStore.refresh).toBe("r");
    tokenStore.clear();
    expect(tokenStore.access).toBeNull();
  });
});

describe("ApiError", () => {
  it("reports the first message for a field and falls back to detail", () => {
    const error = new ApiError(400, { email: ["Already taken.", "Pick another."], detail: "Check the form." });
    expect(error.messageFor("email")).toBe("Already taken.");
    expect(error.messageFor("unknown")).toBe("Check the form.");
    expect(error.messageFor("detail")).toBe("Check the form.");
  });
});

describe("request", () => {
  beforeEach(() => {
    tokenStore.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("omits blank params and joins arrays into one query value", async () => {
    const fetchMock = vi.fn(async () => jsonResponse(200, { results: [] }));
    vi.stubGlobal("fetch", fetchMock);

    await api.get("/community/posts/", {
      params: { q: "", page: 2, tags: ["react", "css"], hidden: null, missing: undefined },
    });

    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe(`${API_BASE}/community/posts/?page=2&tags=react%2Ccss`);
  });

  it("refreshes once on 401 and replays the request with the new token", async () => {
    tokenStore.set({ access: "stale", refresh: "refresh-1" });
    const calls = [];
    const fetchMock = vi.fn(async (url, init) => {
      calls.push({ url, auth: init.headers.Authorization });
      if (url.endsWith("/auth/token/refresh/")) return jsonResponse(200, { access: "fresh" });
      if (init.headers.Authorization === "Bearer stale") return jsonResponse(401, { detail: "Expired." });
      return jsonResponse(200, { xp: 995 });
    });
    vi.stubGlobal("fetch", fetchMock);

    const data = await api.get("/dashboard/");

    expect(data).toEqual({ xp: 995 });
    expect(calls.map((call) => call.auth)).toEqual(["Bearer stale", undefined, "Bearer fresh"]);
    expect(tokenStore.access).toBe("fresh");
  });

  it("drops the session and notifies listeners when the refresh is refused", async () => {
    tokenStore.set({ access: "stale", refresh: "expired-refresh" });
    const leftSession = vi.fn();
    const stopListening = onUnauthorized(leftSession);
    const fetchMock = vi.fn(async (url) =>
      url.endsWith("/auth/token/refresh/") ? jsonResponse(401, { detail: "Token blacklisted." }) : jsonResponse(401, { detail: "Expired." })
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.get("/dashboard/")).rejects.toThrow(ApiError);

    expect(tokenStore.access).toBeNull();
    expect(tokenStore.refresh).toBeNull();
    expect(leftSession).toHaveBeenCalledTimes(1);
    stopListening();
  });

  it("keeps the current session when a sign-in attempt is rejected", async () => {
    tokenStore.set({ access: "current", refresh: "current-refresh" });
    const leftSession = vi.fn();
    const stopListening = onUnauthorized(leftSession);
    const fetchMock = vi.fn(async () => jsonResponse(401, { detail: "The email or password is incorrect." }));
    vi.stubGlobal("fetch", fetchMock);

    const error = await api.post("/auth/login/", { email: "ada@example.com", password: "wrong" }).catch((caught) => caught);

    expect(error.status).toBe(401);
    expect(error.messageFor("detail")).toBe("The email or password is incorrect.");
    expect(fetchMock.mock.calls.map((call) => call[0])).toEqual([`${API_BASE}/auth/login/`]);
    expect(tokenStore.access).toBe("current");
    expect(leftSession).not.toHaveBeenCalled();
    stopListening();
  });

  it("turns a network failure into a readable message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      })
    );

    const error = await api.get("/site/stats/").catch((caught) => caught);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(0);
    expect(error.detail).toContain("Cannot reach the CodeHer API");
  });
});
