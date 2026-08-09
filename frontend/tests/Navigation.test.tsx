// @vitest-environment jsdom

import { act } from "react"
import { createRoot, type Root } from "react-dom/client";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
;
import Header from "@/components/Header";
import { NAV_ITEMS } from "@/utils/constants";

vi.mock("@/components/ProfileSwitcher", () => ({
  default: () => null
}));

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

describe("Navigation", () => {
  let container: HTMLDivElement;
  let root: Root;

  const renderNavigation = async () => {
    await act(async () => {
      root.render(
        <MemoryRouter initialEntries={["/"]}>
          <Header />

          <Routes>
            <Route path="/" element={<div>Session</div>} />
            <Route path="/profiles" element={<div>Profiles</div>} />
            <Route path="/library" element={<div>Library</div>} />
            <Route path="/calibrate" element={<div>Calibrate</div>} />
            <Route path="/settings" element={<div>Settings</div>} />
          </Routes>
        </MemoryRouter>
      );
    });
  }

  const findNavLink = (label: string) =>
    Array.from(container.querySelectorAll("a")).find(
      (link) => link.textContent?.trim() === label
    );

  beforeEach(async () => {
    container = document.createElement("div");
    document.body.append(container);
    root = createRoot(container);

    await renderNavigation();
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
  });

  it("renders all navigation tabs", () => {
    for (const item of NAV_ITEMS) {
      expect(findNavLink(item.label)).toBeDefined();
    }
  });
  
  it("start in session page", () => {
    const sessionLink = findNavLink("Session");
    expect(sessionLink).toBeDefined();
    expect(sessionLink?.getAttribute("aria-current")).toBe("page");
  });

  it("navigates through tabs", async () => {
    const profilesLink = findNavLink("Profiles");
    const libraryLink = findNavLink("Library");
    const calibrationLink = findNavLink("Calibration");
    const settingsLink = findNavLink("Settings");
    const sessionLink = findNavLink("Session");

    await act(async () => {
      profilesLink?.click();
    });
    expect(container.textContent).toContain("Profiles")

    await act(async () => {
      libraryLink?.click();
    });
    expect(container.textContent).toContain("Library")

    await act(async () => {
      calibrationLink?.click();
    });
    expect(container.textContent).toContain("Calibrate")

    await act(async () => {
      settingsLink?.click();
    });
    expect(container.textContent).toContain("Settings")

    await act(async () => {
      sessionLink?.click();
    });
    expect(container.textContent).toContain("Session")
  });

  it("updates active tab when navigating", async () => {
    const sessionLink = findNavLink("Session");
    const profilesLink = findNavLink("Profiles");

    expect(sessionLink?.getAttribute("aria-current")).toBe("page");
    expect(profilesLink?.getAttribute("aria-current")).toBeNull();

    await act(async () => {
      profilesLink?.click();
    });

    expect(profilesLink?.getAttribute("aria-current")).toBe("page");
    expect(sessionLink?.getAttribute("aria-current")).toBeNull();
  });
})
