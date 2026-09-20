'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Case } from '@/types';
import { fetchCases } from '@/lib/api';
import { CaseCard } from '@/components/CaseCard';
import { SummaryCard } from '@/components/SummaryCard';
import { 
  PlusCircle, 
  ArrowRight, 
  Clock, 
  AlertTriangle, 
  ShieldAlert,
  AlertOctagon,
  CheckCircle2, 
  RefreshCw,
  ArrowRightLeft,
  FileText,
  Cpu,
  ShieldCheck,
  Search,
  Check,
  Lock,
  Layers
} from 'lucide-react';

export default function HomePage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchCases();
      setCases(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load operational cases');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Compute real metrics from the loaded cases
  const unresolvedCount = cases.filter(c => c.status === 'UNRESOLVED').length;
  const atRiskCount = cases.filter(c => c.status === 'AT_RISK').length;
  const overdueCount = cases.filter(c => c.status === 'OVERDUE').length;
  const blockedCount = cases.filter(c => c.status === 'BLOCKED').length;

  const filteredCases = cases.filter(c => {
    const matchesSearch = 
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.case_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.customer && c.customer.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (c.next_action && c.next_action.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (c.owner && c.owner.toLowerCase().includes(searchQuery.toLowerCase()));

    if (!matchesSearch) return false;

    if (selectedFilter === 'ALL') return true;
    if (selectedFilter === 'UNRESOLVED') return c.status === 'UNRESOLVED';
    if (selectedFilter === 'AT_RISK') return c.status === 'AT_RISK';
    if (selectedFilter === 'OVERDUE') return c.status === 'OVERDUE';
    if (selectedFilter === 'BLOCKED') return c.status === 'BLOCKED';
    return true;
  });

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* 3. DASHBOARD HERO: Clean, enterprise-oriented 2-column layout */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-7 sm:p-9 shadow-2xs flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8">
        {/* Left Side: Headline, Paragraph, Actions */}
        <div className="space-y-3.5 max-w-2xl">
          <div className="text-[11px] font-extrabold uppercase tracking-widest text-slate-500">
            WORKPLACE HANDOFF INTELLIGENCE
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-[1.15]">
            Make sure important work<br />
            survives the handoff.
          </h1>

          <p className="text-sm sm:text-[15px] text-slate-600 leading-relaxed max-w-xl pt-0.5">
            Turn messy employee handoffs into accountable work — with context, commitments, blockers, deadlines and evidence preserved.
          </p>

          {/* Buttons: Exactly matched h-11 height, aligned baseline */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link
              href="/handoff/new"
              className="h-11 inline-flex items-center justify-center gap-2 px-5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold shadow-2xs transition-colors whitespace-nowrap"
            >
              <PlusCircle className="w-4 h-4 text-amber-400" />
              Create Handoff
              <ArrowRight className="w-3.5 h-3.5 ml-0.5 text-slate-400" />
            </Link>

            <Link
              href="/queue"
              className="h-11 inline-flex items-center justify-center gap-2 px-5 rounded-xl bg-white border border-slate-300 hover:bg-slate-50 text-slate-900 text-xs font-bold transition-colors whitespace-nowrap shadow-2xs"
            >
              <ArrowRightLeft className="w-4 h-4 text-slate-600" />
              Continuity Queue
            </Link>
          </div>
        </div>

        {/* Right Side: Structured Enterprise Benefit Panel */}
        <div className="w-full lg:w-80 bg-slate-50 rounded-xl p-5 border border-slate-200/80 shadow-2xs space-y-3 shrink-0">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200/80 pb-2">
            Enterprise Continuity Standard
          </div>
          <div className="space-y-2.5 text-xs text-slate-700">
            <div className="flex items-start gap-2">
              <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-900">Zero Context Loss:</strong> Raw notes extracted into structured commitments.
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-900">Deterministic Enforcement:</strong> Code enforces statuses without AI guesswork.
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-900">S3 Audit Traceability:</strong> Immutable proof attached to every transition.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. MOST IMPORTANT FIX — KPI / SUMMARY CARDS: Identical heights, aligned baselines */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          type="unresolved"
          label="UNRESOLVED"
          count={unresolvedCount}
          subtext="Incomplete work items"
          isActive={selectedFilter === 'UNRESOLVED'}
          onClick={() => setSelectedFilter(selectedFilter === 'UNRESOLVED' ? 'ALL' : 'UNRESOLVED')}
        />
        <SummaryCard
          type="at_risk"
          label="AT RISK"
          count={atRiskCount}
          subtext="Approaching deadline"
          isActive={selectedFilter === 'AT_RISK'}
          onClick={() => setSelectedFilter(selectedFilter === 'AT_RISK' ? 'ALL' : 'AT_RISK')}
        />
        <SummaryCard
          type="overdue"
          label="OVERDUE"
          count={overdueCount}
          subtext="Elapsed deadlines"
          isActive={selectedFilter === 'OVERDUE'}
          onClick={() => setSelectedFilter(selectedFilter === 'OVERDUE' ? 'ALL' : 'OVERDUE')}
        />
        <SummaryCard
          type="blocked"
          label="BLOCKED"
          count={blockedCount}
          subtext="External dependency"
          isActive={selectedFilter === 'BLOCKED'}
          onClick={() => setSelectedFilter(selectedFilter === 'BLOCKED' ? 'ALL' : 'BLOCKED')}
        />
      </div>

      {/* 5. ARCHITECTURE / WORKFLOW SECTION: 4 perfectly aligned columns with principle */}
      <div className="bg-[#0B132B] rounded-2xl p-6 sm:p-7 text-white shadow-xs border border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <span className="text-[11px] font-extrabold uppercase tracking-widest text-slate-400">
            HOW CONTINUITY PRESERVES WORKLOAD
          </span>
          <span className="font-mono text-[11px] font-bold text-amber-400 bg-slate-900/90 px-3 py-1 rounded-md border border-slate-800 self-start sm:self-auto shadow-2xs">
            AI EXTRACTS. CODE DECIDES.
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          {/* 01 Ingestion */}
          <div className="bg-slate-900/90 rounded-xl p-4 border border-slate-800 flex flex-col justify-between h-[126px]">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-[10px] text-amber-400 font-bold">01 INGESTION</span>
                <FileText className="w-3.5 h-3.5 text-slate-400" />
              </div>
              <p className="font-bold text-slate-100 text-sm">Employee 1 Notes</p>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Chats, tickets, and emails collected without rigid templates.
            </p>
          </div>

          {/* 02 Extraction */}
          <div className="bg-slate-900/90 rounded-xl p-4 border border-slate-800 flex flex-col justify-between h-[126px]">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-[10px] text-indigo-400 font-bold">02 EXTRACTION</span>
                <Cpu className="w-3.5 h-3.5 text-indigo-400" />
              </div>
              <p className="font-bold text-slate-100 text-sm">Bedrock Nova 2 Lite</p>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Extracts commitments, blockers, deadlines, and exceptions as facts.
            </p>
          </div>

          {/* 03 Policy Engine */}
          <div className="bg-slate-900/90 rounded-xl p-4 border border-slate-800 flex flex-col justify-between h-[126px]">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-[10px] text-emerald-400 font-bold">03 POLICY ENGINE</span>
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <p className="font-bold text-slate-100 text-sm">Deterministic Rules</p>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Code decides operational status: UNRESOLVED, AT_RISK, BLOCKED.
            </p>
          </div>

          {/* 04 Accountability */}
          <div className="bg-slate-900/90 rounded-xl p-4 border border-slate-800 flex flex-col justify-between h-[126px]">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-[10px] text-cyan-400 font-bold">04 ACCOUNTABILITY</span>
                <Layers className="w-3.5 h-3.5 text-cyan-400" />
              </div>
              <p className="font-bold text-slate-100 text-sm">Continuity Queue</p>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Immediate next actions, S3-backed evidence, and audit trails.
            </p>
          </div>
        </div>
      </div>

      {/* 6. ACTIVE CONTINUITY CASES: Headline and controls on identical horizontal baseline */}
      <div className="space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Layers className="w-4 h-4 text-slate-700" />
              Active Continuity Cases ({filteredCases.length})
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Work items actively tracked across shifts with preserved operational context.
            </p>
          </div>

          {/* Controls: Search, Clear Filter, Refresh - Exactly matched h-9 height */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search cases..."
                className="h-9 text-xs pl-8 pr-3 rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900 w-44 sm:w-56"
              />
            </div>

            {selectedFilter !== 'ALL' && (
              <button
                onClick={() => setSelectedFilter('ALL')}
                className="h-9 text-xs font-semibold text-slate-600 hover:text-slate-900 px-3 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors"
              >
                Clear Filter ({selectedFilter})
              </button>
            )}

            <button
              onClick={loadData}
              disabled={isLoading}
              className="h-9 inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white border border-slate-200 hover:bg-slate-50 px-3 rounded-lg transition-colors shadow-2xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Case Cards Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-80 bg-slate-200 rounded-xl" />
            ))}
          </div>
        ) : error ? (
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-center text-rose-800 text-sm">
            {error}. Make sure the FastAPI backend is running at <code className="font-mono text-xs font-bold">http://localhost:8000</code>.
          </div>
        ) : filteredCases.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500 text-sm space-y-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
            <p className="font-bold text-slate-900">No cases match the selected filter ({selectedFilter}).</p>
            <p className="text-xs text-slate-400">
              Select another metric card above or click "Clear Filter" to view all active continuity cases.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCases.map(caseItem => (
              <CaseCard key={caseItem.case_id} caseData={caseItem} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
