import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { 
  Play, 
  Copy, 
  Download, 
  Maximize2,
  Minimize2,
  Terminal as TerminalIcon,
  Code2,
  Trash2,
  Loader2
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import AppLayout from '@/components/layout/AppLayout';
import { compilerAPI } from '@/lib/api';
import Terminal from '@/components/Terminal';
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction
} from '@/components/ui/alert-dialog';

// Separate LineNumbers component that works independently
const LineNumbers = ({ textareaRef, lineNumbersRef }: { 
  textareaRef: React.RefObject<HTMLTextAreaElement>, 
  lineNumbersRef: React.RefObject<HTMLPreElement> 
}) => {
  const [lineNumbers, setLineNumbers] = useState('1');

  useEffect(() => {
    const updateLineNumbers = () => {
      if (textareaRef.current) {
        const content = textareaRef.current.value;
        const lines = content.split('\n');
        const numbers = lines.map((_, i) => i + 1).join('\n');
        setLineNumbers(numbers);
      }
    };

    const textarea = textareaRef.current;
    if (textarea) {
      // Initial update
      updateLineNumbers();

      // Add event listeners for real-time updates
      textarea.addEventListener('input', updateLineNumbers);
      textarea.addEventListener('paste', updateLineNumbers);
      textarea.addEventListener('keydown', updateLineNumbers);

      return () => {
        textarea.removeEventListener('input', updateLineNumbers);
        textarea.removeEventListener('paste', updateLineNumbers);
        textarea.removeEventListener('keydown', updateLineNumbers);
      };
    }
  }, [textareaRef]);

  return (
    <pre
      ref={lineNumbersRef}
      className="absolute left-0 top-0 w-12 h-full text-right pr-2 pt-3 text-sm text-muted-foreground/60 font-mono leading-6 select-none pointer-events-none overflow-hidden bg-muted/20 border-r border-border/50"
      style={{ lineHeight: '1.5rem' }}
    >
      {lineNumbers}
    </pre>
  );
};

const COMPILER_SESSION_KEY = 'compiler:session-id';
const COMPILER_STATE_PREFIX = 'compiler:state:';
const COMPILER_OUTPUT_KEY = 'compiler:output';
const COMPILER_FALLBACK_KEY = 'compiler:code-fallback';
const COMPILER_STATE_TTL_MS = 1000 * 60 * 60 * 24 * 7;
const SAVE_DEBOUNCE_MS = 2500;

type CompilerState = {
  version: 1;
  code: string;
  selection: { start: number; end: number };
  scrollTop: number;
  updatedAt: number;
  compressed: boolean;
  sessionId: string;
};

const getSessionId = () => {
  const existing = sessionStorage.getItem(COMPILER_SESSION_KEY);
  if (existing) {
    return existing;
  }
  const id = typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  sessionStorage.setItem(COMPILER_SESSION_KEY, id);
  return id;
};

const getCompilerStateKey = (sessionId: string) => `${COMPILER_STATE_PREFIX}${sessionId}`;

const uint8ToBase64 = (bytes: Uint8Array) => {
  let binary = '';
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }
  return btoa(binary);
};

const base64ToUint8 = (value: string) => {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
};

const compressString = async (value: string) => {
  if (typeof CompressionStream === 'undefined' || typeof DecompressionStream === 'undefined') {
    return { value, compressed: false };
  }
  const encoder = new TextEncoder();
  const stream = new CompressionStream('gzip');
  const writer = stream.writable.getWriter();
  writer.write(encoder.encode(value));
  await writer.close();
  const buffer = await new Response(stream.readable).arrayBuffer();
  return { value: uint8ToBase64(new Uint8Array(buffer)), compressed: true };
};

const decompressString = async (value: string, compressed: boolean) => {
  if (!compressed) {
    return value;
  }
  if (typeof CompressionStream === 'undefined' || typeof DecompressionStream === 'undefined') {
    return value;
  }
  const bytes = base64ToUint8(value);
  const stream = new DecompressionStream('gzip');
  const writer = stream.writable.getWriter();
  writer.write(bytes);
  await writer.close();
  const buffer = await new Response(stream.readable).arrayBuffer();
  return new TextDecoder().decode(buffer);
};

const saveCompilerState = async (
  state: Omit<CompilerState, 'version' | 'compressed' | 'updatedAt'>
) => {
  const { value, compressed } = await compressString(state.code);
  const payload: CompilerState = {
    version: 1,
    code: value,
    selection: state.selection,
    scrollTop: state.scrollTop,
    updatedAt: Date.now(),
    compressed,
    sessionId: state.sessionId
  };
  try {
    sessionStorage.setItem(getCompilerStateKey(state.sessionId), JSON.stringify(payload));
  } catch {
    void 0;
  }
  try {
    localStorage.setItem(COMPILER_FALLBACK_KEY, state.code);
  } catch {
    void 0;
  }
};

const loadCompilerState = async (sessionId: string) => {
  const key = getCompilerStateKey(sessionId);
  let raw: string | null = null;
  try {
    raw = sessionStorage.getItem(key);
  } catch {
    raw = null;
  }
  if (!raw) {
    let legacy: string | null = null;
    try {
      legacy = localStorage.getItem('compiler:code');
    } catch {
      legacy = null;
    }
    if (legacy !== null) {
      try {
        localStorage.removeItem('compiler:code');
      } catch {
        void 0;
      }
      return {
        version: 1,
        code: legacy,
        selection: { start: legacy.length, end: legacy.length },
        scrollTop: 0,
        updatedAt: Date.now(),
        compressed: false,
        sessionId
      } as CompilerState;
    }
    let fallback: string | null = null;
    try {
      fallback = localStorage.getItem(COMPILER_FALLBACK_KEY);
    } catch {
      fallback = null;
    }
    if (fallback !== null) {
      return {
        version: 1,
        code: fallback,
        selection: { start: fallback.length, end: fallback.length },
        scrollTop: 0,
        updatedAt: Date.now(),
        compressed: false,
        sessionId
      } as CompilerState;
    }
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as CompilerState;
    if (!parsed || parsed.version !== 1 || typeof parsed.code !== 'string') {
      try {
        sessionStorage.removeItem(key);
      } catch {
        void 0;
      }
      return null;
    }
    const now = Date.now();
    if (now - parsed.updatedAt > COMPILER_STATE_TTL_MS) {
      try {
        sessionStorage.removeItem(key);
      } catch {
        void 0;
      }
      return null;
    }
    const code = await decompressString(parsed.code, parsed.compressed);
    return {
      ...parsed,
      code,
      selection: parsed.selection ?? { start: code.length, end: code.length },
      scrollTop: parsed.scrollTop ?? 0,
      sessionId
    };
  } catch {
    try {
      sessionStorage.removeItem(key);
    } catch {
      void 0;
    }
    return null;
  }
};

const clearCompilerState = () => {
  const keys = Object.keys(sessionStorage);
  keys.forEach((key) => {
    if (key.startsWith(COMPILER_STATE_PREFIX) || key === 'compiler:code') {
      try {
        sessionStorage.removeItem(key);
      } catch {
        void 0;
      }
    }
  });
  try {
    localStorage.removeItem('compiler:code');
  } catch {
    void 0;
  }
  try {
    localStorage.removeItem(COMPILER_FALLBACK_KEY);
  } catch {
    void 0;
  }
};

const cleanupCompilerStates = () => {
  const keys = Object.keys(sessionStorage);
  const now = Date.now();
  keys.forEach((key) => {
    if (!key.startsWith(COMPILER_STATE_PREFIX)) {
      return;
    }
    let raw: string | null = null;
    try {
      raw = sessionStorage.getItem(key);
    } catch {
      raw = null;
    }
    if (!raw) {
      try {
        sessionStorage.removeItem(key);
      } catch {
        void 0;
      }
      return;
    }
    try {
      const parsed = JSON.parse(raw) as CompilerState;
      if (!parsed.updatedAt || now - parsed.updatedAt > COMPILER_STATE_TTL_MS) {
        try {
          sessionStorage.removeItem(key);
        } catch {
          void 0;
        }
      }
    } catch {
      try {
        sessionStorage.removeItem(key);
      } catch {
        void 0;
      }
    }
  });
};

const saveOutputState = (value: string) => {
  try {
    if (value) {
      sessionStorage.setItem(COMPILER_OUTPUT_KEY, value);
    } else {
      sessionStorage.removeItem(COMPILER_OUTPUT_KEY);
    }
  } catch {
    void 0;
  }
};

const clearOutputState = () => {
  try {
    sessionStorage.removeItem(COMPILER_OUTPUT_KEY);
  } catch {
    void 0;
  }
};

const getFallbackCode = () => {
  try {
    return localStorage.getItem(COMPILER_FALLBACK_KEY);
  } catch {
    return null;
  }
};

const Compiler = () => {
  const navigate = useNavigate();
  const initialCode = getFallbackCode() ?? '';

  // Use refs for everything to prevent re-renders
  const codeRef = useRef(initialCode);
  const [code, setCode] = useState(initialCode);
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [executionStatus, setExecutionStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [terminalSessionId, setTerminalSessionId] = useState<string | null>(null);
  const [terminalWsUrl, setTerminalWsUrl] = useState('');
  const outputRef = useRef<HTMLDivElement>(null);
  const compilerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLPreElement>(null);
  const errorDetectionTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const autoScrollFrameRef = useRef<number | null>(null);
  const lastAutoScrollTimeRef = useRef(0);
  const lastKeyWasEnterRef = useRef(false);
  const scrollPositionRef = useRef(0);
  const selectionRef = useRef<{start: number; end: number}>({ start: 0, end: 0 });
  const saveTimerRef = useRef<number | null>(null);
  const lastSavedStateRef = useRef<Omit<CompilerState, 'version' | 'compressed' | 'updatedAt'> | null>(null);
  const [isClearing, setIsClearing] = useState(false);
  const sessionIdRef = useRef<string | null>(null);



  // Real-time error detection
  const detectSyntaxErrors = (code: string): Array<{line: number, message: string}> => {
    const errors: Array<{line: number, message: string}> = [];
    const lines = code.split('\n');
    
    lines.forEach((line, index) => {
      const trimmed = line.trim();
      const lineNumber = index + 1;
      
      // Check for missing semicolons
      if (trimmed && 
          !trimmed.startsWith('//') && 
          !trimmed.startsWith('/*') && 
          !trimmed.endsWith('{') && 
          !trimmed.endsWith('}') && 
          !trimmed.endsWith(';') &&
          !trimmed.includes('class ') &&
          !trimmed.includes('public static void main') &&
          !trimmed.includes('import ') &&
          !trimmed.includes('package ') &&
          trimmed !== '') {
        errors.push({line: lineNumber, message: 'Missing semicolon'});
      }
      
      // Check for unmatched parentheses in line
      const openParens = (line.match(/\(/g) || []).length;
      const closeParens = (line.match(/\)/g) || []).length;
      if (openParens !== closeParens) {
        errors.push({line: lineNumber, message: 'Unmatched parentheses'});
      }
    });
    
    // Check for missing main method
    if (!code.includes('public static void main')) {
      errors.push({line: 1, message: 'Missing main method'});
    }
    
    // Check for unmatched braces globally
    const openBraces = (code.match(/\{/g) || []).length;
    const closeBraces = (code.match(/\}/g) || []).length;
    if (openBraces !== closeBraces) {
      errors.push({line: 1, message: 'Unmatched braces'});
    }
    
    return errors;
  };

  // Ultra-simplified code change handler
  const scheduleSave = useCallback((nextCode: string, nextSelection: { start: number; end: number }, nextScrollTop: number) => {
    const sessionId = sessionIdRef.current ?? getSessionId();
    sessionIdRef.current = sessionId;
    if (!sessionId) {
      return;
    }
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
    }
    saveTimerRef.current = window.setTimeout(async () => {
      const snapshot = {
        code: nextCode,
        selection: nextSelection,
        scrollTop: nextScrollTop,
        sessionId
      };
      const lastSaved = lastSavedStateRef.current;
      if (lastSaved && lastSaved.code === snapshot.code && lastSaved.scrollTop === snapshot.scrollTop &&
        lastSaved.selection.start === snapshot.selection.start && lastSaved.selection.end === snapshot.selection.end) {
        return;
      }
      try {
        await saveCompilerState(snapshot);
        lastSavedStateRef.current = snapshot;
      } catch (error) {
        const isQuotaError = error instanceof DOMException && (
          error.name === 'QuotaExceededError' || error.name === 'NS_ERROR_DOM_QUOTA_REACHED'
        );
        if (isQuotaError) {
          toast({
            title: "Storage limit reached",
            description: "Unable to save your code because storage is full.",
            variant: "destructive"
          });
        }
      }
    }, SAVE_DEBOUNCE_MS);
  }, []);

  const restoreEditorState = useCallback((state: { code: string; selection: { start: number; end: number }; scrollTop: number }) => {
    codeRef.current = state.code;
    setCode(state.code);
    selectionRef.current = state.selection;
    scrollPositionRef.current = state.scrollTop;
    requestAnimationFrame(() => {
      const textarea = textareaRef.current;
      if (!textarea) {
        return;
      }
      textarea.scrollTop = state.scrollTop;
      if (document.activeElement === textarea) {
        textarea.setSelectionRange(state.selection.start, state.selection.end);
      }
    });
  }, []);

  const handleCodeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const nextValue = e.target.value;
    const nextScrollTop = scrollPositionRef.current;
    const nextSelectionStart = e.target.selectionStart;
    const nextSelectionEnd = e.target.selectionEnd;
    selectionRef.current = {
      start: nextSelectionStart,
      end: nextSelectionEnd
    };
    codeRef.current = nextValue;
    setCode(nextValue);
    requestAnimationFrame(() => {
      const textarea = textareaRef.current;
      if (!textarea) {
        return;
      }
      if (document.activeElement === textarea) {
        textarea.setSelectionRange(nextSelectionStart, nextSelectionEnd);
      }
      if (textarea.scrollTop !== nextScrollTop) {
        textarea.scrollTop = nextScrollTop;
      }
    });
    ensureCursorInView(lastKeyWasEnterRef.current);
    lastKeyWasEnterRef.current = false;
    scheduleSave(nextValue, { start: nextSelectionStart, end: nextSelectionEnd }, nextScrollTop);
  };

  const ensureCursorInView = useCallback((preferSmooth: boolean) => {
    const textarea = textareaRef.current as HTMLTextAreaElement | null;
    if (!textarea) {
      return;
    }
    const selectionStart = textarea.selectionStart;
    const value = textarea.value;
    const computed = window.getComputedStyle(textarea);
    let lineHeight = parseFloat(computed.lineHeight);
    const fontSize = parseFloat(computed.fontSize);
    if (!Number.isFinite(lineHeight)) {
      lineHeight = Number.isFinite(fontSize) ? fontSize * 1.5 : 24;
    }
    const paddingTop = parseFloat(computed.paddingTop) || 0;
    const lineIndex = value.slice(0, selectionStart).split("\n").length - 1;
    const caretTop = paddingTop + lineIndex * lineHeight;
    const caretBottom = caretTop + lineHeight;
    const visibleTop = textarea.scrollTop;
    const visibleBottom = visibleTop + textarea.clientHeight;
    const offset = lineHeight * 2;
    let targetScrollTop = visibleTop;
    if (caretTop < visibleTop + offset) {
      targetScrollTop = caretTop - offset;
    } else if (caretBottom > visibleBottom - offset) {
      targetScrollTop = caretBottom - (textarea.clientHeight - offset);
    }
    const maxScrollTop = Math.max(0, textarea.scrollHeight - textarea.clientHeight);
    targetScrollTop = Math.min(Math.max(0, targetScrollTop), maxScrollTop);
    if (Math.abs(targetScrollTop - visibleTop) < 1) {
      return;
    }
    const now = performance.now();
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches ?? false;
    const shouldSmooth = preferSmooth && !reduceMotion && now - lastAutoScrollTimeRef.current > 120;
    lastAutoScrollTimeRef.current = now;
    if (autoScrollFrameRef.current) {
      cancelAnimationFrame(autoScrollFrameRef.current);
    }
    autoScrollFrameRef.current = requestAnimationFrame(() => {
      if (typeof textarea.scrollTo === "function") {
        textarea.scrollTo({ top: targetScrollTop, behavior: shouldSmooth ? "smooth" : "auto" });
      } else {
        textarea.scrollTop = targetScrollTop;
      }
      scrollPositionRef.current = targetScrollTop;
      const lineNumbers = lineNumbersRef.current;
      if (lineNumbers instanceof HTMLElement) {
        lineNumbers.scrollTop = targetScrollTop;
      }
    });
  }, []);

  const handleSelectionChange = useCallback((e: React.SyntheticEvent<HTMLTextAreaElement>) => {
    const target = e.currentTarget;
    selectionRef.current = {
      start: target.selectionStart,
      end: target.selectionEnd
    };
    ensureCursorInView(false);
    scheduleSave(codeRef.current, selectionRef.current, scrollPositionRef.current);
  }, [ensureCursorInView, scheduleSave]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter") {
      lastKeyWasEnterRef.current = true;
    }
  }, []);

  const handleKeyUp = useCallback((event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    handleSelectionChange(event);
    ensureCursorInView(false);
  }, [ensureCursorInView, handleSelectionChange]);

  // Simple scroll handler
  const handleScroll = useCallback(() => {
    if (textareaRef.current && lineNumbersRef.current) {
      scrollPositionRef.current = textareaRef.current.scrollTop;
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
    scheduleSave(codeRef.current, selectionRef.current, scrollPositionRef.current);
  }, [scheduleSave]);

  // Fullscreen functions
  const exitFullscreen = useCallback(() => {
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {
        toast({
          title: "Exit fullscreen error",
          description: "Unable to exit fullscreen mode.",
          variant: "destructive"
        });
      });
    }
  }, []);

  const toggleFullscreen = useCallback(() => {
    if (document.fullscreenElement) {
      exitFullscreen();
    } else if (compilerRef.current) {
      compilerRef.current.requestFullscreen().catch(() => {
        toast({
          title: "Fullscreen error",
          description: "Unable to enter fullscreen mode. Please try again.",
          variant: "destructive"
        });
      });
    }
  }, [exitFullscreen]);

  // Handle fullscreen change events and cleanup
  useEffect(() => {
    const sessionId = getSessionId();
    sessionIdRef.current = sessionId;
    cleanupCompilerStates();
    const navigationEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined;
    const navigationType = navigationEntry?.type ?? 'navigate';
    if (navigationType === 'reload') {
      clearOutputState();
    }
    loadCompilerState(sessionId).then((state) => {
      if (!state) {
        return;
      }
      restoreEditorState({
        code: state.code,
        selection: state.selection,
        scrollTop: state.scrollTop
      });
      lastSavedStateRef.current = {
        code: state.code,
        selection: state.selection,
        scrollTop: state.scrollTop,
        sessionId
      };
    }).catch(() => {
      void 0;
    });
    if (navigationType !== 'reload') {
      const savedOutput = sessionStorage.getItem(COMPILER_OUTPUT_KEY);
      if (savedOutput) {
        setOutput(savedOutput);
      }
    }

    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    const handleGlobalKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'F11') {
        event.preventDefault();
        toggleFullscreen();
      } 
      else if (event.key === 'Escape' && document.fullscreenElement) {
        event.preventDefault();
        exitFullscreen();
      }
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('keydown', handleGlobalKeyDown);

    const errorTimeout = errorDetectionTimeoutRef.current;
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('keydown', handleGlobalKeyDown);
      
      // Cleanup error detection timeout
      if (errorTimeout) {
        clearTimeout(errorTimeout);
      }
    };
  }, [exitFullscreen, restoreEditorState, toggleFullscreen]);

  useEffect(() => {
    const handleResize = () => {
      ensureCursorInView(false);
    };
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [ensureCursorInView]);

  useEffect(() => {
    const handleBeforeUnload = () => {
      const currentCode = textareaRef.current?.value ?? codeRef.current;
      try {
        localStorage.setItem(COMPILER_FALLBACK_KEY, currentCode);
      } catch {
        void 0;
      }
    };
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        handleBeforeUnload();
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  useEffect(() => {
    const handleStorage = (event: StorageEvent) => {
      if (event.key === 'access_token' && !event.newValue) {
        clearCompilerState();
        clearOutputState();
        codeRef.current = '';
        setCode('');
        setOutput('');
        return;
      }
      const sessionId = sessionIdRef.current;
      if (!sessionId) {
        return;
      }
      const stateKey = getCompilerStateKey(sessionId);
      if (event.key === stateKey && event.newValue) {
        try {
          const parsed = JSON.parse(event.newValue) as CompilerState;
          if (parsed && parsed.code) {
            const restore = async () => {
              const codeValue = await decompressString(parsed.code, parsed.compressed);
              restoreEditorState({
                code: codeValue,
                selection: parsed.selection ?? { start: codeValue.length, end: codeValue.length },
                scrollTop: parsed.scrollTop ?? 0
              });
            };
            void restore();
          }
        } catch {
          void 0;
        }
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => {
      window.removeEventListener('storage', handleStorage);
    };
  }, [restoreEditorState]);

  useEffect(() => {
    return () => {
      if (terminalSessionId) {
        compilerAPI.stopTerminalSession(terminalSessionId).catch(() => void 0);
      }
    };
  }, [terminalSessionId]);

  // Enhanced handleRun with real compilation
  const handleRun = async () => {
    const authToken = localStorage.getItem("access_token");
    if (!authToken) {
      setExecutionStatus('error');
      const message = 'Missing Authorization Header. Please log in again.';
      setOutput(message);
      saveOutputState(message);
      toast({
        title: "Login required",
        description: "Please log in to run code.",
        variant: "destructive"
      });
      navigate('/login');
      return;
    }
    if (terminalSessionId) {
      await compilerAPI.stopTerminalSession(terminalSessionId).catch(() => void 0);
      setTerminalSessionId(null);
      setTerminalWsUrl('');
    }
    setIsRunning(true);
    setExecutionStatus('idle');
    setOutput('');
    saveOutputState('');
    setOutput('Compiling...\r\n');
    saveOutputState('Compiling...\r\n');
    
    // Get current code from textarea ref
    const currentCode = textareaRef.current?.value || codeRef.current;
    scheduleSave(currentCode, selectionRef.current, scrollPositionRef.current);
    
    try {
      console.log('[Compiler] Starting terminal session');
      console.log('[Compiler] Code length:', currentCode.length);
      const requestId = typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
      const result = await compilerAPI.startTerminalSession(currentCode, requestId);
      console.log('[Compiler] Session result:', result);
      console.log('[Compiler] Success:', result.success);
      console.log('[Compiler] Errors:', result.errors);
      console.log('[Compiler] WS URL:', result.ws_url);
      if (result.success && result.session_id) {
        console.log('[Compiler] Setting terminal WS URL:', result.ws_url);
        setTerminalSessionId(result.session_id);
        setTerminalWsUrl(result.ws_url || '');
        setExecutionStatus('success');
        const startedMessage = 'Session started. Waiting for output...\r\n';
        setOutput((previous) => {
          const next = `${previous || ''}${startedMessage}`;
          saveOutputState(next);
          return next;
        });
        toast({
          title: "Session started!",
          description: "Interactive terminal is ready."
        });
      } else {
        console.log('[Compiler] Session failed:', result.errors);
        const errorMessage = result.errors && result.errors.length > 0 ? result.errors.map(err => err.message).join('\n') : 'Compilation failed';
        setOutput(errorMessage);
        setExecutionStatus('error');
        saveOutputState(errorMessage);
        toast({
          title: "Compilation failed",
          description: "Please check your code for errors.",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('[Compiler] Error:', error);
      const message = `Execution error: ${error instanceof Error ? error.message : 'Unknown error'}`;
      setOutput(message);
      setExecutionStatus('error');
      saveOutputState(message);
      toast({
        title: "Execution error",
        description: "An unexpected error occurred.",
        variant: "destructive"
      });
    } finally {
      setIsRunning(false);
    }
  };

  useEffect(() => {
    saveOutputState(output);
  }, [output]);

  const handleCopy = () => {
    const currentCode = textareaRef.current?.value || codeRef.current;
    navigator.clipboard.writeText(currentCode);
    toast({
      title: "Code copied!",
      description: "Code has been copied to clipboard."
    });
  };

  const handleClearCompiler = async () => {
    setIsClearing(true);
    if (terminalSessionId) {
      await compilerAPI.stopTerminalSession(terminalSessionId).catch(() => void 0);
      setTerminalSessionId(null);
      setTerminalWsUrl('');
    }
    clearCompilerState();
    clearOutputState();
    codeRef.current = '';
    setCode('');
    setOutput('');
    selectionRef.current = { start: 0, end: 0 };
    scrollPositionRef.current = 0;
    requestAnimationFrame(() => {
      const textarea = textareaRef.current;
      if (textarea) {
        textarea.scrollTop = 0;
        textarea.setSelectionRange(0, 0);
      }
    });
    setIsClearing(false);
    toast({
      title: "Compiler cleared",
      description: "Your code and output have been removed."
    });
  };

  const handleDownload = () => {
    const currentCode = textareaRef.current?.value || codeRef.current;
    const element = document.createElement("a");
    const file = new Blob([currentCode], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = "code.java";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    
    toast({
      title: "Download started!",
      description: "Your code file is being downloaded."
    });
  };

  return (
    <AppLayout>
      <div ref={compilerRef}>
        <div className={`${isFullscreen ? 'h-screen bg-black overflow-y-auto' : 'min-h-screen'} bg-gradient-to-br from-background via-background to-background/95`}> 
          <div className={`${isFullscreen ? 'p-4' : 'pt-1 px-1 pb-1 sm:pt-1 sm:px-1 sm:pb-1 md:pt-1 md:px-2 md:pb-2 lg:pt-1 lg:px-2 lg:pb-2'}`}> 
            <div className={`${isFullscreen ? 'max-w-full' : 'max-w-7xl'} mx-auto space-y-1`}> 
              
              {/* Main IDE Layout */} 
              <div className={`${isFullscreen ? 'space-y-6' : 'space-y-6'}`}> 
                
                {/* Code Editor Panel with Header and Buttons */} 
                <div className="flex flex-col space-y-3"> 
                  {/* Header */} 
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-1.5 sm:p-1.5 md:p-2 bg-gradient-to-r from-card/50 to-card/30 backdrop-blur-sm border border-primary/10 rounded-t-xl gap-2 sm:gap-0"> 
                    <div className="flex items-center space-x-2 sm:space-x-3"> 
                      <div className="p-1.5 sm:p-2 bg-primary/20 rounded-lg"> 
                        <Code2 className="w-4 h-4 sm:w-5 sm:h-5 text-primary" /> 
                      </div> 
                      <div> 
                        <h1 className="text-lg sm:text-xl font-bold bg-gradient-primary bg-clip-text text-transparent"> 
                          Code Compiler 
                        </h1> 
                        <p className="text-xs sm:text-sm text-muted-foreground"> 
                          main.java {isFullscreen && <span className="text-green-500 hidden sm:inline">• Fullscreen Mode</span>} 
                        </p> 
                      </div> 
                    </div> 
                    
                    <div className="flex items-center space-x-1 sm:space-x-2 w-full sm:w-auto justify-end"> 
                      <Button onClick={handleRun} disabled={isRunning} className="bg-gradient-primary hover:shadow-primary/25 transition-all duration-300 text-xs sm:text-sm px-2 sm:px-4"> 
                        <Play className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" /> 
                        <span className="hidden xs:inline">{isRunning ? 'Running...' : 'Run'}</span>
                        <span className="xs:hidden">{isRunning ? '...' : 'Run'}</span>
                      </Button> 
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="outline"
                            disabled={isClearing}
                            className="hover:bg-primary/10 transition-all duration-200 px-2 sm:px-4"
                            title="Clear Compiler"
                          >
                            {isClearing ? (
                              <Loader2 className="w-3 h-3 sm:w-4 sm:h-4 mr-1 animate-spin" />
                            ) : (
                              <Trash2 className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                            )}
                            <span className="hidden xs:inline">Clear Compiler</span>
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Clear compiler?</AlertDialogTitle>
                            <AlertDialogDescription>
                              This removes all code and output from this session.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction onClick={handleClearCompiler} disabled={isClearing}>
                              {isClearing ? (
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              ) : null}
                              Clear
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                      <Button variant="outline" onClick={handleCopy} className="hover:bg-primary/10 transition-all duration-200 p-2 sm:px-4" title="Copy"> 
                        <Copy className="w-3 h-3 sm:w-4 sm:h-4" /> 
                      </Button> 
                      <Button variant="outline" onClick={handleDownload} className="hover:bg-primary/10 transition-all duration-200 p-2 sm:px-4" title="Download"> 
                        <Download className="w-3 h-3 sm:w-4 sm:h-4" /> 
                      </Button> 

                      <Button 
                        variant="outline" 
                        onClick={toggleFullscreen} 
                        className="hover:bg-primary/10 transition-all duration-200 p-2 sm:px-4"
                        title={isFullscreen ? "Exit Fullscreen (F11/Esc)" : "Enter Fullscreen (F11)"}
                      > 
                        {isFullscreen ? <Minimize2 className="w-3 h-3 sm:w-4 sm:h-4" /> : <Maximize2 className="w-3 h-3 sm:w-4 sm:h-4" />} 
                      </Button> 
                    </div> 
                  </div> 
      
                  {/* Editor */} 
                  <div className={`relative bg-gradient-to-br from-card/80 to-card/60 backdrop-blur-sm border border-primary/10 rounded-b-xl overflow-hidden shadow-2xl ${isFullscreen ? 'h-[87vh]' : 'h-[60vh] sm:h-[65vh] md:h-[70vh] lg:h-[75vh]'}`}> 
                    <div className="flex h-full"> 
                      {/* Line Numbers */} 
                      <div className="w-8 sm:w-10 md:w-12 bg-muted/20 border-r border-primary/10 overflow-hidden relative"> 
                        <LineNumbers textareaRef={textareaRef} lineNumbersRef={lineNumbersRef} />
                      </div> 
                      
                      {/* Code Area */} 
                      <div className="flex-1 relative overflow-hidden"> 
                        {/* Syntax highlighting removed */}
                        
                        <textarea 
                          ref={textareaRef}
                          value={code}
                          onChange={handleCodeChange}
                          onSelect={handleSelectionChange}
                          onKeyDown={handleKeyDown}
                          onKeyUp={handleKeyUp}
                          onScroll={handleScroll}
                          className="relative w-full h-full resize-none border-0 bg-black font-mono text-xs sm:text-sm leading-5 sm:leading-6 p-1 sm:p-2 md:p-3 lg:p-4 focus:ring-0 focus:outline-none focus:border-transparent placeholder:text-muted-foreground/50 overflow-y-auto z-10" 
                          placeholder="Type or paste Java code here..."
                          style={{ 
                            minHeight: '100%', 
                            boxShadow: 'none',
                            scrollbarWidth: 'thin',
                            scrollbarColor: 'rgba(156, 163, 175, 0.3) transparent',
                            caretColor: '#ffffff',
                            color: '#ffffff'
                          }}
                          spellCheck="false"
                          autoComplete="off"
                          autoCorrect="off"
                          autoCapitalize="off"
                        /> 
                        
                        {/* Subtle background gradient */} 
                        <div className="absolute inset-0 pointer-events-none bg-gradient-to-r from-primary/5 via-transparent to-accent/5 opacity-30"></div> 
                        
                        {/* Error indicators removed */}
                      </div> 
                    </div> 
                  </div> 
                </div>
      
                {/* Output Panel */}
                <div className="flex flex-col space-y-3"> 
                  <div className="flex items-center justify-between p-1.5 sm:p-1.5 md:p-2 bg-gradient-to-r from-card/50 to-card/30 backdrop-blur-sm border border-accent/10 rounded-t-xl"> 
                    <div className="flex items-center space-x-2 sm:space-x-3"> 
                      <div className="p-1.5 sm:p-2 bg-accent/20 rounded-lg"> 
                        <TerminalIcon className="w-4 h-4 sm:w-5 sm:h-5 text-accent" /> 
                      </div> 
                      <div> 
                        <h2 className="text-base sm:text-lg font-semibold text-foreground">Console Output</h2> 
                        <p className="text-xs sm:text-sm text-muted-foreground">Execution results</p> 
                      </div> 
                    </div> 
                  </div> 
      
                  <div className={`bg-gradient-to-br from-card/80 to-card/60 backdrop-blur-sm border border-accent/10 rounded-b-xl overflow-hidden shadow-2xl ${isFullscreen ? 'h-[35vh]' : 'h-[30vh]'}`}> 
                    <div className="h-full p-2 sm:p-3 md:p-4 overflow-hidden">
                      <Terminal output={output || ''} wsUrl={terminalWsUrl} dataTestId="compiler-terminal" />
                    </div>
                  </div> 
                </div>
              </div> 
      
              {/* Status Bar */} 
              <div className="flex items-center justify-between p-3 bg-gradient-to-r from-muted/20 to-muted/10 backdrop-blur-sm border border-primary/5 rounded-lg"> 
                <div className="flex items-center space-x-4 text-sm text-muted-foreground"> 
                  <span>Java</span> 
                  <span>•</span> 
                  <span>UTF-8</span> 
                </div> 
                <div className="flex items-center space-x-2 text-sm text-muted-foreground"> 
                  <div className={`w-2 h-2 rounded-full ${executionStatus === 'success' ? 'bg-green-500' : executionStatus === 'error' ? 'bg-red-500' : 'bg-blue-500'} ${isRunning ? 'animate-pulse' : ''}`}></div> 
                  <span>{isRunning ? 'Running...' : executionStatus === 'success' ? 'Success' : executionStatus === 'error' ? 'Error' : 'Ready'}</span> 
                </div> 
              </div> 
            </div> 
          </div> 
        </div> 
      </div>
    </AppLayout>
  );
};

export default Compiler;
