# Tasks: 008-project-drafts — PROGRAMMER-S05-A1
Input: spec/plan/product و D30–32. تست‌ها صریحاً جزو مأموریت‌اند؛ checkbox فقط با شاهد.

## Phase 1: مشخصات و زیرساخت
- [ ] T001 منابع/قفل ابزار و نگاشت کامل در specs/008-project-drafts/ و تحلیل پیش‌کد؛ FR001–009.
- [ ] T002 تست‌های قرارداد/دسترسی/تکرار/نسخه در backend/tests/test_workspace.py قبل از service؛ US1/2.
- [ ] T003 مدل‌ها/migration افزایشی در backend/apps/workspace و catalog0005؛ PG و حفظ داده؛ US1/2/3.

## Phase 2: US1/US2 ذخیره و اختیار
- [ ] T004 service/api و config urls؛ current session/current permission، receipt و409؛ تست چندحساب/سلب اختیار؛ FR001/002.
- [ ] T005 UI فهرست/مالک/سازمان/رسید/تعارض در frontend/src/components/workspace و app/drafts؛ US1/2.

## Phase 3: US3 فرم پروژه
- [ ] T006 schema/validation، typed values و raw inactive/revision در backend/apps/workspace؛ همه ردیف‌های mapping؛ FR003/004.
- [ ] T007 widgetهای واحد/مبنا/شرط/نقص و بازگشت داده در UI؛ آزمون واقعی شروط/007؛ US3.

## Phase 4: US4 فایل خصوصی
- [ ] T008 tests file/quota/race/retention در backend/tests/test_workspace_files.py پیش از سرویس فایل.
- [ ] T009 reserve/stream/scan/derivative/download و retry/replace در backend/apps/workspace و compose؛ FR005/006.
- [ ] T010 حذف/بازیابی/purge و job زمان‌بندی‌شده با clock کنترل‌شده و رقابت ارجاع؛ FR007.
- [ ] T011 پنل فایل/سطل حذف/درخواست سازمان با status و errors؛ US4.

## Phase 5: تحویل
- [ ] T012 pytest PG و regression متأثر، scanner واقعی clean/infected/outage، مرورگر سفر/چهارعرض و حفظ خانه/ورود؛ docs/stage5/a1-evidence/.
- [ ] T013 کیفیت و build نهایی imageهای متأثر، migration واقعی/حفظ داده، اجرای قابل استفاده؛ manifest.
- [ ] T014 تحلیل پایان/converge، docs/stage5/a1-report.md و stage-status فقطA1، diff/کامیت محلی؛ بدونpush/A2/B/C.

وابستگی: T001→T002→T003→T004، T006 سپسT005/7؛ T008→T009→T010→T011؛ تمام مسیرها→T012→T013→T014. هیچ کار پایه چندمرحله‌ای با این تسک‌ها کامل اعلام نمی‌شود.
