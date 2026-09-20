export type CaseStatus = 
  | 'UNRESOLVED' 
  | 'AT_RISK' 
  | 'BLOCKED' 
  | 'EXCEPTION' 
  | 'OVERDUE' 
  | 'RESOLVED' 
  | 'IN_PROGRESS';

export type Priority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export type ActionType = 'RESOLVE' | 'REASSIGN' | 'ESCALATE';

export interface TaskItem {
  task_id: string;
  case_id: string;
  title: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'BLOCKED' | 'COMPLETED';
  owner?: string;
  next_action?: string;
}

export interface Commitment {
  commitment_id: string;
  case_id: string;
  description: string;
  committed_to: string;
  expected_date?: string;
  status: 'ACTIVE' | 'FULFILLED' | 'BREACHED';
}

export interface Blocker {
  blocker_id: string;
  case_id: string;
  description: string;
  blocked_by: string;
  status: 'ACTIVE' | 'RESOLVED';
}

export interface ExceptionItem {
  exception_id: string;
  case_id: string;
  expected: string;
  found: string;
  evidence: string;
  impact?: string;
  required_action: string;
  status: 'ACTIVE' | 'RESOLVED';
}

export interface AuditEvent {
  event_id: string;
  case_id: string;
  timestamp: string;
  actor: string;
  action: string;
  details: string;
}

export interface EvidenceMetadata {
  evidence_id: string;
  case_id: string;
  object_key: string;
  content_type: string;
  original_filename?: string;
  created_at: string;
  created_by?: string;
  size_bytes?: number;
  description?: string;
}

export interface Case {
  case_id: string;
  title: string;
  description?: string;
  owner: string;
  status: CaseStatus;
  priority: Priority;
  deadline?: string;
  customer?: string;
  created_at: string;
  updated_at: string;
  original_context?: string;
  next_action?: string;
  evidence?: string;
  evidence_records?: EvidenceMetadata[];
  tasks: TaskItem[];
  commitments: Commitment[];
  blockers: Blocker[];
  exceptions: ExceptionItem[];
  audit_history: AuditEvent[];
}

export interface HandoffRequest {
  outgoing_employee: string;
  incoming_employee: string;
  raw_notes: string;
  handoff_date?: string;
}

export interface HandoffResponse {
  handoff_id: string;
  outgoing_employee: string;
  incoming_employee: string;
  processed_at: string;
  cases_updated: string[];
  cases_created: string[];
  extraction_summary: {
    completed_count: number;
    unresolved_count: number;
    commitments_count: number;
    blockers_count: number;
    deadlines_count: number;
    exceptions_count: number;
    next_actions_count: number;
  };
  cases: Case[];
}

export interface ActionRequest {
  action: ActionType;
  actor: string;
  new_owner?: string;
  reason?: string;
}

export interface QueueStats {
  unresolved: number;
  at_risk: number;
  blocked: number;
  exceptions: number;
  overdue?: number;
  total: number;
}

export interface QueueResponse {
  stats: QueueStats;
  cases: Case[];
}
