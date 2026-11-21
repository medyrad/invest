export type AssistantItem = {
  id: string;
  revision: string;
  kind: "project" | "fund" | "sale";
  fields: Record<string, unknown>;
  images?: string[];
  matching?: {
    score: string | null;
    coverage: string | null;
    status: string;
    checks: {
      axis: string;
      state: "met" | "unmet" | "unknown";
      reason: string;
    }[];
    warnings: string[];
    policy_version: number;
  };
};

export type AssistantResponse = {
  state: "completed" | "needs_clarification" | "failed";
  interpretation?: {
    criteria: Record<string, unknown>;
    needs_clarification: boolean;
    questions: string[];
  };
  server_result?: {
    items?: AssistantItem[];
    total?: number;
    next?: string | null;
    policy_version?: number;
    rows?: unknown[];
  };
  answer?: string;
  citations?: {
    id: string;
    revision: string;
    field: string;
    value_json?: string;
  }[];
  next?: string[];
  receipt?: string;
  quota?: {
    used: number;
    limit: number;
    remaining: number;
    reset_at: string;
    policy_version: number;
    monthly?: {
      spent_usd: string;
      held_usd: string;
      cap_usd: string;
      remaining_usd: string;
      reset_at: string;
    };
  };
  error?: { code: string; message: string };
  steps?: AssistantStep[];
};

export type AssistantStep = {
  id: "interpretation" | "public_data" | "explanation";
  status: "pending" | "active" | "completed" | "failed" | "not_run";
  detail?: string;
};

export type AssistantStreamEvent =
  | {
      event: "progress";
      stage: AssistantStep["id"];
      status: AssistantStep["status"];
      detail?: string;
      interpretation?: AssistantResponse["interpretation"];
      server_result?: AssistantResponse["server_result"];
    }
  | { event: "result" | "failure"; data: AssistantResponse };

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

export async function assistantTurnStream(
  body: Record<string, unknown>,
  onEvent: (event: AssistantStreamEvent) => void,
  idempotencyKey = crypto.randomUUID(),
) {
  const response = await fetch("/api/v1/assistant/turns/stream", {
    method: "POST",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": await csrf(),
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify(body),
  });
  if (!response.ok || !response.body)
    throw new Error("ارتباط با دستیار انجام نشد.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalValue: AssistantResponse | undefined;
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (!line.trim()) continue;
      const event = JSON.parse(line) as AssistantStreamEvent;
      onEvent(event);
      if (event.event === "result" || event.event === "failure")
        finalValue = event.data;
    }
    if (done) break;
  }
  if (!finalValue) throw new Error("پاسخ کامل و اعتبارسنجی‌شده دریافت نشد.");
  return { value: finalValue, idempotencyKey };
}
