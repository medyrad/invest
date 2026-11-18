# TEST-S05-A1-02

**نتیجه: نیازمند اصلاح.** ایراد rollback قبلی **S05-A1-IT-001 رفع‌شده** است؛ آزمون‌های پاسخ خصوصی دیررس موفق‌اند. تطبیق فیلدها یک اختلاف بازتولیدشده با الزام محصول نشان داد؛ بنابراین پذیرش کامل A1 صادر نمی‌شود. تأیید انسانی و پایان S04/S05 باز می‌مانند.

## نسخه و حفظ دامنه

محصول `e1d144393d9241a5df4182f183ccbd54863604b1`، نسخه `S05-A1-FIX-01-e7cd7767f27f`؛ HEAD هنگام شروع `07fae12` شامل دستور بازآزمایی بود. فایل‌های source و artifact موجود در manifest بدون اختلاف‌اند. backend فعال و API ایزوله مرورگر با image `sha256:7a65067546515afb593db3853d902621d0cfdf4cb7ef73170128670b6af80742` و test با `sha256:447b1fcda38f418fa9a9d0b550d663879764f8508a25ff334ee90964bc5e27c5` تطبیق دارند. [نسخه](a1-retest-evidence/version.json)، [forward/runtime](a1-retest-evidence/forward-runtime.json).

مقایسه AST هر دو migration با fd94de7، ثابت‌ها/forward/عملیات را پس از کنارگذاشتن import و unseed برابر یافت. اصلاح محصول به reverseها و تست مربوط محدود است؛ اضافه‌شدن شواهد مستقل قبلی در این بازه تغییر محصول محسوب نشد. API مرورگر قدیمی فقط در کانتینر اختصاصی و DB مصنوعی `_browser` با تنظیم test جایگزین شد؛ rebuild لازم نبود. DB فعال فقط SELECT برای migration record و guardها دریافت کرد؛ migrate/rollback فعال اجرا نشد.

## سه محور

| محور | نتیجه و شاهد |
|---|---|
| rollback/داده/guard | تست مستقل اصلی بدون تغییر assertion در session تازه **۱ موفق،۰٫۹۸ثانیه**؛ سپس فقط test_catalog_reverse.py **۱۶ موفق،۹٫۶۸ثانیه**. حفظ تمام تعریف‌های قدیمی و سه نوع مقدار وابسته، چرخه6→5→4 و forward، مصرف‌کننده FK واقعی و allowed_units، بازگشت داده/DDL همان migration پس از شکست، constraint mode و guard فعال/رد UPDATE پوشش دارند. اتمیک‌بودن کل زنجیره ادعا نمی‌شود؛ موفقیت0006 با شکست بعدی0005 می‌تواند باقی بماند. [اصل](a1-retest-evidence/original.txt)، [تکمیلی](a1-retest-evidence/reverse.txt). |
| فیلد و شرط | شاهد ردیفی **۶۹ مقصد** با source واقعی/معنا/واحد/شرط/الزام موجود/widget تهیه شد؛ sourceهای snake_case جعلی schema به‌عنوان شاهد منبع پذیرفته نشدند و symbol واقعی جدا ثبت شد. ۱۱ فرهنگ شرایط با کلید و برچسب و۶ فرهنگ مشترک با کد گزینه تطبیق دارند. پنج گروه مسیر در API خروج/بازگشت و تزریق inactive را موفق گذراندند. یک اختلاف الزام با assertion مستقل شکست خورد: IT-002. [ردیف‌ها](a1-retest-evidence/field-audit.csv)، [منابع و استثناها](a1-retest-evidence/source-review.json)، [گزینه‌ها](a1-retest-evidence/option-review.json)، [API](a1-retest-evidence/conditions-api.txt). |
| UI شروط | fixture نماینده واقعاً active و درخواست approved فقط در DB مرورگر مصنوعی ساخته شد. انتخاب مالک سازمان، پنج مسیر مشارکت/پیمان/خرید/اجاره/میراث، ذخیره unknown، خروج از شرط و بازگشت مقدار، fee میراث و بازگشت مدت بهره‌برداری موفق؛ بررسی جدولی هر۶۹widget و کنترل‌های واحد در UI واقعی موفق. [نماینده/شروط](a1-retest-evidence/conditions-ui-corrected.txt)، [widgetها](a1-retest-evidence/widgets.txt). |
| پاسخ خصوصی دیررس | شش حالت واقعی: GET فهرست، GET جزئیات ناشی از بازخوانی فایل و POST ذخیره × خروج تنها/ورود حساب B. route.fetch ابتدا پاسخ۲۰۰ واقعی حاوی عنوان A را از سرور گرفت؛ gate تا تکمیل خروج/ورود B و ذخیره انتخاب B بسته ماند. سپس همان پاسخ آزاد شد؛ عنوان، فرم، شناسه رسید و نام فایل A در نمای عمومی/B ظاهر نشد، ویرایش B حفظ شد؛ پس از reload و فهرست سرور نیز جداسازی برقرار بود. clock delay ثابت استفاده نشد؛ دو frame پس از تحویل برای ارزیابی DOM طی شد. [اجرای نهایی۶موفق،۱۱٫۲ثانیه](a1-retest-evidence/late-expanded.txt). |

مقابلهٔ منبع با بخش۳ محصول، موارد source بدون widget را نیز تفکیک کرد: id/publishedAt/expert/irrCashflowsVerified سیستمی‌اند؛ routes انتخابگر مستقل، image/guideFileUrl مسیر فایل خصوصی و usageLabel مشتق واژه‌نامه است. خرید/ودیعه از minCapital مرجع با **اختلاف مصوب D31** جدا شده‌اند. شهرستان افزودهٔ کاتالوگ است؛ شهر با آن یکی فرض نشده است. ادعای نگاشت A2/S08 یا اعتبارسنجی عددی IRR تازه نشده؛ شاهد قبلی معتبر A1 برای مبنای کامل IRR، درصد سهم و ظرفیت/واحدها **تاریخی** است و در شمار اجرای تازه نیست.

## S05-A1-IT-002 — متوسط؛ شناسه مدل قرارداد از نقص‌ها حذف شده

اثر کاربری: راهنمای تکمیل پیش‌نویس می‌تواند با نبود شناسه مدل قرارداد، تکمیل اطلاعات را بیش از قرارداد محصول نشان دهد. این ادعای انتشار یا آمادگی واقعی S05-B نیست.

انتظار مصوب: ردیف `stage, phase, model, modelId, owner, revenues` در بخش۳ product-s05-a، پذیرفته‌شده با D31، برای readiness صریح S+U دارد؛ draft ناقص مجاز است ولی نقص مدل قرارداد باید معلوم باشد. پیش‌شرط: حساب مجاز و پیش‌نویس تازه. بازتولید: create_draft با owner شخصی/schema_version1، سپس بررسی DTO.missing بدون ثبت model_id. واقعیت: `model_id` در missing نیست؛ schema مقدار required=false دارد؛ widget نیز آن را اختیاری نشان می‌دهد. آزمون `test_model_id_readiness_matches_product_table` در conditions-api.txt شکست را بازتولید می‌کند.

پیشنهاد اصلاح/بازگشت: هماهنگی required/missing و widget با قرارداد S+U؛ آزمون نبود، unknown/not_applicable صریح و مقدار معتبر، بدون اجبار تکمیل هنگام ایجاد draft. محصول در این مأموریت تغییر نکرد.

مورد نیازمند روشن‌سازی، نه انتظار اختراعی: جدول اصلی durationYears را O می‌نامد، اما جدول شروط اجاره از الزام شرط فعال صحبت می‌کند؛ schema آن را در تمام مسیرهای duration از جمله مشارکت required می‌کند. این اختلاف در شاهد ردیفی آمده؛ تفسیر قطعی تازه به‌جای محصول تصویب نشده است.

## فرمان‌ها، شمار و خطاهای ابزار

پیشوند backend: `docker compose --env-file .env -f deploy/compose.yaml`:

- `run --rm -v "$PWD/docs/stage5/a1-independent-tests:/independent:ro" test /app/.venv/bin/pytest -c /app/pyproject.toml /independent/test_gaps.py::test_incremental_catalog_migrations_preserve_v1_definitions -q --tb=short`
- `run --rm test /app/.venv/bin/pytest -q tests/test_catalog_reverse.py --tb=short`
- `run --rm -v "$PWD/docs/stage5/a1-retest-tests:/independent:ro" test /app/.venv/bin/pytest -c /app/pyproject.toml /independent/test_conditions.py -q --tb=short`: **۵ موفق،۱ناموفق،۰٫۸۷ثانیه**.
- Node قفل‌شده موجود و Playwright موجود با config اجرای مستقل `.tools/test-s05-a1-02/playwright.cjs` (نسخهٔ قابل بازتولید در `docs/stage5/a1-retest-tests/playwright.cjs`)، testDir ابزار تازه و baseURL3109؛ فرمان `node frontend/node_modules/@playwright/test/cli.js test -c …` با grepهای هدفمند `late (list|detail|save):`، `approved representative` و `all project widgets` اجرا شد.

جمع نهایی: **۲۳ مورد pytest یکتا،۲۲موفق/۱ناموفق؛۸سناریوی یکتای مرورگر همگی موفق**. ۴۴۶/۳۳۱ و scanner/EICAR و چهار عرض تکرار نشدند. سه حالت دیررسی logout به‌علت strict locator (چند عنصر مخفی) ابتدا خطای ابزار داشتند؛ انتخابگر به «تمام عناصر قابل مشاهده باید صفر باشند» اصلاح شد، حفظ ورودی مخفی همان حساب الزام پاک‌کردن پیدا نکرد. سناریوی سازمان ابتدا label حدسی داشت؛ فقط label با کنترل واقعی هماهنگ شد. یک شروع مرورگر به‌علت import و یک grep به‌علت انتخاب صفر مورد اجرا نشدند؛ یک شروع معطل به‌علت فرض درخواست GET در بازکردن کارت متوقف و با رخداد واقعی بازخوانی جایگزین شد. این‌ها باگ محصول یا موارد یکتای تازه نیستند. شش سناریو فقط برای افزودن assertion شناسه رسید/فایل و فرصت اعمال DOM دوباره اجرا شدند. در logهای تازه فقط فاصلهٔ انتهای سطر و سطر خالی انتهایی حذف شده است. logهای ابزار قبلی حفظ‌اند؛ هیچ assertion رفتاری حذف یا ضعیف نشده است.

## محدودیت و تحویل

واژه‌نامهٔ usage در منبع خوانده شد؛ تک‌تک گزینه‌های آن در آزمون تعامل مستقل کلیک نشدند. شاهد برابری ZIP همان ممیزی تاریخی PRODUCT-S05-01 است؛ شش فایل واقعی کپی مرجع در این مأموریت خوانده و hash تازه‌شان ثبت شد، استخراج ZIP دوباره اجرا نشد. مبنای کامل IRR/سهم/هم‌ارزی مبلغ و آزمون‌های scanner/رقابتِ بی‌تغییر از اجرای معتبر قبلی استفاده می‌کنند؛ اجرای تازه نامیده نشده‌اند. تأیید انسانی و نگهداری داده واقعی همچنان گیت جداست.

[زمان](a1-retest-evidence/timing.json) و [حفظ فایل‌ها/env](a1-retest-evidence/preservation.json) ثبت شده‌اند. فقط ابزار/گزارش/شواهد تازه کامیت می‌شوند؛ push و A2/B/C انجام نمی‌شود. قدم بعد با دستور کاربر: اصلاح IT-002 و تعیین تکلیف ابهام durationYears، سپس بازآزمایی محدود؛ پس از این گزارش توقف.
