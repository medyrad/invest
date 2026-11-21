export const ASSISTANT_VOCABULARY_VERSION = "assistant-fa-labels-v1";

const routes: Record<string, string> = {
  investor: "سرمایه‌گذاری و مشارکت",
  fund: "صندوق سرمایه‌گذاری",
  buyer: "خرید",
  lessee: "اجاره",
  contractor: "پیمانکاری",
  heritage: "مرمت و احیا",
  operator: "بهره‌برداری",
  charity: "مشارکت خیرخواهانه",
};

const kinds: Record<string, string> = {
  project: "پروژه",
  fund: "صندوق",
  sale: "مورد قابل خرید",
};

const citationFields: Record<string, string> = {
  matching: "نتیجه تطبیق سرور",
  title: "عنوان فرصت",
  kind: "نوع فرصت",
  routes: "مسیرهای فرصت",
  amount: "مبلغ",
  return: "بازده اعلامی",
  risk: "ریسک اعلامی",
  location: "مکان",
  published_at: "زمان انتشار",
  revision: "نسخه عمومی",
  public_revision_id: "نسخه عمومی",
  "match.score": "امتیاز تطبیق",
  "match.coverage": "پوشش اطلاعات",
  "match.policy_version": "نسخه سیاست تطبیق",
};

export const historicalUnknownLabel = "مقدار تاریخی ناشناخته";
export const routeLabel = (value: unknown) => typeof value === "string" ? routes[value] ?? historicalUnknownLabel : historicalUnknownLabel;
export const kindLabel = (value: unknown) => typeof value === "string" ? kinds[value] ?? historicalUnknownLabel : historicalUnknownLabel;
export const citationFieldLabel = (value: unknown) => typeof value === "string" ? citationFields[value] ?? historicalUnknownLabel : historicalUnknownLabel;

export function assistantValueLabel(key: string, value: unknown) {
  if (key === "route") return routeLabel(value);
  if (key === "kind") return kindLabel(value);
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.join("، ");
  return value === null || value === undefined ? historicalUnknownLabel : "ثبت‌شده";
}
