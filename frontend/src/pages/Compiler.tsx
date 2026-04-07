import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
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
  Loader2,
  Wrench,
  X,
  Volume2,
  VolumeX
} from 'lucide-react';
import Editor from '@monaco-editor/react';
import type { OnMount } from '@monaco-editor/react';
import type { editor as MonacoEditor } from 'monaco-editor';
import { useTheme } from 'next-themes';
import { toast } from '@/hooks/use-toast';
import AppLayout from '@/components/layout/AppLayout';
import { authAPI, compilerAPI, settingsAPI } from '@/lib/api';
import { installPanelScrollLock } from '@/lib/panelScrollLock';
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

const COMPILER_SESSION_KEY = 'compiler:session-id';
const COMPILER_STATE_PREFIX = 'compiler:state:';
const COMPILER_OUTPUT_KEY = 'compiler:output';
const COMPILER_FALLBACK_KEY = 'compiler:code-fallback';
const COMPILER_STATE_TTL_MS = 1000 * 60 * 60 * 24 * 7;
const SAVE_DEBOUNCE_MS = 2500;
const EDITOR_FONT_SIZE_KEY = 'settings:editor-font-size';
const EDITOR_THEME_KEY = 'settings:editor-theme';
const EDITOR_UPDATED_AT_KEY = 'settings:editor-updated-at';
const SETTINGS_SUPPORTS_EDITOR_THEME_KEY = 'settings:supports-editor-theme';
const EDITOR_THEME_APP_THEME_KEY = 'settings:editor-theme-app-theme';
const EDITOR_THEME_VALUES = ['vs-dark', 'vs', 'hc-black', 'hc-light', 'github-dark', 'github-light', 'jellyfish'];

type PersistenceKeys = {
  sessionKey: string;
  statePrefix: string;
  outputKey: string;
  fallbackKey: string;
};

const DEFAULT_PERSISTENCE_KEYS: PersistenceKeys = {
  sessionKey: COMPILER_SESSION_KEY,
  statePrefix: COMPILER_STATE_PREFIX,
  outputKey: COMPILER_OUTPUT_KEY,
  fallbackKey: COMPILER_FALLBACK_KEY
};

type CompilerState = {
  version: 1;
  code: string;
  selection: { start: number; end: number };
  scrollTop: number;
  updatedAt: number;
  compressed: boolean;
  sessionId: string;
};

type CompilerError = {
  line?: number;
  column?: number;
  message?: string;
  file?: string;
  type?: string;
  ai_fix_suggestion?: string;
  corrected_code?: string;
  explanation?: string;
};

const buildPointer = (lineText: string, column: number) => {
  if (!lineText) {
    return '';
  }
  const fallbackIndex = Math.max(lineText.search(/\S/), 0);
  const index = column > 0 ? Math.max(column - 1, 0) : fallbackIndex;
  return `${' '.repeat(index)}^`;
};

const explainError = (message: string) => {
  const normalized = message.toLowerCase();
  if (normalized.includes("';' expected")) {
    return 'The compiler found a syntax issue at this location. Check the expression and statement structure around the highlighted line.';
  }
  if (normalized.includes('cannot find symbol')) {
    return 'The compiler cannot resolve a name. This usually means a variable, method, or class is misspelled, not declared, or a required import is missing.';
  }
  if (normalized.includes('reached end of file while parsing')) {
    return 'The parser reached the end of the file while still expecting a closing brace, parenthesis, or quote. Check for a missing } ) or " earlier in the file.';
  }
  if (normalized.includes('class, interface, or enum expected')) {
    return 'Code appears outside a class/interface declaration or braces are unbalanced. Make sure all methods and statements are inside a class and braces match.';
  }
  if (normalized.includes('illegal start of expression')) {
    return 'There is a syntax error where an expression is expected. This can be caused by a missing token, extra symbol, or a misplaced statement.';
  }
  if (normalized.includes('not a statement')) {
    return 'Java found an expression that cannot stand alone as a statement. This can happen if operators or parentheses are misplaced.';
  }
  if (normalized.includes('missing return statement')) {
    return 'A method with a non-void return type does not return a value on every path. Add a return statement for all paths.';
  }
  if (normalized.includes('incompatible types')) {
    return 'The types on both sides do not match. Check assignments, method arguments, and return types to ensure they are compatible.';
  }
  if (normalized.includes('cannot be applied to')) {
    return 'A method or constructor call does not match any available signature. Check the number and types of arguments.';
  }
  return 'The compiler reports a problem at this location. Review the highlighted line for missing symbols, wrong types, or misplaced syntax.';
};

const extractAiSummaryFromFix = (value?: string) => {
  if (!value) {
    return '';
  }
  const summaryMatch = value.match(/error summary:\s*([^\n]+)/i);
  if (summaryMatch?.[1]) {
    return summaryMatch[1].trim();
  }
  return '';
};

const deriveDisplayErrorMessage = (error: CompilerError) => {
  const rawMessage = (error.message || 'Compilation error').trim();
  if (!rawMessage.toLowerCase().includes("';' expected")) {
    return rawMessage;
  }
  const aiSummary = extractAiSummaryFromFix(error.ai_fix_suggestion);
  if (aiSummary && !/semicolon|';' expected/i.test(aiSummary)) {
    return aiSummary;
  }
  const explanation = (error.explanation || '').trim();
  if (explanation && !/semicolon|';' expected/i.test(explanation)) {
    return explanation.split(/[.!?]\s+/)[0].trim();
  }
  return rawMessage;
};

const buildErrorBlock = (payload: {
  file?: string;
  line: number;
  column: number;
  message: string;
  codeLine?: string;
}) => {
  const location = payload.line > 0
    ? `Line ${payload.line}${payload.column > 0 ? `, Col ${payload.column}` : ''}`
    : 'Line unknown';
  const header = payload.file ? `File: ${payload.file}` : 'File: Project';
  const codeLine = payload.codeLine ?? '';
  const pointer = buildPointer(codeLine, payload.column);
  const description = payload.message.trim() || 'Compilation failed';
  const details = explainError(description);
  const lines: string[] = [header, `${location}: ${description}`];
  if (codeLine) {
    lines.push(codeLine);
    if (pointer) {
      lines.push(pointer);
    }
  }
  lines.push(`Description: ${details}`);
  return lines.join('\n');
};

const reduceParsedCompilerErrors = <T extends { file?: string; line: number; message: string }>(items: T[]) => {
  const deduped = items.filter((item, index, arr) =>
    index === arr.findIndex((other) =>
      (other.file || '') === (item.file || '')
      && other.line === item.line
      && other.message.trim().toLowerCase() === item.message.trim().toLowerCase()
    )
  );
  const grouped = new Map<string, T[]>();
  deduped.forEach((item) => {
    const key = `${item.file || ''}:${item.line}`;
    const list = grouped.get(key) || [];
    list.push(item);
    grouped.set(key, list);
  });
  const reduced: T[] = [];
  grouped.forEach((group) => {
    const hasNotStatement = group.some((entry) => entry.message.toLowerCase().includes('not a statement'));
    group.forEach((entry) => {
      const isSemicolonExpected = entry.message.toLowerCase().includes("';' expected");
      if (hasNotStatement && isSemicolonExpected) {
        return;
      }
      reduced.push(entry);
    });
  });
  return reduced;
};

const parseJavacEntries = (output: string, code: string) => {
  const lines = output.split(/\r?\n/);
  const sourceLines = code.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
  const parsed: Array<{
    file?: string;
    line: number;
    column: number;
    message: string;
    codeLine?: string;
  }> = [];
  for (let index = 0; index < lines.length; index += 1) {
    const lineText = lines[index].trim();
    if (!lineText.toLowerCase().includes('error:')) {
      continue;
    }
    const match = lineText.match(/(.+\.java):(\d+)(?::(\d+))?:\s*error:\s*(.+)/);
    if (!match) {
      continue;
    }
    const [, filename, lineNum, , message] = match;
    const contextLine = lines[index + 1] ?? '';
    const caretLine = lines[index + 2] ?? '';
    const caretIndex = caretLine.indexOf('^');
    const column = caretIndex >= 0 ? caretIndex + 1 : 0;
    let lineNumber = Number.parseInt(lineNum, 10) || 0;
    if (lineNumber < 1 || lineNumber > sourceLines.length) {
      lineNumber = 0;
    }
    const codeLine = lineNumber > 0 ? sourceLines[lineNumber - 1] : contextLine;
    parsed.push({
      file: filename,
      line: lineNumber,
      column,
      message,
      codeLine
    });
  }
  return parsed;
};

const parseJavacOutput = (output: string, code: string) => {
  const parsed = parseJavacEntries(output, code);
  const reducedParsed = reduceParsedCompilerErrors(parsed);
  const results = reducedParsed.map((item) => buildErrorBlock(item));
  if (results.length > 0) {
    return results.join('\n');
  }
  return output.trim() || 'Compilation failed';
};

const formatErrors = (errors?: CompilerError[], code?: string) => {
  if (!errors || errors.length === 0) {
    return 'Compilation failed';
  }
  if (code) {
    const raw = errors.find((err) => (err.line ?? 0) <= 0 && (err.message ?? '').includes('.java:') && (err.message ?? '').includes('error:'));
    if (raw?.message) {
      return parseJavacOutput(raw.message, code);
    }
  }
  const sourceLines = code ? code.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n') : [];
  const parsed = errors.map((err) => {
    const line = typeof err.line === 'number' ? err.line : 0;
    const column = typeof err.column === 'number' ? err.column : 0;
    const message = err.message?.trim() || 'Compilation failed';
    const codeLine = line > 0 ? sourceLines[line - 1] : '';
    return {
      file: err.file,
      line,
      column,
      message,
      codeLine
    };
  });
  const reduced = reduceParsedCompilerErrors(parsed);
  return reduced.map((item) => buildErrorBlock(item)).join('\n');
};

const toPanelCompilerErrors = (errors: CompilerError[] | undefined, code: string) => {
  if (!errors || errors.length === 0) {
    return [] as CompilerError[];
  }
  const rawJavac = errors.find(
    (err) => (err.line ?? 0) <= 0 && (err.message ?? '').includes('.java:') && (err.message ?? '').includes('error:')
  );
  if (rawJavac?.message) {
    const parsed = parseJavacEntries(rawJavac.message, code);
    if (parsed.length > 0) {
      return reduceParsedCompilerErrors(parsed).map((item) => ({
        file: item.file,
        line: item.line,
        column: item.column,
        message: item.message,
      }));
    }
  }
  const normalized = errors.map((err) => ({
    ...err,
    line: typeof err.line === 'number' ? err.line : 0,
    message: err.message?.trim() || 'Compilation failed',
  }));
  return reduceParsedCompilerErrors(normalized);
};

const toScopeSuffix = (scope?: string) => {
  if (!scope) {
    return '';
  }
  const normalized = scope.trim().toLowerCase().replace(/[^a-z0-9:_-]+/g, '_');
  return normalized ? `:${normalized}` : '';
};

const getPersistenceKeys = (scope?: string): PersistenceKeys => {
  const suffix = toScopeSuffix(scope);
  if (!suffix) {
    return DEFAULT_PERSISTENCE_KEYS;
  }
  return {
    sessionKey: `${COMPILER_SESSION_KEY}${suffix}`,
    statePrefix: `${COMPILER_STATE_PREFIX}${suffix}:`,
    outputKey: `${COMPILER_OUTPUT_KEY}${suffix}`,
    fallbackKey: `${COMPILER_FALLBACK_KEY}${suffix}`
  };
};

const getSessionId = (sessionKey: string) => {
  const existing = sessionStorage.getItem(sessionKey);
  if (existing) {
    return existing;
  }
  const id = typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  sessionStorage.setItem(sessionKey, id);
  return id;
};

const getCompilerStateKey = (statePrefix: string, sessionId: string) => `${statePrefix}${sessionId}`;

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
  state: Omit<CompilerState, 'version' | 'compressed' | 'updatedAt'>,
  keys: PersistenceKeys
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
    sessionStorage.setItem(getCompilerStateKey(keys.statePrefix, state.sessionId), JSON.stringify(payload));
  } catch {
    void 0;
  }
  try {
    localStorage.setItem(keys.fallbackKey, state.code);
  } catch {
    void 0;
  }
};

const loadCompilerState = async (sessionId: string, keys: PersistenceKeys) => {
  const key = getCompilerStateKey(keys.statePrefix, sessionId);
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
      fallback = localStorage.getItem(keys.fallbackKey);
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

const clearCompilerState = (keysToUse: PersistenceKeys) => {
  const storageKeys = Object.keys(sessionStorage);
  storageKeys.forEach((key) => {
    if (key.startsWith(keysToUse.statePrefix)) {
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
    localStorage.removeItem(keysToUse.fallbackKey);
  } catch {
    void 0;
  }
};

const cleanupCompilerStates = (statePrefix: string) => {
  const keys = Object.keys(sessionStorage);
  const now = Date.now();
  keys.forEach((key) => {
    if (!key.startsWith(statePrefix)) {
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

const saveOutputState = (value: string, outputKey: string) => {
  try {
    if (value) {
      sessionStorage.setItem(outputKey, value);
    } else {
      sessionStorage.removeItem(outputKey);
    }
  } catch {
    void 0;
  }
};

const clearOutputState = (outputKey: string) => {
  try {
    sessionStorage.removeItem(outputKey);
  } catch {
    void 0;
  }
};

const getFallbackCode = (fallbackKey: string) => {
  try {
    return localStorage.getItem(fallbackKey);
  } catch {
    return null;
  }
};

const getStoredFontSize = () => {
  try {
    const stored = localStorage.getItem(EDITOR_FONT_SIZE_KEY);
    if (!stored) {
      return 14;
    }
    const parsed = Number(stored);
    return Number.isFinite(parsed) ? parsed : 14;
  } catch {
    return 14;
  }
};

const getStoredEditorTheme = () => {
  try {
    return localStorage.getItem(EDITOR_THEME_KEY) || 'vs-dark';
  } catch {
    return 'vs-dark';
  }
};

const getStoredEditorUpdatedAt = () => {
  try {
    const stored = localStorage.getItem(EDITOR_UPDATED_AT_KEY);
    const parsed = stored ? Date.parse(stored) : 0;
    return Number.isFinite(parsed) ? parsed : 0;
  } catch {
    return 0;
  }
};

const getStoredEditorThemeSupport = () => {
  try {
    const stored = localStorage.getItem(SETTINGS_SUPPORTS_EDITOR_THEME_KEY);
    if (stored === 'false') {
      return false;
    }
    if (stored === 'true') {
      return true;
    }
    return true;
  } catch {
    return true;
  }
};

const getCurrentAppThemeMode = (): 'dark' | 'light' => {
  try {
    return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
  } catch {
    return 'dark';
  }
};

const getDefaultEditorThemeForAppTheme = (themeMode: 'dark' | 'light') => {
  return themeMode === 'light' ? 'vs' : 'vs-dark';
};

type CompilerProps = {
  withLayout?: boolean;
  onExecutionSuccess?: () => void;
  onCodeChange?: (code: string) => void;
  persistenceScope?: string;
  initialCode?: string;
};

const Compiler = ({ withLayout = true, onExecutionSuccess, onCodeChange, persistenceScope, initialCode = '' }: CompilerProps) => {
  const navigate = useNavigate();
  const { resolvedTheme } = useTheme();
  const persistenceKeys = useMemo(
    () => getPersistenceKeys(withLayout ? undefined : persistenceScope),
    [persistenceScope, withLayout]
  );
  const initialEditorCode = useMemo(
    () => getFallbackCode(persistenceKeys.fallbackKey) ?? initialCode ?? '',
    [persistenceKeys, initialCode]
  );

  // Use refs for everything to prevent re-renders
  const codeRef = useRef(initialEditorCode);
  const [code, setCode] = useState(initialEditorCode);
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [executionStatus, setExecutionStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [compilerErrors, setCompilerErrors] = useState<CompilerError[]>([]);
  const [selectedError, setSelectedError] = useState<CompilerError | null>(null);
  const [isErrorPanelOpen, setIsErrorPanelOpen] = useState(false);
  const [isExplainingError, setIsExplainingError] = useState(false);
  const [errorExplainMessage, setErrorExplainMessage] = useState('');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [terminalSessionId, setTerminalSessionId] = useState<string | null>(null);
  const [terminalWsUrl, setTerminalWsUrl] = useState('');
  const [editorFontSize, setEditorFontSize] = useState(getStoredFontSize());
  const [editorTheme, setEditorTheme] = useState(getStoredEditorTheme());
  const compilerRef = useRef<HTMLDivElement>(null);
  const editorPanelRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<MonacoEditor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<Parameters<OnMount>[1] | null>(null);
  const errorDetectionTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const scrollPositionRef = useRef(0);
  const errorWidgetsRef = useRef<Array<MonacoEditor.IContentWidget>>([]);
  const selectionRef = useRef<{start: number; end: number}>({ start: 0, end: 0 });
  const saveTimerRef = useRef<number | null>(null);
  const lastSavedStateRef = useRef<Omit<CompilerState, 'version' | 'compressed' | 'updatedAt'> | null>(null);
  const [isClearing, setIsClearing] = useState(false);
  const [isSpeakingExplanation, setIsSpeakingExplanation] = useState(false);
  const sessionIdRef = useRef<string | null>(null);
  const speechUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const appThemeRef = useRef<'dark' | 'light'>(getCurrentAppThemeMode());
  const enableInlineErrorHelper = withLayout;

  useEffect(() => {
    onCodeChange?.(code);
  }, [code, onCodeChange]);

  useEffect(() => {
    let isMounted = true;
    const loadSettings = async () => {
      try {
        const data = await settingsAPI.getSettings();
        if (!isMounted) {
          return;
        }
        const localUpdatedAt = getStoredEditorUpdatedAt();
        const apiUpdatedAt = data.updated_at ? Date.parse(data.updated_at) : 0;
        const apiUpdatedAtValue = Number.isFinite(apiUpdatedAt) ? apiUpdatedAt : 0;
        const localFontSize = getStoredFontSize();
        const localTheme = EDITOR_THEME_VALUES.includes(getStoredEditorTheme()) ? getStoredEditorTheme() : 'vs-dark';
        const localIsNewer = localUpdatedAt && (!apiUpdatedAtValue || localUpdatedAt > apiUpdatedAtValue);
        if (localIsNewer) {
          setEditorFontSize(localFontSize);
          setEditorTheme(localTheme);
          try {
            const supportsEditorTheme = getStoredEditorThemeSupport();
            const payload: { font_size: number; editor_theme?: string } = {
              font_size: localFontSize
            };
            if (supportsEditorTheme) {
              payload.editor_theme = localTheme;
            }
            const response = await settingsAPI.updateSettings(payload);
            if (response?.updated_at) {
              localStorage.setItem(EDITOR_UPDATED_AT_KEY, response.updated_at);
            }
            localStorage.setItem(EDITOR_FONT_SIZE_KEY, String(localFontSize));
            localStorage.setItem(EDITOR_THEME_KEY, localTheme);
          } catch (error) {
            const message = error instanceof Error ? error.message : '';
            if (message.includes('Unknown settings: editor_theme')) {
              localStorage.setItem(SETTINGS_SUPPORTS_EDITOR_THEME_KEY, 'false');
              try {
                const response = await settingsAPI.updateSettings({ font_size: localFontSize });
                if (response?.updated_at) {
                  localStorage.setItem(EDITOR_UPDATED_AT_KEY, response.updated_at);
                }
              } catch {
                void 0;
              }
            }
          }
        } else {
          const nextFontSize = Number(data.font_size ?? 14);
          const normalizedFontSize = Number.isFinite(nextFontSize) ? nextFontSize : 14;
          const nextTheme = EDITOR_THEME_VALUES.includes(data.editor_theme) ? data.editor_theme : 'vs-dark';
          setEditorFontSize(normalizedFontSize);
          setEditorTheme(nextTheme);
          try {
            localStorage.setItem(EDITOR_FONT_SIZE_KEY, String(normalizedFontSize));
            localStorage.setItem(EDITOR_THEME_KEY, nextTheme);
            if (data.updated_at) {
              localStorage.setItem(EDITOR_UPDATED_AT_KEY, data.updated_at);
            }
          } catch {
            void 0;
          }
        }
      } catch {
        void 0;
      }
    };
    loadSettings();
    return () => {
      isMounted = false;
    };
  }, []);

  const syncEditorThemeWithAppTheme = useCallback((themeMode: 'dark' | 'light', forceDefault = false) => {
    const defaultTheme = getDefaultEditorThemeForAppTheme(themeMode);
    const storedTheme = getStoredEditorTheme();
    const normalizedStoredTheme = EDITOR_THEME_VALUES.includes(storedTheme) ? storedTheme : defaultTheme;
    let lastThemeMode: string | null = null;
    try {
      lastThemeMode = localStorage.getItem(EDITOR_THEME_APP_THEME_KEY);
    } catch {
      lastThemeMode = null;
    }
    const shouldResetToDefault = forceDefault || lastThemeMode !== themeMode;
    const nextTheme = shouldResetToDefault ? defaultTheme : normalizedStoredTheme;
    setEditorTheme(nextTheme);
    try {
      localStorage.setItem(EDITOR_THEME_KEY, nextTheme);
      localStorage.setItem(EDITOR_THEME_APP_THEME_KEY, themeMode);
      localStorage.setItem(EDITOR_UPDATED_AT_KEY, new Date().toISOString());
    } catch {
      void 0;
    }
  }, []);

  useEffect(() => {
    const themeMode: 'dark' | 'light' =
      resolvedTheme === 'light' ? 'light' : resolvedTheme === 'dark' ? 'dark' : getCurrentAppThemeMode();
    const previousThemeMode = appThemeRef.current;
    appThemeRef.current = themeMode;
    if (previousThemeMode !== themeMode) {
      syncEditorThemeWithAppTheme(themeMode, true);
      return;
    }
    syncEditorThemeWithAppTheme(themeMode, false);
  }, [resolvedTheme, syncEditorThemeWithAppTheme]);

  useEffect(() => {
    const editor = editorRef.current;
    if (editor) {
      editor.updateOptions({ fontSize: editorFontSize });
    }
  }, [editorFontSize]);

  useEffect(() => {
    const monaco = monacoRef.current;
    if (monaco) {
      monaco.editor.setTheme(editorTheme);
    }
  }, [editorTheme]);



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

  const actionableErrors = useMemo(() => {
    if (!enableInlineErrorHelper) {
      return [];
    }
    const seen = new Set<string>();
    const rows = (compilerErrors || [])
      .filter((err) => typeof err.line === 'number' && (err.line ?? 0) > 0 && !!err.message)
      .sort((a, b) => (a.line ?? 0) - (b.line ?? 0));
    const unique: CompilerError[] = [];
    for (const err of rows) {
      const key = `${err.line}:${(err.message || '').trim().toLowerCase()}`;
      if (seen.has(key)) continue;
      seen.add(key);
      unique.push(err);
    }
    return unique;
  }, [compilerErrors, enableInlineErrorHelper]);

  const stopSpeakingExplanation = useCallback(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      return;
    }
    window.speechSynthesis.cancel();
    speechUtteranceRef.current = null;
    setIsSpeakingExplanation(false);
  }, []);

  const handleErrorLineAction = useCallback(async (error: CompilerError) => {
    if (!enableInlineErrorHelper) {
      return;
    }
    stopSpeakingExplanation();
    setIsErrorPanelOpen(true);
    setErrorExplainMessage('');
    const hasExistingInsight = Boolean(error.explanation?.trim() || error.ai_fix_suggestion?.trim());
    if (hasExistingInsight) {
      setSelectedError(error);
      return;
    }
    if (!error.message || !codeRef.current.trim()) {
      setSelectedError(error);
      return;
    }
    setSelectedError({
      ...error,
      explanation: undefined,
      ai_fix_suggestion: undefined,
      corrected_code: undefined,
    });
    setIsExplainingError(true);
    try {
      const ai = await compilerAPI.suggestFix(
        error.message,
        codeRef.current,
        error.type || 'compilation_error',
        error.line,
        error.column
      );
      const isSemicolonMessage = (error.message || '').toLowerCase().includes("';' expected");
      const sanitizeSuggestion = (value?: string) => {
        if (!value) {
          return value;
        }
        const hasSemicolonOnlyHint = /semicolon|';' expected/i.test(value);
        if (!isSemicolonMessage && hasSemicolonOnlyHint) {
          return undefined;
        }
        return value;
      };
      let normalizedExplanation = sanitizeSuggestion(ai.explanation || error.explanation);
      const normalizedFix = sanitizeSuggestion(ai.fix_suggestion || error.ai_fix_suggestion);
      const semicolonPattern = /semicolon|';' expected/i;
      const hasGenericSemicolonExplanation = Boolean(normalizedExplanation && semicolonPattern.test(normalizedExplanation));
      const hasNonSemicolonFix = Boolean(normalizedFix && !semicolonPattern.test(normalizedFix));
      if (hasGenericSemicolonExplanation && hasNonSemicolonFix) {
        normalizedExplanation = undefined;
      }
      const enriched: CompilerError = {
        ...error,
        ai_fix_suggestion: normalizedFix,
        corrected_code: ai.corrected_code || error.corrected_code,
        explanation: normalizedExplanation,
      };
      setSelectedError(enriched);
      setCompilerErrors((prev) => prev.map((item) =>
        item.line === error.line && item.column === error.column && (item.message || '') === (error.message || '')
          ? { ...item, ...enriched }
          : item
      ));
    } catch (e) {
      setErrorExplainMessage(e instanceof Error ? e.message : 'Failed to fetch AI explanation');
    } finally {
      setIsExplainingError(false);
    }
  }, [enableInlineErrorHelper, stopSpeakingExplanation]);

  const clearErrorWidgets = useCallback(() => {
    const editor = editorRef.current;
    if (!editor) return;
    for (const widget of errorWidgetsRef.current) {
      editor.removeContentWidget(widget);
    }
    errorWidgetsRef.current = [];
  }, []);

  const renderErrorWidgets = useCallback(() => {
    clearErrorWidgets();
    if (!enableInlineErrorHelper) {
      return;
    }
    const editor = editorRef.current;
    const monaco = monacoRef.current;
    const model = editor?.getModel();
    if (!editor || !monaco || !model || actionableErrors.length === 0) {
      return;
    }
    const lineCount = model.getLineCount();
    const widgets: MonacoEditor.IContentWidget[] = [];
    actionableErrors.forEach((error, index) => {
      const lineNumber = error.line as number;
      if (lineNumber < 1 || lineNumber > lineCount) return;
      const node = document.createElement('button');
      node.type = 'button';
      node.className = 'compiler-error-line-btn';
      node.textContent = 'Fix';
      node.onclick = (event) => {
        event.preventDefault();
        event.stopPropagation();
        void handleErrorLineAction(error);
      };
      const id = `compiler-error-line-btn-${lineNumber}-${index}`;
      const widget: MonacoEditor.IContentWidget = {
        getId: () => id,
        getDomNode: () => node,
        getPosition: () => ({
          position: {
            lineNumber,
            column: model.getLineMaxColumn(lineNumber),
          },
          preference: [monaco.editor.ContentWidgetPositionPreference.EXACT],
        }),
      };
      editor.addContentWidget(widget);
      widgets.push(widget);
    });
    errorWidgetsRef.current = widgets;
  }, [actionableErrors, clearErrorWidgets, handleErrorLineAction, enableInlineErrorHelper]);

  useEffect(() => {
    if (!enableInlineErrorHelper) {
      setIsErrorPanelOpen(false);
      setSelectedError(null);
    }
  }, [enableInlineErrorHelper]);

  const handleSpeakExplanation = useCallback(() => {
    if (!selectedError) {
      return;
    }
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      toast({
        title: 'Speech not supported',
        description: 'Your browser does not support text-to-speech for this feature.',
        variant: 'destructive'
      });
      return;
    }
    if (isSpeakingExplanation) {
      stopSpeakingExplanation();
      return;
    }
    const convertProgrammingTextForSpeech = (value: string) => {
      return value
        .replace(/```[\s\S]*?```/g, ' code example omitted for clarity. ')
        .replace(/`([^`]+)`/g, '$1')
        .replace(/Error Summary:/gi, 'Summary:')
        .replace(/Suggested Fix:/gi, 'Suggested fix:')
        .replace(/\r?\n+/g, '. ')
        .replace(/!==/g, ' not equal to ')
        .replace(/===/g, ' exactly equals ')
        .replace(/!=/g, ' not equal to ')
        .replace(/==/g, ' equals ')
        .replace(/<=/g, ' less than or equal to ')
        .replace(/>=/g, ' greater than or equal to ')
        .replace(/&&/g, ' and ')
        .replace(/\|\|/g, ' or ')
        .replace(/\s\*\s/g, ' multiplied by ')
        .replace(/\s\/\s/g, ' divided by ')
        .replace(/\s\+\s/g, ' plus ')
        .replace(/\s-\s/g, ' minus ')
        .replace(/';' expected/gi, 'semicolon expected')
        .replace(/\s+/g, ' ')
        .trim();
    };
    const pickPreferredVoice = (voices: SpeechSynthesisVoice[]) => {
      if (voices.length === 0) {
        return null;
      }
      const scored = voices
        .filter((voice) => /^en(-|_)/i.test(voice.lang))
        .map((voice) => {
          const id = `${voice.name} ${voice.lang}`.toLowerCase();
          let score = 0;
          if (voice.lang.toLowerCase().includes('en-in')) score += 6;
          if (/female|woman|zira|hazel|aria|samantha|victoria|allison|karen|moira|google uk english female/.test(id)) score += 5;
          if (/natural|neural|enhanced|premium/.test(id)) score += 3;
          return { voice, score };
        })
        .sort((a, b) => b.score - a.score);
      if (scored.length > 0) {
        return scored[0].voice;
      }
      return voices[0];
    };
    const explanation = selectedError.explanation?.trim();
    const suggestion = selectedError.ai_fix_suggestion?.trim();
    const fallbackMessage = selectedError.message?.trim();
    const combinedText = explanation
      ? `${explanation}${suggestion ? `. Suggested fix: ${suggestion}` : ''}`
      : suggestion || fallbackMessage || 'No explanation available to read.';
    const textToSpeak = convertProgrammingTextForSpeech(combinedText);
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = pickPreferredVoice(voices);
    if (preferredVoice) {
      utterance.voice = preferredVoice;
      utterance.lang = preferredVoice.lang;
    } else {
      utterance.lang = 'en-IN';
    }
    utterance.rate = 0.9;
    utterance.pitch = 1.05;
    utterance.onend = () => {
      speechUtteranceRef.current = null;
      setIsSpeakingExplanation(false);
    };
    utterance.onerror = () => {
      speechUtteranceRef.current = null;
      setIsSpeakingExplanation(false);
    };
    speechUtteranceRef.current = utterance;
    setIsSpeakingExplanation(true);
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }, [isSpeakingExplanation, selectedError, stopSpeakingExplanation]);

  useEffect(() => {
    if (!isErrorPanelOpen) {
      stopSpeakingExplanation();
    }
  }, [isErrorPanelOpen, stopSpeakingExplanation]);

  useEffect(() => {
    return () => {
      stopSpeakingExplanation();
    };
  }, [stopSpeakingExplanation]);

  useEffect(() => {
    renderErrorWidgets();
    return () => {
      clearErrorWidgets();
    };
  }, [renderErrorWidgets, clearErrorWidgets, code]);

  // Ultra-simplified code change handler
  const scheduleSave = useCallback((nextCode: string, nextSelection: { start: number; end: number }, nextScrollTop: number) => {
    const sessionId = sessionIdRef.current ?? getSessionId(persistenceKeys.sessionKey);
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
        await saveCompilerState(snapshot, persistenceKeys);
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
  }, [persistenceKeys]);

  useEffect(() => {
    return () => {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current);
        saveTimerRef.current = null;
      }
      const sessionId = sessionIdRef.current ?? getSessionId(persistenceKeys.sessionKey);
      const currentCode = editorRef.current?.getValue() ?? codeRef.current;
      if (!sessionId) {
        return;
      }
      void saveCompilerState({
        code: currentCode,
        selection: selectionRef.current,
        scrollTop: scrollPositionRef.current,
        sessionId
      }, persistenceKeys);
    };
  }, [persistenceKeys]);

  const restoreEditorState = useCallback((state: { code: string; selection: { start: number; end: number }; scrollTop: number }) => {
    codeRef.current = state.code;
    setCode(state.code);
    selectionRef.current = state.selection;
    scrollPositionRef.current = state.scrollTop;
    const editor = editorRef.current;
    if (!editor) {
      return;
    }
    const model = editor.getModel();
    if (!model) {
      return;
    }
    if (model.getValue() !== state.code) {
      editor.setValue(state.code);
    }
    const start = model.getPositionAt(state.selection.start);
    const end = model.getPositionAt(state.selection.end);
    editor.setSelection({
      startLineNumber: start.lineNumber,
      startColumn: start.column,
      endLineNumber: end.lineNumber,
      endColumn: end.column
    });
    editor.setScrollTop(state.scrollTop);
  }, []);

  const updateSelectionFromEditor = useCallback(() => {
    const editor = editorRef.current;
    const model = editor?.getModel();
    const selection = editor?.getSelection();
    if (!editor || !model || !selection) {
      return;
    }
    selectionRef.current = {
      start: model.getOffsetAt(selection.getStartPosition()),
      end: model.getOffsetAt(selection.getEndPosition())
    };
  }, []);

  const handleCodeChange = useCallback((value: string | undefined) => {
    const nextValue = value ?? '';
    codeRef.current = nextValue;
    setCode(nextValue);
    onCodeChange?.(nextValue);
    const editor = editorRef.current;
    if (editor) {
      const model = editor.getModel();
      const selection = editor.getSelection();
      if (model && selection) {
        selectionRef.current = {
          start: model.getOffsetAt(selection.getStartPosition()),
          end: model.getOffsetAt(selection.getEndPosition())
        };
      }
      scrollPositionRef.current = editor.getScrollTop();
    }
    scheduleSave(nextValue, selectionRef.current, scrollPositionRef.current);
  }, [scheduleSave, onCodeChange]);

  const handleEditorMount: OnMount = useCallback((editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    monaco.editor.defineTheme('github-light', {
      base: 'vs',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '6e7781' },
        { token: 'keyword', foreground: 'cf222e' },
        { token: 'string', foreground: '0a3069' },
        { token: 'number', foreground: '0550ae' },
        { token: 'type.identifier', foreground: '8250df' },
        { token: 'identifier', foreground: '24292f' },
        { token: 'delimiter', foreground: '24292f' }
      ],
      colors: {
        'editor.background': '#ffffff',
        'editor.foreground': '#24292f',
        'editorLineNumber.foreground': '#8c959f',
        'editorCursor.foreground': '#0969da',
        'editor.selectionBackground': '#b6d7ff',
        'editor.inactiveSelectionBackground': '#dbe9ff',
        'editor.lineHighlightBackground': '#f6f8fa'
      }
    });
    monaco.editor.defineTheme('github-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '8b949e' },
        { token: 'keyword', foreground: 'ff7b72' },
        { token: 'string', foreground: 'a5d6ff' },
        { token: 'number', foreground: '79c0ff' },
        { token: 'type.identifier', foreground: 'd2a8ff' },
        { token: 'identifier', foreground: 'c9d1d9' },
        { token: 'delimiter', foreground: 'c9d1d9' }
      ],
      colors: {
        'editor.background': '#0d1117',
        'editor.foreground': '#c9d1d9',
        'editorLineNumber.foreground': '#6e7681',
        'editorCursor.foreground': '#58a6ff',
        'editor.selectionBackground': '#1f6feb66',
        'editor.inactiveSelectionBackground': '#1f6feb33',
        'editor.lineHighlightBackground': '#161b22'
      }
    });
    monaco.editor.defineTheme('jellyfish', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '6b7891' },
        { token: 'keyword', foreground: 'ff7fcf' },
        { token: 'string', foreground: '9be7ff' },
        { token: 'number', foreground: '7fc4ff' },
        { token: 'type.identifier', foreground: '9d7bff' },
        { token: 'identifier', foreground: 'e6f1ff' },
        { token: 'delimiter', foreground: 'e6f1ff' }
      ],
      colors: {
        'editor.background': '#151b28',
        'editor.foreground': '#e6f1ff',
        'editorLineNumber.foreground': '#5c6b8a',
        'editorCursor.foreground': '#7fc4ff',
        'editor.selectionBackground': '#2b4c7e66',
        'editor.inactiveSelectionBackground': '#2b4c7e33',
        'editor.lineHighlightBackground': '#1e2738'
      }
    });
    monaco.editor.setTheme(editorTheme);
    const model = editor.getModel();
    if (model && model.getValue() !== codeRef.current) {
      editor.setValue(codeRef.current);
    }
    if (model) {
      const start = model.getPositionAt(selectionRef.current.start);
      const end = model.getPositionAt(selectionRef.current.end);
      editor.setSelection({
        startLineNumber: start.lineNumber,
        startColumn: start.column,
        endLineNumber: end.lineNumber,
        endColumn: end.column
      });
      editor.setScrollTop(scrollPositionRef.current);
    }
    editor.onDidChangeCursorSelection(() => {
      updateSelectionFromEditor();
      scheduleSave(codeRef.current, selectionRef.current, editor.getScrollTop());
    });
    editor.onDidScrollChange(() => {
      scrollPositionRef.current = editor.getScrollTop();
      scheduleSave(codeRef.current, selectionRef.current, scrollPositionRef.current);
    });
    renderErrorWidgets();
  }, [editorTheme, scheduleSave, updateSelectionFromEditor, renderErrorWidgets]);

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
    const sessionId = getSessionId(persistenceKeys.sessionKey);
    sessionIdRef.current = sessionId;
    cleanupCompilerStates(persistenceKeys.statePrefix);
    const navigationEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined;
    const navigationType = navigationEntry?.type ?? 'navigate';
    if (navigationType === 'reload') {
      clearOutputState(persistenceKeys.outputKey);
    }
    loadCompilerState(sessionId, persistenceKeys).then((state) => {
      if (!state) {
        const fallbackCode = initialEditorCode || '';
        codeRef.current = fallbackCode;
        setCode(fallbackCode);
        selectionRef.current = { start: fallbackCode.length, end: fallbackCode.length };
        scrollPositionRef.current = 0;
        lastSavedStateRef.current = null;
        restoreEditorState({
          code: fallbackCode,
          selection: { start: fallbackCode.length, end: fallbackCode.length },
          scrollTop: 0
        });
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
      const savedOutput = sessionStorage.getItem(persistenceKeys.outputKey);
      if (savedOutput) {
        setOutput(savedOutput);
      } else {
        setOutput('');
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
  }, [exitFullscreen, restoreEditorState, toggleFullscreen, persistenceKeys, initialEditorCode]);

  useEffect(() => {
    const handleResize = () => {
      editorRef.current?.layout();
    };
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  useEffect(() => {
    const panel = editorPanelRef.current;
    if (!panel) {
      return;
    }
    return installPanelScrollLock(panel, {
      getScrollableTarget: (root) => {
        const monacoScrollable = root.querySelector('.monaco-scrollable-element');
        return monacoScrollable instanceof HTMLElement ? monacoScrollable : null;
      },
    });
  }, []);

  useEffect(() => {
    const handleBeforeUnload = () => {
      const currentCode = editorRef.current?.getValue() ?? codeRef.current;
      try {
        localStorage.setItem(persistenceKeys.fallbackKey, currentCode);
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
  }, [persistenceKeys]);

  useEffect(() => {
    const handleStorage = (event: StorageEvent) => {
      if (event.key === 'access_token' && !event.newValue) {
        clearCompilerState(persistenceKeys);
        clearOutputState(persistenceKeys.outputKey);
        codeRef.current = '';
        setCode('');
        setOutput('');
        return;
      }
      if (event.key === EDITOR_FONT_SIZE_KEY && event.newValue) {
        const parsed = Number(event.newValue);
        if (Number.isFinite(parsed)) {
          setEditorFontSize(parsed);
        }
      }
      if (event.key === EDITOR_THEME_KEY && event.newValue) {
        setEditorTheme(event.newValue);
        try {
          localStorage.setItem(EDITOR_THEME_APP_THEME_KEY, appThemeRef.current);
        } catch {
          void 0;
        }
      }
      if (event.key === EDITOR_UPDATED_AT_KEY) {
        const nextFontSize = getStoredFontSize();
        const nextTheme = EDITOR_THEME_VALUES.includes(getStoredEditorTheme()) ? getStoredEditorTheme() : 'vs-dark';
        setEditorFontSize(nextFontSize);
        setEditorTheme(nextTheme);
      }
      const sessionId = sessionIdRef.current;
      if (!sessionId) {
        return;
      }
      const stateKey = getCompilerStateKey(persistenceKeys.statePrefix, sessionId);
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
  }, [restoreEditorState, persistenceKeys]);

  useEffect(() => {
    return () => {
      if (terminalSessionId) {
        compilerAPI.stopTerminalSession(terminalSessionId).catch(() => void 0);
      }
    };
  }, [terminalSessionId]);

  // Enhanced handleRun with real compilation
  const handleRun = async () => {
    let authToken = localStorage.getItem("access_token");
    if (!authToken) {
      const sessionToken = sessionStorage.getItem("access_token");
      if (sessionToken) {
        localStorage.setItem("access_token", sessionToken);
        authToken = sessionToken;
      }
    }
    if (!authToken) {
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const refreshed = await authAPI.refresh();
          authToken = refreshed.access_token;
        } catch {
          void 0;
        }
      }
    }
    if (!authToken) {
      setExecutionStatus('error');
      const message = 'Missing Authorization Header. Please log in again.';
      setOutput(message);
      saveOutputState(message, persistenceKeys.outputKey);
      toast({
        title: "Login required",
        description: "Please log in to run code.",
        variant: "destructive"
      });
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
    setCompilerErrors([]);
    setSelectedError(null);
    setIsErrorPanelOpen(false);
    saveOutputState('', persistenceKeys.outputKey);
    setOutput('Compiling...\r\n');
    saveOutputState('Compiling...\r\n', persistenceKeys.outputKey);
    
    const currentCode = editorRef.current?.getValue() ?? codeRef.current;
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
        onExecutionSuccess?.();
        toast({
          title: "Session started!",
          description: "Interactive terminal is ready."
        });
      } else {
        console.log('[Compiler] Session failed:', result.errors);
        const rawErrors = (result.errors || []) as CompilerError[];
        setCompilerErrors(toPanelCompilerErrors(rawErrors, currentCode));
        const errorMessage = formatErrors(result.errors, currentCode);
        setOutput(errorMessage);
        setExecutionStatus('error');
        saveOutputState(errorMessage, persistenceKeys.outputKey);
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
      setCompilerErrors([]);
      setExecutionStatus('error');
      saveOutputState(message, persistenceKeys.outputKey);
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
    saveOutputState(output, persistenceKeys.outputKey);
  }, [output, persistenceKeys]);

  const handleCopy = () => {
    const currentCode = editorRef.current?.getValue() ?? codeRef.current;
    navigator.clipboard.writeText(currentCode);
    toast({
      title: "Code copied!",
      description: "Code has been copied to clipboard."
    });
  };

  const handleClearOutput = () => {
    setOutput('');
    setCompilerErrors([]);
    setSelectedError(null);
    setIsErrorPanelOpen(false);
    saveOutputState('', persistenceKeys.outputKey);
    setExecutionStatus('idle');
    toast({
      title: "Output cleared",
      description: "Console output has been cleared."
    });
  };

  const handleClearCompiler = async () => {
    setIsClearing(true);
    if (terminalSessionId) {
      await compilerAPI.stopTerminalSession(terminalSessionId).catch(() => void 0);
      setTerminalSessionId(null);
      setTerminalWsUrl('');
    }
    clearCompilerState(persistenceKeys);
    clearOutputState(persistenceKeys.outputKey);
    codeRef.current = '';
    setCode('');
    setOutput('');
    setCompilerErrors([]);
    setSelectedError(null);
    setIsErrorPanelOpen(false);
    selectionRef.current = { start: 0, end: 0 };
    scrollPositionRef.current = 0;
    const editor = editorRef.current;
    if (editor) {
      const model = editor.getModel();
      editor.setValue('');
      if (model) {
        editor.setSelection({
          startLineNumber: 1,
          startColumn: 1,
          endLineNumber: 1,
          endColumn: 1
        });
      }
      editor.setScrollTop(0);
    }
    setIsClearing(false);
    toast({
      title: "Compiler cleared",
      description: "Your code and output have been removed."
    });
  };

  const handleDownload = () => {
    const currentCode = editorRef.current?.getValue() ?? codeRef.current;
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

  const compilerContent = (
    <div ref={compilerRef}>
      <style>{`
        .compiler-error-line-btn {
          background: rgba(239, 68, 68, 0.15);
          border: 1px solid rgba(239, 68, 68, 0.45);
          color: #fecaca;
          border-radius: 6px;
          font-size: 10px;
          line-height: 1;
          padding: 2px 6px;
          margin-left: 10px;
          cursor: pointer;
        }
        .compiler-error-line-btn:hover {
          background: rgba(239, 68, 68, 0.28);
        }
      `}</style>
      <div className={`${isFullscreen ? 'h-screen bg-black overflow-y-auto' : 'min-h-screen'} bg-gradient-to-br from-background via-background to-background/95`}> 
        <div className={`${isFullscreen ? 'p-4' : 'pt-1 px-1 pb-1 sm:pt-1 sm:px-1 sm:pb-1 md:pt-1 md:px-2 md:pb-2 lg:pt-1 lg:px-2 lg:pb-2'}`}> 
          <div className={`${isFullscreen ? 'max-w-full' : 'max-w-7xl'} mx-auto space-y-1`}> 
              
              {/* Main IDE Layout */} 
              <div className={`${isFullscreen ? 'space-y-6' : 'space-y-6'}`}> 
                
                {/* Code Editor Panel with Header and Buttons */} 
                <div className="flex flex-col space-y-3"> 
                  {/* Header */} 
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-1.5 sm:p-1.5 md:p-2 bg-gradient-to-r from-card/92 to-card/80 backdrop-blur-sm border border-border/65 dark:border-border/80 rounded-t-xl gap-2 sm:gap-0 shadow-[0_6px_20px_hsl(0_0%_0%_/_0.08)] dark:shadow-[0_10px_24px_hsl(0_0%_0%_/_0.45)]"> 
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
                  <div ref={editorPanelRef} className={`relative bg-gradient-to-br from-card/95 to-card/88 backdrop-blur-sm border border-border/65 dark:border-border/80 rounded-b-xl overflow-hidden shadow-2xl ${isFullscreen ? 'h-[90vh]' : 'h-[65vh] sm:h-[70vh] md:h-[75vh] lg:h-[80vh]'}`}> 
                    <div className="flex h-full"> 
                      <div className="flex-1 relative overflow-hidden"> 
                        <div data-testid="compiler-editor" className="absolute inset-0">
                          <Editor
                            height="100%"
                            defaultLanguage="java"
                            theme={editorTheme}
                            value={code}
                            onChange={handleCodeChange}
                            onMount={handleEditorMount}
                            options={{
                              automaticLayout: true,
                              minimap: { enabled: false },
                              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                              fontSize: editorFontSize,
                              lineHeight: 20,
                              scrollBeyondLastLine: false,
                              tabSize: 2,
                              insertSpaces: true,
                              wordWrap: 'on',
                              padding: { top: 12, bottom: 12 },
                              scrollbar: {
                                verticalScrollbarSize: 8,
                                horizontalScrollbarSize: 8,
                                alwaysConsumeMouseWheel: false
                              }
                            }}
                          />
                        </div>
                        {!code && (
                          <div className="absolute left-[3.75rem] top-3 text-xs sm:text-sm text-muted-foreground/60 pointer-events-none">
                            Type or paste Java code here...
                          </div>
                        )}
                        <div className="absolute inset-0 pointer-events-none bg-gradient-to-r from-primary/5 via-transparent to-accent/5 opacity-30"></div> 
                        {enableInlineErrorHelper ? (
                        <div
                          className={`absolute top-0 right-0 h-full w-[360px] max-w-[92%] bg-card/95 border-l border-primary/20 shadow-2xl transition-transform duration-300 z-40 ${
                            isErrorPanelOpen ? 'translate-x-0' : 'translate-x-full'
                          }`}
                        >
                          <div className="flex items-center justify-between p-4 border-b border-border/20">
                            <div className="flex items-center gap-2">
                              <Wrench className="w-4 h-4 text-primary" />
                              <span className="text-sm font-semibold">Error Helper</span>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0"
                              onClick={() => setIsErrorPanelOpen(false)}
                            >
                              <X className="w-4 h-4" />
                            </Button>
                          </div>
                          <div className="p-4 space-y-4 text-sm overflow-y-auto h-[calc(100%-60px)]">
                            {selectedError ? (
                              <>
                                <div className="flex items-center justify-between">
                                  <div className="text-muted-foreground">
                                    {typeof selectedError.line === 'number' ? `Line ${selectedError.line}` : 'Line unknown'}
                                    {typeof selectedError.column === 'number' && (selectedError.column ?? 0) > 0 ? `, Col ${selectedError.column}` : ''}
                                  </div>
                                  {(selectedError.explanation || selectedError.ai_fix_suggestion) && !isExplainingError ? (
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      className="h-8 w-8 p-0 border-primary/40 text-primary hover:bg-primary/10"
                                      onClick={handleSpeakExplanation}
                                      aria-label={isSpeakingExplanation ? 'Stop reading explanation' : 'Read explanation aloud'}
                                    >
                                      {isSpeakingExplanation ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                                    </Button>
                                  ) : null}
                                </div>
                                <div className="font-medium text-foreground">{deriveDisplayErrorMessage(selectedError)}</div>
                                {isExplainingError ? (
                                  <div className="text-muted-foreground">Generating detailed AI explanation...</div>
                                ) : null}
                                {errorExplainMessage ? (
                                  <div className="text-destructive text-xs">{errorExplainMessage}</div>
                                ) : null}
                                {!isExplainingError && selectedError.explanation ? (
                                  <div>
                                    <div className="text-xs text-muted-foreground mb-1">Explanation</div>
                                    <div className="text-foreground whitespace-pre-wrap">{selectedError.explanation}</div>
                                  </div>
                                ) : null}
                                {!isExplainingError && selectedError.ai_fix_suggestion ? (
                                  <div>
                                    <div className="text-xs text-muted-foreground mb-1">Suggested Fix</div>
                                    <div className="text-foreground whitespace-pre-wrap">{selectedError.ai_fix_suggestion}</div>
                                  </div>
                                ) : null}
                              </>
                            ) : (
                              <div className="text-muted-foreground">Select an error line button to view details.</div>
                            )}
                          </div>
                        </div>
                        ) : null}
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
                    <Button
                      variant="outline"
                      onClick={handleClearOutput}
                      className="ml-3 hover:bg-accent/15 active:scale-[0.98] transition-all duration-200 px-2 sm:px-3 text-xs sm:text-sm"
                    >
                      Clear Compiler
                    </Button>
                  </div> 
      
                  <div className={`bg-gradient-to-br from-card/80 to-card/60 backdrop-blur-sm border border-accent/10 rounded-b-xl overflow-hidden shadow-2xl ${isFullscreen ? 'h-[45vh]' : 'h-[40vh] sm:h-[42vh] md:h-[45vh]'}`}> 
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
  );
  if (withLayout) {
    return <AppLayout>{compilerContent}</AppLayout>;
  }
  return compilerContent;
};

export default Compiler;
