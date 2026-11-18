# PROGRAMMER-S05-A1-FIX-01

تاریخ: ۲۰۲۶/۱۱/۱۸؛ وضعیت: **آماده بازآزمایی مستقل**. ایراد: **S05-A1-IT-001**.
مبنا `deceb34`، گزارش تستر `429ece8`؛ نسخه اصلاح **S05-A1-FIX-01-e7cd7767f27f**. [manifest و شناسه کامل imageها](a1-fix-evidence/manifest.json).

## علت و اصلاح محدود

روی PostgreSQL واقعی، DELETE تعریف دارای FK ابتدا معوق، رویداد constraint را تا پایان تراکنش نگه می‌داشت؛ `ALTER TABLE ... ENABLE TRIGGER` با `pending trigger events` و SQLSTATE55006 شکست می‌خورد. [آزمون مستقل اولیه](a1-fix-evidence/reproduction.txt) شکست0006 را بازتولید کرد؛ [بازتولید مستقل تابع reverse0005](a1-fix-evidence/reproduction-0005.txt) همان خطا را در تراکنش آزمون تأیید کرد (pass آن فایل یعنی مشاهدهٔ خطای مورد انتظار).

فقط `unseed` و import لازم در migrationهای `0005_project_fields.py` و `0006_project_capacity_units.py` تغییر کردند؛ این استثنا صریحاً در مأموریت مجاز بود. پیش از تغییر triggerها، `SET CONSTRAINTS ALL IMMEDIATE` بررسی‌های معوق را اجرا و حذف‌های بعدی را در **همان تراکنش migration** بررسی می‌کند. پایان تراکنش، mode پیش‌فرض را برمی‌گرداند؛ حالت deferred به‌صورت سراسری تغییر نمی‌کند. [مبنای رسمی PostgreSQL17](https://www.postgresql.org/docs/17/sql-set-constraints.html).

FK/PROTECT دست‌نخورده‌اند؛ ارجاع واحد در `allowed_units` تعریف‌های باقی‌مانده نیز با `ProtectedError` مانع حذف می‌شود. exception بلعیده، consumer حذف یا cascade/fake استفاده نشده است. در موفقیت guardها دوباره فعال می‌شوند؛ در شکست، تراکنش داده و DDL همان migration را برمی‌گرداند. آزمون جدا نشان داد موفقیت0006 با شکست بعدی0005 عقب نمی‌گردد؛ اتمیک‌بودن کل زنجیره ادعا نمی‌شود.

**forward، ثابت‌های FIELDS/UNITS، عملیات migration، شناسه و معنای تعریف‌های قبلی تغییر نکردند**؛ [مقایسه AST](a1-fix-evidence/forward-preservation.json). migration تازه ساخته نشد و روی DB فعال هیچ migrate یا rollback اجرا نشد.

## شواهد تازه

| بررسی | نتیجه و شاهد |
| --- | --- |
| مستقل، assertionهای اصلی دست‌نخورده | **۱موفق،۱٫۰۴ثانیه**؛ [independent-retest](a1-fix-evidence/independent-retest.txt) |
| catalog/value و reverse | **۳۳۱موفق،۱۵٫۵۳ثانیه**؛ شامل۱۶آزمون تکمیلی؛ [related-tests](a1-fix-evidence/related-tests.txt) |
| کیفیت فایل‌های متأثر | Ruff موفق؛ [quality](a1-fix-evidence/quality.txt) |
| build | backend وtest پس از تثبیت اصلاح یک بار ساخته شدند، حدود۲٫۲ثانیه با cache موجود؛ [build](a1-fix-evidence/build.txt) |
| تطبیق و حفظ داده | کد هر دو image با فایل‌های تحویل برابر؛ تمام۳۰جدول قبلی، guardها و migration record و env بدون تغییر؛ [preservation](a1-fix-evidence/preservation.json) |
| اجرای محلی | فقط backend با image تازه جایگزین شد؛ health موفق؛ [health](a1-fix-evidence/health.json). image فرانت/scanner/jobs حفظ شد. |

آزمون‌های تکمیلی در `backend/tests/test_catalog_reverse.py`: reverse/forward مستقل0005 و0006، چرخه6→5→4→6، حفظ تمام ردیف‌های قدیمی تعریف/واحد و سه نوع مقدار، مصرف‌کننده واقعی MoneyValue/Quantity، FK دیتابیس خارج ORM، مصرف واحد از default و allowed_units، بازگشت حذف‌های انجام‌شده پس از شکست، mode FK پس از موفقیت/شکست، guardهای فعال و رد UPDATE عادی، و همخوانی schema با ثبت هر migration. همه عملیات مخرب با کنترل `INVEST_ENV=test` و نام `test_` انجام شدند.

اجرای ترکیبی نخست، آزمون مستقل را پس از flush آزمون‌های تراکنشی قرار داد و seed آن در دسترس نبود؛ [شاهد ابزار](a1-fix-evidence/combined-ordering-fixture.txt) حفظ شد. آزمون مستقل در session تازه و مجموعه مرتبط جدا اجرا شدند؛ هیچ assertion تغییر نکرد. جمع نهایی **۳۳۲آزمون یکتای موفق** است. اجرای تاریخی۴۴۶مورد، مرورگر، scanner و OTP دوباره اجرا یا در این شمار محاسبه نشدند.

## بازتولید و فایل‌ها

از ریشه با env موجود و image test همین تحویل (خود pytest فقط DB آزمون می‌سازد):

```bash
docker compose --env-file .env -f deploy/compose.yaml run --rm -v "$PWD/docs/stage5/a1-independent-tests:/independent:ro" test /app/.venv/bin/pytest -c /app/pyproject.toml /independent/test_gaps.py::test_incremental_catalog_migrations_preserve_v1_definitions -q --tb=short
docker compose --env-file .env -f deploy/compose.yaml run --rm test /app/.venv/bin/pytest -q tests/test_catalog.py tests/test_values.py tests/test_values_fixes.py tests/test_catalog_reverse.py --tb=short
```

فایل‌های کد فقط همان دو reverse و تست تکمیلی‌اند. اسناد feature008 شامل spec/plan/tasks/checklist/analysis به‌اندازه FR010 و T015–018 تکمیل و وضعیت همین اصلاح در stage-status ثبت شد. شواهد قدیمی و فایل‌های تستر حفظ شدند؛ بازنویسی spec/plan محصول یا ساخت feature تازه انجام نشد.

## زمان و محدودیت‌ها

مطالعه اولیه پیش از marker جدا آغاز شد و مدت دقیق آن ثبت نشده است؛ این محدودیت اندازه‌گیری پنهان نمی‌شود. از marker۱۰:۵۸:۳۷ تا تثبیت۱۱:۰۳:۰۸UTC، آماده‌سازی/بازتولید/ساخت آزمون و اصلاح۴دقیقه۳۱ثانیه ثبت شد. build حدود۲٫۲ثانیه؛ اجرای نهایی مستقل+مرتبط۱۶٫۶ثانیه، جدا از بازتولید و عیب‌یابی fixture. تهیه گزارش/manifest و تطبیق از حدود۱۱:۰۵UTC تا timestamp manifest انجام شد. ریز timestampها در manifest است.

پذیرش مستقل اصلاح، تأیید انسانی و پایان A1/S05 باز می‌مانند. تکمیل پذیرش منبع/شرط تمام فیلدها و پاسخ خصوصی دیررس پس از تغییر حساب، محدودیت مأموریت بعدی تستر است و در این اصلاح باگ اثبات‌شده فرض نشده است. push، انتشار و A2/B/C انجام نشدند. قدم بعد: **بازآزمایی مستقل همین اصلاح**؛ پس از تحویل توقف.
