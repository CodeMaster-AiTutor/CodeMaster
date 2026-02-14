import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import Compiler from "./Compiler";

let navigationSpy: ReturnType<typeof vi.spyOn>;

vi.mock("@/components/layout/AppLayout", () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));
vi.mock("@/components/Terminal", () => ({
  default: () => <div data-testid="compiler-terminal" />,
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

const getTextarea = () =>
  screen.getByPlaceholderText("Type or paste Java code here...") as HTMLTextAreaElement;

beforeEach(() => {
  localStorage.setItem("access_token", "test-token");
  sessionStorage.setItem("compiler:session-id", "test-session");
  navigationSpy = vi.spyOn(window.performance, "getEntriesByType").mockReturnValue([
    { type: "navigate" } as PerformanceNavigationTiming
  ]);
  vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback: FrameRequestCallback) => {
    callback(0);
    return 0;
  });
});

afterEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("Compiler textarea behavior", () => {
  it("accepts uninterrupted multi-character input", async () => {
    render(<Compiler />);
    const textarea = getTextarea();
    const text = "public class Main";
    for (let i = 0; i < text.length; i += 1) {
      fireEvent.change(textarea, { target: { value: text.slice(0, i + 1) } });
    }
    expect(textarea.value).toBe("public class Main");
  });

  it("keeps cursor focus until explicit blur", async () => {
    render(<Compiler />);
    const textarea = getTextarea();
    const user = userEvent.setup();
    textarea.focus();
    textarea.setSelectionRange(0, 0);
    await user.type(textarea, "class A");
    expect(textarea.selectionStart).toBe(textarea.value.length);
    expect(textarea.selectionEnd).toBe(textarea.value.length);
  });

  it("keeps the cursor in view after edits", () => {
    render(<Compiler />);
    const textarea = getTextarea();
    const styleSpy = vi.spyOn(window, "getComputedStyle").mockReturnValue({
      lineHeight: "24px",
      paddingTop: "0px",
      fontSize: "16px",
    } as CSSStyleDeclaration);
    Object.defineProperty(textarea, "clientHeight", { value: 200, configurable: true });
    Object.defineProperty(textarea, "scrollHeight", { value: 2000, configurable: true });
    const initialText = Array.from({ length: 60 }, (_, i) => `Line ${i + 1}`).join("\n");
    fireEvent.change(textarea, { target: { value: initialText } });
    textarea.scrollTop = 0;
    textarea.setSelectionRange(initialText.length, initialText.length);
    fireEvent.change(textarea, { target: { value: `${initialText}\nLine 61` } });
    expect(textarea.scrollTop).toBeGreaterThan(0);
    styleSpy.mockRestore();
  });

  it("avoids unwanted auto-scroll to top", () => {
    render(<Compiler />);
    const textarea = getTextarea();
    const styleSpy = vi.spyOn(window, "getComputedStyle").mockReturnValue({
      lineHeight: "24px",
      paddingTop: "0px",
      fontSize: "16px",
    } as CSSStyleDeclaration);
    Object.defineProperty(textarea, "clientHeight", { value: 200, configurable: true });
    Object.defineProperty(textarea, "scrollHeight", { value: 2000, configurable: true });
    const initialText = Array.from({ length: 80 }, (_, i) => `Row ${i + 1}`).join("\n");
    fireEvent.change(textarea, { target: { value: initialText } });
    textarea.scrollTop = 300;
    fireEvent.scroll(textarea, { target: { scrollTop: 300 } });
    textarea.setSelectionRange(initialText.length, initialText.length);
    fireEvent.change(textarea, { target: { value: `${initialText}\nRow 81` } });
    expect(textarea.scrollTop).not.toBe(0);
    styleSpy.mockRestore();
  });

  it("auto-scrolls to keep the cursor visible on enter", () => {
    render(<Compiler />);
    const textarea = getTextarea();
    const styleSpy = vi.spyOn(window, "getComputedStyle").mockReturnValue({
      lineHeight: "24px",
      paddingTop: "0px",
      fontSize: "16px",
    } as CSSStyleDeclaration);
    Object.defineProperty(textarea, "clientHeight", { value: 200, configurable: true });
    Object.defineProperty(textarea, "scrollHeight", { value: 2000, configurable: true });
    const initialText = Array.from({ length: 200 }, (_, i) => `Line ${i + 1}`).join("\n");
    fireEvent.change(textarea, { target: { value: initialText } });
    textarea.scrollTop = 0;
    textarea.setSelectionRange(initialText.length, initialText.length);
    fireEvent.keyDown(textarea, { key: "Enter" });
    fireEvent.change(textarea, { target: { value: `${initialText}\n` } });
    expect(textarea.scrollTop).toBeGreaterThan(0);
    styleSpy.mockRestore();
  });
});

describe("Compiler persistence", () => {
  it("saves editor state to localStorage after debounce", async () => {
    render(<Compiler />);
    const textarea = getTextarea();
    fireEvent.change(textarea, { target: { value: "class Debounced {}" } });
    await new Promise((resolve) => setTimeout(resolve, 2600));
    const saved = sessionStorage.getItem("compiler:state:test-session");
    expect(saved).not.toBeNull();
    const parsed = JSON.parse(saved ?? "{}") as { code?: string; compressed?: boolean };
    expect(typeof parsed.compressed).toBe("boolean");
    expect(typeof parsed.code).toBe("string");
    if (!parsed.compressed) {
      expect(parsed.code).toBe("class Debounced {}");
    }
    expect(localStorage.getItem("compiler:code-fallback")).toBe("class Debounced {}");
  });

  it("restores editor state from localStorage", async () => {
    localStorage.setItem("compiler:code-fallback", "class Restored {}");
    render(<Compiler />);
    const restored = await screen.findByDisplayValue("class Restored {}");
    expect(restored).toBeTruthy();
  });

  it("clears output on reload navigation", () => {
    sessionStorage.setItem("compiler:output", "Previous output");
    navigationSpy.mockReturnValue([
      { type: "reload" } as PerformanceNavigationTiming
    ]);
    render(<Compiler />);
    expect(screen.getByTestId("compiler-terminal")).toBeTruthy();
  });

  it("clears compiler state via confirmation dialog", async () => {
    render(<Compiler />);
    const textarea = getTextarea();
    const user = userEvent.setup();
    fireEvent.change(textarea, { target: { value: "class ClearMe {}" } });
    const clearButton = screen.getByRole("button", { name: "Clear Compiler" });
    await user.click(clearButton);
    const confirmButton = screen.getByRole("button", { name: "Clear" });
    await user.click(confirmButton);
    expect(textarea.value).toBe("");
    expect(localStorage.getItem("compiler:code-fallback")).toBeNull();
  });
});
