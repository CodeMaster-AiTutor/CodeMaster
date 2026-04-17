import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import Landing from "./pages/Landing";
import Login from "./pages/Auth/Login";
import ForgotPassword from "./pages/Auth/ForgotPassword";
import Signup from "./pages/Auth/Signup";
import VerifyEmail from "./pages/Auth/VerifyEmail";
import VerifyPending from "./pages/Auth/VerifyPending";
import GoogleCallback from "./pages/Auth/GoogleCallback";
import GithubCallback from "./pages/Auth/GithubCallback";
import SocialOnboarding from "./pages/Auth/SocialOnboarding";
import Dashboard from "./pages/Dashboard/Dashboard";
import Compiler from "./pages/Compiler";
import Explainer from "./pages/Explainer";
import Generator from "./pages/Generator";
import Practice from "./pages/Practice";
import PracticeSolve from "./pages/PracticeSolve";
import TheoryCourse from "./pages/TheoryCourse";
import Profile from "./pages/Profile";
import Settings from "./pages/Settings";
import Assessment from "./pages/Assessment";
import Analytics from "./pages/Analytics";
import HelpSupport from "./pages/Help";
import Pricing from "./pages/Pricing";
import About from "./pages/About";
import Terms from "./pages/Terms";
import Privacy from "./pages/Privacy";
import Upgrade from "./pages/Upgrade";
import NotFound from "./pages/NotFound";
import LearningPathTutorial from "./pages/LearningPathTutorial";

const queryClient = new QueryClient();

const App = () => {
  console.log('CodeMaster App is loading...');
  return (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/verify-pending" element={<VerifyPending />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/auth/google/callback" element={<GoogleCallback />} />
          <Route path="/auth/github/callback" element={<GithubCallback />} />
          <Route path="/auth/social-onboarding" element={<SocialOnboarding />} />
          <Route path="/terms" element={<Terms />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/compiler" element={<Compiler />} />
          <Route path="/explainer" element={<Explainer />} />
          <Route path="/generator" element={<Generator />} />
          <Route path="/practice" element={<Practice />} />
          <Route path="/practice/solve/:level/:title" element={<PracticeSolve />} />
          <Route path="/theory-course" element={<TheoryCourse />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/assessment" element={<Assessment />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/help" element={<HelpSupport />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/about" element={<About />} />
          <Route path="/upgrade" element={<Upgrade />} />
          <Route path="/learning-path/java/:conceptId" element={<LearningPathTutorial />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  </QueryClientProvider>
  );
};

export default App;
