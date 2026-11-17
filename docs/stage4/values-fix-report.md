# اصلاح PROGRAMMER-S04-04

**آماده بازآزمایی مستقل**؛ نسخه **S04-VALUES-FIX-82f03c66ac3b** روی http://127.0.0.1:3108. [نسخه و image کامل](values-fix-evidence/manifest.json). مرجع شکست: [TEST-S04-03](values-independent-test-report.md)، کامیت `54c5c81` و نسخه معیوب `S04-VALUES-41a4dee62c26`.

| ایراد | علت و اصلاح |
|---|---|
| IT-001 | `check_ref` فقط نوع/تهی‌بودن رشته را می‌سنجید؛ NUL به lookup و driver می‌رسید. متن قرارداد پیش از lookup رد می‌شود؛ code=`nul_not_allowed`، پیام فارسی و مسیر دقیق فیلد. مسیر واحد افق، source و start_basis نیز پوشش دارند؛ Unicode نامعتبر که driver/renderer را می‌شکند هم رد می‌شود. حذف NUL یا catch عمومی خطاهای سرور انجام نشد. ورودی معتبر و normalize بدون ذخیره حفظ‌اند. |
| IT-002 | guard۰۰۰۳ فقط نوع/واحد/عدد و `return_type` را می‌سنجید؛ Model.clean در QuerySet/SQL فراخوانی نمی‌شد. migration افزایشی **۰۰۰۴** guard مستقل basis را برای INSERT/UPDATE اضافه کرد: کلیدهای دقیق، نوع اعضا، enum/نسخه، واحد افق موجود، افق مثبت canonical و دقیق، تاریخ Gregorian معتبر و منبع غیرخالی. پول و مقدار غیرمدت فقط null؛ مدت در تمام وضعیت‌ها start_basis معتبر می‌خواهد؛ Return غیرknown، null یا مبنای کامل معتبر می‌پذیرد و known بدون مبنای کامل ذخیره نمی‌شود. SQL NULL/JSON null صریح‌اند؛ نتیجه‌ای جز TRUE رد می‌شود. |

migrationهای تحویل‌شده **۰۰۰۱ تا۰۰۰۳ تغییر نکردند**. audit پیش از اعمال، هر سه جدول مقدار را خالی و بدون ناسازگاری یافت؛ [قبل](values-fix-evidence/audit-before.json). migration خودش نیز preflight تراکنشی دارد و در وجود داده ناسازگار متوقف می‌شود، بدون حذف یا اصلاح معنای داده. اعمال محلی موفق شد؛ [log](values-fix-evidence/migrate-live.txt). hash تمام ردیف‌های **۱۹ جدول catalog/identity** قبل و بعد برابر است؛ [بعد](values-fix-evidence/audit-after.json). rollback، درج داده نامعتبر و شکست atomic migration فقط روی PostgreSQL آزمون با نام `test_*` بررسی شدند؛ داده fixture ناسازگار در شکست migration باقی ماند و نصب نیمه‌کاره نشد.

| اجرا روی نسخه نهایی | نتیجه |
|---|---|
| شش بازتولید مستقل روی نسخه معیوب | همان۶شکست؛ [شاهد حفظ‌شده](values-fix-evidence/reproduction.txt) |
| `… run --rm test /app/.venv/bin/pytest -q tests/test_values.py tests/test_catalog.py tests/test_contract.py --tb=short` | **۱۰۶ موفق،۳٫۸۱ثانیه**؛ [خروجی](values-fix-evidence/related-final.txt) |
| `… run --rm -v "$PWD/docs/stage4/values-independent-tests:/independent:ro" test /app/.venv/bin/pytest -c /app/pyproject.toml /independent/test_values_independent.py -q --tb=short` | **۵۳ موفق،۷٫۴۷ثانیه**، همان assertionهای مستقل بدون تغییر؛ [خروجی](values-fix-evidence/independent-final.txt) |
| `… run --rm test /app/.venv/bin/pytest -q tests/test_values_fixes.py --tb=short` | **۲۲۹ موفق،۲٫۰۳ثانیه**؛ ساختار/عضو/نسخه/تاریخ/حدود، INSERT و UPDATE منفی و مثبت، هر دو null، unknown/not_applicable، update کامل و rollback؛ [خروجی](values-fix-evidence/new-tests-final.txt) |
| Ruff check/format و `makemigrations --check --dry-run` | موفق، بدون drift؛ [کیفیت](values-fix-evidence/quality-final.txt)، [format](values-fix-evidence/format-final.txt)، [migration](values-fix-evidence/migration-check.txt) |
| `docker compose --env-file .env -f deploy/compose.yaml build backend test` | یک build نهایی، بدون نصب؛ [خروجی](values-fix-evidence/build.txt) |
| endpoint روی image فعال | ورودی معتبر۲۰۰ با `1500000000`؛ هر۳NUL برابر۴۰۰ با پیام/fields درست؛ [HTTP](values-fix-evidence/runtime-http.json)، [hash فایل اجراشده](values-fix-evidence/runtime.json) |

پیشوند `…` همان `docker compose --env-file .env -f deploy/compose.yaml` است. مجموعه۱۰۶تایی و۵۳تایی هرکدام یک بار پس از تثبیت اصلاح اجرا شدند؛ آزمون‌های مقدماتی با source mount و ابزار موجود بودند. اجرای ابزار مستقل توسط برنامه‌نویس، **پذیرش مستقل اصلاحات نیست**.

فایل‌های کد: `backend/apps/catalog/values.py`، migration جدید `0004_basis_integrity.py` و `backend/tests/test_values_fixes.py`. spec/plan/data-model/contracts/tasks/checklist فقط در بسته موجود007 اصلاح شدند؛ feature جدید ساخته نشد. بازبینی سازگاری، FR-009/010 و SC-004 را به T011..013 و شواهد نگاشت کرد؛ تعارض دامنه یا کار مجاز جامانده یافت نشد.

زمان دیواری: آماده‌سازی **563.42ثانیه**، build **40.32ثانیه**، آزمون/اجرای محلی **114.49ثانیه**، گزارش تا ثبت شاهد **280.43ثانیه**؛ [تفکیک](values-fix-evidence/timing.json).

فرانت/image آن، OTP، env، داده قبلی و گزارش‌ها/ابزار/شواهد تاریخی حفظ شدند. تست مرورگر/OTP و build فرانت تکرار نشد. حد تضمین، نوشتن عادی SQL با triggerهای نصب‌شده است؛ حذف guard با اختیار مالک DB یا TRUNCATE معیار این قرارداد نیست. فرم‌های پنهان آینده و S05 خارج از دامنه‌اند. پذیرش مستقل اصلاحات، تأیید انسانی و پایان کل S04 باز است. پس از بررسی diff، فقط فایل‌های این مأموریت محلی کامیت می‌شوند؛ hash در تحویل نهایی می‌آید، push انجام نمی‌شود.

در logهای تازه فقط فاصله انتهای سطر و سطر خالی انتهایی حذف شد؛ محتوای آزمون‌ها و شواهد تاریخی تغییر نکرد.
