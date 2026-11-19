import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

// jsdom has no IntersectionObserver, and framer-motion's whileInView (used by every
// revealed card) constructs one during its mount effect. Without it the effect throws
// and React tears the whole tree down mid-test, so page tests see an empty document
// rather than the component they rendered. Reporting as intersecting is what a real
// viewport does for the content a test asserts on.
class IntersectionObserverStub {
  constructor(callback) {
    this.callback = callback;
  }

  observe(target) {
    this.callback([{ target, isIntersecting: true, intersectionRatio: 1 }], this);
  }

  unobserve() {}

  disconnect() {}

  takeRecords() {
    return [];
  }
}

vi.stubGlobal("IntersectionObserver", IntersectionObserverStub);
vi.stubGlobal("ResizeObserver", class ResizeObserverStub {
  observe() {}

  unobserve() {}

  disconnect() {}
});

// jsdom keeps localStorage between tests; the token store would leak a session.
afterEach(() => {
  cleanup();
  localStorage.clear();
});
