'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Case, ActionType, ActionRequest } from '@/types';
import { fetchCase, performCaseAction } from '@/lib/api';
import { StatusBadge } from '@/components/StatusBadge';
import { AuditTimeline } from '@/components/AuditTimeline';
import { ActionModal } from '@/components/ActionModal';
import { 
  ArrowLeft, 
  User, 
  Calendar, 
  Clock, 
  AlertCircle, 
  CheckCircle2, 
  ShieldAlert, 
  Sparkles, 
  FileText, 
  Paperclip, 
  UserCheck, 
  AlertTriangle,
  RefreshCw,
  Eye,
  X
} from 'lucide-react';

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = params.id as string;

  const [caseData, setCaseData] = useState<Case | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Action Modal State
  const [activeModalAction, setActiveModalAction] = useState<ActionType | null>(null);

  // Evidence Viewer Modal State
  const [isEvidenceModalOpen, setIsEvidenceModalOpen] = useState(false);
  const [selectedEvidenceContent, setSelectedEvidenceContent] = useState<string>('');
  const [selectedEvidenceKey, setSelectedEvidenceKey] = useState<string>('');

  const loadCase = async () => {
    if (!caseId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchCase(caseId);
      setCaseData(data);
    } catch (err: any) {
      setError(err.message || `Failed to load case ${caseId}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCase();
  }, [caseId]);

  const handleActionSubmit = async (request: ActionRequest) => {
    if (!caseId) return;
    const updated = await performCaseAction(caseId, request);
    setCaseData(updated);
  };

  const openEvidenceModal = (content: string, keyName: string) => {
    setSelectedEvidenceContent(content);
    setSelectedEvidenceKey(keyName);
    setIsEvidenceModalOpen(true);
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto py-12 space-y-6 animate-pulse">
        <div className="h-6 w-36 bg-slate-200 rounded" />
        <div className="h-28 bg-slate-200 rounded-2xl" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-96 bg-slate-200 rounded-2xl" />
          <div className="h-96 bg-slate-200 rounded-2xl" />
        </div>
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="max-w-2xl mx-auto py-12 text-center space-y-4">
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-rose-800 text-sm font-medium">
          {error || 'Continuity case not found.'}
        </div>
        <Link
          href="/queue"
          className="inline-flex items-center gap-2 text-xs font-bold text-slate-900 hover:text-slate-700 underline"
        >
          <ArrowLeft className="w-4 h-4" />
          Return to Continuity Queue
        </Link>
      </div>
    );
  }

  const completedTasks = caseData.tasks?.filter((t) => t.status === 'COMPLETED') || [];
  const pendingTasks = caseData.tasks?.filter((t) => t.status !== 'COMPLETED') || [];
  const activeCommitments = caseData.commitments?.filter((c) => c.status === 'ACTIVE') || [];
  const activeBlockers = caseData.blockers?.filter((b) => b.status === 'ACTIVE') || [];
  const activeExceptions = caseData.exceptions?.filter((e) => e.status === 'ACTIVE') || [];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          href="/queue"
          className="inline-flex items-center gap-2 text-xs font-bold text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 text-slate-400" />
          Back to Continuity Queue
        </Link>

        <button
          onClick={loadCase}
          className="h-8 inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white border border-slate-200 hover:bg-slate-50 px-3 rounded-lg transition-colors shadow-2xs"
        >
          <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
          Sync Case
        </button>
      </div>

      {/* TOP HEADER: Case Title, Status, Priority, Owner, Deadline */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-7 sm:p-8 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-3 max-w-3xl">
            {/* Badges Row: Exactly matched h-6 heights */}
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="font-mono text-xs font-bold px-3 h-6 inline-flex items-center rounded-md bg-slate-900 text-white shadow-2xs">
                {caseData.case_id}
              </span>
              <StatusBadge status={caseData.status} size="md" />
              <span className={`text-[11px] font-extrabold uppercase px-2.5 h-6 inline-flex items-center rounded-md border ${
                caseData.priority === 'URGENT' 
                  ? 'bg-rose-50 text-rose-700 border-rose-200' 
                  : caseData.priority === 'HIGH' 
                  ? 'bg-orange-50 text-orange-700 border-orange-200' 
                  : 'bg-slate-100 text-slate-700 border-slate-200'
              }`}>
                {caseData.priority} PRIORITY
              </span>
            </div>

            {/* Case Title */}
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight leading-tight">
              {caseData.title}
            </h1>

            {/* Key Metadata Row: Aligned with icons */}
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 pt-1 text-xs text-slate-600">
              <span className="flex items-center gap-1.5">
                <User className="w-4 h-4 text-slate-400 shrink-0" />
                <span className="text-slate-500">Accountable Owner:</span>
                <strong className="text-slate-900 font-bold">{caseData.owner}</strong>
              </span>

              {caseData.customer && (
                <span className="flex items-center gap-1.5">
                  <span className="text-slate-500">Customer:</span>
                  <strong className="text-slate-900 font-bold">{caseData.customer}</strong>
                </span>
              )}

              {caseData.deadline && (
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-slate-400 shrink-0" />
                  <span className="text-slate-500">Target Deadline:</span>
                  <strong className={`font-bold ${
                    caseData.deadline.toLowerCase().includes('today') || caseData.status === 'OVERDUE'
                      ? 'text-red-700' 
                      : 'text-slate-900'
                  }`}>
                    {caseData.deadline}
                  </strong>
                </span>
              )}

              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-slate-400 shrink-0" />
                <span className="text-slate-500">Last Synced:</span>
                <span className="text-slate-700 font-mono font-medium">{caseData.updated_at}</span>
              </span>
            </div>
          </div>

          {/* Action Trigger Buttons: Exactly matched h-10 heights */}
          <div className="flex flex-wrap md:flex-col gap-2 shrink-0">
            <button
              onClick={() => setActiveModalAction('RESOLVE')}
              disabled={caseData.status === 'RESOLVED'}
              className="h-10 inline-flex items-center justify-center gap-2 px-4 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 rounded-xl transition-colors shadow-2xs"
            >
              <CheckCircle2 className="w-4 h-4" />
              Mark Resolved
            </button>

            <button
              onClick={() => setActiveModalAction('REASSIGN')}
              className="h-10 inline-flex items-center justify-center gap-2 px-4 text-xs font-bold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 rounded-xl transition-colors shadow-2xs"
            >
              <UserCheck className="w-4 h-4 text-slate-500" />
              Reassign Owner
            </button>

            <button
              onClick={() => setActiveModalAction('ESCALATE')}
              disabled={caseData.priority === 'URGENT'}
              className="h-10 inline-flex items-center justify-center gap-2 px-4 text-xs font-bold text-rose-700 bg-rose-50 border border-rose-200 hover:bg-rose-100 disabled:opacity-50 rounded-xl transition-colors shadow-2xs"
            >
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              Escalate Case
            </button>
          </div>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Sections 1 through 8 */}
        <div className="lg:col-span-2 space-y-6">

          {/* 1. IMMEDIATE NEXT ACTION (Strongest Visual Anchor) */}
          <div className="bg-slate-900 rounded-2xl p-6 text-white shadow-sm border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-amber-400 shrink-0" />
                Immediate Next Action
              </span>
              <span className="text-[11px] font-mono bg-slate-800 text-slate-300 px-2.5 py-1 rounded-md border border-slate-700">
                Owner: {caseData.owner}
              </span>
            </div>
            <p className="text-base font-bold text-slate-100 leading-relaxed pt-1">
              {caseData.next_action || 'Review initial case context and confirm stakeholder update timeline.'}
            </p>
          </div>

          {/* 2. WHAT HAPPENED */}
          <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-2xs space-y-3">
            <h2 className="text-xs font-extrabold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <FileText className="w-4 h-4 text-slate-700" />
              1. What Happened
            </h2>
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/80 text-sm text-slate-800 leading-relaxed">
              {caseData.description && !caseData.description.toLowerCase().includes('auto-generated')
                ? caseData.description
                : `Work context transferred to ${caseData.owner}. Facts were parsed by Bedrock Nova 2 Lite from raw notes, and the policy engine evaluated the operational state as ${caseData.status}.`}
            </div>
          </div>

          {/* 3. DELIVERABLES BREAKDOWN (Completed & Unresolved) */}
          <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-2xs space-y-4">
            <h2 className="text-xs font-extrabold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-700" />
              2 & 3. Deliverables Breakdown
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Completed Work */}
              <div className="space-y-2.5">
                <div className="text-xs font-bold text-emerald-800 flex items-center justify-between border-b border-emerald-100 pb-1.5">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Completed Work ({completedTasks.length})
                  </span>
                </div>

                {completedTasks.length === 0 ? (
                  <p className="text-xs text-slate-400 italic p-3 bg-slate-50 rounded-lg">
                    No completed items logged in this handoff.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {completedTasks.map((t) => (
                      <div key={t.task_id} className="text-xs bg-emerald-50/60 border border-emerald-200 rounded-lg p-3 text-emerald-950 space-y-0.5">
                        <p className="font-bold">{t.title}</p>
                        {t.next_action && <p className="text-[11px] text-emerald-700">{t.next_action}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Unresolved Work */}
              <div className="space-y-2.5">
                <div className="text-xs font-bold text-slate-800 flex items-center justify-between border-b border-slate-200 pb-1.5">
                  <span className="flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-slate-600" />
                    Unresolved Work ({pendingTasks.length})
                  </span>
                </div>

                {pendingTasks.length === 0 ? (
                  <p className="text-xs text-slate-400 italic p-3 bg-slate-50 rounded-lg">
                    No unresolved deliverables outstanding.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {pendingTasks.map((t) => (
                      <div key={t.task_id} className="text-xs bg-slate-50 border border-slate-300 rounded-lg p-3 text-slate-900 space-y-0.5">
                        <p className="font-bold">{t.title}</p>
                        {t.next_action && <p className="text-[11px] text-slate-600">{t.next_action}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 4. COMMITMENTS */}
          <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-2xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h2 className="text-xs font-extrabold uppercase tracking-wider text-slate-800 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-slate-700" />
                4. Commitments & External Promises
              </h2>
              <span className="text-xs font-mono font-bold text-slate-500">
                {activeCommitments.length} active
              </span>
            </div>

            {activeCommitments.length === 0 ? (
              <p className="text-xs text-slate-400 italic p-3 bg-slate-50 rounded-lg">
                No external commitments logged.
              </p>
            ) : (
              <div className="space-y-2.5">
                {activeCommitments.map((com) => (
                  <div key={com.commitment_id} className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 text-xs space-y-1.5">
                    <p className="font-bold text-slate-900">{com.description}</p>
                    <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-600 pt-1">
                      <span>
                        Promised to: <strong className="text-slate-800">{com.committed_to}</strong>
                      </span>
                      {com.expected_date && (
                        <span className="font-bold text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200">
                          Due: {com.expected_date}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 5. BLOCKERS */}
          <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-2xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h2 className="text-xs font-extrabold uppercase tracking-wider text-rose-800 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-600" />
                5. Active Blockers & Dependencies
              </h2>
              <span className="text-xs font-mono font-bold text-rose-700">
                {activeBlockers.length} blockers
              </span>
            </div>

            {activeBlockers.length === 0 ? (
              <p className="text-xs text-slate-400 italic p-3 bg-slate-50 rounded-lg">
                No active blockers. Work is free of external blocks.
              </p>
            ) : (
              <div className="space-y-2.5">
                {activeBlockers.map((blk) => (
                  <div key={blk.blocker_id} className="bg-rose-50/70 rounded-xl p-4 border border-rose-200 text-xs space-y-1">
                    <p className="font-bold text-rose-950 text-sm">{blk.description}</p>
                    <p className="text-rose-800 font-medium">
                      Blocked by: <span className="font-bold text-rose-950">{blk.blocked_by}</span>
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 6. EXCEPTIONS (Visually Prominent) */}
          {activeExceptions.length > 0 && (
            <div className="bg-purple-50/60 rounded-2xl border-2 border-purple-300 p-6 space-y-4">
              <div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-wider text-purple-900">
                <AlertCircle className="w-5 h-5 text-purple-700" />
                6. Operational Exceptions & Discrepancies
              </div>

              {activeExceptions.map((exc) => (
                <div key={exc.exception_id} className="bg-white rounded-xl p-5 border border-purple-200 shadow-xs space-y-3 text-xs">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                      <span className="font-bold text-slate-600 block text-[10px] uppercase tracking-wider">
                        Expected State
                      </span>
                      <p className="font-bold text-slate-900 mt-1">{exc.expected}</p>
                    </div>

                    <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
                      <span className="font-bold text-purple-800 block text-[10px] uppercase tracking-wider">
                        Actual State Found
                      </span>
                      <p className="font-bold text-purple-950 mt-1">{exc.found}</p>
                    </div>
                  </div>

                  {exc.evidence && (
                    <div className="pt-2">
                      <span className="font-bold text-slate-600 block text-[10px] uppercase tracking-wider">
                        Discrepancy Evidence
                      </span>
                      <p className="text-slate-800 font-mono text-xs mt-1 bg-slate-50 p-3 rounded-lg border border-slate-200">
                        {exc.evidence}
                      </p>
                    </div>
                  )}

                  <div className="pt-2 border-t border-slate-100">
                    <span className="font-bold text-slate-700 block text-[10px] uppercase tracking-wider">
                      Required Action
                    </span>
                    <p className="font-bold text-slate-950 mt-1">{exc.required_action}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 8. EVIDENCE (Traceable Preservation) */}
          <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-2xs space-y-4">
            <div className="border-b border-slate-100 pb-2">
              <h2 className="text-xs font-extrabold uppercase tracking-wider text-slate-800 flex items-center gap-2">
                <Paperclip className="w-4 h-4 text-slate-700" />
                8. Evidence Preservation
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                The AI's extracted facts and policy decisions are traceable directly back to original evidence.
              </p>
            </div>

            {/* Original Handoff Context Preview */}
            <div className="space-y-2">
              <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                Original Handoff Notes
              </span>
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 text-xs font-mono text-slate-800 whitespace-pre-wrap leading-relaxed">
                {caseData.original_context || 'No raw notes context available.'}
              </div>
            </div>

            {/* S3 Evidence Artifacts */}
            {caseData.evidence_records && caseData.evidence_records.length > 0 && (
              <div className="space-y-2 pt-2">
                <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                  S3-Backed Evidence Artifacts ({caseData.evidence_records.length})
                </span>

                <div className="space-y-2">
                  {caseData.evidence_records.map((rec) => (
                    <div 
                      key={rec.evidence_id}
                      className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-slate-900">{rec.object_key}</span>
                          <span className="text-[10px] font-mono bg-slate-200 text-slate-800 px-2 py-0.5 rounded font-bold">
                            {rec.size_bytes} bytes
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500">
                          Archived by: <strong className="text-slate-700">{rec.created_by}</strong> • {rec.created_at}
                        </p>
                      </div>

                      <button
                        onClick={() => openEvidenceModal(
                          caseData.original_context || 'Original notes preserved in S3.',
                          rec.object_key
                        )}
                        className="h-8 inline-flex items-center gap-1.5 px-3 rounded-lg bg-white border border-slate-300 hover:bg-slate-100 text-slate-800 text-xs font-bold transition-colors shadow-2xs shrink-0"
                      >
                        <Eye className="w-3.5 h-3.5 text-slate-600" />
                        View Evidence
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: 9. AUDIT TRAIL */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-2xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-sm font-extrabold text-slate-900 tracking-tight">
                  9. Audit Trail & History
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Immutable chronological timeline.
                </p>
              </div>
              <span className="text-xs font-mono font-bold text-slate-600 bg-slate-100 px-2 py-1 rounded">
                {caseData.audit_history?.length || 0} events
              </span>
            </div>

            <AuditTimeline events={caseData.audit_history || []} />
          </div>
        </div>
      </div>

      {/* Action Execution Modal */}
      <ActionModal
        isOpen={activeModalAction !== null}
        onClose={() => setActiveModalAction(null)}
        actionType={activeModalAction}
        caseId={caseData.case_id}
        currentOwner={caseData.owner}
        onSubmit={handleActionSubmit}
      />

      {/* Evidence Viewer Modal */}
      {isEvidenceModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Paperclip className="w-4 h-4 text-slate-700" />
                <h3 className="text-sm font-extrabold text-slate-900">
                  Original Evidence Artifact
                </h3>
              </div>
              <button
                onClick={() => setIsEvidenceModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="text-xs font-mono text-slate-500">
              Object Key: <span className="font-bold text-slate-800">{selectedEvidenceKey}</span>
            </div>

            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 font-mono text-xs text-slate-800 whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto">
              {selectedEvidenceContent}
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setIsEvidenceModalOpen(false)}
                className="h-10 px-5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition-colors shadow-2xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
