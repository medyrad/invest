# تسک‌های PROGRAMMER-S04-01

## Phase 1: مشخصات و منبع
- [X] T001 تطبیق ZIP، spec/plan/contracts/checklist و تحلیل پیش از کد در docs/stage4؛ FR-001..008.
- [X] T002 استخراج fixture کاتالوگ و نمونه نسخه‌دار در backend/apps/catalog/fixtures با شاهد شمارش و منبع؛ FR-003/007.

## Phase 2: US3 کاتالوگ
- [X] T003 تست PG در backend/tests/test_catalog.py؛ FR-003/004/007.
- [X] T004 مدل/migration و import_reference در backend/apps/catalog؛ FR-003/004.
- [X] T005 API و schema و منع fixture عمومی؛ FR-004/007.

## Phase 3: US1 خانه
- [X] T006 انتقال اجزای فعال خانه و دارایی/توکن مرجع، رفع TypingHint و کاهش حرکت؛ FR-001/008.
- [X] T007 تفکیک AuthContext و header/dropdown/mobile/footer و مقصدهای مرحله بعد؛ FR-002/007.
- [X] T008 اتصال fixture نمونه بدون matching یا احراز/آمار جعلی؛ FR-006/007.

## Phase 4: US2 انتخاب
- [X] T009 اتصال انتخابگر دسته/مکان و رابطه/خطا/loading/خالی/retry به API در frontend؛ FR-005.

## Phase 5: تحویل
- [X] T010 تست مرورگر خانه، انتخاب‌ها، قطعی، موبایل و حرکت؛ FR-008 و SC-002.
- [X] T011 بازگشت S03 با هدر واقعی و آزمون قواعد قبلی؛ FR-002.
- [X] T012 مقایسه تصویری sectionها و کنترل کیفیت/build/runtime در docs/stage4/evidence؛ SC-001..003.
- [X] T013 بازبینی plan/tasks و گزارش/manifest و وضعیت آماده آزمون مستقل؛ بدون تأیید کل S04.

ترتیب T001→T002/T003→T004/T005→T006..T009→T010..T013. بخش‌های مستقل backend/UI می‌توانند جدا پیش بروند؛ اجرا در این مأموریت تک‌ایجنت است.

## شاهد اجرا

T001: pre-code-analysis و reference-integrity؛ T002: fixtureها و API/runtime؛ T003..T005:۹۷ تست PostgreSQL و قرارداد ماشین‌خوان؛ T006..T009: کد خانه/انتخابگر و تصاویر section؛ T010:۲۲ تست خانه، حرکت و لمس/صفحه‌کلید در مجموعه۵۹تایی؛ T011: بازگشت سه باگ و سفر S03 در همان مجموعه؛ T012:۷جفت تصویر production، چهار عرض، quality/build و image-browser؛ T013: docs/stage4/report.md، manifest و stage-status. همه شواهد در docs/stage4/evidence. این علامت‌ها تحویل پیاده‌سازی همین مأموریت‌اند، نه پذیرش مستقل یا انسانی یا پایان کل S04.

## اصلاح محدود PROGRAMMER-S04-02

- [X] T014 رفع S04-IT-001: عنوان «شهر»، پیام مصوب و راهنمای مشتری در `catalog-selectors.tsx`؛ بدون تغییر رابطه/قاعده. شاهد: `docs/stage4/fix-evidence/browser.json` و تصاویر چهار عرض؛ تست شهرستان فاقد شهر/دارای شهر و تغییر والد.
- [X] T015 رفع S04-IT-002: favicon از نشان موجود هدر، ICO چهاراندازه و metadata؛ شاهد HTTP معتبر و decode مرورگر تازه روی image نهایی در `docs/stage4/fix-evidence/favicon-http.json` و `browser.json`. پذیرش محدود مستقل و انسانی همچنان باز است.
