'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  ArrowLeft, 
  Sparkles, 
  FileText, 
  User, 
  Calendar, 
  ArrowRight,
  ClipboardPaste,
  ShieldCheck
} from 'lucide-react';

const DEMO_SAMPLE_NOTES = `Payment API integration is complete.
Webhook handling is still pending.
Finance has not approved the discount yet.
I promised the client the revised version before Friday.
Follow up with Finance and finish webhook validation.`;

export default function CreateHandoffPage() {
  const router = useRouter();
  const [outgoingEmployee, setOutgoingEmployee] = useState('Arun Kumar');
  const [incomingEmployee, setIncomingEmployee] = useState('Priya Sharma');
  const [handoffDate, setHandoffDate] = useState('Today');
  const [rawNotes, setRawNotes] = useState(DEMO_SAMPLE_NOTES);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleLoadSample = () => {
    setRawNotes(DEMO_SAMPLE_NOTES);
  };

  const handleClear = () => {
    setRawNotes('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawNotes.trim()) return;

    setIsSubmitting(true);
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('continuity_handoff_payload', JSON.stringify({
        outgoing_employee: outgoingEmployee,
        incoming_employee: incomingEmployee,
        raw_notes: rawNotes.trim(),
        handoff_date: handoffDate
      }));
    }

    router.push('/handoff/processing');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Navigation Breadcrumb */}
      <div>
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Dashboard
        </Link>
      </div>

      {/* Screen 2 Header Hierarchy */}
      <div className="bg-white p-7 sm:p-8 rounded-2xl border border-slate-200/90 shadow-2xs space-y-2">
        <div className="text-[11px] font-extrabold uppercase tracking-widest text-slate-500">
          WORKPLACE HANDOFF
        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Give CONTINUITY the context you already have.
        </h1>

        <p className="text-sm text-slate-600 max-w-2xl leading-relaxed pt-1">
          Paste the notes, context, decisions and evidence from the outgoing owner. CONTINUITY will reconstruct the operational state for the next owner.
        </p>
      </div>

      {/* Main Input Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-slate-200/90 shadow-2xs p-7 sm:p-8 space-y-6">
        {/* Large Notes Textarea Area */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-800">
              Raw Handoff Notes & Operational Context
            </label>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleLoadSample}
                className="h-8 inline-flex items-center gap-1.5 text-xs font-semibold text-slate-800 hover:text-slate-950 px-2.5 rounded-md bg-slate-100 hover:bg-slate-200 transition-colors"
              >
                <ClipboardPaste className="w-3.5 h-3.5 text-amber-500" />
                Load Demo Sample
              </button>
              <button
                type="button"
                onClick={handleClear}
                className="h-8 text-xs font-medium text-slate-400 hover:text-slate-600 px-2 rounded hover:bg-slate-100 transition-colors"
              >
                Clear
              </button>
            </div>
          </div>

          <textarea
            rows={9}
            required
            value={rawNotes}
            onChange={(e) => setRawNotes(e.target.value)}
            placeholder={`Example:

Payment API integration is complete.
Webhook handling is still pending.
Finance has not approved the discount yet.
I promised the client the revised version before Friday.
Follow up with Finance and finish webhook validation.`}
            className="w-full text-sm font-mono rounded-xl border border-slate-300 p-4 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 leading-relaxed placeholder:font-sans placeholder:text-slate-400 shadow-2xs"
          />

          <p className="text-xs text-slate-500 flex items-center gap-1.5 pt-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>
              <strong>Deterministic Policy Guarantee:</strong> Bedrock Nova extracts facts; our policy engine evaluates status (<span className="font-mono">UNRESOLVED</span>, <span className="font-mono">AT_RISK</span>, <span className="font-mono">BLOCKED</span>).
            </span>
          </p>
        </div>

        {/* Employee Selectors Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-100">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-slate-400" />
              Outgoing Employee
            </label>
            <select
              value={outgoingEmployee}
              onChange={(e) => setOutgoingEmployee(e.target.value)}
              className="w-full h-10 text-xs font-medium rounded-lg border border-slate-300 bg-white px-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900"
            >
              <option value="Arun Kumar">Arun Kumar</option>
              <option value="Priya Sharma">Priya Sharma</option>
              <option value="Marcus Vance">Marcus Vance</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-slate-400" />
              Incoming Employee
            </label>
            <select
              value={incomingEmployee}
              onChange={(e) => setIncomingEmployee(e.target.value)}
              className="w-full h-10 text-xs font-medium rounded-lg border border-slate-300 bg-white px-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900"
            >
              <option value="Priya Sharma">Priya Sharma</option>
              <option value="Arun Kumar">Arun Kumar</option>
              <option value="Marcus Vance">Marcus Vance</option>
              <option value="Neha Patel">Neha Patel</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              Handoff Date
            </label>
            <input
              type="text"
              value={handoffDate}
              onChange={(e) => setHandoffDate(e.target.value)}
              className="w-full h-10 text-xs font-medium rounded-lg border border-slate-300 bg-white px-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900"
            />
          </div>
        </div>

        {/* Primary CTA Footer */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
          <Link
            href="/"
            className="h-11 inline-flex items-center px-4 text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={isSubmitting || !rawNotes.trim()}
            className="h-11 inline-flex items-center gap-2 px-6 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold shadow-2xs transition-colors disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-amber-400" />
            Create Continuity Case
            <ArrowRight className="w-3.5 h-3.5 ml-0.5 text-slate-400" />
          </button>
        </div>
      </form>
    </div>
  );
}
