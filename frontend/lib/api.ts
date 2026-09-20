import { Case, QueueResponse, HandoffRequest, HandoffResponse, ActionRequest } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchHealth(): Promise<{ status: string; ai_provider: string; version: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { cache: 'no-store' });
    if (!res.ok) throw new Error('Health check failed');
    return await res.json();
  } catch (err) {
    return { status: 'disconnected', ai_provider: 'offline', version: '1.0.0' };
  }
}

export async function fetchQueue(owner?: string): Promise<QueueResponse> {
  const url = owner 
    ? `${API_BASE_URL}/queue?owner=${encodeURIComponent(owner)}` 
    : `${API_BASE_URL}/queue`;
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch queue: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchCases(): Promise<Case[]> {
  const res = await fetch(`${API_BASE_URL}/cases`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch cases: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchCase(caseId: string): Promise<Case> {
  const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch case ${caseId}: ${res.statusText}`);
  }
  return res.json();
}

export async function submitHandoff(data: HandoffRequest): Promise<HandoffResponse> {
  const res = await fetch(`${API_BASE_URL}/handoff`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to submit handoff: ${res.statusText}`);
  }
  return res.json();
}

export async function performCaseAction(caseId: string, actionData: ActionRequest): Promise<Case> {
  const res = await fetch(`${API_BASE_URL}/cases/${encodeURIComponent(caseId)}/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(actionData),
  });
  if (!res.ok) {
    throw new Error(`Failed to execute action on case ${caseId}: ${res.statusText}`);
  }
  return res.json();
}
