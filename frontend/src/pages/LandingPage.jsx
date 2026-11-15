import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Radio,
  ShieldAlert,
  Video,
  Cctv,
  Cpu,
  Database,
  ArrowRight,
  CheckCircle2,
  Zap,
  Activity,
  MessageSquare,
  Eye,
  Sliders,
  Layers,
  Sparkles,
  Play,
  Lock,
  Clock,
  ChevronRight,
  BarChart3,
  ExternalLink,
} from 'lucide-react';
import { api } from '../api/client';
import { ActivityBadge } from '../components/StatusBadge';

export const LandingPage = () => {
  const [systemHealth, setSystemHealth] = useState({
    status: 'checking',
    device: 'gpu',
    model: 'r2plus1d_18',
    classesCount: 7,
  });

  const [activeTab, setActiveTab] = useState('Fighting');

  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      try {
        const data = await api.getHealth();
        if (isMounted) {
          setSystemHealth({
            status: 'online',
            device: data.model?.device || 'cuda',
            model: data.model?.name || 'r2plus1d_18',
            classesCount: data.model?.classes?.length || 7,
          });
        }
      } catch {
        if (isMounted) {
          setSystemHealth({
            status: 'offline',
            device: 'cpu',
            model: 'r2plus1d_18',
            classesCount: 7,
          });
        }
      }
    };

    checkHealth();
  }, []);

  const anomalyCategories = [
    {
      id: 'Fighting',
      name: 'Fighting',
      recall: '98.4%',
      precision: '88.5%',
      f1: '93.2%',
      color: 'rose',
      description: 'Violent physical altercations, brawls, and aggressive confrontations detected with near-zero missed incidents.',
      characteristics: 'Rapid body movement, clustered trajectories, high spatiotemporal kinetic velocity.',
    },
    {
      id: 'RoadAccidents',
      name: 'Road Accidents',
      recall: '71.4%',
      precision: '64.3%',
      f1: '67.7%',
      color: 'cyan',
      description: 'Vehicle collisions, pedestrian impacts, and sudden traffic obstruction events on roadways.',
      characteristics: 'High-speed object trajectory changes, sudden deceleration, scattered visual debris.',
    },
    {
      id: 'Robbery',
      name: 'Robbery',
      recall: '69.2%',
      precision: '59.0%',
      f1: '63.7%',
      color: 'amber',
      description: 'Active armed confrontation, register threats, and forceful theft at stores or commercial premises.',
      characteristics: 'Pointed weapon postures, abrupt customer immobilization, rapid register reaching.',
    },
    {
      id: 'Shoplifting',
      name: 'Shoplifting',
      recall: '56.4%',
      precision: '62.0%',
      f1: '59.0%',
      color: 'purple',
      description: 'Concealment of store merchandise into pockets, bags, or jackets without payment.',
      characteristics: 'Repeated head-turning, lingering by merchandise aisles, swift pocketing gestures.',
    },
    {
      id: 'Burglary',
      name: 'Burglary',
      recall: '25.0%',
      precision: '55.1%',
      f1: '34.4%',
      color: 'orange',
      description: 'Forced entry through windows, doors, or perimeter gates during off-hours.',
      characteristics: 'Low-light stealth motion, door lock manipulation, repetitive prying mechanics.',
    },
    {
      id: 'Vandalism',
      name: 'Vandalism',
      recall: '23.5%',
      precision: '64.0%',
      f1: '34.4%',
      color: 'fuchsia',
      description: 'Deliberate property destruction, wall graffiti tagging, and facility defacement.',
      characteristics: 'Stationary posturing against walls, repetitive spray gestures, surface striking.',
    },
    {
      id: 'Normal',
      name: 'Normal Activity',
      recall: '61.0%',
      precision: '52.1%',
      f1: '56.2%',
      color: 'emerald',
      description: 'Regular pedestrian walking, standard customer browsing, and authorized workplace movement.',
      characteristics: 'Smooth non-anomalous optical flow, standard velocity, steady motion vectors.',
    },
  ];

  const currentCategory = anomalyCategories.find((c) => c.id === activeTab) || anomalyCategories[0];

  const features = [
    {
      icon: Cpu,
      title: 'Spatiotemporal R(2+1)D-18 Backbone',
      description: 'Decomposed 3D convolutions (1x3x3 spatial + 3x1x1 temporal) fine-tuned on surveillance anomalies for high motion discrimination.',
      badge: 'Deep Learning',
    },
    {
      icon: Cctv,
      title: 'Live CCTV RTSP Streaming',
      description: 'Multi-camera stream ingestion supporting IP RTSP cameras, USB webcams, and synthetic surveillance video streams with zero frame lag.',
      badge: 'Real-Time',
    },
    {
      icon: ShieldAlert,
      title: 'Automated Evidence Capture',
      description: 'Instant extraction and storage of peak-confidence anomaly frames with timestamped video bookmarks for rapid security dispatch.',
      badge: 'Evidence Safe',
    },
    {
      icon: MessageSquare,
      title: 'AI Surveillance Assistant',
      description: 'Natural language semantic search powered by LLM intelligence. Ask questions about past events, suspect timing, and anomaly patterns.',
      badge: 'Conversational',
    },
    {
      icon: Database,
      title: 'Dual Database Persistence',
      description: 'High-throughput document indexing in MongoDB paired with an ACID-compliant SQLite fallback for unbreakable system resilience.',
      badge: 'Hybrid Storage',
    },
    {
      icon: Zap,
      title: 'Edge & Budget GPU Optimized',
      description: 'Trained and optimized with PyTorch FP16 Automatic Mixed Precision (AMP), safely running under 4 GB VRAM on NVIDIA GTX 1650 cards.',
      badge: '4GB VRAM Safe',
    },
  ];

  const pipelineSteps = [
    {
      step: '01',
      title: 'Stream Ingestion',
      description: 'Live RTSP cameras or uploaded CCTV files are ingested and converted into uniform 30 FPS spatiotemporal buffers.',
    },
    {
      step: '02',
      title: 'Temporal Window Sampling',
      description: 'Sliding 2-second windows extract 16 normalized frames (112x112) with Kinetics-400 channel statistics.',
    },
    {
      step: '03',
      title: '3D Neural Classification',
      description: 'The R(2+1)D-18 network evaluates spatiotemporal feature embeddings to predict anomaly probabilities across all 7 classes.',
    },
    {
      step: '04',
      title: 'Instant Alert & Evidence Logging',
      description: 'Events exceeding confidence thresholds trigger real-time WebSocket alerts and save evidence snapshots to the database.',
    },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-100 selection:bg-blue-600 selection:text-white">
      {/* ---------------- Navigation Bar ---------------- */}
      <header className="sticky top-0 z-50 bg-[#0B0F17]/85 backdrop-blur-md border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="p-2 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400 group-hover:scale-105 transition-transform">
              <Radio className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-lg tracking-tight text-white">VisionIQ</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-semibold border border-blue-500/30">
                  PRO
                </span>
              </div>
              <div className="text-[11px] text-slate-400 leading-none">AI Surveillance System</div>
            </div>
          </Link>

          {/* Quick Nav Anchors */}
          <nav className="hidden md:flex items-center gap-6 text-xs font-medium text-slate-400">
            <a href="#features" className="hover:text-white transition-colors">
              Platform Features
            </a>
            <a href="#classes" className="hover:text-white transition-colors">
              7 Anomaly Classes
            </a>
            <a href="#architecture" className="hover:text-white transition-colors">
              Pipeline Architecture
            </a>
            <a href="#specs" className="hover:text-white transition-colors">
              Specifications
            </a>
          </nav>

          {/* Right Action & System Status */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px] font-mono">
              <span
                className={`w-2 h-2 rounded-full ${
                  systemHealth.status === 'online' ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]' : 'bg-amber-400'
                }`}
              />
              <span className="text-slate-300">
                {systemHealth.status === 'online' ? `Engine Online (${systemHealth.device.toUpperCase()})` : 'Backend Standby'}
              </span>
            </div>

            <Link
              to="/overview"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <span>Launch Console</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* ---------------- Hero Section ---------------- */}
      <section className="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-28">
        {/* Ambient Glows */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-blue-600/10 blur-[130px] pointer-events-none rounded-full" />
        <div className="absolute top-1/3 right-1/4 w-[400px] h-[250px] bg-indigo-600/10 blur-[110px] pointer-events-none rounded-full" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-3xl mx-auto space-y-6">
            {/* Pill Banner */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-medium animate-in fade-in duration-300">
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
              <span>Phase 1 v2 Retrained Model Live • 66.7% Test Accuracy</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-tight">
              Real-Time Suspicious Activity Recognition for{' '}
              <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-cyan-400 bg-clip-text text-transparent">
                CCTV Surveillance
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-base sm:text-lg text-slate-300/90 leading-relaxed max-w-2xl mx-auto font-normal">
              Autonomous computer vision powered by spatiotemporal 3D deep learning. Instantly detect fighting,
              robberies, road accidents, and shoplifting with zero human fatigue and sub-second evidence generation.
            </p>

            {/* Call to Actions */}
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Link
                to="/overview"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold bg-blue-600 hover:bg-blue-500 text-white shadow-xl shadow-blue-600/30 transition-all hover:scale-105 active:scale-95"
              >
                <span>Launch Surveillance Console</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/live"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/80 transition-all hover:text-white"
              >
                <Cctv className="w-4 h-4 text-emerald-400" />
                <span>Live Surveillance</span>
              </Link>
              <Link
                to="/analysis"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/80 transition-all hover:text-white"
              >
                <Video className="w-4 h-4 text-blue-400" />
                <span>Analyze CCTV Video</span>
              </Link>
            </div>
          </div>

          {/* Interactive Live Surveillance HUD Simulation */}
          <div className="mt-14 max-w-5xl mx-auto rounded-2xl border border-slate-800 bg-[#0F172A]/80 backdrop-blur-xl shadow-2xl overflow-hidden">
            {/* Top Bar of CCTV Simulator */}
            <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between bg-slate-950/60 text-xs">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1.5 text-rose-400 font-mono font-bold">
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                  REC [00:14:32]
                </span>
                <span className="text-slate-500">•</span>
                <span className="text-slate-400 font-mono">CAM-02 // STORE_FRONT_EAST</span>
              </div>
              <div className="flex items-center gap-3 text-slate-400 font-mono text-[11px]">
                <span>30.0 FPS</span>
                <span>R(2+1)D-18 AMP</span>
                <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  GPU ACCELERATED
                </span>
              </div>
            </div>

            {/* Video Viewport Mockup */}
            <div className="relative aspect-video w-full bg-gradient-to-br from-slate-950 via-[#0B0F19] to-slate-900 flex items-center justify-center p-6 overflow-hidden">
              {/* Surveillance Grid Lines */}
              <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b15_1px,transparent_1px),linear-gradient(to_bottom,#1e293b15_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none" />

              {/* Mock Video Scene Visual */}
              <div className="relative z-10 w-full max-w-2xl bg-slate-900/90 border border-slate-700/60 rounded-xl p-6 shadow-2xl space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ActivityBadge activity="Fighting" />
                    <span className="text-xs text-slate-400 font-mono">Temporal Window: 16 Frames (2.0s)</span>
                  </div>
                  <span className="text-xs font-mono font-bold text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded-md border border-rose-500/30">
                    CRITICAL ALERT
                  </span>
                </div>

                {/* Simulated Target Detection Box */}
                <div className="h-44 rounded-lg border-2 border-dashed border-rose-500/60 bg-rose-500/5 relative flex items-center justify-center overflow-hidden">
                  <div className="absolute top-2 left-2 text-[10px] font-mono text-rose-400 bg-black/80 px-2 py-0.5 rounded border border-rose-500/40">
                    TARGET: CONFRONTATION_CLUSTER_01
                  </div>
                  <div className="text-center space-y-1">
                    <div className="text-2xl font-black text-white font-mono tracking-wider">
                      98.4% CONFIDENCE
                    </div>
                    <div className="text-xs text-rose-300/90">
                      Physical Aggression & Dynamic Spatiotemporal Impact Detected
                    </div>
                  </div>
                  <div className="absolute bottom-2 right-2 text-[10px] font-mono text-slate-400 bg-black/80 px-2 py-0.5 rounded">
                    LATENCY: 118ms
                  </div>
                </div>

                {/* Progress / Status metrics */}
                <div className="grid grid-cols-3 gap-3 pt-2 text-center text-xs">
                  <div className="bg-slate-950/70 p-2 rounded-lg border border-slate-800">
                    <div className="text-slate-400 text-[10px] uppercase font-mono">Prediction Head</div>
                    <div className="font-bold text-slate-200">Softmax Prob: 0.984</div>
                  </div>
                  <div className="bg-slate-950/70 p-2 rounded-lg border border-slate-800">
                    <div className="text-slate-400 text-[10px] uppercase font-mono">Evidence Capture</div>
                    <div className="font-bold text-emerald-400">Snapshot Saved</div>
                  </div>
                  <div className="bg-slate-950/70 p-2 rounded-lg border border-slate-800">
                    <div className="text-slate-400 text-[10px] uppercase font-mono">Dispatch Action</div>
                    <div className="font-bold text-blue-400">WebSocket Broadcast</div>
                  </div>
                </div>
              </div>

              {/* View Live Feed Button Overlay */}
              <div className="absolute bottom-4 right-4 z-20">
                <Link
                  to="/live"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-black/80 hover:bg-black text-white rounded-lg text-xs font-medium border border-slate-700 backdrop-blur-sm transition-all"
                >
                  <Eye className="w-3.5 h-3.5 text-blue-400" />
                  <span>Open Full Camera Wall</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- Key Numbers & Benchmarks ---------------- */}
      <section className="py-12 border-y border-slate-800/80 bg-[#0F172A]/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-6 rounded-2xl bg-[#111827] border border-slate-800 text-center space-y-1">
              <div className="text-3xl sm:text-4xl font-extrabold text-white">66.70%</div>
              <div className="text-xs font-semibold text-blue-400">Overall Test Accuracy</div>
              <div className="text-[11px] text-slate-400">Tested on 1,168 independent test clips</div>
            </div>

            <div className="p-6 rounded-2xl bg-[#111827] border border-slate-800 text-center space-y-1">
              <div className="text-3xl sm:text-4xl font-extrabold text-rose-400">98.40%</div>
              <div className="text-xs font-semibold text-rose-300">Fighting Recall</div>
              <div className="text-[11px] text-slate-400">Critical violent event detection rate</div>
            </div>

            <div className="p-6 rounded-2xl bg-[#111827] border border-slate-800 text-center space-y-1">
              <div className="text-3xl sm:text-4xl font-extrabold text-emerald-400">&lt; 122ms</div>
              <div className="text-xs font-semibold text-emerald-300">Inference Latency</div>
              <div className="text-[11px] text-slate-400">Fast seek & mixed precision forward pass</div>
            </div>

            <div className="p-6 rounded-2xl bg-[#111827] border border-slate-800 text-center space-y-1">
              <div className="text-3xl sm:text-4xl font-extrabold text-cyan-400">7 Classes</div>
              <div className="text-xs font-semibold text-cyan-300">Zero-Leakage Splitting</div>
              <div className="text-[11px] text-slate-400">Surveillance recording group stratified</div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- 7 Activity Classes Showcase ---------------- */}
      <section id="classes" className="py-20 lg:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-12">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-400">
              Activity Recognition Coverage
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
              7 Discrete Surveillance Classes
            </h2>
            <p className="text-sm text-slate-400">
              Trained on real-world CCTV surveillance footage from the DCSASS dataset, balanced and validated across
              zero-leakage parent camera recordings.
            </p>
          </div>

          {/* Interactive Class Selector Tabs */}
          <div className="flex flex-wrap items-center justify-center gap-2 mb-8">
            {anomalyCategories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setActiveTab(cat.id)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 ${
                  activeTab === cat.id
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                    : 'bg-[#111827] text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                <span>{cat.name}</span>
                <span className="text-[10px] font-mono opacity-80">{cat.recall}</span>
              </button>
            ))}
          </div>

          {/* Selected Class Deep Dive Card */}
          <div className="max-w-4xl mx-auto bg-[#111827] border border-slate-800 rounded-3xl p-6 sm:p-10 shadow-2xl relative overflow-hidden">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <ActivityBadge activity={currentCategory.name} />
                  <span className="text-xs font-mono text-slate-400">F1-Score: {currentCategory.f1}</span>
                </div>

                <h3 className="text-2xl font-bold text-white">{currentCategory.name} Detection</h3>
                <p className="text-sm text-slate-300 leading-relaxed">{currentCategory.description}</p>

                <div className="pt-2 border-t border-slate-800 space-y-2">
                  <div className="text-xs font-semibold text-slate-400">Spatiotemporal Dynamics:</div>
                  <div className="text-xs text-slate-300 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                    {currentCategory.characteristics}
                  </div>
                </div>

                <div className="pt-2">
                  <Link
                    to={`/events?activity=${currentCategory.name}`}
                    className="inline-flex items-center gap-2 text-xs font-semibold text-blue-400 hover:text-blue-300"
                  >
                    <span>Inspect genuine {currentCategory.name} event logs</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>

              {/* Performance Metrics Breakdown Box */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-6 space-y-4">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Model Verification Metrics
                </div>

                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Detection Rate (Recall)</span>
                      <span className="font-bold text-emerald-400">{currentCategory.recall}</span>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-emerald-500 h-2 rounded-full"
                        style={{ width: currentCategory.recall }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Precision Rate</span>
                      <span className="font-bold text-blue-400">{currentCategory.precision}</span>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: currentCategory.precision }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Harmonic Mean (F1)</span>
                      <span className="font-bold text-indigo-400">{currentCategory.f1}</span>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-indigo-500 h-2 rounded-full"
                        style={{ width: currentCategory.f1 }}
                      />
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between font-mono">
                  <span>Class: {currentCategory.id}</span>
                  <span>Tested on 1,168 clips</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- Core Capabilities ---------------- */}
      <section id="features" className="py-20 lg:py-28 bg-[#0F172A]/40 border-y border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-14">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-400">Enterprise AI Engine</span>
            <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
              Built for Real-World Surveillance Demands
            </h2>
            <p className="text-sm text-slate-400">
              VisionIQ combines spatiotemporal video action recognition, low-latency live camera streaming, and
              conversational investigation in one unified platform.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => {
              const Icon = f.icon;
              return (
                <div
                  key={i}
                  className="bg-[#111827] border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-all hover:-translate-y-1 group"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="p-3 rounded-xl bg-blue-600/10 border border-blue-500/20 text-blue-400 group-hover:bg-blue-600/20 transition-colors">
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                      {f.badge}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-white mb-2">{f.title}</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">{f.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ---------------- 4-Step Pipeline Architecture ---------------- */}
      <section id="architecture" className="py-20 lg:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-16">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-400">End-to-End Flow</span>
            <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">How VisionIQ Operates</h2>
            <p className="text-sm text-slate-400">
              From raw CCTV camera feeds to verified actionable evidence in under two seconds.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {pipelineSteps.map((st) => (
              <div
                key={st.step}
                className="bg-[#111827] border border-slate-800 rounded-2xl p-6 relative overflow-hidden"
              >
                <div className="text-4xl font-black text-slate-800/80 mb-3 font-mono">{st.step}</div>
                <h3 className="text-sm font-bold text-white mb-2">{st.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{st.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------- Hardware Specifications ---------------- */}
      <section id="specs" className="py-16 bg-[#0F172A]/50 border-t border-slate-800/80">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-[#111827] border border-slate-800 rounded-2xl p-6 sm:p-8 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Cpu className="w-5 h-5 text-blue-400" />
                <h3 className="text-base font-bold text-white">Engineered for Budget & Edge GPU Deployments</h3>
              </div>
              <p className="text-xs text-slate-400 max-w-xl">
                Tuned specifically for NVIDIA GTX 1650 (4 GB VRAM) and AMD Ryzen laptops. Micro-batch execution,
                Automatic Mixed Precision (AMP), and feature-frozen backbones prevent memory overflow while maintaining
                30 FPS continuous processing.
              </p>
            </div>

            <Link
              to="/status"
              className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition-all shrink-0"
            >
              <span>View System Diagnostics</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* ---------------- Call to Action ---------------- */}
      <section className="py-20 lg:py-24 text-center relative overflow-hidden">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <div className="w-14 h-14 rounded-2xl bg-blue-600/20 border border-blue-500/30 text-blue-400 flex items-center justify-center mx-auto">
            <Radio className="w-7 h-7" />
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Ready to Monitor CCTV Streams with VisionIQ?
          </h2>
          <p className="text-sm text-slate-300/80 max-w-xl mx-auto">
            Open the real-time surveillance console to monitor live feeds, analyze video files, or query detected
            suspicious incidents.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link
              to="/overview"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold bg-blue-600 hover:bg-blue-500 text-white shadow-xl shadow-blue-600/30 transition-all"
            >
              <span>Launch Surveillance Console</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/chat"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold bg-[#111827] hover:bg-slate-800 text-slate-300 border border-slate-800 transition-all"
            >
              <MessageSquare className="w-4 h-4 text-indigo-400" />
              <span>Ask AI Assistant</span>
            </Link>
          </div>
        </div>
      </section>

      {/* ---------------- Footer ---------------- */}
      <footer className="border-t border-slate-800/80 bg-slate-950/80 py-12 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="p-1.5 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30">
              <Radio className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-white">VisionIQ Pro</span> — AI-Powered CCTV Suspicious Activity Recognition
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-6">
            <Link to="/overview" className="hover:text-white transition-colors">
              Overview
            </Link>
            <Link to="/live" className="hover:text-white transition-colors">
              Live Surveillance
            </Link>
            <Link to="/analysis" className="hover:text-white transition-colors">
              Video Analysis
            </Link>
            <Link to="/events" className="hover:text-white transition-colors">
              Detected Events
            </Link>
            <Link to="/chat" className="hover:text-white transition-colors">
              AI Assistant
            </Link>
            <Link to="/status" className="hover:text-white transition-colors">
              System Status
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
