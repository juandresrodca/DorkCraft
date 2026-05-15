/**
 * DorkCraft — API client
 * ----------------------
 * Centralises all calls to the FastAPI backend.
 * Update API_BASE_URL to point to your deployed backend when going to production.
 */

/** Set this to your deployed backend URL in production. */
export const API_BASE_URL =
  import.meta.env.PUBLIC_API_URL ?? 'http://localhost:8000';

export interface DorkResponse {
  dork: string;
  explanation: string[];
  variations: string[];
  category?: string;
}

export interface ErrorResponse {
  error: string;
}

export type GenerateResult =
  | { success: true; data: DorkResponse }
  | { success: false; error: string };

/**
 * POST /generate
 * Sends the user's plain-English query to the backend and returns the result.
 */
export async function generateDork(query: string): Promise<GenerateResult> {
  try {
    const res = await fetch(`${API_BASE_URL}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });

    const json = await res.json();

    if (!res.ok) {
      return { success: false, error: (json as ErrorResponse).error ?? 'Unknown error' };
    }

    return { success: true, data: json as DorkResponse };
  } catch (err) {
    return {
      success: false,
      error: 'Could not reach the DorkCraft backend. Is it running?',
    };
  }
}
