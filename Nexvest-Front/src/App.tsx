import { useState, useCallback } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import SplashScreen from "./components/SplashScreen";
import Dashboard from "./pages/Dashboard";
import AssetExplorer from "./pages/AssetExplorer";
import SimilarityAnalysis from "./pages/SimilarityAnalysis";
import CorrelationHeatmap from "./pages/CorrelationHeatmap";
import PatternDetection from "./pages/PatternDetection";
import RiskDashboard from "./pages/RiskDashboard";
import SettingsPage from "./pages/Settings";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => {
  const [showSplash, setShowSplash] = useState(true);
  const handleSplashComplete = useCallback(() => setShowSplash(false), []);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        {showSplash && <SplashScreen onComplete={handleSplashComplete} />}
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/asset-explorer" element={<AssetExplorer />} />
              <Route path="/similarity" element={<SimilarityAnalysis />} />
              <Route path="/correlation" element={<CorrelationHeatmap />} />
              <Route path="/patterns" element={<PatternDetection />} />
              <Route path="/risk" element={<RiskDashboard />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
