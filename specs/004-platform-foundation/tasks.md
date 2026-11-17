# Tasks: زیرساخت S02

همه مسیرها نسبت به ریشه‌اند. داستان‌ها به spec همین feature اشاره دارند؛ شماره تسک با baseline یکی نیست. تست‌ها به درخواست کاربر قبل از کد تعریف/اجرا می‌شوند.

## Phase 1: Setup

- [x] T001 ثبت مجوز S02، spec/plan/research/data-model/contracts/checklist و analyze در specs/004-platform-foundation/ و docs/stage-status.json — FR-013 SC-006.

- [x] T002 ساخت manifest و lockهای دقیق در backend/pyproject.toml و backend/uv.lock و frontend/package.json و frontend/package-lock.json؛ runtimeهای قفل‌شده و ثبت نسخه docs/stage2/dependencies.json — FR-001 FR-012 SC-001.

- [x] T003 ساخت env خصوصی بدون بازنویسی فایل موجود در scripts/dev_env.py و جدایی DB/volume/پورت در deploy/compose.yaml؛ .env.example و .gitignore/.dockerignore — FR-001 FR-002 FR-008 SC-001.

## Phase 2: US1 — داده و حساب پایه

- [x] T004 [US1] نوشتن تست PostgreSQL برای User canonical/unique/check/unusable password و حساب مستقل در backend/tests/test_accounts.py و backend/tests/conftest.py؛ ثبت شکست پیش از کد — FR-002 FR-003 SC-002.

- [x] T005 [US1] ساخت config/env.py و config/settings.py و apps/identity/models.py در backend؛ User UUID، mobile حداکثر۱۶ و regex ^\+[1-9][0-9]{7,14}$ با unique/check، verified_at=null، active=true/staff=false و زمان‌ها؛ AUTH_USER_MODEL پیش از migration — FR-002 FR-003 FR-008 SC-002.

- [x] T006 [US1] تولید backend/apps/identity/migrations/0001_initial.py و اجرای migration روی DBخالی؛ تست مدل و fixture چندحسابی با backend/manage.py — FR-002 FR-003 SC-001 SC-002.

## Phase 3: US3 — مرز امنیت

- [x] T007 [US3] نوشتن کنترل مثبت/منفی public و CSRF مهمان/واردشده در backend/tests/test_settings.py و backend/tests/test_security.py؛ URLConf probe فقط backend/tests/ — FR-007 FR-008 SC-004.

- [x] T008 [US3] ساخت APIView امن در backend/config/api.py و session/cookie/CSRF/public fail-closed در backend/config/settings.py؛ log/خطا بدون secret — FR-005 FR-007 FR-008 SC-004.

## Phase 4: US2 — قرارداد و سلامت

- [x] T009 [US2] نوشتن سناریوهای health/error/request-id و OpenAPI در backend/tests/test_api.py و backend/tests/test_contract.py پیش از endpoint — FR-004 FR-005 FR-006 FR-011 SC-003.

- [x] T010 [US2] ساخت middleware/request-id و handlerهای JSON در backend/config/middleware.py و config/api.py؛ مسیرهای live/ready/csrf/schema در config/urls.py و config/views.py با SELECT1 و timeout3s — FR-004 FR-005 FR-006 FR-007 SC-003 SC-004.

- [x] T011 [US2] ساخت helper syntax مثبت If-Match و کلید ASCII1..128 در backend/config/protocol.py و اتصال contracts/openapi.yaml؛ عدم ادعای ledger/domain عملیاتی — FR-011 SC-003.

- [x] T012 [US2] اجرای pytest کامل و OpenAPI validator با PostgreSQL واقعی و ثبت خروجی docs/stage2/verification.json؛ خطا/CSRF/public و حالت DB ناموجود پوشش داده شود — FR-004 FR-005 FR-006 FR-007 FR-008 FR-011 SC-003 SC-004.

## Phase 5: US4 — فرانت و هم‌مبدأ

- [x] T013 [US4] نوشتن تست browser با probe test-only و production server در frontend/tests/browser/foundation.spec.ts، frontend/playwright.config.ts و backend/tests/browser_settings.py؛ method/body/query/cookie/status و CSRF — FR-009 FR-010 SC-004 SC-005.

- [x] T014 [US4] ساخت Next standalone و rewrite build-time در frontend/next.config.ts و پوسته فارسی/RTL با فونت/مجوز مرجع در frontend/src/app/ و frontend/public/fonts/؛ lint مستقیم ESLint/TS/Next — FR-009 FR-010 FR-012 SC-005.

- [x] T015 [US4] اجرای lint/typecheck/build و Playwright390/1440 روی standalone؛ ثبت تصویر صرفاً foundation در docs/stage2/evidence/ و نتیجه verification.json — FR-009 FR-010 FR-012 SC-005.

## Phase 6: Delivery and convergence

- [x] T016 ساخت imageهای غیرroot قفل‌شده در deploy/backend.Dockerfile و deploy/frontend.Dockerfile و اجرای compose با DB واقعی و فرمان migration مستقل — FR-001 FR-002 FR-008 FR-012 SC-001.

- [x] T017 ساخت .github/workflows/ci.yml با SHA Action، contents:read و PostgreSQL و lock/migrate/pytest/lint/build/browser؛ اجرای remote ادعا نشود — FR-012 FR-013 SC-001 SC-006.

- [x] T018 ثبت راه واقعی اجرا در docs/development.md و Makefile و ابزار scripts/foundation_smoke.py؛ stop بدون حذف volume و ثبت شواهد بدون secret — FR-002 FR-004 FR-013 SC-001 SC-002 SC-003.

- [x] T019 اجرای fresh-install/build/compose smoke، restart دوحساب و قطع/بازگشت DB در scripts/foundation_smoke.py؛ کنترل عدم دخالت پروژه‌های دیگر و health کمتر از۸ثانیه در قطعی — FR-001 FR-002 FR-004 SC-001 SC-002 SC-003.

- [x] T020 اجرای analyze/converge و رفع یافته‌های همین دامنه؛ به‌روزرسانی docs/stage2/report.md و verification.json و stage-status و baseline tasks؛ تعیین قدم بعد S03 — FR-013 SC-006.

## Dependencies

Setup → US1 → US3 (امنیت پایه) → US2 (API امن) → US4 → delivery. US1 با مدل/DB، US3 با probe آزمون، US2 با API و US4 با مرورگر مستقل قابل آزمون‌اند. کار frontend پس از قرارداد می‌تواند از نظر فایل مستقل باشد؛ در این اجرا توالی حفظ می‌شود. MVP فقط زیرساخت است و هیچ قابلیت محصول حذف نمی‌شود. پس از هر phase نتیجه ثبت و پس از گام گزارش/توقف برای دستور بعدی. چک‌لیست custom تأیید انسانی نیست؛ دستور جاری اجرای S02 و بررسی‌های لازم همان مرحله را مجاز کرده است.

## Phase 7: Convergence

- [x] T021 اصلاح حفظ code خطای protocol در backend/config/api.py و آزمون عبور سرآیند نامعتبر تا پاسخ API در backend/tests/test_contract.py و backend/tests/urls.py؛ FR-005 FR-011 SC-003 (partial، HIGH؛ get_codes در ValidationError فهرست برمی‌گرداند).

- [x] T022 ثبت شکست نصب با manifest/lock ناسازگار در scripts/check_lock_drift.py و docs/stage2/evidence/lock-drift.json؛ US1/AC3 FR-001 FR-012 SC-001 (partial، MEDIUM؛ نصب مثبت ثابت آزموده شده، شاهد منفی هنوز نبود).
