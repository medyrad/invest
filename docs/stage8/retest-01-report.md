# گزارش بازآزمایی مستقل TEST-S08-FIX-01

نتیجه: **قبول فنی تجمیعی در دامنه S08**. هر شش یافته `S08-IT-001..006` در نسخهٔ هدف رفع شده‌اند و regression محدود مأموریت موفق است. این نتیجه تأیید انسانی طراحی، pixel-perfect کل محصول، داوری کیفی D28، production readiness، S09/F40 یا مجوز عرضه عمومی نیست.

## نسخه و محیط آزمون

- checkout: `/Users/mehdi/Projex/invest`، شاخه `main`، HEAD آغاز/اجرای مأموریت `b3c411570865026fb3c7ed540121d6dc4ecb49f3`.
- commit اصلاح محصول: `7c2632c7b7e487a8ad5406155cdf4c2027a1b518`؛ commit تحویل: `6328756c9cf25debe10c938d86d76fe7ec822134`.
- نسخهٔ هر دو endpoint فعال: `S08-FIX-01-e47b3701a586` در `http://127.0.0.1:3108`.
- BuildKit برای imageهای فعال revision `8ac58adb73e603eb96313d83ce6801229b60d0e8` را ثبت کرده است. از `7c2632c` تا این revision در `backend/`، `frontend/`، `deploy/` و `contracts/` هیچ تفاوتی نیست؛ commitهای بعدی فقط سند/validator برنامه‌اند.
- backend فعال: `sha256:6d89ce7d7ba975ce4246497b93596e2ae296eaa2cefb50e03209095843acff5a`. digest خروجی provenance، tag محلی و container فعال برابرند. همهٔ ۱۰۸ فایل `apps/` و `config/` داخل container byte-for-byte با checkout برابرند.
- web فعال: `sha256:d94025bdbfaaa9706cfd24b8d9d9dfdf868eeb078e324e184a19ebdb5c4e5c91`. digest خروجی provenance، tag و container فعال برابرند. `BUILD_ID=nOtT7Gffv1YsTdRUE1UcS`؛ hash مستقل تمام ۵۸۸ فایل `.next` با الگوریتم `SHA256(sorted(relative-path + NUL + bytes + NUL))` برابر `50c70e8762325de104bc35e82e68a7e2a41234797b08aaabe41d1f7b7786b1a9` است.
- PostgreSQL واقعی `17.12-alpine` روی میزبان `55433` بود. آزمون‌های Django فقط روی DB دارای پیشوند `test_` اجرا شدند؛ DB فعال reset، rollback، migrate یا seed نشد.
- hash imageها و BUILD_ID با manifest تاریخی متفاوت‌اند، اما buildهای تازهٔ ۱۹ نوامبر از revision بالا و همان کد محصول ساخته شده‌اند. برابری باینری با image تاریخی ادعا نمی‌شود و برای پذیرش این نسخه لازم نیست.

## نتیجهٔ هر یافته

### S08-IT-001 — قبول

- شدت/اثر سابق: زیاد؛ امکان دریافت HTML/ZIP خصوصی توسط نمایندهٔ قبلی پس از جانشینی.
- نیازمندی: D27، US2/US4، FR-003/008 و قرارداد اختیار جاری.
- انتظار: اگر جانشینی اول commit شود، نماینده قبلی 403/409 بگیرد؛ اگر دریافت اول شروع شود، قفل سازمان تا ساخت کامل بایت حفظ و writer واقعاً منتظر DB بماند. مسیر HTML، ZIP، JSON گزارش core و فایل مرتبط باید یک ترتیب اختیار داشته باشند.
- اجرای تازه: دو بازتولید HTTP تاریخی `download/package` بدون تغییر و سه حالت مکمل `HTML/ZIP/JSON` روی دو connection واقعی اجرا شدند. `pg_blocking_pids` انتظار writer را مشاهده کرد؛ timeout یا نخ ناتمام شاهد موفقیت شمرده نشد.
- نتیجهٔ واقعی: جانشینی زودتر دسترسی قبلی را رد کرد؛ دریافت زودتر writer را تا پایان ساخت بایت مرتب کرد و پس از commit، دریافت بعدی 403 شد. مسیر فایل و JSON در مجموعهٔ مرتبط نیز موفق بودند.
- شاهد: اجرای نهایی سه race تاریخی `3 passed in 21.67s`؛ اجرای مرتبط ۸۴تایی؛ منبع تست دست‌نخورده با SHA256=`67d78e80d78ae26ef416d8e4cdb80c7f01ed61fd8b8b02dd2a4e26210237521b`.
- آزمون بازگشت: حفظ `test_download_race.py` و تست‌های `test_download_holds_org_until_bytes_and_revoked_customer_is_rejected` برای هر سه خروجی.

### S08-IT-002 — قبول

- شدت/اثر سابق: زیاد؛ ورود فایل قرنطینه‌شده به ZIP و احتمال ترتیب قفل ناسازگار.
- نیازمندی: US2، FR-006/008 و قرارداد بستهٔ خصوصی.
- انتظار: `quarantined/pending_check/deleted` اگر زودتر commit شوند 409؛ اگر ساخت ZIP زودتر باشد writer تا کامل‌شدن archive منتظر بماند. قفل پس از موفقیت و خطا آزاد شود؛ فقط SQLSTATE `55P03` به 409 ترجمه شود.
- اجرای تازه: race تاریخی محتوای واقعی ZIP، مکمل `pg_blocking_pids`، هر سه وضعیت نامجاز، مسیر مستقیم فایل و رفتار `lock_timeout` اجرا شدند.
- نتیجهٔ واقعی: ZIP زودتر فقط بایت PDF clean همان snapshot را ساخت و تغییر وضعیت تا پایان آن block شد؛ تغییر وضعیت زودتر هر سه حالت را 409 کرد. تست بعدی پس از موفقیت/خطا بدون قفل مانده اجرا شد؛ خطای نامرتبط `OperationalError` باقی ماند و فقط `55P03` به Fault 409 تبدیل شد. هیچ streaming یا پس‌گرفتن بایت تحویل‌شده ادعا نمی‌شود.
- شاهد: همان سه race تاریخی و مجموعهٔ مرتبط ۸۴تایی؛ بررسی منبع `download_transaction` و ترتیب organization→file.
- آزمون بازگشت: حفظ assertion عضو واقعی `attachments/`، سه state و تست تفکیک SQLSTATE.

### S08-IT-003 — قبول

- شدت/اثر سابق: متوسط؛ پیشرفت موبایل به ستون تک‌واژه‌ای و تداخل دکمه تبدیل می‌شد.
- نیازمندی: D09/D23، FR-002 و اصل II constitution.
- انتظار: در ۳۶۰ و ۳۹۰ متن پیشرفت خوانا، دکمه در سطر جدا، بدون overlap؛ click و Tab فوکوس واقعی را حفظ کنند.
- نتیجهٔ واقعی: تست تاریخی هر دو viewport موفق بود. probe مستقل در ۳۶۰ عرض متن را `171px` و ارتفاع را `50.375px` اندازه گرفت؛ focus پس از پرش روی سؤال «چگونه مایل به ورود هستید؟» و پس از Tab روی `INPUT` بود. تصاویر تازه مستقیم بازبینی شدند و ستون تک‌واژه‌ای یا تداخل دیده نشد.
- شاهد: [۳۶۰](retest-01-evidence/progress-360.png)، [۳۹۰](retest-01-evidence/progress-390.png)، `browser-probes.json`.
- آزمون بازگشت: دو viewport، متن فارسی، حداقل عرض/حداکثر ارتفاع، ترتیب هندسی دکمه و focus/Tab.

### S08-IT-004 — قبول

- شدت/اثر سابق: متوسط؛ گروه‌بندی مرجع حقوق/اسکان حذف شده بود.
- نیازمندی: D09/D23، FR-001/002 و headingهای `r1/r2` مرجع.
- انتظار: دو گروه واقعی «محدوده، حقوق و مشوق‌های قابل بررسی» و «ساکنان و اسکان موقت» با فیلدهای متعلق، ترتیب و شروط در ۱۴۴۰/۳۹۰؛ تغییر yes→no→yes داده raw را حفظ و effective را درست حذف/برگرداند.
- نتیجهٔ واقعی: هر heading دقیقاً یک بار در probe دیده شد. ترتیب گروه حقوق `gis, authority, evidenceDate, parcels, incentive, incentiveRef` بود و پیش از گروه اسکان قرار گرفت. `displacement=yes` فیلدهای households/deposit/rent را نشان داد، `no` آن‌ها را از UI/effective حذف کرد؛ regression سرور بازگشت شرط و حفظ raw را موفق کرد. تصاویر تازهٔ desktop/mobile ساختار موضوعی واقعی را نشان می‌دهند.
- شاهد: [۱۴۴۰](retest-01-evidence/renewal-groups-1440.png)، [۳۹۰](retest-01-evidence/renewal-groups-390.png)، `browser-source-controls.json` و مجموعهٔ ۸۴تایی.
- آزمون بازگشت: heading/ترتیب/عضویت فیلد و رفت‌وبرگشت شرط در مرورگر، همراه آزمون سروری raw/effective.

### S08-IT-005 — قبول

- شدت/اثر سابق: متوسط؛ فیلتر risk منبع بین‌المللی حذف شده بود.
- نیازمندی: D09/D23، FR-001/002 و رفتار `fi-source-filter` مرجع.
- انتظار: risk فقط کارت‌های پوشش ریسک منبع را نشان دهد؛ all/development/finance محفوظ؛ معرفی تاریخی وعدهٔ بیمه یا اعتبار واقعی نشود.
- نتیجهٔ واقعی: گزینه‌های `all/development/finance/risk` موجودند. risk دقیقاً یک کارت ICIEC نشان داد؛ finance/development کارت ICIEC را نشان ندادند و all هشت کارت داشت. متن کارت صریحاً «وضعیت فعلی احراز نشده» و «معرفی ابزار تضمین صدور بیمه نیست» را حفظ کرده است.
- شاهد: [risk در ۱۴۴۰](retest-01-evidence/international-risk-1440.png)، `browser-source-controls.json` و تست Playwright فیلتر.
- آزمون بازگشت: شمار/طبقه‌بندی هر چهار فیلتر و متن عدم‌احراز.

### S08-IT-006 — قبول

- شدت/اثر سابق: کم؛ شناسهٔ انگلیسی مرحله و مقدار خام boolean در متن مشتری.
- نیازمندی: FR-002/005، D29 و زبان فارسی محصول.
- انتظار: عنوان هر ۹ خدمت فارسی؛ undefined/true/false در فرم به «هنوز پاسخ داده نشده/بله/خیر»؛ false و صفر حذف یا با هم اشتباه نشوند؛ فیلد اختیاری بی‌پاسخ به‌عنوان مقدار ساختگی وارد HTML نشود.
- اجرای تازه: تست تاریخی چهارم هدفمند موفق شد؛ probe مستقل هر ۹ route را با HTTP 200 و عنوان فارسی خواند. checkbox charity سه وضعیت و جمع‌بندی `خیر` را نشان داد. دو گزارش تازه از endpoint HTTP روی PostgreSQL ایزوله دریافت شدند.
- نتیجهٔ واقعی: هر ۹ عنوان فارسی؛ true=`بله`، false=`خیر` و بی‌پاسخ مستقل. HTML charity مقدار false را `خیر` و بدون رشتهٔ `false` نشان داد. HTML proposal مقدار known zero را `0 تومان` نشان داد و optional بی‌پاسخ «توضیحات تکمیلی» را از پاسخ‌های فعال حذف کرد.
- شاهد: `ui-semantic-probe.json`، [جمع‌بندی false](retest-01-evidence/charity-false-summary-1440.png)، [HTML تازه در ۳۶۰](retest-01-evidence/fresh-charity-false-360.png)، `fresh-charity-false.html` و `fresh-proposal-zero-unanswered.html`.
- آزمون بازگشت: ۹ عنوان، سه وضعیت boolean، summary/snapshot و دانلود HTTP تازه با false/zero/unanswered.

## فرمان‌ها و نتایج تازه

فرمان‌های اصلی با Docker CLI مک (`/Applications/Docker.app/Contents/Resources/bin/docker`) اجرا شدند:

```sh
docker compose --env-file .env -f deploy/compose.yaml run --rm --no-deps --user 1000 \
  -e PYTHONPATH=/src -v "$PWD/backend:/src:ro" -v "$PWD/contracts:/contracts:ro" \
  -v "$PWD/docs/stage8/independent-tests:/independent:ro" -w /src test \
  /app/.venv/bin/pytest -c /src/pyproject.toml -o cache_dir=/tmp/pytest-cache -q \
  tests/test_service_downloads.py tests/test_services.py tests/test_core.py \
  -k 'download or service or malformed_land or case_journey or pause_blocks or owner_contact or organization_review_successor or file_reference_retained or personal_isolation'
# 84 passed, 52 deselected in 107.69s

# همان runner با /independent/test_download_race.py
# 3 passed in 21.67s

# همان runner با /retest/test_fresh_html.py و RETEST_EVIDENCE_DIR=/retest
# 1 passed in 9.20s
```

Playwright 1.65.1 در image رسمی، Chrome واقعی و proxy محلی حفظ‌کنندهٔ origin اجرا شد. فایل تاریخی کپی‌شده فقط مسیر خروجی تازه داشت؛ assertionها تغییر نکردند. سه تست در اجرای تجمیعی و تست فارسی/boolean در بازاجرای هدفمند موفق شدند: **۴ تست یکتا موفق**. دو probe تاریخی نیز با مقصد `retest-01-evidence` موفق شدند. probe مستقل semantic، ۹ عنوان، سه حالت boolean و render HTML تازه را موفق کرد.

شمار pytest یکتا: **۸۸ موفق، صفر شکست محصول** = ۸۴ مرتبط + ۳ race تاریخی + ۱ دانلود HTML تازه. بازاجراها، شکست fixture تازه و timeout محیطی به شمار یکتا افزوده نشده‌اند. ۱۸۰۱ قاعده، ۹ سفر کامل و suite احراز طبق مأموریت دوباره اجرا نشدند؛ پوشش معتبرشان از گزارش مستقل قبلی شاهد تاریخی است، نه اجرای تازهٔ این گزارش.

## تلاش‌های ناموفق محیطی و تفکیک آن‌ها

- اجرای نخست race: ۲ موفق و یک `ConnectionTimeout` هنگام fixture؛ teardown نیز `DROP DATABASE test_invest` را با statement timeout دید. پس از پایان connection مانده، همان سه تست بدون تغییر ۳/۳ موفق شدند. این شکست محصول نیست و نتیجهٔ نخست قبولی شمرده نشد.
- اتصال in-app Browser پیش از انتخاب tab با `SIGABRT` در خواندن نسخه Node نامتاح شد. fallback از Chrome واقعی Playwright و بازبینی مستقیم تصاویر استفاده کرد.
- سه تلاش ابتدایی مرورگر به‌ترتیب نبود dependency محلی، loopback اشتباه container و timeout ۳۰ثانیه‌ای runner داشتند. assertion محصول در اجرای صحیح origin/timeout تغییر نکرد؛ خروجی‌های JSON تلاش‌ها حفظ شده‌اند.
- تست تازه HTML در تلاش اول fixture شرطی نامعتبر داشت؛ fixture به حداقل معتبر مستقل کاهش یافت و ۱/۱ موفق شد.
- probe semantic تازه در آماده‌سازی charity ابتدا دو فیلد اجباری را پر نکرد؛ تصویر debug حفظ و fixture صریح شد. اجرای نهایی موفق است.

## مرجع طراحی و بخش‌های آزموده‌نشده

ZIP واقعی `Investment_Advisor-main.zip` در checkout یا `.tools` موجود نبود. تصاویر baseline تاریخی `docs/stage8/evidence/reference-*` با تصاویر تازه مقایسه و خود تصاویر تازه مستقیم مشاهده شدند؛ این کار بازبینی تازهٔ آرشیو معرفی نمی‌شود. responsive مصوب و تفاوت‌های D26/D29/D32 حفظ شده‌اند.

این retest فقط شش اصلاح را می‌پذیرد. تفاوت‌های بصری باز گزارش قبلی، pixel-perfect تمام صفحات، دستگاه موبایل واقعی، داوری کارشناس D28، اتصال واقعی OpenAI/SMS، retention عملیاتی، S09/F40 و عرضه عمومی آزموده/تأیید نشده‌اند. probe تاریخی F30 در DB فعال صفر item داشت؛ status و برابری ranking را گذراند، اما این اجرای خاص شاهد کیفیت/غنای نتایج F30 نیست.

## زمان

- آماده‌سازی و مطالعه/provenance/tooling: زمان‌سنج مستقل از نخستین پیام فعال نبود؛ حدود ۲۵ دقیقه تا شروع runner و حدود ۱۵ دقیقه آماده‌سازی fallback مرورگر ثبت عملی دارد.
- build محصول: **صفر**؛ backend/web rebuild یا restart نشدند. build یک‌بارهٔ image ابزار test از lock موجود: **۴ دقیقه و ۱ ثانیه** طبق BuildKit.
- اجرای نهایی قابل استناد: pytest مرتبط ۱۰۷٫۶۹ثانیه، raceها ۲۱٫۶۷ثانیه، HTML تازه ۹٫۲۰ثانیه؛ مرورگر تجمیعی ۵۹٫۶ثانیه، تست چهارم هدفمند ۴۲٫۴ثانیه، دو probe تاریخی حدود۴۱ثانیه و probe semantic نهایی حدود۴۶ثانیه. تلاش‌های محیطی/fixture جدا و در شمار پذیرش نیستند.
- نگارش و بازبینی گزارش/manifest: حدود ۱۲ دقیقه؛ مقدار تقریبی است و با زمان تست جمع نشده است.

## نظر پذیرش

هر شش مانع گزارش مستقل قبلی رفع و regressionهای مأموریت روی PostgreSQL واقعی ایزوله و Chrome واقعی موفق‌اند. بنابراین دامنهٔ فنی S08 پس از FIX-01 **قابل قبول است**. هماهنگ‌کننده/کاربر باید وضعیت پذیرش مرحله را جدا به‌روز کنند؛ این مأموریت هیچ push، deploy، شروع مرحله بعد یا تأیید انسانی طراحی انجام نمی‌دهد.
