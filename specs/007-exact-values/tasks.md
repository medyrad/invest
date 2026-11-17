# تسک‌های PROGRAMMER-S04-03

## فاز۱ — آماده‌سازی
- [X] T001 خواندن D29/منبع و ثبت mapping در specs/007-exact-values/mapping.md؛ FR-007.
- [X] T002 تحلیل spec/plan/contracts و checklist پیش از کد؛ همه FR/SC.
## فاز۲ — US1 مقدار
- [X] T003 تست parser و تبدیل/خطا/مرز در backend/tests/test_values.py؛ FR-002..005 و SC-001.
- [X] T004 numeric field و normalize/DTO در backend/apps/catalog/{decimal_field.py,values.py}؛ FR-002..006.
## فاز۳ — US3 تعریف و ذخیره
- [X] T005 مدل‌ها و migration/seed نسخه‌دار در backend/apps/catalog/models.py و migrations؛ FR-001/007.
- [X] T006 round-trip و قیود SQL و forward/backward در backend/tests/test_values.py؛ SC-001/003.
## فاز۴ — US2 مبنا/قرارداد
- [X] T007 helper مقایسه و تست ناهم‌مبنا/نسخه/ارز و unknown؛ FR-005/006 و SC-002.
- [X] T008 API/serializers و OpenAPI و تست قرارداد/خطای فارسی؛ FR-008.
## فاز۵ — تحویل
- [X] T009 quality و تست مرتبط catalog/contract و شاهد PG؛ SC-001..003.
- [X] T010 بازبینی/converge، ثبت TEST-S04-02، ردیابی جزئی T009/T011 پایه، گزارش/نسخه/زمان و توقف؛ SC-003.

ترتیب T001/T002→T003→T004/T005→T006/T007/T008→T009/T010؛ اجرای تک‌ایجنت. تسک پایه T011 به علت فرم‌های پنهان آینده کامل نمی‌شود؛ spec/plan کل محصول تغییر نمی‌کنند.

## شاهد تکمیل همین بسته
T001/T002: mapping و values-pre-code-analysis؛ T003/T004: grammar/حدود/تبدیل و عدم alias خروجی؛ T005/T006: migration۰۰۰۲/۰۰۰۳، immutable و PG round-trip/SQL scale/backward-forward؛ T007: نوع/مبنای بازده و واحد/نسخه/ارز نامقایسه؛ T008: OpenAPI۱٫۳ و API واقعی؛ T009:۱۰۶ آزمون مرتبط و quality/check/drift؛ T010: values-report، manifest و stage-status. همه در docs/stage4/values-evidence. تأیید کل S04/انسانی یا کل T009/T011 پایه از این علامت‌ها نتیجه نمی‌شود.
