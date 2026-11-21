# تسک‌های invest — پیش‌نویس مرحله‌بندی‌شده

ورودی: spec/plan/research/data-model/contracts/test-plan. این baseline چندمرحله‌ای، شاخص تکمیل محصول نیست؛ checkboxها و ارجاع‌های تحویل پایین دامنه انجام‌شده را مشخص می‌کنند. شماره‌های T001 به بعد اجرایی و T01 تا T29 بسته‌های قدیمی backlog هستند؛ با هم اشتباه نشوند. B01–B04 مصوب‌اند؛ کارهای وابسته به تصمیم‌های باز و schema تفصیلی تا بستن گیت مربوط قابل اجرا نیستند. در PRODUCT-COMP-AI-FREEZE-01 فقط ثبت/انجماد مستندات مجاز است؛ اجرای غیرعمومی T062–T067 برای برنامه‌نویس مجاز شده، اما هیچ تسک با صرف این ثبت کامل علامت نمی‌خورد.

## فاز 1: آماده‌سازی و بستن گیت‌ها

مرحله: S01–S02. پذیرش S01: تصمیم‌ها و تحلیل مستند؛ پذیرش S02 پس از دستور کاربر: نسخه/قرارداد پایه، نصب تمیز، migration و CI. T001 کار پیوسته تا S10 است؛ ردیف‌های وابسته هر قابلیت پیش از اجرای همان قابلیت کامل شوند.

- [ ] T001 در S01 تا S10 تکمیل تدریجی نگاشت معنایی DF/DR و ۶۷ فیلد و تعیین مقصد همهٔ ۴۴ قابلیت در docs/catalogs/implementation-traceability.json؛ source/model/API/widget/acceptance و اختلاف مصوب هر ردیف؛ سیاست D29 مصوب و B06 باز — بسته T01؛ FR-016 FR-020 FR-021 FR-022 SC-001 SC-008.
- [x] T002 ثبت D25–D29 مصوب B01–B04 و پنج پاسخ کاربر و ثبت نتیجه در docs/03-decisions.md و specs/001-business-baseline/spec.md؛ قواعد حدسی ممنوع؛ سپس analyze مجدد — بسته T01؛ FR-020 FR-022.
- [x] T003 ثبت اجازه و دامنهٔ S02 در docs/stage-status.json پس از گزارش گام و دستور کاربر؛ تولید spec/plan/tasks/checklist زیرساخت در specs/004-platform-foundation/ و قرارداد پایه و analyze پیش از کد؛ آماده‌بودن کل محصول را از این اجازه استنتاج نکنید — بسته T01؛ FR-020 FR-022.
- [x] T004 بررسی/قفل نسخه‌های سازگار و ثبت اجرای تمیز backend/pyproject.toml، backend/uv.lock، frontend/package.json و frontend/package-lock.json مطابق research؛ کد مرجع فقط مبنای UI — بسته T02؛ FR-022.
- [x] T005 ایجاد تنظیمات سرویس و PostgreSQL محلی در backend/config/settings.py و deploy/compose.yaml با جدایی development/test/public و .env.example بدون secret؛ مدل پایه حساب در backend/apps/identity/models.py و تنظیم AUTH_USER_MODEL و migration اولیه پیش از جداول وابسته/fixtureها؛ منطق ورود در S03 — بسته T02؛ FR-017 FR-022.
- [x] T006 ساخت CI با PostgreSQL، migration خالی، backend/frontend checks و browser artifacts در .github/workflows/ci.yml؛ نوشتن راه اجرای تمیز docs/development.md — بسته T03؛ FR-022 SC-005.

## فاز 2: پایهٔ مشترک

مرحله: S02–S04. پذیرش مستقل: schema API، مجوز پایه، دادهٔ کاتالوگ و ابزار آزمون مستقل قابل بررسی باشند.

- [x] T007 پس از مدل پایه حساب T005، ایجاد fixtureهای چندحسابی و DB تراکنشی در backend/tests/conftest.py؛ بدون SQLite برای شاهد رقابت — بسته T03؛ FR-017 SC-004 SC-005.
- [x] T008 تعریف envelope خطا، CSRF ناشناس، version/idempotency و schema ماشین‌خوان در backend/config/api.py و contracts/openapi.yaml؛ تست در backend/tests/test_contract.py — بسته T03؛ FR-022 SC-004.
- [ ] T009 طبق D29 تعریف MoneyValue/Quantity/ReturnMetric و FieldDefinition نسخه‌دار/namespace با TOMAN دقیق، واحد ورودی/ضریب و unknown؛ ابزار مقدار/واحد در backend/apps/catalog/values.py و تعریف و taxonomy/geography در backend/apps/catalog/models.py و backend/apps/catalog/schemas.py؛ migration در backend/apps/catalog/migrations/ — بسته T07؛ FR-016 FR-021 SC-008 FR-029 FR-030.
- [ ] T010 ایجاد فرمان import نمونه با برچسب صریح و منع seed در public mode در backend/apps/catalog/management/commands/import_reference.py؛ ۱۱ گروه/۷۸ نوع و ۲۷۳ نمونه بدون جعل داده واقعی — بسته T07؛ FR-016 SC-001.
- [ ] T011 طبق AC-D29-01..08/12 آزمون round-trip دقیق، عدد فارسی/عربی و ورودی مبهم/بیش‌دقت، صفر/unknown/نامربوط، واحد نسخه‌دار/ارز و مبنای بازده و حذف اثر مقدار فیلد پنهان در UI و سرور در backend/tests/unit/test_catalog.py؛ fixture از نگاشت مصوب — بسته T07؛ FR-016 FR-021 SC-008 FR-029 FR-030.
- [ ] T012 تکمیل ماتریس صفحه/state شامل راهنما/صندوق/فروش و popover/خطا/مراحل؛ تثبیت زمان و حرکت baseline و طرح پیشنهادی موبایل در tests/browser/visual/baseline-manifest.json؛ B08 — بسته T06؛ FR-015 FR-019 SC-003 SC-006.

## فاز 3: US05 ورود و فضای شخصی

مرحله: S03 سپس S07. پذیرش مستقل: ورود واقعی آزمایشی، جداسازی دو حساب و بازیابی دو دستگاه؛ پذیرش AC-D05 و SC-004.

- [x] T013 [US05] نوشتن تست TTL/تلاش/replay/CSRF/challenge binding و عدم افشای public OTP در backend/tests/integration/test_otp.py؛ مقادیر سیاست قبل از اجرا در spec هویت ثبت شوند — بسته T04؛ FR-010 FR-011 SC-004.
- [x] T014 [US05] تکمیل مدل پایه User ساخته‌شده در T005 و پیاده‌سازی Session/OTPChallenge و migrationهای بعدی و adapter تحویل test/SMS در backend/apps/identity/models.py و backend/apps/identity/otp.py؛ مصرف اتمیک و gate public — بسته T04؛ FR-010 FR-011.
- [x] T015 [US05] ساخت endpointهای CSRF/challenge/verify/me/logout با نشست و مجوز در backend/apps/identity/api.py؛ ابطال/چرخش نشست — بسته T04؛ FR-010 FR-011 FR-017.
- [x] T016 [US05] اتصال دیالوگ اصلی ورود به API، OTP notification همان صفحه و حالت خطا/انقضا در frontend/src/components/auth/login-dialog.tsx؛ secret یا نقش در localStorage نباشد — بسته T04؛ FR-010 FR-015 FR-019.
- [ ] T017 [US05] اجرای سفر ورود/خروج و screenshot دیالوگ مصوب موبایل/دسکتاپ در tests/browser/journeys/auth.spec.ts و tests/browser/visual/auth.spec.ts — بسته T04؛ FR-010 FR-019 SC-002 SC-006.
- [ ] T018 [US05] در S07 نوشتن تست همگامی دو دستگاه، جداسازی مالک و زمان تازه واقعی در backend/tests/integration/test_workspace.py — بسته T15؛ FR-017 SC-004.
- [ ] T019 [US05] ساخت SavedListing/SavedSearch و CRUD مجاز، last_seen_at واقعی و migration در backend/apps/workspace/models.py و backend/apps/workspace/api.py — بسته T15؛ FR-017.
- [ ] T020 [US05] پیش از اعلان S07 بستن بخش کانال/رفتار اعلان B06 با کاربر در docs/stage7/notification-decisions.md؛ سپس ساخت پروفایل اختیاری بدون اعطای role و اعلان فقط مخاطب مجاز در backend/apps/notifications/models.py و backend/apps/workspace/profile.py؛ migration و تست backend/tests/integration/test_notifications.py — بسته T17؛ FR-017 SC-004.
- [ ] T021 [US05] اتصال منتخب/شرایط/پروفایل/اعلان و حالت فرصت متوقف‌شده به طرح مرجع در frontend/src/app/saved/page.tsx و frontend/src/components/workspace/notifications.tsx؛ سفر در tests/browser/journeys/workspace.spec.ts — بسته T15 T17؛ FR-017 FR-019 SC-006.

## فاز 4: US02 مالک و انتشار

مرحله: S03/S05. پذیرش مستقل: ثبت فرد/سازمان و بررسی مستقل نمایندگی و revision؛ AC-D10/D11 و درخواست مستقیم غیرمجاز.

- [ ] T022 [US02] بر اساس D25/D27 تست مالکیت، دو approval مستقل، منع خودتأییدی، شواهد مستقل، قطع اختیار قبلی، جداسازی چند سازمان و رقابت جانشین در backend/tests/integration/test_organizations.py و رقابت نسخه در backend/tests/integration/test_publication.py؛ pending revision در جست‌وجو/AI نشت نکند — بسته T05 T08 T10؛ FR-001 FR-002 FR-003 FR-004 SC-004 SC-005 FR-023 FR-027.
- [ ] T023 [US02] ساخت Organization/Representation/VerificationEvidence/RepresentationChange/Owner طبق D27 با حداکثر یک نماینده فعال، چند سازمان مستقل، مدارک/شاهد بررسی و گردش تغییر/توقف اختیار در backend/apps/organizations/models.py و backend/apps/organizations/services.py؛ migration و سیاست تغییر نماینده مصوب — بسته T05 T08؛ FR-001 FR-002 FR-027.
- [ ] T024 [US02] پیش از فایل S05 بستن نوع/حجم/نگهداری/حذف فایل B07 با کاربر در docs/stage5/file-policy.md؛ سپس ساخت upload/download خصوصی با بررسی mime/content/size و مجوز در backend/apps/documents/storage.py و backend/apps/documents/api.py؛ تست حدس URL در backend/tests/integration/test_files.py — بسته T09؛ FR-002 FR-017 SC-004.
- [ ] T025 [US02] ساخت Opportunity/Revision نوع‌دار، schema validation و draft API در backend/apps/opportunities/models.py و backend/apps/opportunities/api.py؛ فرم پروژه/صندوق/فروش و migration — بسته T08 T09؛ FR-001 FR-016 FR-021.
- [ ] T026 [US02] ساخت submit/review/approve با version، تراکنش و public_revision immutable در backend/apps/opportunities/publication.py؛ توقف فوری مالک، بازنشر/رفع تعلیق ادمین، انقضا و رد patch نسخه ارسال‌شده مطابق D25؛ تست AC-D25-01/02/11؛ بازخوانی وضعیت اختیار سازمان طبق D27 هنگام publish و عدم دورزدن توقف با بازنشر — بسته T10؛ FR-002 FR-003 FR-004 SC-005 FR-023 FR-027.
- [ ] T027 [US02] طرح و اجرای پنل مالک/نماینده، فرم نسخه‌دار و پیوست/خطا با اجزای مرجع در frontend/src/app/owner/opportunities/page.tsx و frontend/src/components/owner/editor.tsx؛ انتخاب سازمان با اختیار مستقل و فرم مدارک/اعتبار و درخواست جانشین طبق D27 در frontend/src/app/owner/organizations/page.tsx؛ B08 — بسته T08 T09؛ FR-001 FR-002 FR-019 FR-027.
- [ ] T028 [US02] طرح و اجرای پنل ادمین بررسی نمایندگی و فرصت و diff نسخه‌ها در frontend/src/app/admin/reviews/page.tsx؛ دلیل تصمیم و حالت conflict؛ ثبت شواهد بررسی مستقل، تعویض/توقف اختیار و منع خودتأییدی طبق D27 — بسته T10؛ FR-002 FR-003 FR-004 FR-019 FR-027.
- [ ] T029 [US02] سفر انتشار، رد اصلاح، حفظ نسخه قبلی و approval جدید در tests/browser/journeys/publication.spec.ts؛ AC-D27-01..10 برای مدارک خصوصی/نماینده قدیم و جدید/دو سازمان/توقف و نشان نمایندگی در tests/browser/journeys/organizations.spec.ts؛ visual پنل مصوب در tests/browser/visual/publication.spec.ts — بسته T10؛ FR-004 FR-019 SC-002 SC-003 FR-001 FR-002 FR-027 SC-004 SC-005.

## فاز 5: US01 کشف و مقایسه

مرحله: S06 سپس S07. پذیرش مستقل: دادهٔ نامعلوم/نامتناسب حذف نشود؛ مقایسهٔ ۲–۴ هم‌نوع با واحد معتبر؛ AC-D12/D14.

- [ ] T030 [US01] طبق D28/D29 و پس از نگاشت معنای فیلدهای مسیر نوشتن fixture با انتظار مستقل برای AC-D28-01..14، پنج مثال عددی، W/K صفر، عدم بهبود با حذف داده، مخرج/وزن غیرتکراری، unknown/صفر و حدود مبلغ/مکان؛ ثبت نمونه و قضاوت کارشناس هر مسیر در docs/validation/matching-review.md و تست در backend/tests/unit/test_matching.py؛ تمام مسیرهای سرمایه/صندوق/پیمان/خرید/اجاره/میراث/بهره‌برداری — بسته T11 T12؛ FR-005 SC-002 FR-028 FR-029 FR-030.
- [ ] T031 [US01] ساخت MatchPolicy نسخه‌دار و ارزیابی با score/coverage/reasons در backend/apps/matching/policy.py و backend/apps/matching/services.py؛ D28: همه ترجیحات فقط رتبه، وزن‌های ۳۰/۲۰/۱۵/۲۰/۱۵/۱۵ و مخرج ثابت، تفکیک unknown/unmet، W/K صفر، مبلغ ورود/خرید/اجاره و مکان نوع‌دار؛ تغییر سیاست نسخه تازه و وابسته به بازبینی نمونه‌ها — بسته T12؛ FR-005 FR-021 FR-028.
- [ ] T032 [US01] ساخت public list/detail با cursor پایدار، sort و revision و جغرافیای واقعی در backend/apps/opportunities/public_api.py؛ D28: ورود مستقیم بدون شرط، total_count بدون min_score، sort دقیق/coverage/انتشار/شناسه و cursor با سیاست/شرایط ثابت؛ تست عدم تکرار/افتادگی روی داده ثابت و عدم نشت draft در backend/tests/contracts/test_discovery.py — بسته T11؛ FR-005 FR-016 FR-028.
- [ ] T033 [US01] بازسازی فیلتر/نتایج/نقشه و شناسنامه اصلی با اتصال API در frontend/src/app/opportunities/page.tsx و frontend/src/app/opportunities/[id]/page.tsx؛ متن ناسازگار strictLocation مطابق D12/D28 اصلاح شود؛ ورود مستقیم، score/coverage جدا و برچسب اطلاعات ناکافی/بدون ترجیح و شرط مهم نامنطبق در frontend/src/components/opportunities/match-explanation.tsx؛ هویت و چیدمان مرجع حفظ شود — بسته T11 T12؛ FR-005 FR-015 FR-019 FR-028.
- [ ] T034 [US01] سفر کشف D28 با ورود مستقیم، همه نتایج نامتناسب/unknown، تفکیک امتیاز/پوشش و شرط مهم، تغییر شرط/نسخه و صفحه‌بندی پایدار و تصویر حالت‌ها در tests/browser/journeys/discovery.spec.ts و tests/browser/visual/discovery.spec.ts — بسته T11 T12؛ FR-005 FR-019 SC-002 SC-003 SC-006 FR-028.
- [ ] T035 [US01] در S07 تست ۱/۲/۴/۵، mixed/duplicate/unpublished، ارز/واحد و unknown و مبنای بازده طبق D29؛ بدون IRR ساختگی یا برنده cross-currency برای هر سه kind در backend/tests/unit/test_comparison.py — بسته T16؛ FR-006 SC-002 FR-029 FR-030.
- [ ] T036 [US01] ساخت comparison API و metric schema مستقل پروژه/صندوق/فروش در backend/apps/matching/comparison.py؛ داده و revision مبنا در پاسخ؛ D29: واحد دقیق/مبنای شاخص و comparable=false با دلیل برای ناسازگاری — بسته T16؛ FR-006 FR-029 FR-030.
- [ ] T037 [US01] بازسازی جدول/نمودار/انتخاب مقایسه و حالت خالی از مرجع در frontend/src/app/compare/page.tsx و frontend/src/components/compare/metrics.tsx؛ unknown برنده نشود و جدول موبایل قابل پیمایش — بسته T16؛ FR-006 FR-019 SC-003 SC-006.
- [ ] T038 [US01] اجرای سه سفر مقایسه و حذف/توقف مورد و تصاویر در tests/browser/journeys/comparison.spec.ts و tests/browser/visual/comparison.spec.ts — بسته T16؛ FR-006 SC-002 SC-006.

## فاز 6: US03 درخواست و پیگیری

مرحله: S06. پذیرش مستقل: بدون رضایت شماره درخواست ثبت/ارجاع/پاسخ شود؛ AC-D06 و ارسال صریح و رسید واحد.

- [ ] T039 [US03] بر اساس D25/D26 تست نقش/ارجاع/لغو رضایت، replay و stale revision در backend/tests/integration/test_enquiries.py؛ خواندن مستقیم فایل/شماره حساب دوم رد شود — بسته T13 T14؛ FR-007 FR-008 FR-009 FR-013 SC-004 SC-005 FR-024 FR-025 SC-009 FR-026.
- [ ] T040 [US03] ساخت Enquiry/Snapshot/ContactConsent/CaseEvent و migration و submit اتمیک در backend/apps/enquiries/models.py و backend/apps/enquiries/submission.py؛ قرارداد/پول خارج سامانه؛ related_enquiry_id و رسید پیگیری پس از closed/cancelled و عدم ادغام خاموش درخواست مستقل مطابق D25 — بسته T13؛ FR-008 FR-009 FR-013 FR-018 FR-023 FR-024.
- [ ] T041 [US03] ساخت assignment/message/transition و مجوز recipient-scoped contact در backend/apps/enquiries/services.py و backend/apps/enquiries/api.py؛ در submit وضعیت جاری اختیار سازمان طبق D27 بررسی و intake تازه در اختلاف متوقف شود ولی پرونده/پیام قبلی برقرار بماند؛ بدون رضایت phone اصلاً در response نباشد؛ قرارداد D26 برای گیرنده نام‌برده/لغو/عدم دسترسی cache و مسیر استثنایی سروری با نقش مجزا/احراز مجدد/دلیل در backend/apps/identity/account_support.py و تست backend/tests/integration/test_contact_privacy.py؛ اجرای D25 و job بستن هفت‌روزه/هشدار پاسخ در backend/apps/enquiries/jobs.py، تقویم/موعد/آمادگی تیم در backend/apps/enquiries/operations.py؛ clock/race tests در backend/tests/integration/test_case_lifecycle.py — بسته T14؛ FR-007 FR-008 FR-009 FR-024 FR-025 SC-009 FR-026 FR-027.
- [ ] T042 [US03] ساخت بازبینی ارسال بدون رضایت پیشینی به کارشناس نامشخص، رسید و replay UI در frontend/src/components/enquiries/submit.tsx؛ اقدام صریح کاربر تنها راه ارسال — بسته T13؛ FR-008 FR-009 FR-013 FR-019.
- [ ] T043 [US03] طرح و ساخت پرونده/پیام برای کاربر، کارتابل کارشناس و ارجاع ادمین با هویت مرجع در frontend/src/app/enquiries/[id]/page.tsx و frontend/src/app/expert/page.tsx و frontend/src/app/admin/enquiries/page.tsx؛ نمایش پاسخ/بستن/لغو/پیگیری مرتبط و هدف پاسخ مطابق D25؛ D26: کنترل رضایت به نام گیرنده و لغو همان صفحه در frontend/src/components/enquiries/contact-consent.tsx و صفحه مستقل مسئول امنیت/بازیابی در frontend/src/app/account-support/page.tsx؛ B08 — بسته T14؛ FR-007 FR-008 FR-019 FR-024 FR-025 FR-009 FR-026.
- [ ] T044 [US03] اجرای اولین سفر سرتاسری بدون phone consent، پاسخ و تعویض ارجاع در tests/browser/journeys/enquiry.spec.ts؛ AC-D25-03..10/12 شامل پیام هم‌زمان با بستن، تعطیلی، تعویض کارشناس و عدم reset موعد؛ AC-D26-01..08 برای گیرنده/لغو/استثنای نقش/احراز مجدد/هدف و عدم افشای پاسخ؛ کنترل DOM/network/attachments و visual پنل‌ها — بسته T13 T14؛ FR-007 FR-008 FR-009 FR-013 SC-002 SC-004 SC-006 FR-024 FR-025 SC-009 FR-026.

## فاز 7: US06 هویت بصری و خدمات تخصصی

مرحله: پوسته S04، راهنما S07، خدمات S08. پذیرش مستقل: همان هویت و تمام جریان‌های تخصصی با draft/report/submit مستقل؛ هر جریان test شرط/مرز مستقل دارد.

- [ ] T045 [US06] در S04 انتقال asset/font/token و بازسازی layout/header/footer/home از مرجع در frontend/src/app/layout.tsx و frontend/src/app/page.tsx و frontend/src/styles/tokens.css؛ اصلاح hydration بدون تغییر طرح — بسته T06؛ FR-015 FR-019 SC-003 SC-006.
- [ ] T046 [US06] تأیید و اجرای layout موبایل و ماتریس state در frontend/src/components/site/header.tsx و tests/browser/visual/shell.spec.ts؛ تست touch/keyboard/motion مستقل — بسته T06؛ FR-015 FR-019 SC-003 SC-006.
- [ ] T047 [US06] در S07 تست snapshot راهنما و HTML فارسی دانلود، کتابخانه و پرونده فرصت در backend/tests/unit/test_reports.py؛ دانلود هرگز submitted نشود؛ D29: تغییر واحد/فرض/قاعده گزارش قبلی را تغییر ندهد — بسته T18؛ FR-016 FR-018 SC-008 FR-029 FR-030.
- [ ] T048 [US06] ساخت راهنما/کتابخانه نسخه‌دار و گزارش با snapshot واحد/داده/فرض/نسخه قاعده طبق D29 در backend/apps/documents/reports.py و frontend/src/app/guide/[id]/page.tsx و frontend/src/app/tools/library/page.tsx؛ ساخت پرسش اختصاصی پرونده فرصت در backend/apps/services/dossier.py و frontend/src/app/tools/ma-notice/page.tsx با تست backend/tests/unit/test_dossier.py — بسته T18؛ FR-016 FR-018 FR-029 FR-030.
- [ ] T049 [US06] قبل از S08 بستن schemaهای draft/معرفی طرح/ایده، شرط‌ها/واحدها و پذیرش هر DF/DR مرتبط در specs/002-specialized-services/spec.md و contracts/services/proposal.json و contracts/services/ideas.json — بسته T19؛ FR-016 FR-017 FR-021 SC-008.
- [ ] T050 [US06] تست منابع/کسری/مرحله/پیوست و ادامه پیش‌نویس در backend/tests/unit/test_proposals.py؛ سپس service در backend/apps/services/proposals.py و فرم در frontend/src/components/services/proposals.tsx — بسته T19؛ FR-016 FR-017 FR-021.
- [ ] T051 [US06] نهایی‌کردن schema زمین و تست بسته چندخدمتی/ترتیب/تکرار/حذف اثر شرط در contracts/services/land.json و backend/tests/unit/test_land.py؛ نگاشت DF/DR ثبت شود — بسته T20؛ FR-016 FR-021 SC-008.
- [ ] T052 [US06] ساخت جریان زمین و summary/report/submit با API مشترک در backend/apps/services/land.py و frontend/src/components/services/land.tsx؛ legacy iframe مقصد نیست — بسته T20؛ FR-016 FR-021 FR-019.
- [ ] T053 [US06] نهایی‌کردن schema و تست ارز/کشور/آورده/منبع بدون تبدیل خودکار و واحد/ضریب صریح طبق D29 در contracts/services/international.json و backend/tests/unit/test_international.py — بسته T21؛ FR-016 FR-021 SC-008 FR-029.
- [ ] T054 [US06] ساخت جریان بین‌المللی با واحد و مدرک و گزارش در backend/apps/services/international.py و frontend/src/components/services/international.tsx؛ جابه‌جایی پول ادعا نشود — بسته T21؛ FR-016 FR-021 FR-019.
- [ ] T055 [US06] نهایی‌کردن schema و تست AC-D29-09/10 برای خانوار×ودیعه و خانوار×اجاره×ماه، خروجی ودیعه برگشت‌پذیر جدا از هزینه اجاره، داده ناقص و واحد/مدت صریح در contracts/services/renewal.json و backend/tests/unit/test_renewal.py — بسته T22؛ FR-016 FR-021 SC-008 FR-029 FR-030.
- [ ] T056 [US06] ساخت نوسازی/اسکان موقت و فرض‌های محاسبه و ودیعه/اجاره مستقل طبق D29 در backend/apps/services/renewal.py و frontend/src/components/services/renewal.tsx — بسته T22؛ FR-016 FR-021 FR-019 FR-029 FR-030.
- [ ] T057 [US06] نهایی‌کردن دو schema جدا و تست حق استفاده/مالکیت/مدت/تسویه در contracts/services/rental.json و contracts/services/exchange.json و backend/tests/unit/test_rental_exchange.py — بسته T23؛ FR-016 FR-021 SC-008.
- [ ] T058 [US06] ساخت دو جریان مستقل اجاره‌داری/معاوضه در backend/apps/services/rental.py و backend/apps/services/exchange.py و frontend/src/components/services/rental.tsx و frontend/src/components/services/exchange.tsx — بسته T23؛ FR-016 FR-021 FR-019.
- [ ] T059 [US06] نهایی‌کردن ۶۱ پیکربندی و قواعد ساختمان/زمین/خیریه و همهٔ شرط‌های DF/DR مربوط در contracts/services/advisories.json و backend/tests/unit/test_advisories.py؛ AC-D29-11/12: هزینه واحد/ظرفیت/دوره با منبع/تاریخ؛ ضریب نمونه واقعی نباشد و نبود مبنا needs_expert_estimate دهد — بسته T24؛ FR-016 FR-021 SC-008 FR-029 FR-030.
- [ ] T060 [US06] ساخت advisory/charity و summary با فرض‌های مصوب D29 و نتیجه نیازمند برآورد کارشناس بدون عدد ساختگی در نبود مبنا در backend/apps/services/advisories.py و frontend/src/components/services/advisories.tsx و frontend/src/components/services/charity.tsx — بسته T24؛ FR-016 FR-021 FR-019 FR-029 FR-030.
- [ ] T061 [US06] اجرای سفر هر خدمت تا draft/report/explicit submit و شرط‌های toggle/مرزی و D29: پاسخ پنهان نامربوط، حفظ واحد/فرض گزارش، ودیعه/اجاره جدا و خیریه بدون مبنا در tests/browser/journeys/services.spec.ts؛ تصویر هر مرحله در tests/browser/visual/services.spec.ts و شاهد نگاشت docs/catalogs/implementation-traceability.json — بسته T19 T20 T21 T22 T23 T24؛ FR-016 FR-017 FR-019 FR-021 SC-002 SC-003 SC-006 SC-008 FR-029 FR-030.

## فاز 8: US04 دستیار متصل

مرحله: S09. پذیرش مستقل: جست‌وجو/توضیح/مقایسه از داده مجاز و امتیاز سرور با سهمیه واقعی؛ AC-D07/D20 و AC-AI01..10. PC-D02-01..05 در docs/comp-ai-decision-package.md مصوب‌اند. در PROGRAMMER-COMP-AI-COMPLETE-01 بخش فنی T062–T066 پیاده و برای بازآزمایی مستقل آماده شد؛ T067 به‌علت نبود credential خصوصی، اجرای واقعی Sol/Luna و رأی انسانی فارسی باز است. مسیر specs/003-assistant در outline قدیمی ساخته نشد؛ اسناد همین baseline صاحب مسئله باقی ماندند.

- [x] T062 [US04] بستن B05 و قفل‌کردن مدل/عدد/هزینه/خطا/retention در baseline، OpenAPI و policy اجرایی؛ کلید فقط از محیط خصوصی backend — بسته T25؛ FR-012 FR-014. شاهد: گزارش تجمیعی S09 و `contracts/openapi.yaml`.
- [x] T063 [US04] تست quota اتمیک مهمان/حساب و permission ابزار/context injection و retry در `backend/tests/test_assistant.py`؛ fixture فارسی قفل‌شده در `backend/tests/fixtures/assistant_cases.json`؛ D28 بدون تغییر — بسته T25 T27؛ FR-012 FR-013 FR-014 SC-004 SC-005 FR-028.
- [x] T064 [US04] ساخت QuotaPolicy/UsageReservation/Ledger بی‌محتوا و migration، policy ادمین و adapter Responses در `backend/apps/assistant/`؛ عمداً Conversation/Message پایدار ساخته نشد — بسته T25؛ FR-012 FR-014.
- [x] T065 [US04] چهار ابزار read-only روی revision عمومی، parse/validate criteria و استناد، timeout/retry/تسویه مصرف در `backend/apps/assistant/tools.py` و `api.py`؛ submit/private/web tool وجود ندارد — بسته T25 T26؛ FR-012 FR-013 FR-014 FR-028.
- [x] T066 [US04] سفر خانه/فرصت، برداشت قابل اصلاح، picker، کارت/فهرست، ذخیره با رسید، مقایسه و مسیر دستی در `frontend/src/app/assistant/`، component دستیار و chat مقایسه؛ چهار عرض در تست مرورگر — بسته T26؛ FR-012 FR-013 FR-014 FR-019.
- [ ] T067 [US04] اجرای ارزیابی فارسی و smoke محدود واقعی OpenAI جدا از mock؛ ثبت مدل/نسخه/نتیجه بدون secret در docs/stage9/verification.json و tests/browser/journeys/assistant.spec.ts — بسته T27؛ FR-012 FR-013 FR-014 SC-002 SC-007.

وضعیت T067: fixture قفل‌شده، fake قطعی، runner و شواهد UI فنی آماده‌اند؛ چون `OPENAI_API_KEY` امن در محیط مأموریت نبود، provider call واقعی صفر و هزینه صفر است. smoke بیست‌مکالمه، eval واقعی Sol، مقایسه همان held-out با Luna و رأی انسانی فارسی تکمیل/قبول نشده‌اند.

به‌روزرسانی PROGRAMMER-COMP-AI-EVAL-INTEGRATION-01: مسیر فنی T063/T065/T066 با orchestrator مشترک، schema برداشت مدل نسخه‌دار، seed عمومی مصنوعی ۱۵ فرصت قفل‌شده، scorerهای مستقل با مخرج‌های ۴۴/۵۳/۱۲۰، guard عدم dispatch و خروجی allowlist بی‌محتوا تکمیل شد. کدهای canonical UI با واژگان فارسی نسخه‌دار نمایش داده می‌شوند. تماس واقعی، هزینه، رأی فارسی و انتخاب مدل انجام نشده‌اند؛ T067 باز می‌ماند.

الحاق FIX-01: قرارداد public model را نمی‌پذیرد؛ router سروری نسخه‌دار، سقف فردی ماهانه، secret-file runtime، credential جداگانه eval، progress واقعی و تعامل چندنوبتی/picker/compare در دامنه T062–T066 تقویت شدند. runner T067 دیگر placeholder نیست و با `--confirm-live` و credential خصوصی قابل اجراست، ولی چون credential موجود نبود همان بخش live و رأی انسانی همچنان باز و checkbox T067 بدون تغییر است.

تفصیل لازم همان تسک‌ها، بدون backlog/feature موازی:

به‌روزرسانی PRODUCT-COMP-AI-EVAL-ORACLE-01: آمادگی runner در بندهای قبلی ادعای تحویل برنامه‌نویس بود، نه اعتبار ارزیابی. oracle مستقل در `contracts/assistant-evaluation-oracle.json` منجمد شد؛ runner فعلی prompt/schema عمومی مستقل دارد، چهار ابزار/context واقعی محصول را طی نمی‌کند و extraction/citation/router را نمره نمی‌دهد. T067 باز می‌ماند؛ تکمیل تاریخی T062–T066 رأی مستقل یا پایان اصلاحات زیر نیست. اجرای این مأموریت فقط oracle/اسناد بوده است.

| مالک موجود | کار باقی‌مانده یکپارچه / شاهد پایان |
|---|---|
| T063/T065/T067 | اتصال runner به مسیر واقعی prompt/tool/schema محصول و پایگاه مصنوعی نسخه‌دار oracle؛ قفل hash، scorer حافظه‌ای با تفکیک server/model extraction، citation field-level و router مستقل؛ negative/fault بدون تماس واقعی، خروجی فقط allowlist sanitized؛ آزمون contract/متامورفیک scorer برای حذف/جعل استناد، unknown→zero، route/model اشتباه، denominator و leak. هیچ تغییر انتظار برای سبزشدن محصول. |
| T066/T067 | regression تأییدشده در `docs/stage9/evidence/fix-01/browser/assistant-complete-390.png`: نمایش investor/project در chips و revision روی کارت. برچسب فارسی از واژگان مرجع/مصوب، بدون دستکاری مقدار canonical یا استناد واقعی؛ fallback به کد داخلی ممنوع. شاهد مرورگر چهار عرض و حالت کامل/مقایسه/خطا؛ این اصلاح تصمیم تازه بیزینسی یا رأی طراحی نیست. |

پرامپت نهایی handoff: «PROGRAMMER-COMP-AI-EVAL-INTEGRATION-01؛ پس از واگذاری هماهنگ‌کننده، AGENTS/constitution/stage-status، مصوبات FIX-01، baseline001/US04 و قرارداد ارزیابی در contracts/api.md، test-plan و oracle قفل‌شده را بخوان. بدون تغییر ID/input/split/انتظار، runner را به orchestrator، prompt، چهار ابزار read-only و schema واقعی محصول روی داده عمومی مصنوعی ایزوله متصل کن؛ مقادیر مورد انتظار وارد prompt نشوند. scorer حافظه‌ای extraction exact/unknown/absent/clarification، citation ID+revision+field+value، router مستقل و guard عدم dispatch را با تست منفی اثبات کن. criteria سرور را کیفیت مدل جا نزن؛ اگر model extraction قابل مشاهده نیست، مانع را رفع یا پیش از live به محصول ارجاع بده. نسبت‌های مخرج۴۴/۲۴case-۵۳tuple/۸۰ در held-out حفظ و N/A جدا بماند. Sol و Luna روی همان۸۰ case و split/hash ثابت، با مسیر بدون provider برای negative/fault، بدون fallback و زیر سقف مشترک eval۱۵دلار/ماه۱۰۰دلار/principal۱۰دلار سنجیده شوند؛ credentials فقط محیط خصوصی و live فقط با مجوز/بودجه جاری. در این handoff آغاز تماس واقعی خودکار مجاز نیست؛ نخست آمادگی مسیر/scorer تأیید شود. prompt/response/tool payload یا error body پایدار نشود؛ فقط metric/case/model/token/cost/failure code و manifest نسخه/hash مجاز. رأی فارسی را انسان با مشاهده موقت بدهد؛ بدون آن انتخاب نهایی صادر نکن. regression investor/project/revision را با برچسب فارسی و حفظ canonical data اصلاح و شاهد چهار عرض ارائه کن. یک تحویل تجمیعی با تست‌های اثرمحور، مسائل باز، گیت‌های انسانی مستقل و commit محلی؛ بدون push/deploy، تغییر D28 یا شروع بسته دیگر. پس از گزارش متوقف شو.»

| تسک | خروجی کامل و شرط پایان پس از مجوز | پذیرش/وابستگی |
|---|---|---|
| T062 | مصرف پاسخ مصوب پنج PC-D02 در docs/03-decisions.md و تکمیل artifact اجرایی S09؛ مدل/قیمت/retention/quotas و rubric نهایی، analyze و قرارداد ماشین‌خوان. تحقیق رسمی قبلی جای دسترسی واقعی حساب نیست؛ credential در سند نیاید. | AC-AI10؛ D04/D07/D20؛ قبل T063–T067، بدون تیک با صرف ثبت مصوبات |
| T063 | fixture مصنوعی فارسی با انتظار مستقل، fake provider پایدار و تست قرارداد/مجوز/grounding/رقابت PostgreSQL/timeout/cost؛ تعداد و آستانه مصوب از test-plan؛ حفظ وزن/فرمول D28. | AC-AI02..08/10؛ T062؛ زبان واقعی از fake نتیجه نشود |
| T064 | adapter خصوصی و quota/ledger/version policy اتمیک، تفکیک سهمیه پاسخ/هزینه تلاش، ادغام ورود، رزرو بودجه نامعلوم و retention انتخاب‌شده؛ Conversation مفهومی الزام DB محتوا نیست. | AC-AI06/07/10؛ T063؛ PC-D02-01..04 |
| T065 | چهار ابزار قرارداد با داده عمومی و خروجی واقعی server IDs/revisions/policy/score/coverage/reasons؛ strict+کنترل مستقل، اعتبارسنجی/مجوزسنجی دوباره تاریخچه و نتایج غیرقابل‌اعتماد کلاینت، محافظ تزریق و stale، هزینه/timeout تسویه‌شونده؛ نه private/web/submit tool. | AC-AI01..08؛ T063/T064؛ مصرف API هسته پذیرفته‌شده |
| T066 | سفر یکپارچه خانه/فرصت→برداشت→کشف/مقایسه→فرم دستی/اقدام صریح؛ picker، ذخیره با رسید، chips، کارت/فهرست، highlight جدول، نوبت کهنه و همه حالات شکست؛ چهار عرض و فونت/حرکت، متن/criteria هنگام اختلال محفوظ. | AC-AI01..09؛ T065 و منبع واقعی در بسته تصمیم؛ رأی طراحی جدا |
| T067 | گزارش تجمیعی تسترپسند: fake، smoke واقعی و eval فارسی جدا، Sol اولیه و مقایسه الزامی Luna روی همان۸۰ held-out در سقف مشترک eval، پیشنهاد انتخاب نهایی طبق PC-D02-01 بدون تعویض خودکار، مخرج/فایل شکست/مدل/قیمت/prompt/tool/revision/usage، زمان‌ها، محدودیت، طراحی و کیفیت انسانی باز یا با رأی واقعی؛ آماده بررسی مستقل، نه قبول خودکار. | AC-AI09/10 و SC-007؛ T063–T066؛ مجوز تماس/credential خصوصی؛ بدون استنتاج کیفیت D28 |

این شش تسک یک مأموریت کامل سفر کاربرند؛ توقف بعد از هر فایل/تسک لازم نیست، ولی تصمیم/مجوز یا credential مفقود نباید با حدس دور زده شود. گیت‌های فنی و انسانی و production مستقل گزارش شوند.

## فاز 9: تطبیق نهایی و بهره‌برداری

مرحله: S10–S11. پذیرش مستقل: همهٔ گیت‌ها با شاهد واقعی بسته؛ اجرای مرحله/انتشار فقط با دستور جدید کاربر.

- [ ] T068 تطبیق تمام ۴۴ قابلیت، DF/DR و فرم‌های مرجع با محصول در docs/catalogs/implementation-traceability.json و docs/catalogs/feature-coverage.csv؛ ردیف باز/حذف خاموش مانع تحویل است — بسته T28؛ FR-016 FR-021 FR-022 SC-001 SC-008.
- [ ] T069 بستن بخش اتصال بیرونی B06 و اجرای فقط اتصال مصوب بازآفرینی با قرارداد واقعی در backend/apps/services/external.py و backend/tests/contracts/test_external.py؛ در نبود API وضعیت deferred با تصمیم صریح، نه fake success — بسته T28؛ FR-016 FR-018.
- [ ] T070 فعال‌سازی SMS واقعی، حذف OTP response/UI در public و اجرای smoke کنترل‌شده؛ شاهد در docs/stage11/sms-verification.json و تست gate در backend/tests/integration/test_public_launch.py — بسته T29؛ FR-011 SC-007.
- [ ] T071 تکمیل بخش عرضه B07 و بازبینی سیاست فایل ثبت‌شده در T024، تست بار هدف/حریم/retention و backup/restore مستقل و rollback در deploy/backup.sh و deploy/restore.sh و tests/load/scenarios.js؛ gate تیم/تقویم/جانشین D25 و fixture تعطیلی/خارج ساعات کاری هم بررسی شود؛ نتیجه docs/stage11/verification.json — بسته T29؛ FR-017 FR-022 SC-004 SC-005 FR-025 SC-009.
- [ ] T072 اجرای تمام سفرهای مصوب و مقایسه تصویری/موبایل/حرکت در tests/browser/؛ ثبت اختلاف و پذیرش انسانی در docs/stage11/acceptance.md؛ baseline بدون دلیل عوض نشود — بسته T06 T28 T29؛ FR-015 FR-019 FR-022 SC-003 SC-006.
- [ ] T073 بازبینی spec/plan/tasks/checklist و analyze/converge، گزارش نتیجه/محدودیت/قدم بعد در docs/stage-status.json و docs/stage11/report.md؛ انتشار و هر مرحله بعد منتظر دستور کاربر — بسته T01 T29؛ FR-020 FR-022 SC-001 SC-002.

## وابستگی و اجرای مستقل

Setup → Foundation → US05 هویت → US02 انتشار → US01 کشف → US03 پرونده. در S07 شاخه مقایسه US01 و فضای شخصی US05 و گزارش US06 تکمیل می‌شوند؛ S08 خدمات US06؛ سپس S09 دستیار US04 و در انتها S10/S11. پوسته US06 از S04 آغاز می‌شود؛ ترتیب سطرهای داستان به معنی تقدم تمام آن داستان بر همهٔ داستان‌های بعدی نیست. `stage` مرجع زمان اجراست.

اجرای موازی پس از قرارداد مشترک: US05 تست workspace و طراحی اعلان در فایل‌های جدا؛ US02 طراحی پنل و تست publication؛ US01 تست comparison و طراحی جدول؛ US03 طراحی پرونده و تست مجوز؛ US06 جریان‌های زمین/بین‌المللی/نوسازی با schemaهای مستقل؛ US04 ارزیابی فارسی و طراحی UI خطا. هیچ سطر با [P] علامت نخورده چون هنوز قراردادهای این پیش‌نیازها نهایی نشده‌اند. بعد از نهایی‌شدن، استقلال فایل/داده دوباره سنجیده شود.

## روش اجرا و پایان هر گام

تسک‌های آزمون هر قابلیت قبل از پیاده‌سازی اجرا/ناموفق‌بودن اولیه‌شان ثبت شوند؛ سپس همان سناریوها پس از کد سبز شوند. نام فایل آزمون به معنی آزمون انجام‌شده نیست. اولین سفر کامل S06 تحویل می‌شود؛ خدمات و AI از نسخهٔ کامل حذف نمی‌شوند. در شروع هر مرحله فقط تسک‌های همان مرحله و پیش‌نیاز کامل انتخاب شوند؛ spec تفصیلی/plan/checklist/analyze تازه، سپس اجرا در دامنهٔ دستور همان مرحله؛ پیش از رفع مانع، اجرا آغاز نشود. در پایان نتیجه و شواهد و گیت‌های باز و قدم بعد گزارش شود و توقف برای دستور بعدی.


## شواهد مأموریت PROGRAMMER-S03-01

T013–T016 با پیاده‌سازی و شواهد docs/stage3/report.md پوشش داده شدند. مسیر واقعی تست‌ها backend/tests/test_identity.py و test_identity_races.py و frontend/tests/browser/auth.spec.ts است؛ این نگاشت جای مسیر پیشنهادی قبلی را در تحویل حاضر می‌گیرد. adapter واقعی پیامک عمداً پیکربندی‌نشده و شکست صریح دارد؛ اتصال آن گیت S11 است. T017 با وجود سفر و تصاویر موفق، تا تأیید انسانی طراحی باز می‌ماند. T018–T021 به S07 و T041/T044 به اجرای واقعی S06 تعلق دارند و تکمیل علامت نخورده‌اند.

### ردیابی PROGRAMMER-S04-03 — T009/T011
هسته مقدار/واحد/تعریف فیلد namespace و نسخه‌دار، مدل/قرارداد و نگاشت محدود۸فیلد در specs/007-exact-values و docs/stage4/values-report.md اجرا شد. T009 از نظر مدل مشترک این بسته شاهد دارد؛ نگاشت همه فیلدها و شرط‌های مقصدهای آینده تکمیل نشده و تیک کل تسک حفظ می‌شود. بخش مرتبط T011 برای تبدیل دقیق/parser/ذخیره/واحد/بازده آزموده شد؛ پذیرش hidden-field در UI/سرور فرم‌های واقعی، گزارش snapshot خدمات و همهٔ DF/DR باقی است؛ T011 کامل علامت نمی‌خورد.


## ارجاع اجرای جاری — ممیزی ۲۰۲۶/۱۱/۱۹

این checkboxها شاخص تکمیل کل محصول نیستند؛ 009 و 010 شواهد اجرای دامنه‌دار را دارند. T001/T061/T068 به index ردیابی موجود و نگاشت‌های صاحب feature اشاره می‌کنند؛ فایل semantic-mapping.csv برنامه‌ریزی‌شده ساخته نشده و دیگر مرجعِ ظاهراً موجود معرفی نمی‌شود. T030 و مسیر matching-review آن همچنان کار داوریِ انجام‌نشده‌اند؛ اعداد فرمول با داوری کیفیت فرق دارند. بسته‌های باقی‌مانده در [roadmap](../../docs/02-delivery-roadmap.md)، یافته‌های مرزی در [ممیزی](../../docs/product-completion-audit.md) و وضعیت واقعی در [stage-status](../../docs/stage-status.json) ثبت‌اند؛ معیارها و تسک‌های چندمرحله‌ای برای سازگارکردن نتیجه تیک نخورده‌اند.
