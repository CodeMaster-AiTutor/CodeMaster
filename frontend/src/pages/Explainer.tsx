import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Brain, Code2, Lightbulb, Copy, Trash2 } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import AppLayout from '@/components/layout/AppLayout';
import { explainerAPI } from '@/lib/api';
import { useNavigate } from 'react-router-dom';

const Explainer = () => {
  const navigate = useNavigate();
  const [code, setCode] = useState('');
  const [explanation, setExplanation] = useState('');
  const [isLoading, setIsLoading] = useState(false);



  const handleExplain = async () => {
    if (!code.trim()) {
      toast({
        title: "No code provided",
        description: "Please paste some code to explain.",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);
    
    try {
      // Call backend API for code explanation
      const response = await explainerAPI.explainCode(code, 'java');
      
      // Format explanation with breakdown if available
      let formattedExplanation = response.explanation || '';
      
      if (response.breakdown && response.breakdown.length > 0) {
        formattedExplanation += '\n\n**Line-by-Line Breakdown:**\n\n';
        response.breakdown.forEach(item => {
          formattedExplanation += `**Line ${item.line}: ${item.code.trim()}**\n`;
          formattedExplanation += `${item.explanation}\n\n`;
        });
      }
      
      setExplanation(formattedExplanation);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to explain code. Please try again.';
      if (errorMessage.toLowerCase().includes('session expired')) {
        toast({
          title: "Session expired",
          description: "Please login again to continue.",
          variant: "destructive"
        });
        navigate('/login');
        return;
      }
      toast({
        title: "Explanation failed",
        description: errorMessage,
        variant: "destructive"
      });
      setExplanation('');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyExplanation = () => {
    navigator.clipboard.writeText(explanation);
    toast({
      title: "Explanation copied!",
      description: "The explanation has been copied to your clipboard."
    });
  };

  const handleClear = () => {
    setCode('');
    setExplanation('');
    toast({
      title: "Cleared!",
      description: "Code input and explanation have been cleared."
    });
  };

  // Interactive highlighting functionality can be added here in the future

  return (
    <AppLayout>
      <div className="h-[calc(100vh-8rem)] -m-6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 mx-6 mt-4 mb-0 border-b border-border/20 bg-gradient-to-r from-background/95 to-muted/20 backdrop-blur-sm">
          <div className="flex items-center">
            <div className="p-2 rounded-xl bg-gradient-to-br from-primary to-accent mr-3">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              Code Explainer
            </h1>
          </div>
          
          <div className="flex items-center space-x-3">
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleExplain}
              disabled={!code.trim() || isLoading}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 mr-2 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Explaining...
                </>
              ) : (
                <>
                  <Brain className="w-4 h-4 mr-2" />
                  Explain
                </>
              )}
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleClear}
              className="text-destructive hover:text-destructive hover:bg-destructive/10 transition-colors"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Clear
            </Button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 mx-6 mt-4 mb-4">
          <div className="flex h-[calc(100vh-200px)]">
            {/* Left Panel - Code Input */}
            <div className="flex-1 bg-gray-900/50 dark:bg-gray-950/70 border border-border flex flex-col">
              <div className="p-3 border-b border-border bg-gray-800/60 dark:bg-gray-900/80">
                <div className="flex items-center">
                  <Code2 className="w-5 h-5 mr-2 text-primary" />
                  <h3 className="font-semibold">Code Input</h3>
                </div>
              </div>
              <div className="flex-1 p-4 flex flex-col">
                <Textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="flex-1 font-mono text-sm resize-none border-0 bg-transparent focus:ring-0 focus:outline-none focus-visible:ring-0 focus-visible:ring-offset-0"
                  placeholder="Paste your code here to get an AI-powered explanation...

Examples:
• JavaScript functions
• Python classes  
• Java methods
• SQL queries
• And much more!"
                />
              </div>
            </div>

            {/* Right Panel - Explanation */}
            <div className="flex-1 bg-gray-900/50 dark:bg-gray-950/70 border-t border-r border-b border-border flex flex-col">
              <div className="p-3 border-b border-border bg-gray-800/60 dark:bg-gray-900/80">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Lightbulb className="w-5 h-5 mr-2 text-primary" />
                    <h3 className="font-semibold">Code Explanation</h3>
                  </div>
                  {explanation && (
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={handleCopyExplanation}
                      className="h-6 w-6 p-0"
                    >
                      <Copy className="w-3 h-3" />
                    </Button>
                  )}
                </div>
              </div>
              <div className="flex-1 p-4 overflow-hidden">
                {explanation ? (
                  <div className="prose prose-sm max-w-none dark:prose-invert h-full">
                    <div className="space-y-4 h-full overflow-y-auto explanation-scrollbar pr-2">
                      {explanation.split('\n\n').map((paragraph, index) => (
                        <div key={index}>
                          {paragraph.startsWith('**') && paragraph.endsWith('**') ? (
                            <h3 className="font-semibold text-primary mb-2 flex items-center">
                              <Lightbulb className="w-4 h-4 mr-2" />
                              {paragraph.slice(2, -2)}
                            </h3>
                          ) : paragraph.startsWith('```') ? (
                            <pre className="bg-muted p-4 rounded-lg font-mono text-sm overflow-x-auto">
                              <code>{paragraph.slice(3, -3)}</code>
                            </pre>
                          ) : /^[-*•]\s+/.test(paragraph.trim()) ? (
                            <ul className="ml-2 space-y-2">
                              {paragraph
                                .split('\n')
                                .map((line) => line.trim())
                                .filter((line) => /^[-*•]\s+/.test(line))
                                .map((line, bulletIndex) => (
                                  <li key={`${index}-${bulletIndex}`} className="text-white leading-relaxed">
                                    • {line.replace(/^[-*•]\s+/, '')}
                                  </li>
                                ))}
                            </ul>
                          ) : (
                            <p className="text-white leading-relaxed">{paragraph}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center text-muted-foreground">
                    <div className="text-center space-y-3">
                      <Brain className="w-12 h-12 mx-auto text-muted-foreground/50" />
                      <div className="space-y-1">
                        <p className="font-medium">Ready to explain your code!</p>
                        <p className="text-sm">Paste your code in the left panel and click "Explain Code" to get a detailed explanation</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
};

export default Explainer;
