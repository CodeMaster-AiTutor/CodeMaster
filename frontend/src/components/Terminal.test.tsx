import React from "react";
import { render } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import Terminal from "./Terminal";

vi.mock("xterm", () => {
  class MockTerminal {
    loadAddon = vi.fn();
    open = vi.fn();
    write = vi.fn();
    dispose = vi.fn();
    onData = vi.fn(() => ({ dispose: vi.fn() }));
  }
  return { Terminal: MockTerminal };
});

vi.mock("xterm-addon-fit", () => {
  class MockFitAddon {
    fit = vi.fn();
  }
  return { FitAddon: MockFitAddon };
});

describe("Terminal component", () => {
  const originalWebSocket = global.WebSocket;
  const sockets = [];

  beforeEach(() => {
    sockets.length = 0;
    class MockWebSocket {
      static OPEN = 1;
      readyState = MockWebSocket.OPEN;
      url;
      onmessage = null;
      onclose = null;
      onerror = null;
      constructor(url) {
        this.url = url;
        sockets.push(this);
      }
      send = vi.fn();
      close = vi.fn(() => {
        if (this.onclose) {
          this.onclose();
        }
      });
    }
    global.WebSocket = MockWebSocket;
  });

  afterEach(() => {
    global.WebSocket = originalWebSocket;
  });

  it("creates a WebSocket connection and renders container", () => {
    const { getByTestId, unmount } = render(
      <Terminal wsUrl="ws://localhost:5000/ws/terminal" dataTestId="terminal" />
    );
    expect(getByTestId("terminal")).toBeTruthy();
    expect(sockets.length).toBe(1);
    expect(sockets[0].url).toBe("ws://localhost:5000/ws/terminal");
    unmount();
  });
});
