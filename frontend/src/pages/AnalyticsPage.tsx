import React, { useEffect, useState, useMemo } from 'react';
import { Card } from '../components/ui/Card';
import { StatCard } from '../components/ui/StatCard';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { ApiErrorState } from '../components/ui/ApiErrorState';
import { apiService } from '../services/api';
import { BenchmarkRecord, ProcessorProfile, AnalyticsSummary } from '../types';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  CartesianGrid,
} from 'recharts';
import { BarChart3, Zap, Cpu, HardDrive, ShieldCheck, Activity } from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [benchmarks, setBenchmarks] = useState<BenchmarkRecord[]>([]);
  const [processors, setProcessors] = useState<ProcessorProfile[]>([]);

  const fetchAnalyticsData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [analyticsRes, benchmarksRes, processorsRes] = await Promise.all([
        apiService.getAnalytics(),
        apiService.getBenchmarks('baseline'),
        apiService.getProcessors(),
      ]);
      setAnalytics(analyticsRes);
      setBenchmarks(benchmarksRes);
      setProcessors(processorsRes);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch analytics dataset from backend API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  // Chart 1: Execution Latency (KeyGen, Encap, Decap in microseconds)
  const latencyData = useMemo(() => {
    return benchmarks
      .filter((d) => d.verification_status === 'PASS')
      .map((d) => ({
        name: `${d.mcu} (${d.variant})`,
        KeyGen: typeof d.keygen_us === 'number' ? d.keygen_us : 0,
        Encap: typeof d.encap_us === 'number' ? d.encap_us : 0,
        Decap: typeof d.decap_us === 'number' ? d.decap_us : 0,
      }));
  }, [benchmarks]);

  // Chart 2: CPU Cycles Breakdown
  const cyclesData = useMemo(() => {
    return benchmarks
      .filter((d) => d.verification_status === 'PASS')
      .map((d) => ({
        name: `${d.mcu}-${d.variant}`,
        KeyGenCycles: typeof d.keygen_cycles === 'number' ? Math.round(d.keygen_cycles / 1000) : 0,
        EncapCycles: typeof d.encap_cycles === 'number' ? Math.round(d.encap_cycles / 1000) : 0,
        DecapCycles: typeof d.decap_cycles === 'number' ? Math.round(d.decap_cycles / 1000) : 0,
      }));
  }, [benchmarks]);

  // Chart 3: RAM Footprint Comparison
  const ramData = useMemo(() => {
    return benchmarks.map((d) => ({
      name: `${d.mcu} (${d.variant})`,
      RAM: d.ram_kb,
      Status: d.verification_status,
    }));
  }, [benchmarks]);

  // Chart 4: Flash Capacity Comparison
  const flashData = useMemo(() => {
    return processors.map((p) => ({
      name: p.mcu,
      FlashKB: p.flash,
      FrequencyMHz: p.frequency,
    }));
  }, [processors]);

  // Chart 5: Energy Consumption Comparison (Microjoules)
  const energyData = useMemo(() => {
    return benchmarks
      .filter((d) => d.verification_status === 'PASS' && d.energy_uj)
      .map((d) => ({
        name: `${d.mcu} (${d.variant})`,
        Energy_uJ: d.energy_uj || 0,
      }));
  }, [benchmarks]);

  // Chart 6: Verification Status Pie Chart
  const statusPieData = useMemo(() => {
    const passes = analytics?.totalPasses || benchmarks.filter((b) => b.verification_status === 'PASS').length;
    const ooms = analytics?.totalOOMs || benchmarks.filter((b) => b.verification_status === 'OOM').length;
    return [
      { name: 'PASS (Execution Success)', value: passes, color: '#059669' },
      { name: 'OOM (Out-Of-Memory)', value: ooms, color: '#DC2626' },
    ];
  }, [analytics, benchmarks]);

  // Chart 7: Multi-Dimensional Variant Evaluation Radar
  const radarData = [
    { subject: 'Security Level', MLKEM512: 40, MLKEM768: 75, MLKEM1024: 100 },
    { subject: 'Execution Speed', MLKEM512: 95, MLKEM768: 75, MLKEM1024: 50 },
    { subject: 'RAM Efficiency', MLKEM512: 90, MLKEM768: 65, MLKEM1024: 40 },
    { subject: 'Ciphertext Overhead', MLKEM512: 85, MLKEM768: 65, MLKEM1024: 45 },
    { subject: 'IoT Compatibility', MLKEM512: 100, MLKEM768: 70, MLKEM1024: 35 },
  ];

  const tooltipStyle = {
    backgroundColor: '#ffffff',
    borderColor: '#e2e8f0',
    borderRadius: '6px',
    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
    fontSize: '12px',
    color: '#0f172a',
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Header */}
      <Card className="p-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded bg-slate-100 border border-slate-200 text-slate-800">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Performance & Resource Analytics</h1>
            <p className="text-xs text-slate-500">
              Quantitative comparison of CPU cycles, execution latencies, SRAM footprints, Flash capacity, and energy consumption
            </p>
          </div>
        </div>
      </Card>

      {loading ? (
        <Card className="p-8">
          <LoadingSpinner label="Loading analytics dataset from backend API..." />
        </Card>
      ) : error ? (
        <ApiErrorState
          title="Failed to Load Analytics Data"
          message={error}
          onRetry={fetchAnalyticsData}
        />
      ) : (
        <>
          {/* KPI Cards Header */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Total Benchmarks"
              value={analytics ? analytics.totalBenchmarks.toLocaleString() : '0'}
              subtitle="Total empirical simulation runs"
              icon={<Zap className="w-5 h-5 text-slate-700" />}
            />
            <StatCard
              title="Pass Rate"
              value={analytics ? `${analytics.passRatePercent}%` : '0%'}
              subtitle={`${analytics?.totalPasses || 0} Successful PASS runs`}
              icon={<ShieldCheck className="w-5 h-5 text-emerald-600" />}
            />
            <StatCard
              title="SRAM Safety Bound"
              value="16 KB SRAM"
              subtitle="Min RAM bound for ML-KEM-512"
              icon={<HardDrive className="w-5 h-5 text-slate-700" />}
            />
            <StatCard
              title="Avg Encap Latency"
              value={analytics ? `${(analytics.avgEncapLatencyUs / 1000).toFixed(1)} ms` : '0 ms'}
              subtitle="Average across target MCUs"
              icon={<Activity className="w-5 h-5 text-slate-700" />}
            />
          </div>

          {/* Chart Row 1: Execution Time & CPU Cycles */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Execution Time Comparison */}
            <div className="lg:col-span-6">
              <Card className="p-5">
                <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-slate-700" /> Execution Time Comparison (Microseconds µs)
                </h3>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={latencyData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 9 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 9 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Legend wrapperStyle={{ fontSize: '11px' }} />
                      <Bar dataKey="KeyGen" fill="#1E3A8A" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="Encap" fill="#2563EB" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="Decap" fill="#7C3AED" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </div>

            {/* CPU Execution Cycles */}
            <div className="lg:col-span-6">
              <Card className="p-5">
                <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-slate-700" /> CPU Execution Cycles (in Kilo-Cycles)
                </h3>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={cyclesData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 9 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 9 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Legend wrapperStyle={{ fontSize: '11px' }} />
                      <Line type="monotone" dataKey="KeyGenCycles" stroke="#1E3A8A" strokeWidth={2} dot={{ r: 3 }} />
                      <Line type="monotone" dataKey="EncapCycles" stroke="#059669" strokeWidth={2} dot={{ r: 3 }} />
                      <Line type="monotone" dataKey="DecapCycles" stroke="#D97706" strokeWidth={2} dot={{ r: 3 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </div>
          </div>

          {/* Chart Row 2: RAM Footprint & Energy Graph */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* RAM Footprint Bar Chart */}
            <div className="lg:col-span-6">
              <Card className="p-5">
                <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <HardDrive className="w-4 h-4 text-slate-700" /> SRAM Footprint per Target (KB)
                </h3>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={ramData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 9 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 9 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="RAM" fill="#D97706" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </div>

            {/* Energy Consumption Chart */}
            <div className="lg:col-span-6">
              <Card className="p-5">
                <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-slate-700" /> Energy Consumption per Operation (Microjoules µJ)
                </h3>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={energyData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 9 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 9 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="Energy_uJ" fill="#059669" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </div>
          </div>

          {/* Chart Row 3: Flash Capacity, Radar Evaluation & Verification Status */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Flash Usage Graph */}
            <div className="lg:col-span-4">
              <Card className="p-5">
                <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <HardDrive className="w-4 h-4 text-slate-700" /> Flash Memory Capacity (KB)
                </h3>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={flashData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 9 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 9 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="FlashKB" fill="#2563EB" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </div>

            {/* Multi-Dimensional Variant Evaluation Radar */}
            <div className="lg:col-span-5">
              <Card className="p-5">
                <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-slate-700" /> Multi-Dimensional Variant Comparison
                </h3>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                      <PolarGrid stroke="#cbd5e1" />
                      <PolarAngleAxis dataKey="subject" stroke="#475569" tick={{ fontSize: 9 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#94a3b8" />
                      <Radar name="ML-KEM-512" dataKey="MLKEM512" stroke="#2563eb" fill="#2563eb" fillOpacity={0.2} />
                      <Radar name="ML-KEM-768" dataKey="MLKEM768" stroke="#059669" fill="#059669" fillOpacity={0.2} />
                      <Radar name="ML-KEM-1024" dataKey="MLKEM1024" stroke="#7c3aed" fill="#7c3aed" fillOpacity={0.2} />
                      <Legend wrapperStyle={{ fontSize: '11px' }} />
                      <Tooltip contentStyle={tooltipStyle} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </div>

            {/* Verification Status Distribution (Pie Chart) */}
            <div className="lg:col-span-3">
              <Card className="p-5 flex flex-col justify-between h-full">
                <h3 className="text-sm font-bold text-slate-900 mb-2 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" /> Verification Status
                </h3>
                <div className="h-48 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={statusPieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={65}
                        paddingAngle={4}
                        dataKey="value"
                      >
                        {statusPieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={tooltipStyle} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex flex-col gap-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-slate-700">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-600" /> PASS:
                    </span>
                    <span className="font-bold text-slate-900 font-mono">
                      {analytics ? `${analytics.passRatePercent}%` : '87.3%'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-slate-700">
                      <span className="w-2.5 h-2.5 rounded-full bg-rose-600" /> OOM:
                    </span>
                    <span className="font-bold text-slate-900 font-mono">
                      {analytics ? `${(100 - analytics.passRatePercent).toFixed(1)}%` : '12.7%'}
                    </span>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
