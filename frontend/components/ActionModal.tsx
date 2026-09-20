'use client';

import React, { useState } from 'react';
import { ActionType, ActionRequest } from '@/types';
import { X, CheckCircle2, UserCheck, AlertTriangle } from 'lucide-react';

interface ActionModalProps {
  isOpen: boolean;
  onClose: () => void;
  actionType: ActionType | null;
  caseId: string;
  currentOwner: string;
  onSubmit: (request: ActionRequest) => Promise<void>;
}

export const ActionModal: React.FC<ActionModalProps> = ({
  isOpen,
  onClose,
  actionType,
  caseId,
  currentOwner,
  onSubmit,
}) => {
  const [newOwner, setNewOwner] = useState('Priya Sharma');
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen || !actionType) return null;

  const teamMembers = [
    'Arun Kumar',
    'Priya Sharma',
    'Marcus Vance',
    'Neha Patel',
    'Warehouse Operations',
    'Finance Operations'
  ].filter(m => m !== currentOwner);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await onSubmit({
        action: actionType,
        actor: 'Priya Sharma', // Active user context
        new_owner: actionType === 'REASSIGN' ? newOwner : undefined,
        reason: reason.trim() || undefined,
      });
      onClose();
    } catch (err) {
      console.error('Failed to submit action:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const titles = {
    RESOLVE: 'Mark Case as Resolved',
    REASSIGN: 'Reassign Case Ownership',
    ESCALATE: 'Escalate Case to Urgent Priority',
  };

  const icons = {
    RESOLVE: <CheckCircle2 className="w-5 h-5 text-emerald-600" />,
    REASSIGN: <UserCheck className="w-5 h-5 text-blue-600" />,
    ESCALATE: <AlertTriangle className="w-5 h-5 text-rose-600" />,
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2.5">
            {icons[actionType]}
            <h3 className="text-sm font-semibold text-slate-900">
              {titles[actionType]}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div className="text-xs text-slate-500">
            Applying action to <strong className="text-slate-800 font-mono">{caseId}</strong>
          </div>

          {actionType === 'REASSIGN' && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Select New Owner
              </label>
              <select
                value={newOwner}
                onChange={(e) => setNewOwner(e.target.value)}
                className="w-full text-xs rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
              >
                {teamMembers.map((member) => (
                  <option key={member} value={member}>
                    {member}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              {actionType === 'RESOLVE' 
                ? 'Resolution Notes / Evidence' 
                : actionType === 'ESCALATE' 
                ? 'Escalation Reason' 
                : 'Reassignment Context'}
            </label>
            <textarea
              rows={3}
              required={actionType === 'ESCALATE'}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder={
                actionType === 'RESOLVE'
                  ? 'e.g. Warehouse confirmed replacement stock; tracking #TRK-882 dispatched.'
                  : actionType === 'ESCALATE'
                  ? 'e.g. Customer delivery SLA at risk; warehouse manager unresponsive for > 4 hours.'
                  : 'e.g. Handing off to shift supervisor due to shift rotation.'
              }
              className="w-full text-xs rounded-md border border-slate-300 p-2.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
            />
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className={`px-4 py-2 text-xs font-semibold text-white rounded-md transition-colors shadow-xs ${
                actionType === 'RESOLVE'
                  ? 'bg-emerald-600 hover:bg-emerald-700'
                  : actionType === 'ESCALATE'
                  ? 'bg-rose-600 hover:bg-rose-700'
                  : 'bg-slate-900 hover:bg-slate-800'
              }`}
            >
              {isSubmitting ? 'Updating...' : 'Confirm Action'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
