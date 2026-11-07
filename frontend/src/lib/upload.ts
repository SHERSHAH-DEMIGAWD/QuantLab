export const MAX_CSV_BYTES = 10 * 1024 * 1024;
export const MAX_METADATA_BYTES = 64 * 1024;

export function decodeCsv(bytes: ArrayBuffer): string {
  try { return new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes); }
  catch { throw new Error('CSV must be valid UTF-8. Re-export the source file as UTF-8 without repairing individual rows.'); }
}
export async function readCsv(file: File): Promise<string> {
  if (file.size > MAX_CSV_BYTES) throw new Error('CSV exceeds the 10 MiB import limit.');
  return decodeCsv(await file.arrayBuffer());
}
export function validateUpload(csv: string, metadata: string): string {
  if (!csv.trim()) throw new Error('Choose a CSV file or load the synthetic example.');
  if (new TextEncoder().encode(csv).length > MAX_CSV_BYTES) throw new Error('CSV exceeds the 10 MiB import limit.');
  const raw = metadata.replace(/^\uFEFF/, '');
  if (new TextEncoder().encode(raw).length > MAX_METADATA_BYTES) throw new Error('Metadata exceeds the 64 KiB input limit.');
  let parsed: unknown;
  try { parsed = JSON.parse(raw); } catch { throw new Error('Metadata must be valid JSON. Check commas, quotes and brackets.'); }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('Metadata must be a JSON object.');
  return raw; // Do not reserialize: duplicate keys must reach the authoritative validator.
}
