import React, { useEffect, useMemo, useRef } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import { cn } from '@/lib/utils';

const resolveWebSocketUrl = (providedUrl) => {
  if (providedUrl === '') {
    return '';
  }
  const envUrl = typeof import.meta !== 'undefined' ? import.meta.env?.VITE_TERMINAL_WS_URL : undefined;
  let url = providedUrl ?? envUrl;
  if (!url && typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    url = `${protocol}://${window.location.host}/ws/terminal`;
  }
  if (!url) {
    return '';
  }
  try {
    const parsed = new URL(url);
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (token) {
      parsed.searchParams.set('token', token);
    }
    return parsed.toString();
  } catch {
    return url;
  }
};

const TerminalComponent = ({ className, wsUrl, output, dataTestId }) => {
  const containerRef = useRef(null);
  const terminalRef = useRef(null);
  const fitRef = useRef(null);
  const socketRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const isUnmountingRef = useRef(false);
  const disableReconnectRef = useRef(false);
  const lastOutputRef = useRef('');

  const resolvedUrl = useMemo(() => resolveWebSocketUrl(wsUrl), [wsUrl]);

  useEffect(() => {
    if (!containerRef.current || terminalRef.current) {
      return;
    }
    const term = new Terminal({
      convertEol: true,
      cursorBlink: true,
      fontFamily: 'JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
      fontSize: 12,
      theme: {
        background: 'transparent'
      }
    });
    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(containerRef.current);
    fitAddon.fit();
    terminalRef.current = term;
    fitRef.current = fitAddon;

    if (output) {
      term.write(output);
      lastOutputRef.current = output;
    }

    const resizeObserver = typeof ResizeObserver !== 'undefined'
      ? new ResizeObserver(() => {
          fitAddon.fit();
        })
      : null;
    if (resizeObserver) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
      term.dispose();
      terminalRef.current = null;
      fitRef.current = null;
    };
  }, [output]);

  useEffect(() => {
    if (!terminalRef.current) {
      return;
    }
    if (!output) {
      terminalRef.current.clear();
      lastOutputRef.current = '';
      return;
    }
    if (output === lastOutputRef.current) {
      return;
    }
    if (output.startsWith(lastOutputRef.current)) {
      const delta = output.slice(lastOutputRef.current.length);
      terminalRef.current.write(delta);
      lastOutputRef.current = output;
      return;
    }
    terminalRef.current.write(output);
    lastOutputRef.current = output;
  }, [output]);

  useEffect(() => {
    if (!resolvedUrl) {
      console.log('[Terminal] No wsUrl provided');
      return;
    }
    if (!terminalRef.current) {
      console.log('[Terminal] Terminal ref not ready');
      return;
    }
    isUnmountingRef.current = false;
    disableReconnectRef.current = false;
    const decoder = new TextDecoder('utf-8');
    const maskedUrl = resolvedUrl.replace(/token=[^&]+/, 'token=***');
    console.log('[Terminal] Connecting to WebSocket:', {
      wsUrl: resolvedUrl,
      fullUrl: maskedUrl
    });

    const connect = () => {
      if (isUnmountingRef.current) {
        return;
      }
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      const socket = new WebSocket(resolvedUrl);
      socket.binaryType = 'arraybuffer';
      socketRef.current = socket;

      socket.onopen = () => {
        console.log('[Terminal] ✅ WebSocket OPENED');
      };

      const handleData = terminalRef.current.onData((data) => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(data);
        }
      });

      socket.onmessage = (event) => {
        if (!terminalRef.current) {
          console.warn('[Terminal] Terminal ref not ready');
          return;
        }
        if (typeof event.data === 'string') {
          const preview = event.data.slice(0, 100);
          console.log('[Terminal] 📨 Received:', preview);
          if (
            event.data === 'Missing sessionId' ||
            event.data === 'Session invalid' ||
            event.data === 'Unauthorized' ||
            event.data === 'Unable to attach to session'
          ) {
            console.error('[Terminal] ❌ Backend error:', event.data);
            disableReconnectRef.current = true;
          }
          if (event.data.includes('Session not found') || event.data.includes('Unauthorized') || event.data.includes('Session invalid')) {
            disableReconnectRef.current = true;
          }
          if (!event.data.includes('Session invalid')) {
             terminalRef.current.write(event.data);
          }
        } else if (event.data instanceof ArrayBuffer) {
          terminalRef.current.write(decoder.decode(event.data));
        } else if (event.data instanceof Blob) {
          event.data.arrayBuffer().then((buffer) => {
            if (terminalRef.current) {
              terminalRef.current.write(decoder.decode(buffer));
            }
          }).catch(() => void 0);
        }
      };

      socket.onclose = () => {
        console.log('[Terminal] 🔌 WebSocket CLOSED');
        handleData.dispose();
        if (isUnmountingRef.current || disableReconnectRef.current) {
          return;
        }
        reconnectAttemptsRef.current += 1;
        const delay = Math.min(1000 * 2 ** reconnectAttemptsRef.current, 10000);
        reconnectTimerRef.current = window.setTimeout(() => {
          connect();
        }, delay);
      };

      socket.onerror = () => {
        console.error('[Terminal] ❌ WebSocket ERROR');
        socket.close();
      };
    };

    connect();

    return () => {
      isUnmountingRef.current = true;
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.close();
      }
      socketRef.current = null;
      reconnectAttemptsRef.current = 0;
    };
  }, [resolvedUrl]);

  return (
    <div className={cn("h-full w-full", className)} data-testid={dataTestId}>
      <div ref={containerRef} className="h-full w-full" />
    </div>
  );
};

export default TerminalComponent;
