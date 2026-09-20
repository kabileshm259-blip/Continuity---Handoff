import React from 'react';
import { AuditEvent } from '@/types';
import { Clock, ShieldCheck, Cpu, User, AlertCircle, RefreshCw } from 'lucide-react';

interface AuditTimelineProps {
  events: AuditEvent[];
}

export const AuditTimeline: React.FC<AuditTimelineProps> = ({ events }) => {
  if (!events || events.length === 0) {
    return (
      <div className="text-sm text-slate-500 py-4 text-center italic">
        No audit events recorded yet.
      </div>
    );
  }

  const getActorBadge = (actor: string) => {
    const actorLower = actor.toLowerCase();
    if (actorLower.includes('policy')) {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
          <ShieldCheck className="w-3 h-3" />
          {actor}
        </span>
      );
    }
    if (actorLower.includes('ai')) {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200">
          <Cpu className="w-3 h-3" />
          {actor}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
        <User className="w-3 h-3" />
        {actor}
      </span>
    );
  };

  return (
    <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
      {events.map((event, index) => (
        <div key={event.event_id || index} className="relative group">
          {/* Timeline Dot */}
          <div className="absolute -left-6 top-1 w-3 h-3 rounded-full border-2 border-white bg-slate-400 group-hover:bg-indigo-600 transition-colors shadow-xs" />

          <div className="bg-white p-3.5 rounded-lg border border-slate-200 shadow-xs space-y-1.5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-900">
                  {event.action}
                </span>
                {getActorBadge(event.actor)}
              </div>
              <div className="flex items-center gap-1 text-xs text-slate-600 font-mono">
                <Clock className="w-3 h-3 text-slate-600" />
                {event.timestamp}
              </div>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              {event.details}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};
