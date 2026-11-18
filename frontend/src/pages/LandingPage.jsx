import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Radio,
  Cctv,
  ShieldAlert,
  MessageSquare,
  ArrowRight,
  CheckCircle2,
  Lock,
  Cpu,
  Database,
  Layers,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';

export const LandingPage = () => {
  const { isAuthenticated, user } = useAuth();
  const [systemOnline, setSystemOnline] = useState(true);
  const [device, setDevice] = useState('cuda');

  useEffect(() => {
    let isMounted = true;
    api.getHealth()
      .then((data) => {
        if (isMounted) {
          setSystemOnline(true);
          setDevice(data.model?.device || 'cpu');
        }
      })
      .catch(() => {
        if (isMounted) setSystemOnline(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const scrollToSection = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const activityClasses = [
    { name: 'Fighting', color: 'border-rose-500/40 text-rose-400 bg-rose-500/10' },
    { name: 'Robbery', color: 'border-amber-500/40 text-amber-400 bg-amber-500/10' },
    { name: 'Shooting', color: 'border-red-500/40 text-red-400 bg-red-500/10' },
    { name: 'Explosion', color: 'border-orange-500/40 text-orange-400 bg-orange-500/10' },
    { name: 'Stealing', color: 'border-yellow-500/40 text-yellow-400 bg-yellow-500/10' },
    { name: 'Abuse', color: 'border-purple-500/40 text-purple-400 bg-purple-500/10' },
    { name: 'Normal Activity', color: 'border-emerald-500/40 text-emerald-400 bg-emerald-500/10' },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-200 selection:bg-blue-600 selection:text-white">
      {/* ------------------------------------------------------------- */}
      {/* 1. Navigation Header                                          */}
      {/* ------------------------------------------------------------- */}
      <header className="sticky top-0 z-50 bg-[#0B0F17]/85 backdrop-blur-md border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="p-2 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400 group-hover:scale-105 transition-transform">
              <Radio className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-base tracking-tight text-white">VisionIQ</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-semibold border border-blue-500/30">
                  PRO
                </span>
              </div>
              <div className="text-[10px] text-slate-400 -mt-0.5">AI Surveillance System</div>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
            <button
              onClick={() => scrollToSection('home')}
              className="hover:text-blue-400 transition-colors cursor-pointer"
            >
              Home
            </button>
            <button
              onClick={() => scrollToSection('features')}
              className="hover:text-blue-400 transition-colors cursor-pointer"
            >
              Features
            </button>
            <button
              onClick={() => scrollToSection('how-it-works')}
              className="hover:text-blue-400 transition-colors cursor-pointer"
            >
              How It Works
            </button>
            <button
              onClick={() => scrollToSection('about')}
              className="hover:text-blue-400 transition-colors cursor-pointer"
            >
              About
            </button>
          </nav>

          {/* Action CTAs */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <Link
                to="/overview"
                className="py-2 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/25 transition-all flex items-center gap-1.5"
              >
                <span>Dashboard ({user?.name?.split(' ')[0] || 'Console'})</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="py-2 px-3.5 rounded-xl text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="py-2 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/25 transition-all flex items-center gap-1.5"
                >
                  <span>Sign Up</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ------------------------------------------------------------- */}
      {/* 2. Hero Section                                               */}
      {/* ------------------------------------------------------------- */}
      <section id="home" className="relative pt-12 pb-20 md:pt-20 md:pb-32 overflow-hidden">
        {/* Cyber Glow Accents */}
        <div className="absolute top-10 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-blue-600/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-1/3 right-10 w-[400px] h-[300px] bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-3xl mx-auto">
            {/* Live Engine Telemetry Pill */}
            <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-[#0F172A] border border-blue-500/30 text-xs text-slate-300 shadow-md shadow-blue-900/20 mb-6">
              <span className="relative flex h-2 w-2">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${systemOnline ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                <span className={`relative inline-flex rounded-full h-2 w-2 ${systemOnline ? 'bg-emerald-500' : 'bg-amber-500'}`} />
              </span>
              <span className="font-mono text-[11px] text-blue-400 font-semibold tracking-wide uppercase">
                R(2+1)D-18 Temporal Core
              </span>
              <span className="text-slate-600">•</span>
              <span className="text-slate-400 text-[11px]">
                {systemOnline ? `Operational on ${device.toUpperCase()}` : 'System Standby'}
              </span>
            </div>

            {/* Main Hero Heading */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-tight">
              Intelligent Surveillance. <br />
              <span className="bg-gradient-to-r from-blue-400 via-cyan-400 to-sky-300 bg-clip-text text-transparent">
                Smarter Security.
              </span>
            </h1>

            {/* Subheading */}
            <p className="mt-6 text-base sm:text-lg text-slate-400 leading-relaxed max-w-2xl mx-auto">
              Transform standard CCTV cameras and video feeds into proactive anomaly detectors.
              VisionIQ couples spatiotemporal deep learning, instant forensic snapshotting, and grounded natural-language security querying in an isolated, multi-user architecture.
            </p>

            {/* CTAs */}
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to={isAuthenticated ? '/overview' : '/register'}
                className="w-full sm:w-auto py-3.5 px-7 rounded-xl bg-gradient-to-r from-blue-600 via-blue-500 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-semibold text-sm shadow-xl shadow-blue-600/30 transition-all flex items-center justify-center gap-2 group"
              >
                <span>{isAuthenticated ? 'Open Surveillance Dashboard' : 'Get Started Free'}</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
              <button
                onClick={() => scrollToSection('features')}
                className="w-full sm:w-auto py-3.5 px-6 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 text-slate-300 hover:text-white font-medium text-sm transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>Explore Capabilities</span>
                <ChevronRight className="w-4 h-4 text-slate-500" />
              </button>
            </div>
          </div>

          {/* Hero Visual Mockup: Simulated CCTV Feed Console */}
          <div className="mt-14 max-w-5xl mx-auto">
            <div className="relative rounded-2xl bg-[#0F172A] border border-slate-800 shadow-2xl p-2 sm:p-4 backdrop-blur-xl">
              {/* Window Controls Bar */}
              <div className="flex items-center justify-between pb-3 px-3 border-b border-slate-800/80 text-xs text-slate-400">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-rose-500/80" />
                  <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                  <span className="ml-2 font-mono text-[11px] text-slate-500">
                    FEED://CAM-NORTH-01 [1080p @ 30FPS]
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1.5 font-mono text-[10px] text-emerald-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    LIVE INFERENCE ACTIVE
                  </span>
                </div>
              </div>

              {/* Simulated Camera Video View */}
              <div className="relative aspect-video w-full rounded-xl bg-slate-950 overflow-hidden border border-slate-800/60 mt-3 flex items-center justify-center">
                {/* Surveillance Grid Overlay */}
                <div
                  className="absolute inset-0 opacity-15 pointer-events-none"
                  style={{
                    backgroundImage:
                      'linear-gradient(to right, #38bdf8 1px, transparent 1px), linear-gradient(to bottom, #38bdf8 1px, transparent 1px)',
                    backgroundSize: '40px 40px',
                  }}
                />

                {/* Radar Targeting Reticle (Simulated CCTV Detection Bounding) */}
                <div className="absolute inset-10 border border-cyan-500/20 rounded-lg pointer-events-none flex flex-col justify-between p-3">
                  <div className="flex justify-between items-start">
                    <span className="font-mono text-[10px] text-cyan-400/80 bg-slate-900/80 px-2 py-0.5 rounded border border-cyan-500/30">
                      ZONE: SECTOR 4A • SUSPICIOUS MOTION
                    </span>
                    <span className="font-mono text-[10px] text-slate-400 bg-slate-900/80 px-2 py-0.5 rounded">
                      REC 00:03:42:19
                    </span>
                  </div>

                  {/* Bounding Box Simulation */}
                  <div className="self-center w-64 h-40 border-2 border-dashed border-rose-500/80 bg-rose-500/10 rounded-lg p-2.5 flex flex-col justify-between relative animate-pulse">
                    <div className="flex items-center justify-between text-[11px] font-bold text-rose-300">
                      <span className="flex items-center gap-1 bg-rose-950/90 px-1.5 py-0.5 rounded border border-rose-500/50">
                        <ShieldAlert className="w-3 h-3 text-rose-400" /> FIGHTING
                      </span>
                      <span className="font-mono bg-black/60 px-1.5 py-0.5 rounded text-white">
                        94.2% CONF
                      </span>
                    </div>
                    <div className="text-[10px] font-mono text-rose-300/80 self-end">
                      EVIDENCE SNAPSHOT SAVED
                    </div>
                  </div>

                  <div className="flex justify-between items-end text-[11px] font-mono text-slate-400">
                    <span>MODEL: R(2+1)D-18 • 16-FRAME WINDOW</span>
                    <span>TENANT ISOLATED: SHA-256 USER CONTEXT</span>
                  </div>
                </div>
              </div>

              {/* Supported Activity Badges Strip */}
              <div className="pt-3 px-2 flex items-center justify-between flex-wrap gap-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Target Activity Classes:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {activityClasses.map((ac) => (
                    <span
                      key={ac.name}
                      className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${ac.color}`}
                    >
                      {ac.name}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 3. Features Section (Only Implemented Capabilities)           */}
      {/* ------------------------------------------------------------- */}
      <section id="features" className="py-20 bg-[#0F172A]/50 border-t border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-xs font-bold text-cyan-400 uppercase tracking-widest">
              Core Architecture
            </h2>
            <p className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Engineered for Real-World CCTV Defense
            </p>
            <p className="mt-3 text-sm text-slate-400">
              Every feature below is actively implemented, backed by genuine neural models, MongoDB persistence, and verified cryptographic ownership.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="bg-[#0F172A] border border-slate-800 rounded-2xl p-6 hover:border-blue-500/40 transition-all group">
              <div className="p-3 rounded-xl bg-blue-600/15 border border-blue-500/30 text-blue-400 w-fit mb-4 group-hover:scale-105 transition-transform">
                <Cpu className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white mb-2">
                3D Spatiotemporal Action Recognition
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Powered by a customized R(2+1)D-18 convolutional neural network factorizing 3D convolutions into spatial 2D and temporal 1D kernels for rapid sliding-window anomaly classification.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-[#0F172A] border border-slate-800 rounded-2xl p-6 hover:border-cyan-500/40 transition-all group">
              <div className="p-3 rounded-xl bg-cyan-600/15 border border-cyan-500/30 text-cyan-400 w-fit mb-4 group-hover:scale-105 transition-transform">
                <Cctv className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white mb-2">
                Live CCTV Stream Ingestion
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Seamlessly connects to RTSP surveillance endpoints, hardware webcams, and synthetic test streams. Employs background threads and WebSockets for zero-delay security alerts.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-[#0F172A] border border-slate-800 rounded-2xl p-6 hover:border-blue-500/40 transition-all group">
              <div className="p-3 rounded-xl bg-blue-600/15 border border-blue-500/30 text-blue-400 w-fit mb-4 group-hover:scale-105 transition-transform">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white mb-2">
                Temporal Localization & Evidence
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Detects start/end timestamps down to the second. Automatically extracts high-resolution forensic snapshot frames at peak confidence, cataloged safely on disk for incident reports.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="bg-[#0F172A] border border-slate-800 rounded-2xl p-6 hover:border-cyan-500/40 transition-all group">
              <div className="p-3 rounded-xl bg-cyan-600/15 border border-cyan-500/30 text-cyan-400 w-fit mb-4 group-hover:scale-105 transition-transform">
                <MessageSquare className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white mb-2">
                Conversational AI Assistant (RAG)
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Ask questions about your camera feeds in plain English. Natural language parsing interprets wall-clock hours, relative offsets, and activity types, returning grounded evidence links.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="bg-[#0F172A] border border-slate-800 rounded-2xl p-6 hover:border-emerald-500/40 transition-all group">
              <div className="p-3 rounded-xl bg-emerald-600/15 border border-emerald-500/30 text-emerald-400 w-fit mb-4 group-hover:scale-105 transition-transform">
                <Lock className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white mb-2">
                Strict Multi-Tenant Privacy & IDOR Protection
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Every video, detection event, evidence image, live stream, and AI chat query is strictly scoped to the verified JWT session. Zero cross-user data leakage and no IDOR vulnerabilities.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="bg-[#0F172A] border border-slate-800 rounded-2xl p-6 hover:border-blue-500/40 transition-all group">
              <div className="p-3 rounded-xl bg-blue-600/15 border border-blue-500/30 text-blue-400 w-fit mb-4 group-hover:scale-105 transition-transform">
                <Database className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white mb-2">
                MongoDB Primary + SQLite Dual-Sync
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                High-scale MongoDB document storage with indexed query execution, paired with an automated SQLite relational fallback ensuring resilient offline persistence and uptime.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 4. How It Works Section                                       */}
      {/* ------------------------------------------------------------- */}
      <section id="how-it-works" className="py-20 border-t border-slate-800/80 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-xs font-bold text-blue-400 uppercase tracking-widest">
              Automated Pipeline
            </h2>
            <p className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
              From Raw Ingestion to Instant Threat Insight
            </p>
            <p className="mt-3 text-sm text-slate-400">
              The four-stage automated lifecycle executed for every uploaded video or live surveillance stream.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 relative">
            {/* Step 1 */}
            <div className="flex flex-col items-center text-center p-6 bg-[#0F172A]/80 border border-slate-800 rounded-2xl relative">
              <div className="w-10 h-10 rounded-full bg-blue-600/20 border border-blue-500/40 text-blue-400 font-bold flex items-center justify-center text-sm mb-4">
                1
              </div>
              <h3 className="text-sm font-bold text-white mb-2">Stream / Video Ingest</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Upload MP4/AVI videos or configure live RTSP camera feeds. OpenCV extracts metadata, FPS, and frame sequences.
              </p>
            </div>

            {/* Step 2 */}
            <div className="flex flex-col items-center text-center p-6 bg-[#0F172A]/80 border border-slate-800 rounded-2xl relative">
              <div className="w-10 h-10 rounded-full bg-cyan-600/20 border border-cyan-500/40 text-cyan-400 font-bold flex items-center justify-center text-sm mb-4">
                2
              </div>
              <h3 className="text-sm font-bold text-white mb-2">3D Temporal Inference</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Sliding temporal windows feed normalized clip tensors to the R(2+1)D-18 neural model on GPU/CPU for classification.
              </p>
            </div>

            {/* Step 3 */}
            <div className="flex flex-col items-center text-center p-6 bg-[#0F172A]/80 border border-slate-800 rounded-2xl relative">
              <div className="w-10 h-10 rounded-full bg-blue-600/20 border border-blue-500/40 text-blue-400 font-bold flex items-center justify-center text-sm mb-4">
                3
              </div>
              <h3 className="text-sm font-bold text-white mb-2">Evidence Capture & Save</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Consecutive windows are merged into discreet events. Peak-confidence evidence snapshots are saved with owner tags.
              </p>
            </div>

            {/* Step 4 */}
            <div className="flex flex-col items-center text-center p-6 bg-[#0F172A]/80 border border-slate-800 rounded-2xl relative">
              <div className="w-10 h-10 rounded-full bg-emerald-600/20 border border-emerald-500/40 text-emerald-400 font-bold flex items-center justify-center text-sm mb-4">
                4
              </div>
              <h3 className="text-sm font-bold text-white mb-2">Query, Alert & Audit</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Inspect events on the interactive timeline, query with the AI Assistant, or receive live WebSocket notifications.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 5. About Section                                              */}
      {/* ------------------------------------------------------------- */}
      <section id="about" className="py-20 bg-[#0F172A]/40 border-t border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-2">
                About VisionIQ
              </h2>
              <h3 className="text-3xl font-bold text-white tracking-tight sm:text-4xl">
                Built to Eliminate Manual CCTV Fatigue
              </h3>
              <p className="mt-4 text-sm text-slate-400 leading-relaxed">
                Traditional video surveillance systems record thousands of hours of passive footage that are only inspected after an incident has occurred. VisionIQ shifts the paradigm toward autonomous, proactive security.
              </p>
              <p className="mt-3 text-sm text-slate-400 leading-relaxed">
                By integrating specialized action recognition networks with strict multi-user privacy, VisionIQ enables security teams, facility managers, and enterprise administrators to manage their own isolated feeds with complete confidence that no unauthorized parties can inspect their data.
              </p>

              <div className="mt-6 space-y-3">
                <div className="flex items-center gap-3 text-xs text-slate-300">
                  <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />
                  <span>Custom R(2+1)D-18 model trained on DCSASS spatiotemporal benchmark</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-300">
                  <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />
                  <span>Enterprise multi-tenant privacy: video files and evidence tagged to user ID</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-300">
                  <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />
                  <span>MongoDB primary document store with dual-sync SQLite engine</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-300">
                  <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />
                  <span>Real-time WebSocket alerting broker for multi-camera feeds</span>
                </div>
              </div>
            </div>

            {/* Architecture Stack Card */}
            <div className="bg-[#111827] border border-slate-800 rounded-2xl p-6 shadow-xl">
              <h4 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-400" />
                Technology Stack Overview
              </h4>

              <div className="space-y-3">
                <div className="p-3 bg-[#0B0F17] rounded-xl border border-slate-800/80 flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-300">Neural Network Architecture</span>
                  <span className="text-xs font-mono text-blue-400">PyTorch R(2+1)D-18</span>
                </div>
                <div className="p-3 bg-[#0B0F17] rounded-xl border border-slate-800/80 flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-300">API Backend Framework</span>
                  <span className="text-xs font-mono text-cyan-400">FastAPI & Uvicorn (ASGI)</span>
                </div>
                <div className="p-3 bg-[#0B0F17] rounded-xl border border-slate-800/80 flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-300">Primary Database</span>
                  <span className="text-xs font-mono text-emerald-400">MongoDB v6.0+ (PyMongo)</span>
                </div>
                <div className="p-3 bg-[#0B0F17] rounded-xl border border-slate-800/80 flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-300">Fallback Persistence</span>
                  <span className="text-xs font-mono text-amber-400">SQLite + SQLAlchemy Dual-Sync</span>
                </div>
                <div className="p-3 bg-[#0B0F17] rounded-xl border border-slate-800/80 flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-300">Frontend Application</span>
                  <span className="text-xs font-mono text-sky-400">React 19 + Tailwind CSS + Vite</span>
                </div>
                <div className="p-3 bg-[#0B0F17] rounded-xl border border-slate-800/80 flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-300">Authentication & Security</span>
                  <span className="text-xs font-mono text-purple-400">Bcrypt + JWT (Bearer & HttpOnly)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 6. CTA Banner Section                                         */}
      {/* ------------------------------------------------------------- */}
      <section className="py-16 border-t border-slate-800/80 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/20 via-cyan-900/10 to-blue-900/20 pointer-events-none" />
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Ready to secure your premises with autonomous AI?
          </h2>
          <p className="mt-3 text-xs sm:text-sm text-slate-400 max-w-xl mx-auto">
            Create an account now to start analyzing videos, streaming RTSP cameras, and querying incident history in your own secure tenant.
          </p>
          <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to={isAuthenticated ? '/overview' : '/register'}
              className="py-3 px-6 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-semibold text-xs shadow-lg shadow-blue-600/30 transition-all flex items-center gap-2"
            >
              <span>{isAuthenticated ? 'Enter Dashboard Console' : 'Register New Account'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 7. Footer                                                     */}
      {/* ------------------------------------------------------------- */}
      <footer className="bg-[#0B0F17] border-t border-slate-800/80 py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400">
              <Radio className="w-4 h-4 animate-pulse" />
            </div>
            <div>
              <div className="font-bold text-sm text-white flex items-center gap-1.5">
                <span>VisionIQ</span>
                <span className="text-[9px] px-1.5 py-0.2 rounded bg-blue-500/20 text-blue-400 font-semibold border border-blue-500/30">
                  ENTERPRISE
                </span>
              </div>
              <p className="text-[11px] text-slate-500">Autonomous AI Surveillance & Forensics</p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs text-slate-400">
            <button onClick={() => scrollToSection('home')} className="hover:text-white transition-colors cursor-pointer">
              Home
            </button>
            <button onClick={() => scrollToSection('features')} className="hover:text-white transition-colors cursor-pointer">
              Features
            </button>
            <button onClick={() => scrollToSection('how-it-works')} className="hover:text-white transition-colors cursor-pointer">
              How It Works
            </button>
            <button onClick={() => scrollToSection('about')} className="hover:text-white transition-colors cursor-pointer">
              About
            </button>
            <a
              href="http://127.0.0.1:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              API Docs <ExternalLink className="w-2.5 h-2.5" />
            </a>
          </div>

          <div className="text-[11px] text-slate-500 text-center md:text-right">
            &copy; 2026 VisionIQ Security Systems. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
