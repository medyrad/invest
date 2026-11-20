export type AssistantItem = {
  id: string;
  revision: string;
  kind: "project" | "fund" | "sale";
  fields: Record<string, unknown>;
  matching?: {
    score: string | null;
    coverage: string | null;
    status: string;
    checks: { axis: string; state: "met" | "unmet" | "unknown"; reason: string }[];
    warnings: string[];
    policy_version: number;
  };
};

export type AssistantResponse = {
  state: "completed" | "needs_clarification" | "failed";
  interpretation?: { criteria: Record<string, unknown>; needs_clarification: boolean; questions: string[] };
  server_result?: { items?: AssistantItem[]; total?: number; next?: string | null; policy_version?: number; rows?: unknown[] };
  answer?: string;
  citations?: { id: string; revision: string; field: string }[];
  next?: string[];
  receipt?: string;
  quota?: { used: number; limit: number; remaining: number; reset_at: string; policy_version: number; model: string };
  error?: { code: string; message: string };
  steps?: { id: "interpretation" | "public_data" | "explanation"; status: "completed" | "failed" | "not_run" }[];
};

async function csrf() {
  const response = await fetch("/api/v1/auth/csrf", { cache: "no-store" });
  if (!response.ok) throw new Error("دریافت مجوز درخواست انجام نشد.");
  return (await response.json()).csrfToken as string;
}

export async function assistantTurn(body: Record<string, unknown>) {
  const response = await fetch("/api/v1/assistant/turns", {
    method: "POST",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": await csrf(),
      "Idempotency-Key": crypto.randomUUID(),
    },
    body: JSON.stringify(body),
  });
  const value = (await response.json()) as AssistantResponse;
  if (!response.ok && !value.interpretation && !value.server_result) {
    throw new Error(value.error?.message || "ارتباط با دستیار انجام نشد.");
  }
  return value;
}
