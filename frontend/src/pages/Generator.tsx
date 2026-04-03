import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Send, 
  Mic, 
  Trash2, 
  Copy,
  Code2,
  MessageSquare,
  History,
  Plus,
  X,
  Check,
  Pencil,
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { generatorAPI, profileAPI } from '@/lib/api';
import AppLayout from '@/components/layout/AppLayout';
import { useNavigate } from 'react-router-dom';

type SpeechRecognitionCtor = new () => {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: {
    resultIndex: number;
    results: ArrayLike<{ 0: { transcript: string }; isFinal: boolean }>;
  }) => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  }
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  code?: string;
}

interface ChatHistory {
  id: number;
  title: string;
  lastMessage: Date;
  messageCount: number;
}

type GeneratorUiCache = {
  activeChatId: number | null;
  chatHistories: Array<{ id: number; title: string; lastMessage: string; messageCount: number }>;
  messages: Array<{ id: string; role: 'user' | 'assistant'; content: string; timestamp: string; code?: string }>;
};

const GENERATOR_UI_CACHE_KEY = 'generator:ui-cache:v1';

const readGeneratorUiCache = (): GeneratorUiCache | null => {
  try {
    const raw = localStorage.getItem(GENERATOR_UI_CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as GeneratorUiCache;
    if (!parsed || !Array.isArray(parsed.messages) || !Array.isArray(parsed.chatHistories)) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
};

const createWelcomeMessage = (): Message => ({
  id: `welcome-${Date.now()}`,
  role: 'assistant',
  content: 'Hello! I\'m your AI code generator. I can help you create code in various programming languages. What would you like me to help you build today?',
  timestamp: new Date(),
});

const Generator = () => {
  const cachedUi = readGeneratorUiCache();
  const extractCleanCode = (raw: string) => {
    const text = (raw || '').trim();
    const fencedAnywhere = text.match(/```(?:\w+)?\s*([\s\S]*?)\s*```/);
    if (fencedAnywhere?.[1]) {
      return fencedAnywhere[1].trim();
    }
    const fenced = text.match(/^```(?:\w+)?\s*([\s\S]*?)\s*```$/);
    if (fenced) {
      return fenced[1].trim();
    }
    const withoutTicks = text.replace(/```/g, '').trim();
    const lines = withoutTicks.split('\n').map((line) => line.trimEnd());
    const filtered = lines.filter((line, index) => {
      const l = line.trim().toLowerCase();
      if (!l) return true;
      if (index === 0 && (l === 'java' || l === ':java')) return false;
      if (index === 0 && l.startsWith("here's a java solution for your request")) return false;
      return true;
    });
    return filtered.join('\n').trim();
  };

  const getGeneratedCodeName = (prompt: string, code: string) => {
    const classMatch = code.match(/public\s+class\s+([A-Za-z_]\w*)/);
    if (classMatch?.[1]) {
      return classMatch[1];
    }
    const cleanedPrompt = prompt.replace(/\s+/g, ' ').trim();
    if (!cleanedPrompt) {
      return 'requested code';
    }
    return cleanedPrompt.length > 48 ? `${cleanedPrompt.slice(0, 48)}...` : cleanedPrompt;
  };

  const isLikelyJavaCode = (text: string) => {
    const value = (text || '').trim();
    if (!value) return false;
    const markers = ['public class', 'class ', 'public static void main', 'System.out', ';', '{', '}'];
    return markers.filter((marker) => value.includes(marker)).length >= 2;
  };

  const formatAssistantCodeMessage = (content: string, code?: string) => {
    const rawCode = (code || '').trim() || (isLikelyJavaCode(content) ? content : '');
    if (!rawCode) {
      return content || '';
    }
    const cleanedCode = extractCleanCode(rawCode);
    if (!cleanedCode) {
      return content || '';
    }
    const alreadyFormatted = (content || '').includes("Here's a Java solution for your request:")
      && (content || '').includes('is generated successfully');
    if (alreadyFormatted) {
      return content;
    }
    const codeName = getGeneratedCodeName('', cleanedCode);
    return `Here's a Java solution for your request:\n\n${cleanedCode}\n\nRequested code "${codeName}" is generated successfully 🙂`;
  };
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>(() => {
    if (!cachedUi || cachedUi.messages.length === 0) {
      return [createWelcomeMessage()];
    }
    return cachedUi.messages.map((item) => ({
      id: item.id,
      role: item.role,
      content: item.content,
      code: item.code,
      timestamp: item.timestamp ? new Date(item.timestamp) : new Date(),
    }));
  });
  
  const [inputValue, setInputValue] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [chatHistories, setChatHistories] = useState<ChatHistory[]>(() =>
    cachedUi
      ? cachedUi.chatHistories.map((item) => ({
          id: item.id,
          title: item.title,
          lastMessage: item.lastMessage ? new Date(item.lastMessage) : new Date(),
          messageCount: item.messageCount || 0,
        }))
      : []
  );
  const [activeChatId, setActiveChatId] = useState<number | null>(cachedUi?.activeChatId ?? null);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [editingChatId, setEditingChatId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [workingChatId, setWorkingChatId] = useState<number | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [skillPoints, setSkillPoints] = useState<number>(() => {
    try {
      const raw = localStorage.getItem('user');
      if (!raw) return 0;
      const parsed = JSON.parse(raw) as { total_points?: number };
      return Number(parsed.total_points || 0);
    } catch {
      return 0;
    }
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<{
    start: () => void;
    stop: () => void;
    onend: (() => void) | null;
    onerror: ((event: { error?: string }) => void) | null;
    onresult: ((event: {
      resultIndex: number;
      results: ArrayLike<{ 0: { transcript: string }; isFinal: boolean }>;
    }) => void) | null;
  } | null>(null);
  const voiceBaseTextRef = useRef('');
  const voiceFinalTranscriptRef = useRef('');
  const voiceManualStopRef = useRef(false);

  // Auto-scroll to bottom when new messages are added or when generating
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isGenerating]);

  useEffect(() => {
    try {
      const payload: GeneratorUiCache = {
        activeChatId,
        chatHistories: chatHistories.map((item) => ({
          id: item.id,
          title: item.title,
          lastMessage: item.lastMessage.toISOString(),
          messageCount: item.messageCount,
        })),
        messages: messages.map((item) => ({
          id: item.id,
          role: item.role,
          content: item.content,
          code: item.code,
          timestamp: item.timestamp.toISOString(),
        })),
      };
      localStorage.setItem(GENERATOR_UI_CACHE_KEY, JSON.stringify(payload));
    } catch {
      void 0;
    }
  }, [messages, chatHistories, activeChatId]);

  useEffect(() => {
    let isMounted = true;
    const syncPoints = async () => {
      try {
        const profile = await profileAPI.getProfile();
        if (!isMounted) return;
        const points = Number(profile.total_points || 0);
        setSkillPoints(points);
        try {
          const raw = localStorage.getItem('user');
          if (raw) {
            const user = JSON.parse(raw) as Record<string, unknown>;
            user.total_points = points;
            localStorage.setItem('user', JSON.stringify(user));
          }
        } catch {
          void 0;
        }
      } catch {
        void 0;
      }
    };
    void syncPoints();
    const interval = window.setInterval(() => {
      void syncPoints();
    }, 15000);
    return () => {
      isMounted = false;
      window.clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        voiceManualStopRef.current = true;
        recognitionRef.current.stop();
      }
    };
  }, []);

  const stopVoiceInput = () => {
    if (recognitionRef.current) {
      voiceManualStopRef.current = true;
      recognitionRef.current.stop();
    }
  };

  const upsertHistoryItem = (chatId: number, title?: string) => {
    setChatHistories((prev) => {
      const now = new Date();
      const existing = prev.find((item) => item.id === chatId);
      const nextItem: ChatHistory = {
        id: chatId,
        title: title || existing?.title || 'New Generation Chat',
        lastMessage: now,
        messageCount: (existing?.messageCount || 0) + 2,
      };
      const filtered = prev.filter((item) => item.id !== chatId);
      return [nextItem, ...filtered];
    });
  };

  const loadChat = async (chatId: number) => {
    try {
      const response = await generatorAPI.getChat(chatId);
      const serverMessages = (response.chat.messages || []).map((item) => ({
        id: String(item.id),
        role: item.role,
        content: item.role === 'assistant'
          ? formatAssistantCodeMessage(item.content || '', item.code || undefined)
          : (item.content || ''),
        code: item.code || undefined,
        timestamp: item.timestamp ? new Date(item.timestamp) : new Date(),
      })) as Message[];
      setActiveChatId(chatId);
      setMessages([createWelcomeMessage(), ...serverMessages]);
    } catch (error) {
      toast({
        title: "Failed to load chat",
        description: error instanceof Error ? error.message : 'Unable to load selected chat.',
        variant: "destructive",
      });
    }
  };

  const startNewChat = async () => {
    try {
      const response = await generatorAPI.createChat('New Generation Chat');
      const chat = response.chat;
      const nextHistory: ChatHistory = {
        id: chat.id,
        title: chat.title,
        lastMessage: chat.updated_at ? new Date(chat.updated_at) : new Date(),
        messageCount: Array.isArray(chat.messages) ? chat.messages.length : 0,
      };
      setChatHistories((prev) => [nextHistory, ...prev.filter((item) => item.id !== chat.id)]);
      setActiveChatId(chat.id);
      setMessages([createWelcomeMessage()]);
      setInputValue('');
    } catch (error) {
      toast({
        title: "Failed to create chat",
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: "destructive",
      });
    }
  };

  const startEditChat = (chat: ChatHistory) => {
    setEditingChatId(chat.id);
    setEditingTitle(chat.title);
  };

  const cancelEditChat = () => {
    setEditingChatId(null);
    setEditingTitle('');
  };

  const saveEditChat = async (chatId: number) => {
    const nextTitle = editingTitle.trim();
    if (!nextTitle) {
      toast({
        title: "Invalid title",
        description: "Chat title cannot be empty.",
        variant: "destructive",
      });
      return;
    }
    setWorkingChatId(chatId);
    try {
      const response = await generatorAPI.renameChat(chatId, nextTitle);
      setChatHistories((prev) =>
        prev.map((item) => (item.id === chatId ? { ...item, title: response.chat.title } : item))
      );
      cancelEditChat();
    } catch (error) {
      const errorText = error instanceof Error ? error.message : 'Unable to rename chat.';
      const friendly = errorText.toLowerCase().includes('405') || errorText.toLowerCase().includes('method not allowed')
        ? 'Backend is running an older version. Restart backend server and try again.'
        : errorText;
      toast({
        title: "Rename failed",
        description: friendly,
        variant: "destructive",
      });
    } finally {
      setWorkingChatId(null);
    }
  };

  const removeChat = async (chatId: number) => {
    setWorkingChatId(chatId);
    try {
      await generatorAPI.deleteChat(chatId);
      setChatHistories((prev) => prev.filter((item) => item.id !== chatId));
      if (activeChatId === chatId) {
        const next = chatHistories.find((item) => item.id !== chatId);
        if (next) {
          await loadChat(next.id);
        } else {
          await startNewChat();
        }
      }
      toast({
        title: "Chat deleted",
        description: "Saved chat removed successfully.",
      });
    } catch (error) {
      const errorText = error instanceof Error ? error.message : 'Unable to delete chat.';
      const friendly = errorText.toLowerCase().includes('405') || errorText.toLowerCase().includes('method not allowed')
        ? 'Backend is running an older version. Restart backend server and try again.'
        : errorText;
      toast({
        title: "Delete failed",
        description: friendly,
        variant: "destructive",
      });
    } finally {
      if (editingChatId === chatId) {
        cancelEditChat();
      }
      setWorkingChatId(null);
    }
  };

  useEffect(() => {
    let mounted = true;
    const loadHistory = async () => {
      setIsHistoryLoading(true);
      try {
        const response = await generatorAPI.getHistory();
        if (!mounted) return;
        const mapped = (response.history || []).map((item) => ({
          id: item.id,
          title: item.title || 'New Generation Chat',
          lastMessage: item.updated_at ? new Date(item.updated_at) : new Date(),
          messageCount: item.message_count || 0,
        })) as ChatHistory[];
        setChatHistories(mapped);
        if (mapped.length > 0) {
          await loadChat(mapped[0].id);
        } else {
          await startNewChat();
        }
      } catch (error) {
        if (!mounted) return;
        const errorText = error instanceof Error ? error.message : 'Failed to fetch history.';
        if (errorText.toLowerCase().includes('session expired')) {
          navigate('/login');
          return;
        }
        toast({
          title: "History unavailable",
          description: errorText,
          variant: "destructive",
        });
      } finally {
        if (mounted) {
          setIsHistoryLoading(false);
        }
      }
    };
    loadHistory();
    return () => {
      mounted = false;
    };
  }, []);

  const handleSend = async () => {
    stopVoiceInput();
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const prompt = inputValue;
    setInputValue('');
    setIsGenerating(true);

    try {
      // Call backend API for code generation
      const response = await generatorAPI.generateCode(prompt, 'java', activeChatId);
      const cleanedCode = extractCleanCode(response.code || '');
      const codeName = getGeneratedCodeName(prompt, cleanedCode);
      if (typeof response.remaining_points === 'number') {
        setSkillPoints(response.remaining_points);
        try {
          const raw = localStorage.getItem('user');
          if (raw) {
            const user = JSON.parse(raw) as Record<string, unknown>;
            user.total_points = response.remaining_points;
            localStorage.setItem('user', JSON.stringify(user));
          }
        } catch {
          void 0;
        }
      }
      
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Here's a Java solution for your request:\n\n${cleanedCode}\n\nRequested code "${codeName}" is generated successfully 🙂`,
        timestamp: new Date(),
        code: cleanedCode
      };
      
      setMessages(prev => [...prev, aiResponse]);
      if (response.chat_id) {
        setActiveChatId(response.chat_id);
        upsertHistoryItem(response.chat_id, response.chat_title);
      }
    } catch (error) {
      const errorText = error instanceof Error ? error.message : 'Failed to generate code. Please try again.';
      if (errorText.includes('Only Java Language Supported.')) {
        const languageGuardMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: 'Only Java Language Supported. ',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, languageGuardMessage]);
        return;
      }
      if (errorText.toLowerCase().includes('session expired')) {
        toast({
          title: "Session expired",
          description: "Please login again to continue.",
          variant: "destructive"
        });
        navigate('/login');
        return;
      }
      toast({
        title: "Generation failed",
        description: errorText,
        variant: "destructive"
      });
      
      const errorMessageItem: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I apologize, but I encountered an error while generating code: ${errorText}. Please try again or rephrase your request.`,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessageItem]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (isListening) {
      stopVoiceInput();
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearChat = () => {
    void startNewChat();
  };

  const handleVoiceInput = () => {
    const RecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!RecognitionCtor) {
      toast({
        title: "Voice input not supported",
        description: "Your browser does not support speech recognition.",
        variant: "destructive"
      });
      return;
    }
    if (isListening && recognitionRef.current) {
      stopVoiceInput();
      return;
    }
    const recognition = new RecognitionCtor();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    voiceManualStopRef.current = false;
    voiceBaseTextRef.current = inputValue ? `${inputValue.trim()} ` : "";
    voiceFinalTranscriptRef.current = "";
    recognition.onresult = (event) => {
      let interimTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const piece = event.results[i][0].transcript || "";
        if (event.results[i].isFinal) {
          voiceFinalTranscriptRef.current += `${piece} `;
        } else {
          interimTranscript += piece;
        }
      }
      const combined = `${voiceBaseTextRef.current}${voiceFinalTranscriptRef.current}${interimTranscript}`.trim();
      setInputValue(combined);
    };
    recognition.onerror = (event) => {
      if (voiceManualStopRef.current || event?.error === 'aborted') {
        return;
      }
      if (event?.error === 'no-speech') {
        return;
      }
      setIsListening(false);
      recognitionRef.current = null;
      toast({
        title: "Voice input error",
        description: "Could not capture voice. Please try again.",
        variant: "destructive"
      });
    };
    recognition.onend = () => {
      if (voiceManualStopRef.current) {
        setIsListening(false);
        recognitionRef.current = null;
        return;
      }
      try {
        recognition.start();
      } catch {
        setTimeout(() => {
          try {
            recognition.start();
          } catch {
            setIsListening(false);
            recognitionRef.current = null;
          }
        }, 120);
      }
    };
    recognitionRef.current = recognition;
    setIsListening(true);
    recognition.start();
  };

  const copyCode = (content: string, code?: string) => {
    const codeToCopy = (code || '').trim() || content.trim();
    if (!codeToCopy) return;
    navigator.clipboard.writeText(codeToCopy);
    toast({
      title: "Code copied!",
      description: "Code has been copied to clipboard."
    });
  };

  return (
    <AppLayout>
      <div className="flex h-[calc(100vh-6rem)] relative -m-6">
        {/* Main Chat Interface */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-4 mx-6 mt-4 mb-0 border-b border-border/20 bg-gradient-to-r from-background/95 to-muted/20 backdrop-blur-sm">
            <div className="flex items-center">
              <div className="p-2 rounded-xl bg-gradient-to-br from-primary to-accent mr-3">
                <Code2 className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                Code Generator
              </h1>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className="px-3 py-1.5 rounded-md border border-primary/30 bg-primary/10 text-sm font-medium">
                Skill Points: {skillPoints}
              </div>
              <Button 
                variant="outline" 
                size="sm"
                onClick={handleClearChat}
                className="text-destructive hover:text-destructive hover:bg-destructive/10 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
              {!showHistory && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowHistory(true)}
                  className="hover:bg-primary/10 transition-colors"
                >
                  <History className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>

          {/* Messages */}
          <ScrollArea className="flex-1 p-6 mx-6 bg-gradient-to-b from-background to-muted/10 h-[calc(100vh-16rem)]">
            <div className="max-w-4xl mx-auto space-y-6 min-h-full">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`group flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'} animate-in slide-in-from-bottom-2 duration-300`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl p-4 shadow-sm ${
                      message.role === 'user'
                        ? 'bg-gradient-to-br from-primary to-accent text-white'
                        : 'bg-card border border-border/50 backdrop-blur-sm'
                    }`}
                  >
                    <div className="whitespace-pre-wrap text-sm leading-relaxed">
                      {message.content}
                    </div>
                  </div>
                  
                  <div className={`flex items-center gap-1 mt-2 transition-opacity ${message.role === 'assistant' ? 'ml-2' : 'mr-2 justify-end opacity-0 group-hover:opacity-100'}`}>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 hover:bg-muted/50 transition-colors"
                        onClick={() => copyCode(message.content, message.code)}
                        title="Copy"
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                </div>
              ))}
              
              {isGenerating && (
                <div className="flex justify-start animate-in slide-in-from-bottom-2 duration-300">
                  <div className="bg-card border border-border/50 backdrop-blur-sm rounded-2xl p-4 max-w-[80%] shadow-sm">
                    <div className="flex items-center space-x-3">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                      </div>
                      <span className="text-sm text-muted-foreground">Generating your code...</span>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Scroll target for auto-scroll */}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input Area original */}
          {/* <div className="border-t border-border/20 px-6 py-2 mx-6 mt-0 bg-card/50 backdrop-blur-sm">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-end space-x-4">
                <div className="flex-1 relative">
                  <Input
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Describe what code you want me to generate..."
                    className="pr-12 h-12 text-base rounded-xl border-2 focus:border-primary/50 transition-colors"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 hover:bg-primary/10 transition-colors"
                    onClick={handleVoiceInput}
                  >
                    <Mic className="w-4 h-4" />
                  </Button>
                </div>
                <Button 
                  onClick={handleSend} 
                  disabled={!inputValue.trim() || isGenerating}
                  className="bg-gradient-to-r from-primary to-accent hover:from-primary/90 hover:to-accent/90 h-12 px-6 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
              <div className="flex items-center justify-center mt-3">
                <p className="text-xs text-muted-foreground">
                  Press Enter to send • Shift+Enter for new line
                </p>
              </div>
            </div>
          </div> */}

        {/* Input Area */}
        <div className="border-t border-border/20 px-6 py-4 bg-card/50 backdrop-blur-sm mt-auto">
          <div className="max-w-4xl mx-auto flex items-end space-x-4">
            <div className="flex-1 relative">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleInputKeyDown}
                placeholder="Describe what code you want me to generate..."
                className="pr-12 h-12 text-base rounded-xl border-2 focus:border-primary/50 transition-colors"
              />
              <Button
                variant="ghost"
                size="sm"
                className={`absolute right-2 top-1/2 -translate-y-1/2 hover:bg-primary/10 transition-colors ${isListening ? 'text-primary' : ''}`}
                onClick={handleVoiceInput}
                title={isListening ? "Stop voice input" : "Start voice input"}
              >
                <Mic className="w-4 h-4" />
              </Button>
            </div>
            <Button 
              onClick={handleSend} 
              disabled={!inputValue.trim() || isGenerating}
              className="bg-gradient-to-r from-primary to-accent hover:from-primary/90 hover:to-accent/90 h-12 px-6 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
       </div>

        {/* Chat History Sidebar - Right Side */}
        <div className={`${showHistory ? 'w-72' : 'w-0'} transition-all duration-300 overflow-hidden border-l border-border/20 bg-card/30 backdrop-blur-sm`}>
          <Card className="h-full rounded-none border-0 bg-transparent">
            <CardHeader className="border-b border-border/20 bg-gradient-to-r from-card to-muted/20">
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center">
                  <History className="w-5 h-5 mr-2 text-primary" />
                  History
                </div>
                <div className="flex items-center space-x-1">
                  <Button variant="ghost" size="sm" onClick={startNewChat} className="hover:bg-primary/10">
                    <Plus className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setShowHistory(false)} className="hover:bg-destructive/10">
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[calc(100vh-240px)]">
                {isHistoryLoading ? (
                  <div className="p-4 text-sm text-muted-foreground">Loading chats...</div>
                ) : null}
                {!isHistoryLoading && chatHistories.length === 0 ? (
                  <div className="p-4 text-sm text-muted-foreground">No chats yet</div>
                ) : null}
                {chatHistories.map((chat) => (
                  <div
                    key={chat.id}
                    className={`p-3 border-b border-border/10 hover:bg-primary/5 cursor-pointer transition-all duration-200 group ${
                      activeChatId === chat.id ? 'bg-primary/10' : ''
                    }`}
                    onClick={() => {
                      if (editingChatId !== chat.id) {
                        void loadChat(chat.id);
                      }
                    }}
                  >
                    <div className="flex items-start gap-2">
                      <MessageSquare className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors mt-0.5" />
                      <div className="min-w-0 flex-1">
                        {editingChatId === chat.id ? (
                          <div className="flex items-center gap-1">
                            <Input
                              value={editingTitle}
                              onChange={(e) => setEditingTitle(e.target.value)}
                              className="h-7 text-xs"
                              onClick={(e) => e.stopPropagation()}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  e.preventDefault();
                                  void saveEditChat(chat.id);
                                }
                                if (e.key === 'Escape') {
                                  e.preventDefault();
                                  cancelEditChat();
                                }
                              }}
                              autoFocus
                            />
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0"
                              onClick={(e) => {
                                e.stopPropagation();
                                void saveEditChat(chat.id);
                              }}
                              disabled={workingChatId === chat.id}
                            >
                              <Check className="w-3.5 h-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0"
                              onClick={(e) => {
                                e.stopPropagation();
                                cancelEditChat();
                              }}
                              disabled={workingChatId === chat.id}
                            >
                              <X className="w-3.5 h-3.5" />
                            </Button>
                          </div>
                        ) : (
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0">
                              <div className="text-sm font-medium truncate">{chat.title}</div>
                            </div>
                            <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 w-7 p-0"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  startEditChat(chat);
                                }}
                                disabled={workingChatId === chat.id}
                              >
                                <Pencil className="w-3.5 h-3.5" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  void removeChat(chat.id);
                                }}
                                disabled={workingChatId === chat.id}
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
};

export default Generator;
