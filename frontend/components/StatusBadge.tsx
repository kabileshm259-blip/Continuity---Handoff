import React from 'react';
import { CaseStatus } from '@/types';
import { 
  AlertTriangle, 
  AlertOctagon, 
  ShieldAlert, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  Activity 
} from 'lucide-react';

interface StatusBadgeProps {
  status: CaseStatus;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ 
  status, 
  className = '' 
}) => {
  // Enterprise-standard unified badge dimensions: exactly h-6, px-2.5, text-[11px]
  const baseClasses = 'inline-flex items-center justify-center h-6 px-2.5 gap-1.5 rounded-md text-[11px] font-bold uppercase tracking-wider border whitespace-nowrap shrink-0 transition-colors';
  const iconClasses = 'w-3 h-3 shrink-0';

  switch (status) {
    case 'OVERDUE':
      return (
        <span 
          className={`${baseClasses} bg-red-50 text-red-700 border-red-300 shadow-2xs ${className}`}
          title="Past commitment deadline — requires immediate intervention"
        >
          <AlertOctagon className={`${iconClasses} text-red-600`} />
          OVERDUE
        </span>
      );
    case 'AT_RISK':
      return (
        <span 
          className={`${baseClasses} bg-amber-50 text-amber-800 border-amber-300 shadow-2xs ${className}`}
          title="Approaching deadline with unresolved dependency"
        >
          <AlertTriangle className={`${iconClasses} text-amber-600`} />
          AT RISK
        </span>
      );
    case 'BLOCKED':
      return (
        <span 
          className={`${baseClasses} bg-rose-50 text-rose-700 border-rose-300 shadow-2xs ${className}`}
          title="External dependency or team blocker active"
        >
          <ShieldAlert className={`${iconClasses} text-rose-600`} />
          BLOCKED
        </span>
      );
    case 'EXCEPTION':
      return (
        <span 
          className={`${baseClasses} bg-purple-50 text-purple-700 border-purple-300 shadow-2xs ${className}`}
          title="System record or physical discrepancy detected"
        >
          <AlertCircle className={`${iconClasses} text-purple-600`} />
          EXCEPTION
        </span>
      );
    case 'UNRESOLVED':
      return (
        <span 
          className={`${baseClasses} bg-blue-50 text-blue-700 border-blue-200 shadow-2xs ${className}`}
          title="Deliverable or work item incomplete"
        >
          <Clock className={`${iconClasses} text-blue-600`} />
          UNRESOLVED
        </span>
      );
    case 'RESOLVED':
      return (
        <span 
          className={`${baseClasses} bg-emerald-50 text-emerald-700 border-emerald-300 shadow-2xs ${className}`}
          title="All commitments fulfilled and verified"
        >
          <CheckCircle2 className={`${iconClasses} text-emerald-600`} />
          RESOLVED
        </span>
      );
    case 'IN_PROGRESS':
    default:
      return (
        <span 
          className={`${baseClasses} bg-slate-100 text-slate-700 border-slate-300 shadow-2xs ${className}`}
        >
          <Activity className={`${iconClasses} text-slate-500`} />
          IN PROGRESS
        </span>
      );
  }
};
