import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// jsdom keeps localStorage between tests; the token store would leak a session.
afterEach(() => {
  cleanup();
  localStorage.clear();
});
