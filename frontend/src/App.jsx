import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import OverviewPage from './pages/OverviewPage';
import VideoAnalysisPage from './pages/VideoAnalysisPage';
import EventsPage from './pages/EventsPage';
import SystemStatusPage from './pages/SystemStatusPage';
import ChatPage from './pages/ChatPage';
import LiveSurveillancePage from './pages/LiveSurveillancePage';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Full-Width Landing Page */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/landing" element={<LandingPage />} />

        {/* Console / Surveillance App Routes (Wrapped in Layout Shell) */}
        <Route
          path="/overview"
          element={
            <Layout>
              <OverviewPage />
            </Layout>
          }
        />
        <Route path="/dashboard" element={<Navigate to="/overview" replace />} />
        <Route
          path="/live"
          element={
            <Layout>
              <LiveSurveillancePage />
            </Layout>
          }
        />
        <Route
          path="/analysis"
          element={
            <Layout>
              <VideoAnalysisPage />
            </Layout>
          }
        />
        <Route
          path="/events"
          element={
            <Layout>
              <EventsPage />
            </Layout>
          }
        />
        <Route
          path="/chat"
          element={
            <Layout>
              <ChatPage />
            </Layout>
          }
        />
        <Route
          path="/status"
          element={
            <Layout>
              <SystemStatusPage />
            </Layout>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
