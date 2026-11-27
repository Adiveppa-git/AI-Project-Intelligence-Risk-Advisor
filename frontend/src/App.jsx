import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import OverviewDashboard from './pages/OverviewDashboard';
import DocumentUpload from './pages/DocumentUpload';
import RAGPipeline from './pages/RAGPipeline';
import ScopeAgentPage from './pages/ScopeAgentPage';
import RiskAgentPage from './pages/RiskAgentPage';
import BlockerAgentPage from './pages/BlockerAgentPage';
import MultiAgentPage from './pages/MultiAgentPage';
import MilestoneTracker from './pages/MilestoneTracker';
import ArchitectureOverview from './pages/ArchitectureOverview';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [sharedText, setSharedText] = useState('');
  
  // Independent Connection & Service States
  const [connectionStatus, setConnectionStatus] = useState('connecting'); // 'connecting' | 'online' | 'offline'
  const [healthStatus, setHealthStatus] = useState(null);
  const [ragStats, setRagStats] = useState(null);
  const [ragError, setRagError] = useState(null);
  const [agentStats, setAgentStats] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Unified global status fetcher:
  // - Evaluates GET /health independently to control FastAPI Online / Connecting / Offline
  // - Evaluates GET /api/rag/status independently so 503 during initialization does NOT mark FastAPI as offline
  // - Centralized polling avoids redundant, repeated calls across components
  const fetchGlobalStatus = useCallback(async (isManual = false) => {
    if (isManual) setIsRefreshing(true);

    // 1. Health check strictly determines FastAPI connection state
    try {
      const healthRes = await api.getHealth();
      if (healthRes && (healthRes.status === 'ok' || healthRes.status === 'ready' || typeof healthRes === 'object')) {
        setHealthStatus(healthRes);
        setConnectionStatus('online');
      } else {
        setHealthStatus(null);
        setConnectionStatus('offline');
      }
    } catch (err) {
      console.warn("FastAPI health check failed:", err.message);
      setHealthStatus(null);
      setConnectionStatus('offline');
    }

    // 2. RAG status check is decoupled from FastAPI connectivity
    try {
      const ragRes = await api.getRAGStatus();
      setRagStats(ragRes);
      setRagError(null);
    } catch (err) {
      // 503 when vector store is initializing or recovering
      setRagStats(null);
      setRagError(err.message || 'RAG status 503');
    }

    // 3. Agent status check
    try {
      const agentRes = await api.getAgentStatus();
      setAgentStats(agentRes);
    } catch {
      // Non-critical background status
    } finally {
      if (isManual) setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    // Initial fetch on application load
    fetchGlobalStatus();

    // Single periodic poll every 30 seconds to avoid unnecessary repeated requests
    const interval = setInterval(() => {
      fetchGlobalStatus(false);
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchGlobalStatus]);

  const handleNavigate = (tab, textToPass = null) => {
    if (textToPass) {
      setSharedText(textToPass);
    }
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleRunSampleAnalysis = (sample) => {
    setSharedText(sample.text);
    setActiveTab('orchestrator');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleAnalyzeText = (text) => {
    setSharedText(text);
    setActiveTab('orchestrator');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Explicit, authoritative page component mapping for all 9 views
  const renderActivePage = () => {
    switch (activeTab) {
      case 'orchestrator':
        return (
          <MultiAgentPage 
            preloadedText={sharedText} 
            onNavigate={handleNavigate} 
          />
        );
      case 'upload':
        return (
          <DocumentUpload 
            onNavigate={handleNavigate} 
            onAnalyzeText={handleAnalyzeText} 
            onIndexSuccess={() => fetchGlobalStatus(true)}
          />
        );
      case 'rag':
        return (
          <RAGPipeline 
            onIndexSuccess={() => fetchGlobalStatus(true)}
          />
        );
      case 'scope':
        return (
          <ScopeAgentPage 
            preloadedText={sharedText} 
          />
        );
      case 'risks':
        return (
          <RiskAgentPage 
            preloadedText={sharedText} 
          />
        );
      case 'blockers':
        return (
          <BlockerAgentPage 
            preloadedText={sharedText} 
          />
        );
      case 'milestones':
        return <MilestoneTracker />;
      case 'architecture':
        return <ArchitectureOverview />;
      case 'overview':
      default:
        return (
          <OverviewDashboard 
            onNavigate={handleNavigate} 
            onRunSampleAnalysis={handleRunSampleAnalysis}
            health={healthStatus}
            connectionStatus={connectionStatus}
            ragStatus={ragStats}
            ragError={ragError}
            agentStatus={agentStats}
            isRefreshing={isRefreshing}
            onRefresh={() => fetchGlobalStatus(true)}
          />
        );
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 font-sans antialiased text-slate-900 overflow-hidden">
      {/* Sidebar Navigation */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={handleNavigate}
        onSelectTab={handleNavigate}
        onNavigate={handleNavigate}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header with live FastAPI and independent ChromaDB status */}
        <Header 
          activeTab={activeTab} 
          connectionStatus={connectionStatus}
          systemStatus={healthStatus}
          ragStatus={ragStats}
          ragError={ragError}
          onNavigate={handleNavigate}
        />

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            {renderActivePage()}
          </div>
        </main>
      </div>
    </div>
  );
}
