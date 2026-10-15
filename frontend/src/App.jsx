import React, { useState } from 'react';
import { useLocation, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import HomeTab from './components/HomeTab';
import AnalysisTab from './components/AnalysisTab';
import PastAnalysisTab from './components/PastAnalysisTab';
import InsightsTab from './components/InsightsTab';
import ReportModal from './components/ReportModal';

export default function App() {
  const [selectedReport, setSelectedReport] = useState(null);
  const [runningState, setRunningState] = useState({ isRunning: false, ticker: '' });
  const location = useLocation();

  // Lazy initial state for pastAnalyses from localStorage
  const [pastAnalyses, setPastAnalyses] = useState(() => {
    try {
      const saved = localStorage.getItem('trading_agents_past_analyses');
      return saved ? JSON.parse(saved) : [];
    } catch (e) {
      console.error('Failed to load past analyses:', e);
      return [];
    }
  });

  const handleAnalysisComplete = (newRecord) => {
    setPastAnalyses((prev) => {
      const updated = [newRecord, ...prev];
      try {
        localStorage.setItem('trading_agents_past_analyses', JSON.stringify(updated.slice(0, 50)));
      } catch (e) {
        console.error('Failed to save analysis:', e);
      }
      return updated;
    });
  };

  const handleClearHistory = () => {
    setPastAnalyses([]);
    try {
      localStorage.removeItem('trading_agents_past_analyses');
    } catch (e) {
      console.error('Failed to clear localStorage:', e);
    }
  };

  const path = location.pathname;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-dark)' }}>
      {/* NAVBAR */}
      <Navbar runningState={runningState} />

      {/* MAIN CONTENT WITH PERSISTENT ANALYSIS TAB */}
      <main style={{ flex: 1 }}>
        <div style={{ display: (path === '/' || path === '') ? 'block' : 'none' }}>
          <HomeTab 
            pastAnalyses={pastAnalyses} 
            onSelectReport={setSelectedReport} 
          />
        </div>

        <div style={{ display: path === '/analysis' ? 'block' : 'none' }}>
          <AnalysisTab 
            onAnalysisComplete={handleAnalysisComplete} 
            onRunningStateChange={setRunningState}
          />
        </div>

        <div style={{ display: path === '/past-analysis' ? 'block' : 'none' }}>
          <PastAnalysisTab 
            pastAnalyses={pastAnalyses} 
            onClearHistory={handleClearHistory} 
            onSelectReport={setSelectedReport} 
          />
        </div>

        <div style={{ display: path === '/insights' ? 'block' : 'none' }}>
          <InsightsTab />
        </div>

        {!['/', '', '/analysis', '/past-analysis', '/insights'].includes(path) && (
          <Navigate to="/" replace />
        )}
      </main>

      {/* FOOTER */}
      <Footer />

      {/* REPORT MODAL */}
      {selectedReport && (
        <ReportModal 
          report={selectedReport} 
          onClose={() => setSelectedReport(null)} 
        />
      )}
    </div>
  );
}
