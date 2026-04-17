import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const Terms = () => {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        <Link to="/signup" className="inline-flex items-center text-muted-foreground hover:text-foreground">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Link>
        <h1 className="text-3xl font-bold">Terms of Service</h1>
        <p className="text-muted-foreground">Effective date: April 12, 2026</p>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">1. Service Scope</h2>
          <p>CodeMaster provides coding practice, AI-assisted explanation and generation, Java compilation, assessments, analytics, and learning path features for educational use.</p>
          <p>You agree to use the platform only for lawful learning, interview preparation, and software skill improvement activities.</p>
        </section>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">2. Account Responsibilities</h2>
          <p>You must register with a valid email address and keep your credentials secure.</p>
          <p>You are responsible for activity performed through your account, including generated content and submitted code.</p>
        </section>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">3. Acceptable Use</h2>
          <p>You must not attempt to abuse compiler execution, API rate, authentication, or platform infrastructure.</p>
          <p>You must not upload malware, run harmful payloads, scrape user data, or attempt unauthorized access to any account or system component.</p>
        </section>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">4. AI and Compiler Output</h2>
          <p>AI suggestions and generated code are provided for assistance and may contain mistakes.</p>
          <p>You are responsible for reviewing, testing, and securing code before production use.</p>
        </section>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">5. Points, Streaks, and Progress</h2>
          <p>Skill points, streaks, and activity logs are platform metrics for learning engagement and can be adjusted if fraud or abuse is detected.</p>
        </section>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">6. Account Suspension and Deletion</h2>
          <p>We may suspend or remove accounts involved in abuse, impersonation, repeated policy violations, or malicious activity.</p>
        </section>
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">7. Limitation of Liability</h2>
          <p>CodeMaster is provided on an as-available basis. We do not guarantee uninterrupted access, perfect output, or suitability for any specific professional decision.</p>
        </section>
      </div>
    </div>
  );
};

export default Terms;
