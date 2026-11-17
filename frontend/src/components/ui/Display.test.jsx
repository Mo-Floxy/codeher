import { render } from "@testing-library/react";
import { Avatar } from "./index";

// hash32 returns an unsigned 32-bit value, so roughly half of all seeds land above
// 2**31. Reading those bits with a signed shift made the palette index negative, which
// looked up AVATAR_ANCHORS[-1] and threw before the page painted anything.
const SEEDS = ["1", "7", "42", "318", "9001", "2147483647", "2147483648", "4294967295", "amara", "nina.k"];

describe("Avatar artwork", () => {
  it.each(SEEDS)("paints a whole avatar for member id %s", (id) => {
    const { container } = render(<Avatar user={{ id, display_name: "Ada Lovelace" }} />);
    const art = container.querySelector("svg.avatar__art");
    expect(art).not.toBeNull();
    expect(art.getAttribute("aria-label")).toBe("Ada Lovelace avatar");

    const circles = [...art.querySelectorAll("circle")];
    expect(circles).toHaveLength(3);
    for (const circle of circles) {
      for (const attribute of ["cx", "cy", "r"]) {
        expect(Number(circle.getAttribute(attribute))).toBeGreaterThanOrEqual(0);
      }
    }
    const ring = circles[2];
    expect(Number(ring.getAttribute("stroke-width"))).toBeGreaterThan(0);
  });

  it("uses the photo when the member has uploaded one", () => {
    const { container } = render(<Avatar user={{ id: 3, display_name: "Ada", avatar: "/media/avatars/ad.png" }} />);
    expect(container.querySelector("img")).toHaveAttribute("src", "/media/avatars/ad.png");
    expect(container.querySelector("svg.avatar__art")).toBeNull();
  });
});
