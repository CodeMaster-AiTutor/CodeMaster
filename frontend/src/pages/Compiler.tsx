import React, { useState, useRef, useEffect, useCallback, useLayoutEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { 
  Play, 
  Share2, 
  Copy, 
  Download, 
  Maximize2,
  Minimize2,
  Terminal,
  Code2,
  Zap,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import AppLayout from '@/components/layout/AppLayout';
import { compilerAPI } from '@/lib/api';

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



const Compiler = () => {
  const navigate = useNavigate();
  const initialCode = '';
  const codeStorageKey = 'compiler:code';
  const outputStorageKey = 'compiler:output';

  // Use refs for everything to prevent re-renders
  const codeRef = useRef(initialCode);
  const [code, setCode] = useState(initialCode);
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [executionStatus, setExecutionStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const outputRef = useRef<HTMLDivElement>(null);
  const compilerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLPreElement>(null);
  const errorDetectionTimeoutRef = useRef<NodeJS.Timeout | null>(null);



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
  const handleCodeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const nextValue = e.target.value;
    scrollPositionRef.current = e.target.scrollTop;
    selectionRef.current = {
      start: e.target.selectionStart,
      end: e.target.selectionEnd
    };
    codeRef.current = nextValue;
    setCode(nextValue);
    try {
      localStorage.setItem(codeStorageKey, codeRef.current);
    } catch (error) {
      void error;
    }
  };

  // Simple scroll handler
  const handleScroll = useCallback(() => {
    if (textareaRef.current && lineNumbersRef.current) {
      scrollPositionRef.current = textareaRef.current.scrollTop;
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  }, []);

  // Real Java compilation and execution using backend API
  const compileAndExecuteJava = async (javaCode: string): Promise<{ success: boolean; output: string; error?: string }> => {
    try {
      const requestId = typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
      const response = await compilerAPI.compileAndRun(javaCode, requestId);
      
      if (response.success) {
        const executionTime = response.execution_time 
          ? `${response.execution_time.toFixed(3)} seconds`
          : '';
        const output = response.output || 'Program executed successfully (no output)';
        const outputWithTime = executionTime 
          ? `${output}\n\nProgram executed successfully in ${executionTime}.`
          : output;
        
        return {
          success: true,
          output: outputWithTime
        };
      } else {
        // Handle compilation/execution errors
        const errorMessages = response.errors 
          ? response.errors.map(err => `${err.message} (line ${err.line})`).join('\n')
          : response.error || 'Compilation failed';
        const errorWithRequest = response.request_id ? `${errorMessages}\n\nRequest ID: ${response.request_id}` : errorMessages;
        
        return {
          success: false,
          output: '',
          error: errorWithRequest
        };
      }
    } catch (error) {
      return {
        success: false,
        output: '',
        error: `Execution error: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  };

  // Fullscreen functions
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
  }, []);

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

  // Handle fullscreen change events and cleanup
  useEffect(() => {
    try {
      const savedCode = localStorage.getItem(codeStorageKey);
      if (savedCode !== null) {
        codeRef.current = savedCode;
        setCode(savedCode);
      }
      const savedOutput = localStorage.getItem(outputStorageKey);
      if (savedOutput) {
        setOutput(savedOutput);
      }
    } catch (error) {
      void error;
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

    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('keydown', handleGlobalKeyDown);
      
      // Cleanup error detection timeout
      if (errorDetectionTimeoutRef.current) {
        clearTimeout(errorDetectionTimeoutRef.current);
      }
    };
  }, []);

  // Enhanced handleRun with real compilation
  const handleRun = async () => {
    const authToken = localStorage.getItem("access_token");
    if (!authToken) {
      setExecutionStatus('error');
      const message = 'Missing Authorization Header. Please log in again.';
      setOutput(message);
      try {
        localStorage.setItem(outputStorageKey, message);
      } catch (error) {
        void error;
      }
      toast({
        title: "Login required",
        description: "Please log in to run code.",
        variant: "destructive"
      });
      navigate('/login');
      return;
    }
    setIsRunning(true);
    setExecutionStatus('idle');
    setOutput('Compiling...\n');
    try {
      localStorage.setItem(outputStorageKey, 'Compiling...\n');
    } catch (error) {
      void error;
    }
    
    // Get current code from textarea ref
    const currentCode = textareaRef.current?.value || codeRef.current;
    try {
      localStorage.setItem(codeStorageKey, currentCode);
    } catch (error) {
      void error;
    }
    
    try {
      const result = await compileAndExecuteJava(currentCode);
      
      if (result.success) {
        setOutput(result.output);
        setExecutionStatus('success');
        try {
          localStorage.setItem(outputStorageKey, result.output);
        } catch (error) {
          void error;
        }
        toast({
          title: "Compilation successful!",
          description: "Your Java code executed successfully."
        });
      } else {
        setOutput(result.error || 'Compilation failed');
        setExecutionStatus('error');
        try {
          localStorage.setItem(outputStorageKey, result.error || 'Compilation failed');
        } catch (error) {
          void error;
        }
        toast({
          title: "Compilation failed",
          description: "Please check your code for errors.",
          variant: "destructive"
        });
      }
    } catch (error) {
      setOutput(`Unexpected error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setExecutionStatus('error');
      try {
        localStorage.setItem(outputStorageKey, `Unexpected error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      } catch (storageError) {
        void storageError;
      }
      toast({
        title: "Execution error",
        description: "An unexpected error occurred.",
        variant: "destructive"
      });
    } finally {
      setIsRunning(false);
    }
  };

  // Removed cursor position restoration effect to prevent jumping

  // Restore scroll position effect - using ref instead of state
  const scrollPositionRef = useRef(0);
  const selectionRef = useRef<{start: number; end: number}>({ start: 0, end: 0 });
  
  useEffect(() => {
    if (textareaRef.current && scrollPositionRef.current >= 0) {
      textareaRef.current.scrollTop = scrollPositionRef.current;
    }
  }, []);

  useLayoutEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.scrollTop = scrollPositionRef.current;
      const { start, end } = selectionRef.current;
      textareaRef.current.setSelectionRange(start, end);
    }
  }, [code]);

  const handleCopy = () => {
    const currentCode = textareaRef.current?.value || codeRef.current;
    navigator.clipboard.writeText(currentCode);
    toast({
      title: "Code copied!",
      description: "Code has been copied to clipboard."
    });
  };

  const handleShare = () => {
    toast({
      title: "Share link generated!",
      description: "Share link has been copied to clipboard."
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

  const CompilerContent = () => ( 
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
                  <Button variant="outline" onClick={handleShare} className="hover:bg-primary/10 transition-all duration-200 p-2 sm:px-4" title="Share"> 
                    <Share2 className="w-3 h-3 sm:w-4 sm:h-4" /> 
                  </Button> 
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
                    <Terminal className="w-4 h-4 sm:w-5 sm:h-5 text-accent" /> 
                  </div> 
                  <div> 
                    <h2 className="text-base sm:text-lg font-semibold text-foreground">Console Output</h2> 
                    <p className="text-xs sm:text-sm text-muted-foreground">Execution results</p> 
                  </div> 
                </div> 
              </div> 
  
              <div className={`bg-gradient-to-br from-card/80 to-card/60 backdrop-blur-sm border border-accent/10 rounded-b-xl overflow-hidden shadow-2xl ${isFullscreen ? 'h-[35vh]' : 'h-[30vh]'}`}> 
                <div ref={outputRef} className="h-full p-2 sm:p-3 md:p-4 overflow-y-auto">
                  <pre className="font-mono text-xs sm:text-sm text-foreground whitespace-pre-wrap">
                    {output || "Ready to execute your code..."}
                  </pre>
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
  );

  return (
    <AppLayout>
      <div ref={compilerRef}>
        <CompilerContent />
      </div>
    </AppLayout>
  );
};

export default Compiler;
