'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Case, QueueResponse } from '@/types';
import { fetchQueue } from '@/lib/api';
import { SummaryCard } from '@/components/SummaryCard';
import { CaseCard } from '@/components/CaseCard';
import { 
  Search, 
  RefreshCw, 
  UserCheck, 
  CheckCircle2,
  PlusCircle
} from 'lucide-react';

export default function ContinuityQueuePage() {
  const [queueData, setQueueData] = useState<QueueResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const loadQueue = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchQueue();
      setQueueData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load Continuity Queue');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const cases = queueData?.cases || [];
  
  // Real stats computed from the loaded queue cases
  const unresolvedCount = cases.filter(c => c.status === 'UNRESOLVED').length;
  const atRiskCount = cases.filter(c => c.status === 'AT_RISK').length;
  const overdueCount = cases.filter(c => c.status === 'OVERDUE').length;
  const blockedCount = cases.filter(c => c.status === 'BLOCKED').length;
  const exceptionsCount = cases.filter(c => c.status === 'EXCEPTION').length;
  const totalCount = cases.length;

  // Filter cases based on selected tab and search query
  const filteredCases = cases.filter((c) => {
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
    if (selectedFilter === 'EXCEPTION') return c.status === 'EXCEPTION';
    if (selectedFilter === 'RESOLVED') return c.status === 'RESOLVED';
    return true;
  });

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Banner: Employee 2 Operational Context */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-7 sm:p-8 shadow-2xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-slate-900 text-white shadow-2xs">
              <UserCheck className="w-3.5 h-3.5 text-amber-400" />
              Employee 2 View — Priya Sharma
            </span>
            <span className="text-xs text-slate-400 font-mono">•</span>
            <span className="text-xs text-slate-600 font-semibold">Incoming Shift</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Continuity Queue
          </h1>

          <p className="text-sm text-slate-600 leading-relaxed">
            Work that needs attention after responsibility changes.
          </p>

          <p className="text-xs text-slate-500">
            You do <strong className="text-slate-800 font-semibold">not</strong> have to reread raw notes. Work has been parsed into structured commitments, blockers, system exceptions, and immediate next actions.
          </p>
        </div>

        {/* Actions: matched h-10 heights */}
        <div className="flex items-center gap-3 w-full sm:w-auto shrink-0">
          <button
            onClick={loadQueue}
            disabled={isLoading}
            className="h-10 inline-flex items-center gap-2 px-4 text-xs font-bold text-slate-700 hover:text-slate-900 bg-white border border-slate-200 hover:bg-slate-50 rounded-xl transition-colors shadow-2xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh Queue
          </button>
          <Link
            href="/handoff/new"
            className="h-10 inline-flex items-center gap-2 px-5 text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 rounded-xl transition-colors shadow-2xs"
          >
            <PlusCircle className="w-4 h-4 text-amber-400" />
            Create Handoff
          </Link>
        </div>
      </div>

      {/* Summary KPI Cards: Identical heights and alignment */}
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

      {/* Search and Filter Tabs: Aligned baseline */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
        {/* Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {[
            { id: 'ALL', label: `All Queue (${totalCount})` },
            { id: 'UNRESOLVED', label: `Unresolved (${unresolvedCount})` },
            { id: 'AT_RISK', label: `At Risk (${atRiskCount})` },
            { id: 'OVERDUE', label: `Overdue (${overdueCount})` },
            { id: 'BLOCKED', label: `Blocked (${blockedCount})` },
            { id: 'EXCEPTION', label: `Exceptions (${exceptionsCount})` },
            { id: 'RESOLVED', label: 'Resolved' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedFilter(tab.id)}
              className={`h-8 px-3 rounded-lg text-xs font-bold whitespace-nowrap transition-colors ${
                selectedFilter === tab.id
                  ? 'bg-slate-900 text-white shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search title, blocker, owner..."
            className="h-8 w-full text-xs pl-8 pr-3 rounded-lg border border-slate-300 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 placeholder:text-slate-400"
          />
        </div>
      </div>

      {/* Queue Work Cards Grid */}
      <div>
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-80 bg-slate-200 rounded-xl" />
            ))}
          </div>
        ) : error ? (
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-center text-rose-800 text-sm">
            {error}. Make sure the backend is running at <code className="font-mono text-xs font-bold">http://localhost:8000</code>.
          </div>
        ) : filteredCases.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500 text-sm space-y-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
            <p className="font-bold text-slate-900">No cases match the selected filter ({selectedFilter}).</p>
            <p className="text-xs text-slate-400">All assigned items in this category have been processed or resolved.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCases.map((caseItem) => (
              <CaseCard key={caseItem.case_id} caseData={caseItem} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
