# آزمون مستقل TEST-S04-03

**نتیجه: نیازمند اصلاح.** تبدیل دقیق و نگاشت محدود D29 قبول است؛ دو ایراد مشاهده‌شده در خطای HTTP و یکپارچگی مبنا باقی است. این گزارش پذیرش فیلدهای پنهان آینده، تأیید انسانی طراحی یا پایان S04 نیست.

## نسخه و محیط

کد تحویل `6169d8509fa560e54d3a5a3843d0a532f9bd373a`، نسخه `S04-VALUES-41a4dee62c26`. هر ۵۷ فایل source و ۲۹ artifact در manifest تطبیق داشتند. image فعال backend برابر `sha256:543b20fdab76f25c562266cfb9148cbdd88561b76638066d8f20b0abbe72a500` و image آزمون برابر `sha256:549ca8dbb00876fb8f92123ba9ceece5987cde0bf07affb57b83b0a0c25d300b` است؛ ۵۰ فایل Python داخل image آزمون نیز با workspace برابرند. image موجود استفاده شد؛ rebuild یا تغییر env انجام نشد. [نسخه و containerها](values-independent-evidence/version.json)، [تطبیق image آزمون](values-independent-evidence/test-image-source.json).

آزمون‌های نوشتنی فقط در PostgreSQL واقعیِ pytest با نام آغازشونده با `test_` انجام شدند؛ fixture پیش از هر آزمون این شرط را کنترل می‌کند. اجرای فعال `127.0.0.1:3108` فقط GET تعاریف و POST بدون ذخیره normalize دریافت کرد. هیچ rollback/reset روی DB برنامه اجرا نشد.

## پوشش و نتیجه

| محور | اجرای تازه و نتیجه |
|---|---|
| مبلغ دقیق | ۱٫۵ میلیارد/۱۵۰۰ میلیون، فارسی/عربی، صفر/unknown/not_applicable، مرز ۲۴+۹ و حاصل ضربِ واحد بزرگ در API و round-trip PostgreSQL موفق؛ number/float/bool، ابهام، بیش‌دقت و بیش‌ظرفیت رد شدند، بدون گردکردن. |
| یکپارچگی | جعل مقدار، source، عامل، واحد پایه، نسخه، وضعیت و FK با update مستقیم رد شد؛ UPDATE/DELETE تعریف منتشرشده حتی بدون مصرف‌کننده رد شد؛ افزودن نسخه جدید snapshot قبلی را تغییر نداد. سه bypass در basis باقی است: IT-002. |
| معنا/نگاشت | ارز مستقل، روز/ماه/سال مستقل، ITEM صحیح، جدایی حداقل ورود/کل سرمایه، IRR در برابر نرخ ساده و پنج اختلاف مبنای بازده موفق. هشت نگاشت با محل واقعی type/display مرجع و واحد GET تطبیق شد؛ اجاره ماهانه به ودیعه یا پرداخت یکجا تبدیل نشده؛ مبنای ناقص IRR مرجع جعل نشده است. [شاهد نگاشت](values-independent-evidence/mapping-review.json). |
| HTTP | GET نسخه `invest-values-v1` با ۱۱ واحد و ۸ فیلد؛ CSRF بدون token برابر ۴۰۳؛ JSON خراب/شکل نامعتبر برابر ۴۰۰؛ normalize هیچ رکوردی ننوشت. سه ref دارای NUL برابر ۵۰۰: IT-001، هم در image آزمون و هم اجرای فعال. [اجرای HTTP](values-independent-evidence/runtime-http.json). |
| migration | import مصنوعی و snapshot تمام ستون‌های تمام ردیف‌های ۱۱ گروه/۷۸ زیردسته/۳۱ استان/۴۷۸ شهرستان/۲۲ شهر؛ عقب‌بردن catalog تا 0001 و برگشت تا 0003، حفظ کامل همان ردیف‌ها، بازگشت ۱۱/۸ تعریف و ذخیره دقیق سقف مبلغ موفق. این آزمون تضمین حفظ رکوردهای تازهٔ مقدار هنگام rollback حذف‌کننده جدول‌ها نیست. |

## فرمان‌ها و شمار واقعی

پیشوند فرمان‌های container در همه موارد `docker compose --env-file .env -f deploy/compose.yaml` است؛ هیچ مقدار env در شواهد ثبت نشده است.

- `run --rm test /app/.venv/bin/pytest -q tests/test_values.py tests/test_catalog.py tests/test_contract.py --tb=short`: **۱۰۶ موفق، ۳٫۷۸ثانیه**؛ فقط یک اجرا. [خروجی تازه](values-independent-evidence/programmer-related.txt).
- `run --rm -v "$PWD/docs/stage4/values-independent-tests:/independent:ro" test /app/.venv/bin/pytest -c /app/pyproject.toml /independent/test_values_independent.py -q --tb=short`: ۵۳ مورد؛ اجرای اول ۴۱ موفق/۱۲ شکست در ۷٫۶۳ثانیه. شش شکست به fixture خود آزمون مربوط بود: label لازم برای FieldDefinition مصنوعی جا افتاده بود؛ کد محصول تغییر نکرد. [اجرای اول](values-independent-evidence/independent-tests.txt).
- همان فرمان فقط با `-k 'published_definitions or append_version or currency_calendar'`: پس از افزودن label، **۶ موفق، ۴۷ انتخاب‌نشده، ۱٫۱۹ثانیه**. هیچ assertion ضعیف نشد. [خروجی](values-independent-evidence/fixture-corrected-tests.txt).
- همان فرمان فقط با `-k queryset_cannot_persist_basis`: افزودن refresh برای اثبات ماندگاری SQL؛ **۳ شکست، ۵۰ انتخاب‌نشده، ۰٫۸۳ثانیه**. [شاهد ماندگاری](values-independent-evidence/basis-persistence.txt).
- `python3 docs/stage4/values-independent-tests/probe_runtime.py`: یک normalize صحیح ۲۰۰ و سه ورودی NUL برابر ۵۰۰ روی اجرای فعال؛ بدون ذخیره token/cookie در شاهد.

نتیجه نهایی **۱۵۹ مورد یکتا: ۱۵۳ موفق، ۶ ناموفق**؛ شش مورد ناموفق به دو ایراد زیر مربوط‌اند. تکرارهای هدفمند و چهار probe HTTP دوباره در این شمار حساب نشده‌اند. نتایج قدیمی گزارش برنامه‌نویس، اجرای تازه تلقی نشده‌اند. در فایل‌های log فقط فاصلهٔ انتهای سطر و سطر خالی انتهایی حذف شده است.

## ایرادهای مشاهده‌شده

### S04-VALUES-IT-001 — متوسط؛ ورودی نامعتبر باعث HTTP 500

اثر: مصرف‌کننده به‌جای خطای قابل اصلاح فیلد، خطای داخلی می‌بیند. هیچ افشای secret در پاسخ مشاهده نشد. منبع انتظار: قرارداد HTTP و FR-008؛ ورودی نامعتبر نباید ۵۰۰ شود.

پیش‌شرط: CSRF معتبر و payload معمول min_capital/BILLION_TOMAN، status=known، source_value رشته «۱٫۵»، basis=null. بازتولید: به یکی از `field.namespace`، `field.key` یا `unit.code` نویسه `\u0000` اضافه و به `/api/v1/catalog/values/normalize` POST کنید. انتظار: ۴۰۰ با envelope فارسی و fields؛ واقعیت: هر سه **۵۰۰**، روی نسخهٔ فعال نیز تأیید شد. شاهد: آزمون‌های `test_embedded_nul_reference_is_validation_error_not_http_500` و runtime-http.json. پیشنهاد بازگشت: هر سه محل به‌صورت پارامتری، بدون نوشتن DB و با کنترل code/message/fields؛ اصلاح لازم پیش از پذیرش این بسته.

### S04-VALUES-IT-002 — متوسط؛ bypass اعتبارسنجی مبنا در update مستقیم

اثر: نویسنده داخلیِ استفاده‌کننده از `QuerySet.update` می‌تواند رکوردی ذخیره کند که همان مدل در `full_clean` رد می‌کند؛ از جمله بازده known بدون افق/تاریخ/منبع. normalize عمومی این مسیر را ندارد و پذیرش مقایسهٔ نامعتبر از API مشاهده نشد. منبع: FR-005/006 و بخش موجودیت‌های data-model؛ این یک محدودیت مشاهده‌شدهٔ مرز SQL است، نه شکست constraints عددی.

پیش‌شرط: رکورد معتبر ساخته‌شده با `from_payload(...).save()` در DB آزمون. بازتولید: (۱) MoneyValue.basis را به `{"start_basis":"unexpected"}`، (۲) Quantity مدت را به null، یا (۳) ReturnMetric known با نوع irr را به `{"metric_type":"irr"}` با `objects.filter(pk=...).update(basis=...)` تغییر دهید. انتظار یکپارچگی مدل: مبنای نامعتبر ذخیره نشود؛ واقعیت: full_clean هر سه را رد می‌کند ولی UPDATE هر سه را ذخیره می‌کند و refresh همان مقدار نامعتبر را برمی‌گرداند. شاهد: `test_queryset_cannot_persist_basis_rejected_by_application` و basis-persistence.txt.

دقت دامنه: data-model ضمانت صریح SQL را به نوع/واحد/حدود و return_type محدود کرده است؛ بنابراین ادعای «تمام اعتبارسنجی برنامه در SQL تضمین شده» صحیح نیست. پیش از پذیرش، این شکاف باید تعیین تکلیف شود: یا کنترل مبنای معتبر در مسیر دورزننده افزوده شود، یا مرز قرارداد نویسندگان داخلی صریحاً محدود و تصمیم مربوط تأیید شود. پیشنهاد بازگشت: حفظ سه تست فعلی، همراه با موفقیت update مبنای کاملِ مجاز. این گزارش خودِ قرارداد مصوب را تغییر نمی‌دهد.

## محدودیت و تحویل

مرورگر، OTP، build فرانت، پیامک/provider واقعی، بار عرضه، فرم‌های S05 و اثر فیلد پنهان اجرا نشدند؛ خارج از مأموریت‌اند. مقایسه‌ها قرارداد داخلی زیرساخت‌اند، نه محاسبه IRR یا رتبه‌بندی مالی. تنها سه فایل مرتبط مرجع کاری برای هشت نگاشت بررسی شدند؛ نگاشت کامل خدمات ادعا نمی‌شود. آزمون superuser برای حذف trigger یا TRUNCATE خارج از قرارداد است.

فقط گزارش، دو ابزار مستقل و شواهد تازه در مسیرهای `values-independent-*` افزوده شدند؛ شواهد قبلی، قواعد و محصول دست‌نخورده‌اند. زمان دیواری آماده‌سازی ۲۱۲٫۳۱ثانیه، اجرا و پیگیری‌ها ۱۴۳٫۶۴ثانیه و تهیه گزارش تا ثبت شاهد ۴۷٫۳۷ثانیه است. جزئیات در [timing.json](values-independent-evidence/timing.json) جدا ثبت شده‌اند؛ آماده‌سازی از آغاز تثبیت نسخه محاسبه شده و اجرای مجموعهٔ مرتبط در این بازه هم‌پوشانی داشته است. بازهٔ اجرا شامل تکمیل سناریوها و بررسی نگاشت/HTTP است؛ زمان خود pytest جدا در بالا آمده است. build برابر صفر است.

قدم بعد فقط با دستور کاربر: تعیین تکلیف دو ایراد و بازآزمایی محدود اصلاحات. پس از ثبت گزارش و کامیت فایل‌های مستقل، کار متوقف می‌شود؛ مجوز عرضه یا پذیرش کل مرحله صادر نشده است.
