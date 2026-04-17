import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const Privacy = () => {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        <Link to="/signup" className="inline-flex items-center text-muted-foreground hover:text-foreground">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Link>
        <h1 className="text-3xl font-bold">Privacy Policy</h1>
        <p className="text-muted-foreground">Effective date: April 12, 2026</p>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">1. Information We Collect</h2>
          <p>We collect account data such as email, username, encrypted password hash, and optional profile fields.</p>
          <p>We also collect learning activity data including practice submissions, assessments, points, streaks, and time-spent analytics.</p>
        </section>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">2. How We Use Data</h2>
          <p>We use your data to authenticate access, deliver coding features, track progress, personalize content, and improve reliability.</p>
          <p>Verification emails and support emails are used for account security and communication.</p>
        </section>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">3. AI and Code Content</h2>
          <p>Prompts, code input, compiler output, and explanation/generation requests may be processed to provide platform functionality and maintain service quality.</p>
        </section>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">4. Data Sharing</h2>
          <p>We do not sell personal information. Data is shared only with service components required for functionality, such as database, email transport, and authentication integrations.</p>
        </section>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">5. Security and Retention</h2>
          <p>Passwords are stored as hashes. Account verification tokens are time-limited. We retain data as needed for account operation, security review, and legal compliance.</p>
        </section>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">6. Your Controls</h2>
          <p>You can update profile fields, request account deletion, and contact support for privacy-related requests.</p>
        </section>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">7. Contact</h2>
          <p>For support or privacy concerns, use the Help & Support page in CodeMaster.</p>
        </section>
      </div>
    </div>
  );
};

export default Privacy;
