import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import Landing from "./pages/Landing";
import Login from "./pages/Auth/Login";
import Signup from "./pages/Auth/Signup";
import GoogleCallback from "./pages/Auth/GoogleCallback";
import Dashboard from "./pages/Dashboard/Dashboard";
import Compiler from "./pages/Compiler";
import Explainer from "./pages/Explainer";
import Generator from "./pages/Generator";
import Practice from "./pages/Practice";
import Profile from "./pages/Profile";
import Settings from "./pages/Settings";
import Assessment from "./pages/Assessment";
import Analytics from "./pages/Analytics";
import HelpSupport from "./pages/Help";
import Pricing from "./pages/Pricing";
import About from "./pages/About";
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
          <Route path="/signup" element={<Signup />} />
          <Route path="/auth/google/callback" element={<GoogleCallback />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/compiler" element={<Compiler />} />
          <Route path="/explainer" element={<Explainer />} />
          <Route path="/generator" element={<Generator />} />
          <Route path="/practice" element={<Practice />} />
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
