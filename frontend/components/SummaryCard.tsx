import React from 'react';
import { 
  AlertCircle, 
  AlertTriangle, 
  Clock, 
  ShieldAlert, 
  CheckCircle2, 
  AlertOctagon 
} from 'lucide-react';

interface SummaryCardProps {
  type: 'unresolved' | 'at_risk' | 'overdue' | 'blocked' | 'exceptions' | 'resolved';
  count: number;
  label: string;
  subtext?: string;
  isActive?: boolean;
  onClick?: () => void;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({
  type,
  count,
  label,
  subtext,
  isActive = false,
  onClick
}) => {
  // Enterprise-standard color tokens
  const configs = {
    unresolved: {
      border: 'border-slate-200 hover:border-slate-300',
      activeBorder: 'ring-2 ring-blue-600 border-blue-600 bg-blue-50/30',
      numColor: 'text-slate-900',
      iconContainer: 'bg-blue-50 text-blue-600 border border-blue-100',
      icon: Clock,
      labelColor: 'text-blue-700',
    },
    at_risk: {
      border: 'border-slate-200 hover:border-slate-300',
      activeBorder: 'ring-2 ring-amber-500 border-amber-500 bg-amber-50/30',
      numColor: 'text-slate-900',
      iconContainer: 'bg-amber-50 text-amber-600 border border-amber-100',
      icon: AlertTriangle,
      labelColor: 'text-amber-700',
    },
    overdue: {
      border: 'border-slate-200 hover:border-slate-300',
      activeBorder: 'ring-2 ring-red-600 border-red-600 bg-red-50/30',
      numColor: 'text-slate-900',
      iconContainer: 'bg-red-50 text-red-600 border border-red-100',
      icon: AlertOctagon,
      labelColor: 'text-red-700',
    },
    blocked: {
      border: 'border-slate-200 hover:border-slate-300',
      activeBorder: 'ring-2 ring-rose-600 border-rose-600 bg-rose-50/30',
      numColor: 'text-slate-900',
      iconContainer: 'bg-rose-50 text-rose-600 border border-rose-100',
      icon: ShieldAlert,
      labelColor: 'text-rose-700',
    },
    exceptions: {
      border: 'border-slate-200 hover:border-slate-300',
      activeBorder: 'ring-2 ring-purple-600 border-purple-600 bg-purple-50/30',
      numColor: 'text-slate-900',
      iconContainer: 'bg-purple-50 text-purple-600 border border-purple-100',
      icon: AlertCircle,
      labelColor: 'text-purple-700',
    },
    resolved: {
      border: 'border-slate-200 hover:border-slate-300',
      activeBorder: 'ring-2 ring-emerald-600 border-emerald-600 bg-emerald-50/30',
      numColor: 'text-slate-900',
      iconContainer: 'bg-emerald-50 text-emerald-600 border border-emerald-100',
      icon: CheckCircle2,
      labelColor: 'text-emerald-700',
    }
  };

  const config = configs[type] || configs.unresolved;
  const IconComponent = config.icon;

  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick?.();
        }
      }}
      className={`relative bg-white rounded-xl border p-5 transition-all duration-150 cursor-pointer shadow-2xs flex flex-col justify-between h-[132px] w-full ${
        isActive ? config.activeBorder : config.border
      } hover:shadow-xs focus:outline-none focus:ring-2 focus:ring-slate-900`}
    >
      {/* Top Row: Icon + Label on exact horizontal baseline */}
      <div className="flex items-center justify-between h-8">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${config.iconContainer}`}>
          <IconComponent className="w-4 h-4 shrink-0" />
        </div>
        <span className={`text-[11px] font-bold uppercase tracking-wider ${config.labelColor}`}>
          {label}
        </span>
      </div>

      {/* Middle & Bottom: Number and Supporting description on identical vertical positions */}
      <div className="mt-auto pt-2">
        <div className={`text-3xl font-extrabold tracking-tight leading-none ${config.numColor}`}>
          {count}
        </div>
        <div className="text-xs font-medium text-slate-500 mt-1.5 truncate">
          {subtext || 'Active items'}
        </div>
      </div>
    </div>
  );
};
