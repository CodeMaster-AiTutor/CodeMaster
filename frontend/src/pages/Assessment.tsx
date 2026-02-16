import React, { useState, useEffect, useCallback } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Trophy, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Brain, 
  Target,
  ArrowRight,
  RotateCcw,
  Award,
  Zap,
  Loader2
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { assessmentAPI } from '@/lib/api';

interface Question {
  id: number;
  type: 'multiple-choice' | 'code-completion' | 'debugging';
  question: string;
  options?: string[] | null;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
}

const Assessment = () => {
  const [currentLevel, setCurrentLevel] = useState<'beginner' | 'intermediate' | 'advanced'>('beginner');
  const [isAssessmentActive, setIsAssessmentActive] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [timeLeft, setTimeLeft] = useState(1800); // 30 minutes
  const [isCompleted, setIsCompleted] = useState(false);
  const [score, setScore] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [assessmentId, setAssessmentId] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Get current question
  const currentQuestion = questions[currentQuestionIndex];

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const startAssessment = async () => {
    setIsLoading(true);
    try {
      // Start assessment and get questions
      const [startResponse, questionsResponse] = await Promise.all([
        assessmentAPI.startAssessment(currentLevel),
        assessmentAPI.getQuestions(currentLevel)
      ]);

      setAssessmentId(startResponse.assessment_id);
      setQuestions(questionsResponse.questions);
      setIsAssessmentActive(true);
      setCurrentQuestionIndex(0);
      setAnswers({});
      setTimeLeft(1800);
      setIsCompleted(false);
      setShowResults(false);
      setScore(0);
      
      toast({
        title: "Assessment started!",
        description: `Good luck with your ${currentLevel} level assessment!`,
      });
    } catch (error) {
      console.error('Failed to start assessment:', error);
      toast({
        title: "Failed to start assessment",
        description: error instanceof Error ? error.message : 'Please try again later.',
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswerChange = (value: string) => {
    setAnswers(prev => ({
      ...prev,
      [currentQuestion.id]: value
    }));
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      handleCompleteAssessment();
    }
  };

  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleCompleteAssessment = useCallback(async () => {
    if (!assessmentId) {
      toast({
        title: "Error",
        description: "Assessment ID not found. Please start a new assessment.",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await assessmentAPI.submitAssessment({
        assessment_id: assessmentId,
        answers,
        level: currentLevel,
      });

      setIsCompleted(true);
      setIsAssessmentActive(false);
      setScore(response.score);
      setShowResults(true);

      // Check if user passed (80% or higher)
      if (response.passed) {
        toast({
          title: "Congratulations! 🎉",
          description: `You passed with ${response.score}%! ${response.skill_level_updated ? `Your skill level has been updated to ${response.new_skill_level}.` : 'You\'re ready for the next level.'}`,
        });
      } else {
        toast({
          title: "Keep practicing! 📚",
          description: `You scored ${response.score}%. You need 80% to advance to the next level.`,
        });
      }
    } catch (error) {
      console.error('Failed to submit assessment:', error);
      toast({
        title: "Failed to submit assessment",
        description: error instanceof Error ? error.message : 'Please try again later.',
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  }, [assessmentId, answers, currentLevel]);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isAssessmentActive && timeLeft > 0 && !isCompleted) {
      timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
    } else if (timeLeft === 0 && !isCompleted) {
      handleCompleteAssessment();
    }
    return () => clearTimeout(timer);
  }, [isAssessmentActive, timeLeft, isCompleted, handleCompleteAssessment]);

  const retakeAssessment = () => {
    setShowResults(false);
    setIsCompleted(false);
    startAssessment();
  };

  const advanceLevel = () => {
    if (currentLevel === 'beginner') {
      setCurrentLevel('intermediate');
    } else if (currentLevel === 'intermediate') {
      setCurrentLevel('advanced');
    }
    setShowResults(false);
    setIsCompleted(false);
    toast({
      title: "Level Up! 🚀",
      description: `Welcome to ${currentLevel === 'beginner' ? 'Intermediate' : 'Advanced'} level!`,
    });
  };

  if (showResults) {
    return (
      <AppLayout>
        <div className="p-4">
          <div className="max-w-4xl mx-auto space-y-4">
            <div className="text-center">
              <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                Assessment Results
              </h1>
            </div>

            <Card className="border-border/20 bg-gradient-card">
              <CardContent className="p-8 text-center">
                <div className="mb-6">
                  {score >= 80 ? (
                    <Trophy className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
                  ) : (
                    <Target className="w-16 h-16 text-blue-500 mx-auto mb-4" />
                  )}
                  <h2 className="text-2xl font-bold mb-2">
                    {score >= 80 ? 'Congratulations!' : 'Keep Practicing!'}
                  </h2>
                  <p className="text-4xl font-bold text-primary mb-2">{score}%</p>
                  <p className="text-muted-foreground">
                    You answered {Math.round((score / 100) * questions.length)} out of {questions.length} questions correctly
                  </p>
                </div>

                <div className="space-y-4">
                  {score >= 80 && currentLevel !== 'advanced' && (
                    <Button onClick={advanceLevel} className="bg-gradient-primary">
                      <Award className="w-4 h-4 mr-2" />
                      Advance to {currentLevel === 'beginner' ? 'Intermediate' : 'Advanced'} Level
                    </Button>
                  )}
                  
                  {score >= 80 && currentLevel === 'advanced' && (
                    <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                      <p className="text-yellow-600 font-medium">
                        🏆 Congratulations! You've mastered all levels!
                      </p>
                    </div>
                  )}

                  <div className="flex gap-4 justify-center">
                    <Button variant="outline" onClick={retakeAssessment}>
                      <RotateCcw className="w-4 h-4 mr-2" />
                      Retake Assessment
                    </Button>
                    <Button variant="outline" onClick={() => setShowResults(false)}>
                      Back to Overview
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </AppLayout>
    );
  }

  if (isAssessmentActive) {
    return (
      <AppLayout>
        <div className="p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold">
                  {currentLevel.charAt(0).toUpperCase() + currentLevel.slice(1)} Assessment
                </h1>
                  <p className="text-muted-foreground">
                    Question {currentQuestionIndex + 1} of {questions.length}
                  </p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4" />
                  <span className="font-mono">{formatTime(timeLeft)}</span>
                </div>
                <Badge variant="outline">
                  {questions.length > 0 ? Math.round(((currentQuestionIndex + 1) / questions.length) * 100) : 0}% Complete
                </Badge>
              </div>
            </div>

            {/* Progress */}
            <Progress value={questions.length > 0 ? ((currentQuestionIndex + 1) / questions.length) * 100 : 0} />

            {/* Question */}
            {currentQuestion ? (
              <Card className="border-border/20 bg-gradient-card">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Brain className="w-5 h-5" />
                    <span>Question {currentQuestionIndex + 1}</span>
                    <Badge variant="secondary">{currentQuestion.type}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="text-lg whitespace-pre-wrap">
                    {currentQuestion.question}
                  </div>

                  {currentQuestion.type === 'multiple-choice' && currentQuestion.options && (
                    <RadioGroup
                      value={answers[currentQuestion.id] || ''}
                      onValueChange={handleAnswerChange}
                    >
                      {currentQuestion.options.map((option, index) => (
                        <div key={index} className="flex items-center space-x-2">
                          <RadioGroupItem value={option} id={`option-${index}`} />
                          <Label htmlFor={`option-${index}`} className="flex-1 cursor-pointer">
                            {option}
                          </Label>
                        </div>
                      ))}
                    </RadioGroup>
                  )}

                  {(currentQuestion.type === 'code-completion' || currentQuestion.type === 'debugging') && (
                    <Textarea
                      placeholder="Enter your answer here..."
                      value={answers[currentQuestion.id] || ''}
                      onChange={(e) => handleAnswerChange(e.target.value)}
                      className="min-h-[120px] font-mono"
                    />
                  )}

                  <div className="flex justify-between">
                    <Button
                      variant="outline"
                      onClick={previousQuestion}
                      disabled={currentQuestionIndex === 0}
                    >
                      Previous
                    </Button>
                    <Button
                      onClick={nextQuestion}
                      disabled={!answers[currentQuestion.id] || isSubmitting}
                      className="bg-gradient-primary"
                    >
                      {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                      {currentQuestionIndex === questions.length - 1 ? 'Complete Assessment' : 'Next'}
                      {!isSubmitting && <ArrowRight className="w-4 h-4 ml-2" />}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="border-border/20 bg-gradient-card">
                <CardContent className="p-8 text-center">
                  <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
                  <p>Loading questions...</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          <div className="text-center">
            <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              Skill Assessment
            </h1>
          </div>

          {/* Current Level */}
          <Card className="border-border/20 bg-gradient-card">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Target className="w-5 h-5" />
                <span>Current Level</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-2xl font-bold capitalize">{currentLevel}</h3>
                  <p className="text-muted-foreground">
                    {currentLevel === 'beginner' && 'Master the fundamentals of programming'}
                    {currentLevel === 'intermediate' && 'Dive deeper into algorithms and design patterns'}
                    {currentLevel === 'advanced' && 'Explore complex systems and optimization'}
                  </p>
                </div>
                <Badge variant="secondary" className="text-lg px-4 py-2">
                  {currentLevel === 'beginner' && '🌱'}
                  {currentLevel === 'intermediate' && '🚀'}
                  {currentLevel === 'advanced' && '⭐'}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Assessment Info */}
          <div className="grid md:grid-cols-2 gap-6">
            <Card className="border-border/20">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Brain className="w-5 h-5" />
                  <span>Assessment Details</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span>Questions:</span>
                  <span className="font-medium">20 questions</span>
                </div>
                <div className="flex justify-between">
                  <span>Time Limit:</span>
                  <span className="font-medium">30 minutes</span>
                </div>
                <div className="flex justify-between">
                  <span>Passing Score:</span>
                  <span className="font-medium">80%</span>
                </div>
                <div className="flex justify-between">
                  <span>Question Types:</span>
                  <span className="font-medium">Mixed</span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/20">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Zap className="w-5 h-5" />
                  <span>What to Expect</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-sm">Multiple choice questions</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-sm">Code completion tasks</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-sm">Debugging challenges</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-sm">Instant feedback</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Start Assessment */}
          <Card className="border-border/20 bg-gradient-card">
            <CardContent className="p-8 text-center">
              <h3 className="text-xl font-bold mb-4">Ready to Test Your Skills?</h3>
              <p className="text-muted-foreground mb-6">
                Take the {currentLevel} level assessment to prove your knowledge and advance to the next level.
                You need to score 80% or higher to pass.
              </p>
              <Button 
                onClick={startAssessment} 
                size="lg" 
                className="bg-gradient-primary"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Loading Questions...
                  </>
                ) : (
                  <>
                    <Trophy className="w-5 h-5 mr-2" />
                    Start {currentLevel.charAt(0).toUpperCase() + currentLevel.slice(1)} Assessment
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
};

export default Assessment;
