# TEST-S05-A1-01

**نتیجه: نیازمند اصلاح.** یک ایراد بازتولیدشده در rollback migration ظرفیت وجود دارد؛ سفرهای اجراشدهٔ پیش‌نویس، فایل و جداسازی حساب موفق بودند. این نتیجه پایان S05 یا تأیید انسانی طراحی نیست.

## نسخه و محیط

محصول `fd94de74c8f9018a1f8e954188f063be25b52b65`، نسخه `S05-A1-da7e008e04ec`؛ HEAD هنگام آزمون `2cf8993` فقط مأموریت آزمون را پس از تحویل اضافه کرده بود. دامنهٔ `d713876..fd94de7` شامل `b356582` بررسی و فهرست تغییرها ثبت شد: [دامنه](a1-independent-evidence/change-scope.txt). هر۲۳۵ فایل source و۳۴ artifact manifest برابر بودند.

backend و API مرورگر: `sha256:d42057283dfff7dd71883da06ffb72bf0727f3455c81e9f8fae8dede6c21096c`؛ web: `sha256:839124fa777595a20ec8337d80473acdc63f03fcb215b6b665dd0f9b22d21a60`. [نسخه و image آزمون جدید](a1-independent-evidence/version.json).

در شروع، DB/backend/web متوقف و API اختصاصی مرورگر غایب بود. کانتینرهای موجود invest شروع شدند؛ API مرورگر با همان image روی DB دارای پسوند `_browser` و `INVEST_ENV=test` بازسازی شد؛ هیچ reset یا migrate روی DB اصلی اجرا نشد. restart آزمون مرورگر فقط کانتینر `invest-a1-browser-api` را هدف گرفت. image قدیمی test فایل workspace نداشت و **هیچ آزمونی اجرا نکرد**؛ فقط image test به همین دلیل rebuild شد. محصول، env و سرویس پروژه‌های دیگر تغییر نکردند.

## اجرا و پوشش

| محور | شاهد تازه و نتیجه |
|---|---|
| حفظ پیش‌نویس | سفر واقعی UI ایجاد با پاسخ گم‌شده/کلید ثابت، ذخیره مبلغ دقیق، خواندن دستگاه دوم، حذف/بازیابی؛ تعارض دو تب و حفظ ورودی، انقضای نشست و تغییر حساب، restart API مصنوعی موفق. آزمون مستقل replay ذخیره، برابری رسید/نسخه و خواندن مجدد سرور و رد بدنهٔ متفاوت موفق. |
| اختیار جاری | مجموعهٔ PostgreSQL دو سازمان، pending/جانشین، لغو و فایل approved را پوشش داد. مستقل: hold، revoked و پایان اعتبار، دسترسی به restore و replay رسید حذف و فهرست trash را قطع کردند؛ چهار آزمون مستقل موفق. این‌ها اعطای نقش از مسیر عمومی نبودند. |
| شروط و مقادیر | suite شروط غیرفعال/بازگشت، fee میراث، صفر/نامعلوم/نامربوط، IRR ناقص و واحدهای ظرفیت را اجرا کرد؛ UI مسیر اجاره و میراث و جدایی ودیعه/اجاره را اجرا کرد. schema و renderer و active_keys با نگاشت بررسی شدند. تطبیق دستی تک‌تک ۶۹ ردیف با تمام محل‌های منبع و تمام حالات UI کامل انجام نشد؛ round-trip عمومی به‌تنهایی پذیرش کامل این محور نیست. |
| فایل و HTTP | scanner واقعی سالم/EICAR امن، قطعی اتصال آزمون، parser PDF فعال/رمزدار/پیوست، تصویر متحرک/بیش‌پیکسل، metadata، retry و جایگزینی در suite موفق؛ سفر proxy تصویر خصوصی clean را دریافت و خواند؛ آزمون انتقال۲۰MiB و بیش‌حد اجرا شد. قطعی scanner مشترک ایجاد نشد. |
| رقابت/نگهداری | تست‌های PostgreSQL اتصال واقعی برای ظرفیت/رزرو هم‌زمان، کلید یکسان/نسخه، ذخیره متن هنگام scan و purge، مرزهای۲۴ساعت/۷روز/۳۰روز و incident/reference موفق. مشاهدهٔ job فعال به‌تنهایی تضمین پایش بلندمدت نیست. |
| migration | ساخت DB pytest و forward migrationهای جاری موفق؛ rollback مستقل ظرفیت0006 شکست خورد: IT-001. به‌دلیل توقف در rollback، assertion مستقل مقایسهٔ تمام تعریف‌های قدیمی پس از رفت‌وبرگشت اجرا نشد. |
| UI | یک بررسی layout و keyboard در هر عرض۳۶۰/۳۹۰/۷۶۸/۱۴۴۰، پنج آزمون دسکتاپ و یک سفر۳۹۰ موفق؛ خانه/ناوبری smoke موفق. تصویر۳۶۰ نیز بصری بازبینی شد؛ تصاویر دیگر شاهد خودکار layout هستند، نه تأیید انسانی یا تطابق کامل تصویر مرجع. |

## فرمان‌ها و شمار واقعی

پیشوند backend: `docker compose --env-file .env -f deploy/compose.yaml`.

- `run --rm test /app/.venv/bin/pytest -q tests/test_catalog.py tests/test_values.py tests/test_values_fixes.py tests/test_workspace.py tests/test_workspace_files.py tests/test_workspace_acceptance.py tests/test_workspace_concurrency.py`: اجرای image قدیمی صفر مورد؛ پس از `build test` فقط یک اجرای واقعی: **۴۴۶ موفق،۱۳٫۷۵ثانیه**. [اجرای تازه](a1-independent-evidence/backend-current.txt)، [ناسازگاری قدیمی](a1-independent-evidence/backend.txt)، [build](a1-independent-evidence/test-build.txt).
- از frontend با Node قفل‌شده موجود: `node node_modules/@playwright/test/cli.js test -c playwright.workspace.config.ts` با `A1_RESTART=1` و مسیر خروجی تازه: **۵ موفق،۲۲٫۵ثانیه**؛ همان فرمان با `A1_WIDTH=390` و `--grep 'A1 journey'`: **۱ موفق،۱۰٫۲ثانیه**. [دسکتاپ](a1-independent-evidence/browser.txt)، [موبایل](a1-independent-evidence/browser-mobile.txt). شواهد screenshot تازه در همین پوشه‌اند؛ trace حاوی secrets ذخیره نشده است.
- `run --rm -v "$PWD/docs/stage5/a1-independent-tests:/independent:ro" test /app/.venv/bin/pytest -c /app/pyproject.toml /independent/test_gaps.py -q --tb=short`: یک شکست migration و چهار خطای fixture خود آزمون؛ fixture حسابِ موجود به‌علت مسیر بیرون tests کشف نمی‌شد. پس از import همان fixture، فقط چهار مورد اجرا‌نشده با `-k 'not incremental'` اجرا شدند: **۴ موفق،۰٫۷۶ثانیه**. هیچ assertion محصول یا مستقل ضعیف نشد. [شکست اولیه](a1-independent-evidence/gaps.txt)، [اصلاح ابزار](a1-independent-evidence/gaps-fixture-corrected.txt).

جمع نهایی pytest: **۴۵۱ مورد یکتا؛۴۵۰ موفق و۱ ناموفق**. مرورگر جدا: شش اجرا، پنج سناریوی یکتا؛ journey در دو عرض اجرا شد. نتایج تاریخی برنامه‌نویس در شمار اجرای تازه نیستند.

## S05-A1-IT-001 — متوسط؛ rollback ظرفیت0006 اجرا نمی‌شود

اثر: بازگرداندن نسخهٔ افزایشی در محیط نگهداری متوقف می‌شود؛ تخریب دادهٔ کاربر مشاهده نشد. انتظار: migration دارای reverse باید روی PostgreSQL بدون رکورد وابستهٔ جدید قابل برگشت باشد و تعاریف قدیمی را حفظ کند؛ مبنا مأموریت بخش۶ و reverse صریح migration تحویل.

پیش‌شرط: DB مصنوعی pytest با schema جاری، بدون DraftValue وابسته. بازتولید: `MigrationExecutor(connection).migrate([('catalog','0004_basis_integrity')])` در آزمون transaction=True. واقعیت: در `0006_project_capacity_units.unseed`، پس از حذف Field نسخه۲، دستور `ALTER TABLE catalog_fielddefinition ENABLE TRIGGER immutable_field` با `OperationalError: cannot ALTER TABLE ... because it has pending trigger events` شکست می‌خورد. این خطا پیش از رسیدن به reverse0005 رخ می‌دهد. شاهد: test_incremental_catalog_migrations_preserve_v1_definitions در gaps.txt. همان آزمون finally نسخه جاری را نگه می‌دارد؛ DB اصلی rollback نشد.

پیشنهاد بازگشت: اجرای reverse0006/0005 و forward مجدد روی DB آزمون خالی از مصرف‌کنندهٔ جدید، با مقایسهٔ تمام رکوردهای تعریف نسخه۱؛ در حالت دارای وابستگی، رد کنترل‌شده بدون حذف داده. کد محصول در این مأموریت اصلاح نشد.

## محدودیت و توقف

پوشش کامل دستی منبع/شرط تمام فیلدها، آزمون مستقل تازه برای همهٔ permutationهای رقابت، بازبینی بصری همه تصاویر با مرجع و آزمون تأخیر پاسخ خصوصی پس از تغییر حساب مستقل از suite موجود کامل انجام نشدند؛ قبولی آن‌ها ادعا نمی‌شود. این محدودیت‌ها با ایراد مشاهده‌شده مخلوط نشده‌اند. گیت‌های داده واقعی، نگهداری سوابق B، SMS واقعی، A2/B/C و عرضه خارج این آزمون‌اند.

زمان و محدودیت اندازه‌گیری در [timing](a1-independent-evidence/timing.json) ثبت است؛ مطالعهٔ اولیه پیش از marker جدا اندازه‌گیری نشد. [کنترل حفظ فایل‌های موجود](a1-independent-evidence/preservation.json). فقط گزارش/آزمون مستقل و شواهد تازه کامیت می‌شوند. قدم بعد با دستور کاربر: اصلاح IT-001 و بازآزمایی هدفمند به‌همراه تکمیل محدودیت‌های پذیرش؛ پایان کل S05 و تأیید انسانی باز می‌مانند. پس از گزارش توقف؛ push انجام نمی‌شود.
