import { z } from 'zod';
import { datasetListSchema, datasetSchema, errorSchema, experimentListSchema, experimentSchema, healthSchema,
  importSchema, reproductionSchema, type ExperimentRequest } from './schemas';

export class ApiError extends Error {
  constructor(message: string, public code = 'request_failed', public status = 0, public details?: unknown) { super(message); }
}
export const API_BASE = (import.meta.env.VITE_API_BASE || '/api/v1').replace(/\/$/, '');

async function request<T>(path: string, schema: z.ZodType<T>, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try { response = await fetch(API_BASE + path, init); }
  catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new ApiError('Cannot reach the backend. Start the local API and check the Vite proxy target.', 'backend_unavailable');
  }
  let body: unknown;
  try { body = await response.json(); }
  catch { throw new ApiError('The server returned an unreadable response. Check the API address and backend logs.', 'malformed_response', response.status); }
  if (!response.ok) {
    const parsed = errorSchema.safeParse(body);
    if (!parsed.success) throw new ApiError(`Request failed (HTTP ${response.status}) with an unexpected error response.`, 'malformed_response', response.status);
    throw new ApiError(parsed.data.error.message, parsed.data.error.code, response.status, parsed.data.error.details);
  }
  const parsed = schema.safeParse(body);
  if (!parsed.success) throw new ApiError('The response does not match this dashboard’s supported API contract. Check backend and frontend versions.', 'unexpected_response', response.status);
  return parsed.data;
}
const json = (body: unknown): RequestInit => ({ method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
export const api = {
  health: (signal?: AbortSignal) => request('/health', healthSchema, { signal }),
  datasets: (offset = 0, signal?: AbortSignal) => request(`/datasets?limit=50&offset=${offset}`, datasetListSchema, { signal }),
  dataset: (id: string, signal?: AbortSignal) => request(`/datasets/${encodeURIComponent(id)}`, datasetSchema, { signal }),
  importDataset: (csv: string, metadataJson: string) => request('/datasets', importSchema, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    // Preserve raw metadata object keys so the backend can reject duplicates.
    body: `{"csv_text":${JSON.stringify(csv)},"metadata":${metadataJson}}`,
  }),
  execute: (body: ExperimentRequest) => request('/experiments', experimentSchema, json(body)),
  experiments: (offset = 0, datasetId?: string, signal?: AbortSignal) => request(
    `/experiments?limit=50&offset=${offset}${datasetId ? '&dataset_id=' + encodeURIComponent(datasetId) : ''}`, experimentListSchema, { signal }),
  experiment: (id: string, signal?: AbortSignal) => request(`/experiments/${encodeURIComponent(id)}`, experimentSchema, { signal }),
  reproduce: (id: string) => request(`/experiments/${encodeURIComponent(id)}/reproduce`, reproductionSchema, { method: 'POST' }),
};
