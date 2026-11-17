# تسک‌های PROGRAMMER-S03-01

## Phase 1: مشخصات و پایه
- [x] T001 ثبت spec/plan/contracts/checklist و تحلیل پیش از کد در specs/005-identity-session و docs/stage3/pre-code-analysis.md؛ FR-001..011.
- [x] T002 نوشتن تست‌های سیاست قبل از اجرا در backend/tests/test_identity.py و test_identity_races.py؛ FR-001..009.
- [x] T003 مدل و migration در backend/apps/identity/models.py؛ FR-002..008 و FR-011.

## Phase 2: US1 / ورود
- [x] T004 [US1] اجرای otp.py و api.py برای canonical/issue/verify/logout؛ FR-001..006.
- [x] T005 [US1] اتصال دیالوگ مرجع در frontend/src/components/auth/login-dialog.tsx و CSS/تصاویر؛ FR-010.
- [x] T006 [US1] مرورگر build واقعی و screenshot در frontend/tests/browser/auth.spec.ts؛ SC-001.

## Phase 3: US2 / رقابت
- [x] T007 [US2] اجرای PostgreSQL برای مرزها، retry، provider و رقابت در backend/tests/test_identity*.py؛ FR-002..006 و SC-002.

## Phase 4: US3 / اختیار
- [x] T008 [US3] sessions.py، تغییر اختیار/ابطال، privacy و reauth در api.py؛ FR-007..008 و FR-011.
- [x] T009 [US3] قرارداد نیت و آزمون snapshot/لغو/حساب در otp.py و test_identity.py؛ FR-009.

## Phase 5: شواهد و تحویل
- [x] T010 اجرای lint/build/check/test، بررسی اسرار و نگاشت F01..F12 در docs/stage3/report.md؛ SC-003.
- [x] T011 converge و وضعیت آماده آزمون مستقل در docs/stage-status.json؛ بدون پذیرش انسانی یا عرضه.

وابستگی: T001→T002→T003→T004/T008→T005/T009→T006/T007→T010→T011. تکمیل فقط پس از شاهد. موازی‌سازی فایل‌های مستقل ممکن است؛ این مأموریت تک‌ایجنت اجرا می‌شود. راهبرد: ابتدا US1، سپس محدودسازی و اختیار و در نهایت مرورگر/شواهد؛ همه بخش‌های مجاز همین مأموریت تکمیل می‌شوند.

## Phase 6: Convergence
- [x] T012 [US1] اصلاح فاصله/فونت ورودی دسکتاپ، لایه سایه و آیکون بستن طبق اندازه‌گیری مرجع در frontend/src/app/globals.css و login-dialog.tsx؛ بازاجرای browser و مقایسه در docs/stage3/evidence؛ FR-010 و Constitution II (partial، شدت متوسط).
- [x] T013 همگام‌سازی contracts/openapi.yaml سرویس با قرارداد جدید S03 و اعتبارسنجی پاسخ واقعی در backend/tests/test_identity.py؛ FR-001/FR-005/FR-007 و plan: قرارداد (partial، شدت متوسط).

شاهد تکمیل T001..T013: docs/stage3/report.md، traceability.md و verification.json؛ مرورگر/بک‌اند واقعی و metrics تصویری ثبت شدند. این تکمیل، پذیرش انسانی یا پایان کل S03 نیست.

## Phase 7: اصلاح محدود PROGRAMMER-S03-02
- [x] T014 بازتولید سه شکست مستقل بدون تغییر آزمون/شواهد قبلی؛ خروجی تازه در docs/stage3/fix-evidence/.
- [x] T015 [US1] اصلاح S03-IT-001 در frontend/src/components/auth/login-dialog.tsx؛ حفظ کلید/payload تا تعیین نتیجه، پنهان‌کردن کد قبلی در ابهام و تست بازیابی challenge/TTL/IssueEvent در frontend/tests/browser/auth-fixes.spec.ts.
- [x] T016 [US1] اصلاح S03-IT-002 در همان کامپوننت؛ اعلان بدون راز، me در focus/visibility/pageshow و منع پاسخ کهنه؛ تست دو تب، دستگاه مستقل و عدم تمدید idle در auth-fixes.spec.ts.
- [x] T017 [US1] اصلاح متن S03-IT-003 طبق D26، آزمون خوانایی و تصویر چهار عرض در auth-fixes.spec.ts؛ بدون مسیر S06 یا تغییر طراحی.
- [x] T018 اجرای بازگشت، آزمون‌های مستقل دست‌نخورده، کیفیت/build و ثبت docs/stage3/fix-report.md و manifest نسخه تازه؛ آماده بازآزمایی مستقل، بدون پذیرش نهایی.

شاهد T014–T018: docs/stage3/fix-report.md و fix-evidence؛ سه شکست مستقل بازتولید و اصلاح شدند. یک ابزار با selector قدیمی در وضعیت نامعلوم سازگار نیست و موفق حساب نشده است؛ تأیید مستقل/انسانی همچنان باز است.
