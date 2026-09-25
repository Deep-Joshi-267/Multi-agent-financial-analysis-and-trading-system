import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import HomeTab from './components/HomeTab';
import AnalysisTab from './components/AnalysisTab';
import PastAnalysisTab from './components/PastAnalysisTab';
import InsightsTab from './components/InsightsTab';
import ReportModal from './components/ReportModal';

export default function App() {
  const [selectedReport, setSelectedReport] = useState(null);

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

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-dark)' }}>
      {/* NAVBAR */}
      <Navbar />

      {/* MAIN ROUTED CONTENT */}
      <main style={{ flex: 1 }}>
        <Routes>
          <Route 
            path="/" 
            element={
              <HomeTab 
                pastAnalyses={pastAnalyses} 
                onSelectReport={setSelectedReport} 
              />
            } 
          />
          <Route 
            path="/analysis" 
            element={
              <AnalysisTab 
                onAnalysisComplete={handleAnalysisComplete} 
              />
            } 
          />
          <Route 
            path="/past-analysis" 
            element={
              <PastAnalysisTab 
                pastAnalyses={pastAnalyses} 
                onClearHistory={handleClearHistory} 
                onSelectReport={setSelectedReport} 
              />
            } 
          />
          <Route 
            path="/insights" 
            element={<InsightsTab />} 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
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
