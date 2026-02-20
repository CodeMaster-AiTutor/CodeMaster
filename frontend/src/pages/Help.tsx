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
      question: 'How do I submit my code solution?',
      answer: 'After writing your code in the editor, click the "Run" button to test it, then click "Submit" to submit your final solution. Make sure all test cases pass before submitting.'
    },
    {
      id: 2,
      question: 'What programming languages are supported?',
      answer: 'CodeMaster currently supports Java, Python, C++, JavaScript, and C. We are continuously adding support for more languages based on user feedback.'
    },
    {
      id: 3,
      question: 'How is my code evaluated?',
      answer: 'Your code is tested against multiple test cases including edge cases. The system checks for correctness, efficiency, and handles both visible and hidden test cases.'
    },
    {
      id: 4,
      question: 'Can I save my progress?',
      answer: 'Yes! Your progress is automatically saved. You can access your saved solutions, practice history, and achievements from your profile page.'
    },
    {
      id: 5,
      question: 'How do I upgrade to Pro?',
      answer: 'Click the "Upgrade to Pro" button in the sidebar or go to Settings > Billing. Pro gives you unlimited challenges, priority support, and advanced AI features.'
    },
    {
      id: 6,
      question: 'What if I encounter a bug?',
      answer: 'Please report bugs using the contact form below or email us at support@CodeMaster.com. Include as much detail as possible about the issue you encountered.'
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
              <CardContent className="space-y-2">
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
