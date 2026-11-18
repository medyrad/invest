# TEST-CORE-FIX-01

**قبول فنی تجمیعی در دامنه هسته.** هر سه ایراد CORE-IT-001/002/003 رفع‌شده‌اند؛ regression ضروری CSRF/نشست نیز موفق است. مانع فنی بازِ گزارش قبلی در دامنهٔ این اصلاح مشاهده نشد. تأیید انسانی طراحی، ارزیابی کیفی محصول برای D28 و گیت‌های داده واقعی/عرضه مستقل و باز می‌مانند.

## نسخه و محیط

نسخهٔ هدف `CORE-443ca1cbf0c7`، تحویل `f0c1194` و پیاده‌سازی8b9dbc2/178e555؛ HEAD شروع `39a5c90` حاوی دستور بازآزمایی بود. hash تجمیعی کد مستقلاً بازحساب و با manifest برابر شد؛ تمام artifactهای manifest و endpointهای `/core-version.json` و `/api/v1/core/version` تطبیق دارند. [fingerprint](retest-01-evidence/fingerprint.json).

imageهای موجود backend=`sha256:ffe2286c5618bd01e69dd635caa6c21c37eb0500b37d42ff1f618fa6e1e08b2d`، web=`sha256:60a033b6edff7403739a728eb490679811fb7c70206f2fdb7acd6b81a039def6` و test=`sha256:72c01834d0eadb3681c42139d9bbad2cec33f1d6364d09b1df3b2fad5ff014f1` با manifest برابرند. rebuild یا نصب انجام نشد. [imageها](retest-01-evidence/version.json).

## وضعیت اصلاح‌ها

| مورد | نتیجه مستقل |
|---|---|
| CORE-IT-001 | بازتولید object/list در important و اعضای هم‌خانواده، preferences تو‌در‌تو و مقایسه با شناسه بدشکل در HTTP واقعی کنترل‌شده۴۰۰ شدند؛ پیام فارسی و مسیر فیلد برای معیارهای جست‌وجو بررسی شد. important خالی و نمونه معتبر۲۰۰ هستند. **۱۱ probe تازه موفق**؛ [HTTP](retest-01-evidence/http.json). هشت assertion مستقل تاریخی، از جمله محاسبهٔ مستقل score50/coverage75 برای سه نوع، در همان مجموعه۳۰۶تایی موفق شدند؛ دوباره به شمار اضافه نشده‌اند. catch عمومی جای اعتبارسنجی ننشسته است. |
| CORE-IT-003 | UI با واحد خالی آغاز شد؛۱۸٫۵ روز فارسی با مبنای تحویل کارگاه ذخیره، reload و ادامه، تغییر مسیر/بازگشت، ارسال، تأیید، جزئیات و گزارش ثابت را گذراند. ماتریس DAY/MONTH/YEAR، صفر/unknown/not_applicable، رد واحد/مبنای نادرست، ذخیره ناقص و منع ارسال ناقص، خام خصوصی و حذف inactive از snapshot در suite موفق‌اند. دوره با بودجه/IRR/بازگشت ادغام نشده است. [سفر واقعی](retest-01-evidence/operator-journey.json)، [مرورگر](retest-01-evidence/browser.txt). |
| migration/guard | آزمون consumer و rollback ردشده با حفظ Quantity و guard در مجموعه مرتبط موفق؛ مستقل، reverse0010→0009 و forward0010 بدون مصرف‌کننده جدید اجرا و **تمام تعریف‌ها/واحدهای قدیمی و مقدار پول/مساحت/IRR قبلی** بعد از خواندن مجدد برابر ماندند. [۱آزمون مستقل موفق](retest-01-evidence/migration-independent.txt). hash قبل/بعد migration برنامه‌نویس خوانده و برابری آن بررسی شد؛ اندازه‌گیری مستقل خودم معرفی نشده است. MONTH فقط anchor تعریف است؛ UI انتخاب خالی و ورود صریح واحد را آزموده، داده قدیمی تبدیل نشده است. |
| CORE-IT-002 | پروژه چهار گروه و ترتیب «پول، زمان، ریسک و حقوق، پروژه و محل» را دارد؛ صندوق چهار گروه متناسب و فروش سه گروه بدون زمان ساختگی.۲/۳/۴هم‌نوع، افزودن/حذف، تفاوت‌ها، پیوند گروه و keyboard در۱۴۴۰/۳۹۰ موفق؛ عضویت ردیف‌های API و DOM تطبیق داده شد. منبع واقعی src/lib/compare.ts و تصاویر هم‌عنوان/هم‌عدد مرجع و محصولِ تحویل بازبینی شدند؛ تصاویر تازهٔ پروژه۳۹۰ و فروش۱۴۴۰ نیز مستقیم مشاهده شدند. نبود منحنی فرضی بازگشت/زمانِ بدون مبنا مطابق D29 است، نه حذف تصادفی نمودار. |

شاهد تصویری هم‌دادهٔ تحویل: [مرجع](fix-01-evidence/reference-1440.png)، [محصول اصلاح‌شده](fix-01-evidence/product-after-1440.png). این دو تصویر تاریخیِ همین تحویل‌اند؛ بازبینی آن‌ها تازه است ولی تولیدشان اجرای من شمرده نشده است. [تصویر تازهٔ موبایل](retest-01-evidence/compare-project-390.png) و [فروش دسکتاپ](retest-01-evidence/compare-sale-1440.png). گروه‌بندی فنی بازگشته است؛ اختلاف اندازه/چینش کارت‌ها و پنل دستیار و اطلاعاتِ واقعاً نامعلوم با تطابق کامل پیکسلی یا تأیید انسانی یکی نیست.

## regression اجباری CSRF و نشست

کد core-api و reference-shell خوانده شد: فقط bootstrap درحال‌اجرا مشترک و سپس پاک می‌شود؛ بعد از جغرافیا بار لغوشده متوقف می‌شود. سه سناریوی مقایسهٔ موجود با bootstrap کند۲۰۰ms بدون خطای API گذشتند. regression فضای شخصیِ منتخب/شرایط/گزارش ثابت/خروج نیز موفق بود.

برای خلأ هم‌زمانی/گردش token، ابزار مستقل [csrf.cjs](retest-01-tests/csrf.cjs) **کد واقعی core-api.ts** را با TypeScript موجود برای اجرای مرورگر آماده کرد؛ fetch واقعی و پاسخ واقعی سرور استفاده شد. پاسخ bootstrap با gate رخدادی نگه داشته شد: دو مقایسه هم‌زمان فقط **یک bootstrap و دو POST موفق** داشتند؛ پیش از آزادسازی هیچ POST ارسال نشد. ورود واقعی آزمایشی از UI و سپس خروج کامل شد؛ هر بار مقایسه bootstrap تازه گرفت. POST بدون token در سرور **۴۰۳** شد. token/cookie/OTP ثبت نشده‌اند. [نتیجه](retest-01-evidence/csrf-independent.json).

ابزار مستقل [cancel.cjs](retest-01-tests/cancel.cjs) تمام پاسخ‌های واقعی جغرافیای بار مقایسه را نگه داشت؛ پس از خروج SPA از مقایسه و ناپدیدشدن وضعیت بارگذاری، پاسخ‌ها آزاد شدند. **صفر POST جدید مقایسه** ارسال شد و مسیر خانه باقی ماند. [نتیجه](retest-01-evidence/cancel.json). این بررسی رخدادی است، نه انتظار ثابت دلخواه؛ دو frame برای تکمیل commit رابط طی شد.

## فرمان‌ها و شمار تازه

با پیشوند `docker compose --env-file .env -f deploy/compose.yaml`:

`run --rm --no-deps -v "$PWD/docs/core-delivery/independent-tests:/independent:ro" test /app/.venv/bin/pytest -q tests/test_core.py tests/test_workspace.py tests/test_workspace_required.py tests/test_workspace_acceptance.py tests/test_values.py /independent/test_gaps.py --tb=short`

**۳۰۶ موفق،۱۵٫۱۰ثانیه؛ یک اجرا.** [خروجی](retest-01-evidence/backend.txt). سپس مستقل، در DB مشترک به‌صورت ترتیبی: `run --rm --no-deps -v "$PWD/docs/core-delivery/retest-01-tests:/independent:ro" test /app/.venv/bin/pytest -c /app/pyproject.toml /independent/test_migration.py -q --tb=short`: **۱موفق،۱٫۳۹ثانیه**.

Node/Playwright موجود: config کپی‌شدهٔ محدود `fix.cjs` با فقط import/مسیر شواهد تازه برای `core-fix-01.spec.ts`: **۴موفق،۳۱٫۲ثانیه**؛ config `personal.cjs` با grep=`personal saved`: **۱موفق،۵٫۸ثانیه**. [اصلاحات](retest-01-evidence/browser.txt)، [نشست/فضای شخصی](retest-01-evidence/personal.txt). assertionهای موجود و تاریخی تغییر نکردند. فقط config/مسیر خروجی در `.tools/test-core-fix-01` تطبیق یافت.

جمع: **۳۰۷ مورد یکتای pytest و۵سناریوی یکتای Playwright موفق**؛ دو probe مستقل مرورگر و۱۱probe HTTP جدا هستند. مجموعه‌های اصلی هرکدام فقط یک بار اجرا شدند؛ زیرمجموعهٔ مستقل تاریخی داخل۳۰۶ دوباره شمرده نشده است. suite۶۲۸/تمام سفرهای قبلی و scanner تکرار نشدند.

دو شروع ابزار CSRF به‌علت تبدیل export و baseURL، پیش از آزمون رفتار متوقف شدند. سه تلاش ابزار لغو، به‌دلیل شمردن درخواست پیش از لغو/آزادبودن بار موازی، انتظار نادرست داشتند؛ ابزار نهایی تمام بارهای مربوط را واقعاً نگه داشت و نتیجه موفق شد. logها جدا حفظ‌اند؛ این خطاهای harness با شکست محصول مخلوط نشده‌اند. assertion نهایی همچنان نبود POST تازه پس از لغو کامل را الزام می‌کند.

## پذیرش، محدودیت و تحویل

[TEST-CORE-COMPLETE](independent-test-report.md) شواهد معتبر سفرهای انتشار/نمایندگی، رضایت/پرونده، کشف/منتخب و migration قدیمی را دارد؛ این نتایج **تاریخی** هستند. سه مانع آن با همین بررسی رفع شده‌اند و regression تغییرات تازه نیز موفق است؛ بنابراین **پذیرش فنی تجمیعی هسته** قابل اعلام است. رجیستری و پرچم پذیرش تغییر نکردند. تناسب کیفی D28 باید توسط محصول/کارشناس سنجیده شود؛ منابع بیرونی/SMS، داده واقعی، retention/backup و S08–S11 همچنان گیت‌های خود را دارند.

مقایسه پیکسلی همه حالت‌ها، تأیید انسانی و تست بار عرضه اجرا نشده‌اند. تغییر حالت public، قطع scanner یا rollback روی DB فعال انجام نشد؛ migration فقط PostgreSQL با نام test_ و کنترل محیط آزمون بود؛ UI فقط داده مصنوعی استفاده کرد. [حفظ فایل‌ها/env](retest-01-evidence/preservation.json) و [تفکیک زمان](retest-01-evidence/timing.json) ثبت شده است. فقط فاصله انتهای سطر logهای تازه حذف شد.

طبق دستور تازهٔ کاربر، فقط گزارش/ابزار/شواهد مستقل پس از بررسی diff کامیت و push معمول origin روی شاخه جاری انجام می‌شود؛ نتیجه واقعی push و hash در پاسخ نهایی گزارش خواهد شد. force push/انتشار عمومی مجاز یا انجام‌شده نیست. قدم بعد پیشنهادی: تصمیم هماهنگ‌کننده و بازبینی انسانی طراحی؛ پس از تحویل توقف.
