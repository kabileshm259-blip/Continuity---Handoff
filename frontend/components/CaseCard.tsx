import React from 'react';
import Link from 'next/link';
import { Case } from '@/types';
import { StatusBadge } from './StatusBadge';
import { 
  Calendar, 
  User, 
  ArrowRight,
  ShieldAlert,
  Clock
} from 'lucide-react';

interface CaseCardProps {
  caseData: Case;
}

export const CaseCard: React.FC<CaseCardProps> = ({ caseData }) => {
  const activeBlockers = caseData.blockers?.filter(b => b.status === 'ACTIVE') || [];
  const pendingTasks = caseData.tasks?.filter(t => t.status !== 'COMPLETED') || [];
  const activeCommitments = caseData.commitments?.filter(c => c.status === 'ACTIVE') || [];

  // Determine the primary unresolved summary
  const unresolvedSummary = pendingTasks.length > 0 
    ? pendingTasks[0].title + (pendingTasks[0].next_action ? ` — ${pendingTasks[0].next_action}` : '')
    : caseData.description && !caseData.description.toLowerCase().includes('auto-generated')
    ? caseData.description
    : activeCommitments.length > 0
    ? `Pending fulfillment: ${activeCommitments[0].description}`
    : 'Pending operational verification';

  return (
    <div className="bg-white rounded-xl border border-slate-200/90 hover:border-slate-300 shadow-2xs hover:shadow-xs transition-all duration-150 p-5 flex flex-col justify-between h-full w-full">
      {/* Top Section */}
      <div className="flex flex-col flex-1">
        {/* Row 1: Status, Case ID, Priority - Exactly matched h-6 height */}
        <div className="flex items-center justify-between gap-2 h-6 mb-3">
          <div className="flex items-center gap-2 shrink-0">
            <StatusBadge status={caseData.status} size="sm" />
            <span className="font-mono text-[11px] font-bold text-slate-600 bg-slate-100 px-2 h-6 inline-flex items-center rounded-md border border-slate-200">
              {caseData.case_id}
            </span>
          </div>

          <span className={`h-6 inline-flex items-center text-[10px] font-extrabold uppercase px-2 rounded-md border shrink-0 ${
            caseData.priority === 'URGENT'
              ? 'bg-rose-50 text-rose-700 border-rose-200'
              : caseData.priority === 'HIGH'
              ? 'bg-orange-50 text-orange-700 border-orange-200'
              : 'bg-slate-100 text-slate-700 border-slate-200'
          }`}>
            {caseData.priority} PRIORITY
          </span>
        </div>

        {/* Row 2: Case Title - Fixed h-12 height with line-clamp-2 for identical baseline */}
        <div className="h-12 flex items-center mb-2.5">
          <h3 className="text-[15px] font-bold text-slate-900 leading-snug tracking-tight line-clamp-2">
            {caseData.title}
          </h3>
        </div>

        {/* Row 3: Owner & Deadline metadata */}
        <div className="flex items-center justify-between gap-2 text-xs text-slate-600 border-b border-slate-100 pb-3 mb-3">
          <div className="flex items-center gap-1.5 truncate">
            <User className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="text-slate-500">Owner:</span>
            <strong className="text-slate-900 font-semibold truncate">{caseData.owner}</strong>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="text-slate-500">Deadline:</span>
            <strong className={`font-semibold ${
              caseData.deadline?.toLowerCase().includes('today') || caseData.status === 'OVERDUE'
                ? 'text-red-700 font-bold'
                : 'text-slate-900'
            }`}>
              {caseData.deadline || 'No target date'}
            </strong>
          </div>
        </div>

        {/* Row 4: Unresolved Work box */}
        <div className="bg-slate-50/90 rounded-lg p-3 border border-slate-200/80 mb-2.5 min-h-[66px] flex flex-col justify-center">
          <span className="font-bold text-slate-500 uppercase tracking-wider text-[10px] flex items-center gap-1 mb-0.5">
            <Clock className="w-3 h-3 text-slate-500 shrink-0" />
            Unresolved Work
          </span>
          <p className="text-xs font-semibold text-slate-900 line-clamp-2 leading-relaxed">
            {unresolvedSummary}
          </p>
        </div>

        {/* Row 5: Blocker box (consistent min-height so cards align) */}
        <div className="min-h-[58px] mb-3 flex flex-col justify-center">
          {activeBlockers.length > 0 ? (
            <div className="bg-rose-50/70 rounded-lg p-2.5 border border-rose-200">
              <span className="font-bold text-rose-800 uppercase tracking-wider text-[10px] flex items-center gap-1 mb-0.5">
                <ShieldAlert className="w-3 h-3 text-rose-600 shrink-0" />
                Active Blocker
              </span>
              <p className="text-xs font-bold text-rose-950 truncate">
                {activeBlockers[0].description}
              </p>
              {activeBlockers[0].blocked_by && (
                <p className="text-[11px] text-rose-700 truncate font-medium">
                  Blocked by: <span className="font-bold">{activeBlockers[0].blocked_by}</span>
                </p>
              )}
            </div>
          ) : (
            <div className="bg-slate-50/40 rounded-lg p-2.5 border border-dashed border-slate-200 text-[11px] text-slate-400 italic flex items-center gap-1.5">
              <span>No active blockers identified</span>
            </div>
          )}
        </div>

        {/* Row 6: Immediate Next Action callout */}
        <div className="bg-slate-900 rounded-lg p-3 text-white mb-4 min-h-[64px] flex flex-col justify-center">
          <span className="text-[10px] uppercase font-bold tracking-wider text-amber-400 block mb-0.5">
            Immediate Next Action
          </span>
          <p className="text-xs font-semibold text-slate-100 line-clamp-2 leading-relaxed">
            {caseData.next_action || 'Review continuity case details and verify current state.'}
          </p>
        </div>
      </div>

      {/* Row 7: Bottom CTA Pinned to bottom with mt-auto */}
      <div className="pt-3 border-t border-slate-100 mt-auto">
        <Link
          href={`/cases/${caseData.case_id}`}
          className="w-full h-10 inline-flex items-center justify-center gap-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-900 text-xs font-bold transition-colors group"
        >
          View Continuity Case
          <ArrowRight className="w-3.5 h-3.5 text-slate-600 group-hover:translate-x-0.5 transition-transform" />
        </Link>
      </div>
    </div>
  );
};
