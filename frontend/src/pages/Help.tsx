import React, { useState } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  HelpCircle, 
  Search, 
  Book, 
  MessageCircle, 
  Mail, 
  Phone,
  ChevronDown,
  ChevronRight,
  ExternalLink
} from 'lucide-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { useToast } from '@/hooks/use-toast';
import { supportAPI } from '@/lib/api';

const Help = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [openFAQ, setOpenFAQ] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [isSending, setIsSending] = useState(false);
  const { toast } = useToast();

  const validateForm = () => {
    const nextErrors: Record<string, string> = {};
    if (!formData.name.trim()) {
      nextErrors.name = 'Name is required';
    }
    if (!formData.email.trim()) {
      nextErrors.email = 'Email is required';
    } else if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(formData.email.trim())) {
      nextErrors.email = 'Enter a valid email address';
    }
    if (!formData.subject.trim()) {
      nextErrors.subject = 'Subject is required';
    }
    if (!formData.message.trim()) {
      nextErrors.message = 'Message is required';
    }
    setFormErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleFieldChange = (field: 'name' | 'email' | 'subject' | 'message', value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (formErrors[field]) {
      setFormErrors((prev) => ({ ...prev, [field]: '' }));
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!validateForm()) {
      return;
    }
    setIsSending(true);
    try {
      await supportAPI.sendMessage({
        name: formData.name.trim(),
        email: formData.email.trim(),
        subject: formData.subject.trim(),
        message: formData.message.trim()
      });
      toast({
        title: 'Message sent',
        description: 'Support has received your message. We will reply soon.'
      });
      setFormData({ name: '', email: '', subject: '', message: '' });
      setFormErrors({});
    } catch (error) {
      toast({
        title: 'Failed to send message',
        description: error instanceof Error ? error.message : 'Please try again later.',
        variant: 'destructive'
      });
    } finally {
      setIsSending(false);
    }
  };

  const faqs = [
    {
      id: 1,
      question: 'How are streaks calculated?',
      answer: 'Your streak is date-based. If you are active on consecutive days, your streak increases by 1. If you miss a day, the streak resets based on the next active day.'
    },
    {
      id: 2,
      question: 'What counts as streak activity?',
      answer: 'Completing learning actions like solving practice problems, finishing videos, and other tracked platform activities count toward daily streak continuity.'
    },
    {
      id: 3,
      question: 'Does logging in multiple times in one day increase streak?',
      answer: 'No. Logging in multiple times on the same date does not increase streak multiple times. The streak updates once per date.'
    },
    {
      id: 4,
      question: 'How do streak bonus points work?',
      answer: 'You receive milestone streak bonuses at configured intervals. Milestone rewards are recorded in your skill point history so they are not duplicated.'
    },
    {
      id: 5,
      question: 'What are skill points used for?',
      answer: 'Skill points represent your learning progress and are also used for specific features like AI generation requests where a points cost is applied.'
    },
    {
      id: 6,
      question: 'How do I earn skill points?',
      answer: 'You earn points by solving practice problems, completing videos, passing achievements, weekly goal completion, and streak bonuses.'
    },
    {
      id: 7,
      question: 'Why do points decrease sometimes?',
      answer: 'Some actions consume points, such as AI code generation requests. These appear as “used” entries in your skill points progress history.'
    },
    {
      id: 8,
      question: 'Where can I see point source history?',
      answer: 'Go to Analytics → Skill Points Progress to view record-by-record entries showing source, points delta, and timestamp.'
    },
    {
      id: 9,
      question: 'How are challenge difficulty tags shown?',
      answer: 'Trending challenge tags are color-coded by difficulty: Easy, Medium, and Hard, so you can quickly identify expected difficulty level.'
    },
    {
      id: 10,
      question: 'How are trending challenges selected?',
      answer: 'Trending challenges are selected from your current level only, grouped by difficulty buckets so you get balanced challenge recommendations.'
    },
    {
      id: 11,
      question: 'Can I directly open a challenge from Dashboard?',
      answer: 'Yes. Use the “Go to Challenge” button in Trending Challenges to open the exact problem solve page directly.'
    },
    {
      id: 12,
      question: 'How do achievements unlock?',
      answer: 'Achievements unlock when their specific completion conditions are met, such as passing assessments, solving all level problems, or completing all level videos.'
    },
    {
      id: 13,
      question: 'Are achievements locked by level?',
      answer: 'Yes. Future-level achievements remain locked until your current skill level reaches that stage.'
    },
    {
      id: 14,
      question: 'Do achievements give skill points?',
      answer: 'Yes. Achievement rewards are level-based and awarded once per achievement. Reward transactions are stored to avoid duplicate grants.'
    },
    {
      id: 15,
      question: 'How many videos are required per level for video achievements?',
      answer: 'Video completion achievement totals are configured per level: Beginner 8, Intermediate 8, and Advanced 11.'
    },
    {
      id: 16,
      question: 'What is Learning Path?',
      answer: 'Learning Path is a structured topic roadmap. It guides you through Java concepts level by level with focused concept modules and tutorials.'
    },
    {
      id: 17,
      question: 'How are Learning Path levels enforced?',
      answer: 'Access is level-aware: beginner sees beginner, intermediate gets beginner+intermediate concepts, and advanced can access all levels.'
    },
    {
      id: 18,
      question: 'Do watched Learning Path videos give points only once?',
      answer: 'Yes. Video completion points are one-time per unique video key for each user.'
    },
    {
      id: 19,
      question: 'What is Practice Arena?',
      answer: 'Practice Arena is where you solve coding problems by level and track solved/unsolved progress with real submissions and attempt history.'
    },
    {
      id: 20,
      question: 'How are Practice Arena points awarded?',
      answer: 'Practice problem points are awarded once per solved problem per user. Re-solving the same problem does not duplicate the same one-time reward.'
    },
    {
      id: 21,
      question: 'What is weekly goal in Practice and Dashboard?',
      answer: 'Weekly goal tracks solved practice problems for the current week and grants a weekly bonus when the configured target is reached.'
    },
    {
      id: 22,
      question: 'Why is some data marked as real-time?',
      answer: 'Core stats are synced periodically and after major actions. This keeps streak, points, and progress fresh across Dashboard, Analytics, and navigation.'
    },
    {
      id: 23,
      question: 'What if my displayed points or streak look outdated?',
      answer: 'Try navigating once or waiting for the sync interval. If it still looks wrong, report it via Contact Support and include screenshots and timestamp.'
    },
    {
      id: 24,
      question: 'How do I report a bug related to streak, points, or achievements?',
      answer: 'Use the Contact Support form below with steps to reproduce, expected result, actual result, and your account email so we can investigate quickly.'
    }
  ];

  const resources = [
    {
      title: 'Getting Started Guide',
      description: 'Complete guide for new users to get started with CodeMaster',
      icon: Book,
      link: '#'
    },
    {
      title: 'Algorithm Tutorials',
      description: 'In-depth tutorials on common algorithms and data structures',
      icon: Book,
      link: '#'
    },
    {
      title: 'Community Forum',
      description: 'Connect with other developers and get help from the community',
      icon: MessageCircle,
      link: '#'
    }
  ];

  const filteredFAQs = faqs.filter(faq => 
    faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
    faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <AppLayout>
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">Help & Support</h1>
        </div>

        {/* Search */}
        <Card>
          <CardContent className="pt-6">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search for help topics..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* FAQ Section */}
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <HelpCircle className="h-5 w-5" />
                  <span>Frequently Asked Questions</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 max-h-[19rem] overflow-y-hidden hover:overflow-y-auto pr-1">
                {filteredFAQs.map((faq) => (
                  <Collapsible key={faq.id}>
                    <CollapsibleTrigger
                      className="flex items-center justify-between w-full p-4 rounded-lg hover:bg-muted transition-colors"
                      onClick={() => setOpenFAQ(openFAQ === faq.id ? null : faq.id)}
                    >
                      <span className="font-medium text-left">{faq.question}</span>
                      {openFAQ === faq.id ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </CollapsibleTrigger>
                    <CollapsibleContent className="px-4 pb-4">
                      <p className="text-muted-foreground">{faq.answer}</p>
                    </CollapsibleContent>
                  </Collapsible>
                ))}
              </CardContent>
            </Card>

            {/* Contact Form */}
            <Card>
              <CardHeader>
                <CardTitle>Contact Support</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <form className="space-y-4" onSubmit={handleSubmit}>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Name</label>
                      <Input
                        placeholder="Your name"
                        value={formData.name}
                        onChange={(e) => handleFieldChange('name', e.target.value)}
                      />
                      {formErrors.name ? (
                        <p className="text-sm text-destructive">{formErrors.name}</p>
                      ) : null}
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Email</label>
                      <Input
                        type="email"
                        placeholder="your.email@example.com"
                        value={formData.email}
                        onChange={(e) => handleFieldChange('email', e.target.value)}
                      />
                      {formErrors.email ? (
                        <p className="text-sm text-destructive">{formErrors.email}</p>
                      ) : null}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Subject</label>
                    <Input
                      placeholder="Brief description of your issue"
                      value={formData.subject}
                      onChange={(e) => handleFieldChange('subject', e.target.value)}
                    />
                    {formErrors.subject ? (
                      <p className="text-sm text-destructive">{formErrors.subject}</p>
                    ) : null}
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Message</label>
                    <Textarea
                      placeholder="Please describe your issue in detail..."
                      rows={5}
                      value={formData.message}
                      onChange={(e) => handleFieldChange('message', e.target.value)}
                    />
                    {formErrors.message ? (
                      <p className="text-sm text-destructive">{formErrors.message}</p>
                    ) : null}
                  </div>
                  <Button className="w-full" type="submit" disabled={isSending}>
                    {isSending ? 'Sending...' : 'Send Message'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            {/* Quick Contact */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Contact</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center space-x-3 p-3 rounded-lg bg-muted/50">
                  <Mail className="h-5 w-5 text-primary" />
                  <div>
                    <div className="font-medium">Email Support</div>
                    <div className="text-sm text-muted-foreground">codemaster.aitutor@gmail.com</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3 p-3 rounded-lg bg-muted/50">
                  <MessageCircle className="h-5 w-5 text-primary" />
                  <div>
                    <div className="font-medium">Live Chat</div>
                    <div className="text-sm text-muted-foreground">Available 24/7</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3 p-3 rounded-lg bg-muted/50">
                  <Phone className="h-5 w-5 text-primary" />
                  <div>
                    <div className="font-medium">Phone Support</div>
                    <div className="text-sm text-muted-foreground">+91 9860791587</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Resources */}
            <Card>
              <CardHeader>
                <CardTitle>Helpful Resources</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {resources.map((resource, index) => (
                  <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors cursor-pointer">
                    <div className="flex items-center space-x-3">
                      <resource.icon className="h-5 w-5 text-primary" />
                      <div>
                        <div className="font-medium">{resource.title}</div>
                        <div className="text-xs text-muted-foreground">{resource.description}</div>
                      </div>
                    </div>
                    <ExternalLink className="h-4 w-4 text-muted-foreground" />
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Status */}
            <Card>
              <CardHeader>
                <CardTitle>System Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <span>All Systems Operational</span>
                  <Badge variant="secondary" className="bg-green-100 text-green-800">
                    Online
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  );
};

export default Help;
