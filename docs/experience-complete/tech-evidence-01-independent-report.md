# گزارش مستقل TEST-EXPERIENCE-EVIDENCE-01

تاریخ اجرا: ۱۴۰۵/۰۸/۲۹ (۲۰۲۶-۱۱-۲۰)

مبنای محصول: `79519bb8e88cbf6c0bcf7614c63b3737cc668a70`

تحویل فنی آزموده‌شده: `d351892886409e6989c03bf0dbad0c97f8577f47`
دامنه: فقط بستهٔ `TECH-EXPERIENCE-EVIDENCE-01`؛ بدون تغییر کد محصول، fixture تحویلی، فرمول/وزن D28، رأی انسانی یا stage-status.

## نتیجهٔ اجرایی

| بخش | نتیجه مستقل | توضیح کوتاه |
|---|---|---|
| منشأ commit و حفاظت دامنه | قبول با محدودیت capture | HEAD دقیقاً تحویل فنی و parent آن مبنای محصول است؛ diff رفتاری backend/frontend و تغییر فرمول/وزن/threshold صفر بود. digest اجرای تازهٔ UI در بسته ثبت نشده است. |
| manifest و تاریخچهٔ D28 | قبول | هر ۸۳ فایل، اندازه و SHA-256 صحیح؛ چهار hash ورودی و شکست نخست held-out بدون حذف/تغییر نام حفظ شده‌اند. |
| بستهٔ شواهد طراحی | **رد** | ساختار ۲۶×۴ و جمع طبقه‌بندی درست است، ولی ۹ جایگاه از ۱۵ مورد `representative-covered` شاهد route/state متفاوت دارند و provenance چهار capture تازه کامل نیست. |
| کفایت برای بررسی مالک محصول | **کافی برای شروع، ناکافی برای بستن دور اول** | مالک می‌تواند زیرمجموعه‌های دارای شاهد معتبر را ببیند؛ ۹ جایگاه نماینده باید اصلاح/بازطبقه‌بندی شوند. این گزارش رأی طراحی نیست. |
| fixture فنی D28 | **رد** | به‌جای ۹۶ فرصت واقعاً متمایز، ۸۰ امضای معنایی وجود دارد؛ ۳۲ رکورد در ۱۶ جفت cross-split تکراری‌اند. دو ردیف unit-basis نیز مصرف‌کنندهٔ عددی ندارند. |
| oracle فنی D28 | **قبول** | محاسبهٔ مستقل ۴۸۰ زوج، check/state/weight، score/coverage/status و ترتیب top-5 را بدون اختلاف تأیید کرد و mutation مصنوعی را رد کرد. |
| development تازه | قبول | روی PostgreSQL تازه: ۳۲ سناریو، ۴۸ فرصت، ۱۹۲ زوج و ۱۶۰ top-5؛ صفر اختلاف و cursor چهار صفحهٔ ۱۲تایی/۴۸ شناسهٔ یکتا. |
| held-out موجود | قبول فقط به‌عنوان regression فنی | نخستین اجرا پیش از scoring در `return.basis` شکست؛ اجراهای پس از اصلاح دیگر untouched/confirming نیستند. |
| فرم‌های انسانی | قبول ساختاری؛ **منتظر داوری** | دو فرم هرکدام ۴۰۰ ردیف یکتا و خالی‌اند؛ ورودی داور score/coverage/matching/system rank ندارد. هیچ رأیی ثبت نشد. |

نتیجهٔ تجمیعی: بسته در شکل فعلی برای ادعای «شواهد طراحی کامل» یا «fixture کامل و تعمیم‌پذیر D28» قابل قبول نیست. اجرای development و oracle فنی معتبرند و held-out فعلی فقط regression است. پذیرش تخصصی طراحی، داوری کیفی D28 و پذیرش انسانی همچنان گیت‌های جدا و باز هستند.

## ۱. منشأ، نسخه و حفاظت دامنه

- `git rev-parse HEAD` برابر `d351892...` و parent آن دقیقاً `79519bb...` است.
- `git diff 79519bb..d351892 -- backend frontend` خالی بود؛ کد رفتاری محصول، `discovery.py`، وزن‌ها و threshold تغییر نکرده‌اند.
- image آزمون `investexp-test:8d04efc231b2` کد backend را از checkout جاری به‌صورت read-only bind کرد. PostgreSQL ایزوله image `sha256:005c5c37...` بود. DBهای `evidence_ind_20261120_1222` و `evidence_ind_20261120_1252` تازه ساخته شدند و DB فعال reset/rollback نشد.
- runtime موجود روی ۳۱۱۸ از backend digest `sha256:b26f984e...` و web digest `sha256:40072e8c...` استفاده می‌کرد؛ OCI revision نداشت. این runtime برای اجرای DB مبنا نبود و فقط نمونهٔ تعاملی عمومی library روی آن انجام شد.
- fixture همهٔ ۹۶ فرصت را `synthetic=true` و `market_claim=false` اعلام می‌کند. جست‌وجوی الگوهای کلید خصوصی/API key/password/secret در بسته موردی نیافت. شماره‌ها/داده‌های تستی فقط مصنوعی‌اند.
- فایل‌های بستهٔ D28-human قبلی تغییر نکرده‌اند. اسناد جاری human-design برای افزودن index بستهٔ جدید تغییر کرده‌اند، اما رأی انسانی و تصاویر تاریخی قبلی بازنویسی نشده‌اند.
- manifest شامل ۸۳ ورودی است و verifier مستقل برای همهٔ آن‌ها وجود، byte count و SHA-256 را دوباره محاسبه کرد: ۸۳/۸۳ قبول.

محدودیت provenance: مقدار `product_version` در ماتریس و گزارش hard-code شده، اما برای چهار capture تازه digest image یا hash فایل‌های runtime ثبت نشده است. بنابراین تعلق فایل‌های evidence به commit تحویل ثابت است، ولی تعلق قطعی سرور captureشده به همان source از خود بسته قابل اثبات نیست (`EVID-IT-004`).

## ۲. شواهد طراحی

### کنترل ساختاری و مشاهده

- ۱۰۴ جایگاه = ۲۶ row یکتا × چهار عرض ۳۶۰/۳۹۰/۷۶۸/۱۴۴۰؛ هر عرض ۲۶ بار آمده است.
- جمع طبقه‌بندی دقیق است: ۴۹ `reuse-valid`، ۱۵ `representative-covered`، ۳۶ `reference-component-only` و ۴ `capture-needed→new-evidence`.
- viewport height، canvas، font-ready، motion، identity، دادهٔ مصنوعی، state و مسیر فایل برای ۱۰۴/۱۰۴ مقدار دارند؛ ستون‌های رأی انسانی و تأیید متخصص برای ۱۰۴/۱۰۴ خالی‌اند.
- چهار capture تازه همگی library و DES-035 در چهار عرض‌اند؛ فایل‌ها خوانا و به شکاف واقعی library متصل‌اند. بررسی مستقل مرورگر library در چهار عرض، font-ready، reduced motion، focus، hit-test، click واقعی accordion و نبود overflow افقی را ۴/۴ قبول کرد.
- ۴۸ جایگاه یکتا به‌صورت ریسک‌محور (یک row از هر ۱۲ گروه × چهار عرض) در contact sheet باز شد و مشاهده شد. علاوه بر آن rowهای پرریسک DES-025/026/033/035/036/037/038/039/040 جدا باز شدند. detailهای fund/sale، FIX-02 report، پنل‌های workspace/drafts/requests/admin/expert و library در تصاویر موجود و خوانا بودند.
- نتایج Playwright تحویلی برای detail/library/report و پنل‌ها هرکدام ۴/۴ سبز است؛ interaction JSON پنل‌ها focus/hit/overflow را ثبت می‌کند. این داده‌ها بررسی شدند، اما تصویر ثابت جای تعامل شمرده نشد.
- تلاش مستقل برای ورود role-based در runtime موجود ۳۱۱۸ پس از کلیک واقعی role به navigation نرسید. چون همین runtime با source capture تحویلی bind نشده بود، این مورد شکست محصول طبقه‌بندی نشد؛ تعامل role-based مستقلاً بازاجرا نشده و فقط شاهد تحویلی آن بررسی شده است.

### اشکال نمایندگی

نه جایگاه زیر با تصویر `product-land-stage2-*` پوشش داده شده‌اند، در حالی که route/state ماتریس متفاوت است:

- DES-003 proposal step-3 در عرض‌های ۳۶۰ و ۷۶۸؛
- DES-009 foreign-investment step-1 در ۳۶۰، ۳۹۰ و ۷۶۸؛
- DES-014 ma-renewal step-1 در ۳۶۰ و ۷۶۸؛
- DES-021 charity step-2 در ۳۹۰ و ۷۶۸.

اشتراک ServiceEditor یا breakpoint، شرط صریح «state مشترک» را جایگزین نمی‌کند. در نتیجه ۹/۱۵ جایگاه نماینده معتبر نیست و ادعای ۱۰۴/۱۰۴ تعیین‌تکلیف‌شده قابل قبول نیست (`EVID-IT-003`). شش جایگاه نمایندهٔ compare در عرض نزدیک، component/state یکسان دارند و این ایراد را ندارند.

### تفکیک گیت‌ها

- اعتبار فنی کل بستهٔ طراحی: **رد**.
- قابلیت استفاده برای شروع مرور مالک: **بله، برای جایگاه‌های معتبر و با محدودیت‌های ثبت‌شده**.
- قابلیت بستن دور اول ۱۰۴ جایگاه: **خیر**؛ ۹ جایگاه فوق و provenance capture باید تعیین تکلیف شوند.
- خارج دور اول: ۱۴ row ثانویه/۵۶ جایگاه، زیرحالت‌های ندیده و pixel-perfect کل محصول.
- تأیید تخصصی UI/UX و امضای انسانی: **باز؛ در این مأموریت رأیی ثبت نشد**.

## ۳. fixture و oracle D28

### مخرج و ساختار

- routeها دقیقاً هشت مورد قراردادند: investor، fund، buyer، lessee، contractor، operator، heritage و charity.
- شناسه‌ها یکتا و شمار اسمی صحیح است: ۸۰ سناریو و ۹۶ فرصت؛ splitها ۳۲/۴۸ سناریو و ۴۸/۴۸ فرصت‌اند.
- هر سناریو دقیقاً شش candidate یکتا و مجاز دارد. خروجی‌ها ۱۹۲/۲۸۸ زوج candidate و ۱۶۰/۲۴۰ top-5 دارند.
- پس از حذف ID/revision/title و مقایسهٔ فیلدهای مؤثر scoring، فقط **۸۰ امضای فرصت** باقی ماند. در هر هشت route، indexهای ۴ (unknown) و ۵ (known zero) بین development و held-out عیناً تکرار شده‌اند: ۱۶ امضای تکراری و ۳۲ رکورد. تفاوت UUID/title/split تمایز معنایی نیست (`EVID-IT-001`).
- CSV route×axis دارای ۶۴ کلید یکتای route×axis است. بااین‌حال ردیف unit-basis برای operator و charity به سناریوهایی وصل است که فقط condition/location دارند و هیچ budget/return/معیار عددی ندارند؛ `oracle_result=pass` در این دو مورد مصرف معنایی unit/basis را اثبات نمی‌کند (`EVID-IT-002`).
- known zero، unknown و N/A در داده حضور دارند و verifier آن‌ها را جدا محاسبه کرد؛ ایراد فوق دربارهٔ تمایز cross-split و trace معنایی است، نه نبود مطلق این حالات.

### استقلال و حساسیت oracle

`d28_run.py` برای actual از `discovery.listing` استفاده می‌کند، ولی expectation را با تابع محاسبهٔ خودش می‌سازد و `discovery.score` را برای انتظار فراخوانی نمی‌کند. verifier مستقل این مأموریت نیز هیچ کد scoring محصول را import نکرد و مستقلاً موارد زیر را محاسبه کرد:

- amount و بازه، return/basis، category، location، risk و condition؛
- unknown/zero/NA، وزن‌بندی چند شرط روی یک axis، score، coverage و status؛
- ترتیب tie با score/coverage/index/id و top-5؛
- همهٔ checkهای axis/state/weight در ۴۸۰ زوج تحویلی.

نتیجه: صفر اختلاف در ۴۸۰ زوج و ۸۰ ترتیب top-5. سپس score یک زوج فقط در کپی حافظه به `99.999` تغییر کرد و verifier آن را رد کرد؛ شواهد اصلی تغییر نکرد. cursor اجرای تازه نیز چهار صفحهٔ ۱۲تایی، ۴۸ شناسهٔ یکتا و بدون حذف/تکرار داشت.

### development و held-out

development روی PostgreSQL تازه و checkout منطبق اجرا شد: ۳۲ سناریو، ۴۸ فرصت، ۱۹۲ زوج، ۱۶۰ top-5 و صفر اختلاف با oracle مستقل. اجرای نخست از نظر رفتار قبول بود، ولی metadata runner hash کوتاه‌شدهٔ نادرستی داشت؛ پس از اصلاح فقط metadata، روی DB تازه یک بار تکرار و خروجی قبلی مسیر مستقل جایگزین شد. تعداد یکتای سناریوها افزایش داده نشده است.

زنجیرهٔ held-out به‌طور مستقل با hashها تطبیق شد:

1. `644d9e97...`: development قبول؛ نخستین held-out در `return.basis` پیش از scoring شکست و در `heldout-first-attempt.json` حفظ شد.
2. `0ade0a15...`: basis کامل شد؛ development+held-out به‌عنوان regression قبول.
3. `9125d5a2...`: route×field اصلاح شد؛ regression قبول.
4. `4f74b92e...`: unit metadata اصلاح شد؛ regression نهایی قبول.

`leak-replay-log.json` صریحاً absolute blinding را false و held-out نهایی را regression می‌نامد. نتیجهٔ نامطلوب حذف یا با نام confirming بازنویسی نشده است. تکرار دوبارهٔ همین held-out استقلال ازدست‌رفته را بازنمی‌گرداند، بنابراین اجرا نشد.

### فرم انسانی و امکان ارائه به خبره

- `d28-relevance-labels.csv`: ۴۰۰ زوج یکتا، همهٔ فیلدهای انسانی خالی.
- `d28-critical-review.csv`: ۴۰۰ زوج یکتا، همهٔ فیلدهای انسانی خالی.
- `d28-reviewer-inputs.json`: فاقد score، coverage، matching و system rank.
- coordinator key خروجی فنی را جدا نگه می‌دارد و برای blind reviewer ارسال نمی‌شود.

پس بسته برای توسعه و regression فنیِ فرمول موجود قابل استفاده است، اما fixture با ادعای «۹۶ واقعاً متمایز» و coverage معنایی کامل قابل قبول نیست. پیش از ارائهٔ نهایی به خبره باید duplicateها و دو نگاشت unit-basis اصلاح و دوباره freeze شوند؛ این مأموریت fixture را تغییر نداده است.

## ۴. یافته‌ها

### EVID-IT-001 — شدت زیاد — فرصت‌های cross-split فقط با شناسه/عنوان متفاوت‌اند

- اثر: مخرج تنوع و استقلال held-out بیش‌برآورد می‌شود؛ خبره و ارزیابی تعمیم با نمونه‌های مؤثر تکراری مواجه می‌شوند.
- نیازمندی: ۹۶ فرصت مصنوعی «واقعاً متمایز» و منع تمایز صرفاً UUID.
- پیش‌شرط: checkout تحویل و `d28-inputs.json` با hash نهایی.
- بازتولید: snapshot هر فرصت را بدون `title` و شناسه‌ها canonicalize؛ بر route/index/split گروه‌بندی و development را با held-out مقایسه کنید.
- انتظار: ۹۶ امضای معنایی متمایز و نبود جفت cross-split یکسان.
- واقعیت: ۸۰ امضا؛ indexهای ۴ و ۵ هر هشت route، ۱۶ جفت/۳۲ رکورد تکراری.
- شاهد: `independent-validation.json`، فیلدهای `semantic_opportunity_signatures` و `cross_split_duplicate_pairs`.
- آزمون بازگشت: validator باید uniqueness را روی فیلدهای مؤثر scoring، پس از حذف metadata، هم درون split و هم بین splitها enforce کند.

### EVID-IT-002 — شدت متوسط — دو ادعای unit-basis مصرف معنایی ندارند

- اثر: traceability سبز می‌شود بی‌آنکه unit/basis واقعاً در operator و charity آزموده شود؛ نقص قرارداد می‌تواند پنهان بماند.
- نیازمندی: ۶۴ ردیف route×axis معتبر با سناریوی مصرف‌کننده یا N/A مستدل.
- پیش‌شرط: CSV route×axis و fixture نهایی.
- بازتولید: ردیف‌های `axis=unit-basis, applicable=yes` برای operator/charity را باز و criteria سناریوهای پیوندشده را بررسی کنید.
- انتظار: معیار عددی/return دارای unit یا basis، یا N/A مستدل.
- واقعیت: فقط `experience/charity_type` و location؛ هیچ budget/return/معیار عددی وجود ندارد.
- شاهد: `independent-validation.json`، `weak_unit_basis_routes`.
- آزمون بازگشت: هر ردیف applicable باید به field مصرف‌شده در criteria و check متناظر actual/oracle متصل شود؛ path-only رد شود.

### EVID-IT-003 — شدت زیاد — شاهد نماینده route/state دیگری را نشان می‌دهد

- اثر: مالک محصول ممکن است proposal/foreign-investment/ma-renewal/charity را بر پایهٔ فرم زمین step-2 تأیید کند؛ پوشش واقعی ۱۰۴/۱۰۴ نیست.
- نیازمندی: representative-covered فقط با component، breakpoint، state و ریسک مشترک.
- پیش‌شرط: ماتریس ۱۰۴ جایگاه و تصاویر `product-land-stage2-*`.
- بازتولید: ۱۵ ردیف representative را با route/state نام فایل و محتوای تصویر مقایسه کنید.
- انتظار: route/state یکسان یا استدلال صریح و قابل مشاهدهٔ همان state.
- واقعیت: ۹ جایگاه چهار route/state دیگر از land-preparation step-2 استفاده می‌کنند.
- شاهد: `independent-validation.json`، `wrong_state_representatives` و `visual-sample-G09.png`.
- آزمون بازگشت: validator باید route/state evidence را با row تطبیق دهد و برای نمایندگی cross-route بدون state یکسان fail کند؛ سپس capture همان state یا طبقه‌بندی شکاف ثبت شود.

### EVID-IT-004 — شدت متوسط، نقص شواهد — runtime capture به source bind نشده است

- اثر: چهار تصویر تازه قابل مشاهده‌اند، اما نمی‌توان مستقلاً اثبات کرد دقیقاً از commit ادعاشده گرفته شده‌اند.
- نیازمندی: اعتبار نسخه و شرایط capture تازه/reuse.
- پیش‌شرط: manifest، ماتریس و metadata capture.
- بازتولید: metadata/manifest را برای image digest، BUILD_ID یا hash فایل runtime جست‌وجو کنید.
- انتظار: شناسهٔ runtime قابل محاسبه و اتصال آن به source مبنا.
- واقعیت: فقط رشتهٔ `product_version` و زمان ثبت شده؛ digest/runtime hash وجود ندارد.
- شاهد: `independent-validation.json` و manifest تحویلی.
- آزمون بازگشت: پیش از capture، digest image و hash bundle/source داخل container ثبت و در manifest hash شود.

## ۵. held-out تازهٔ پیشنهادی

برای ادعای generalization یا پذیرش کیفی D28، **held-out مستقل تازه لازم است**. حداقل دامنهٔ قابل دفاع:

- ۸ route؛ حداقل ۴ سناریوی مستقل در هر route (۳۲ سناریو) که مجموعهٔ آن‌ها amount/unit یا N/A، return/basis یا N/A، location، unknown/zero/NA، risk/condition، وزن چندگانه و tie را پوشش دهد؛
- ۶ فرصت در هر route (۴۸ فرصت) که امضای همهٔ فیلدهای مؤثرشان هم با development و هم با held-outهای قبلی متفاوت باشد؛
- candidate pool شش‌تایی و top-5، در مجموع حداقل ۱۹۲ زوج و ۱۶۰ خروجی قابل داوری؛
- fixture و فهرست hashها را **هماهنگ‌کننده‌ای مستقل از پیاده‌ساز** با بازبینی خبرهٔ دامنه/امین داده، پیش از هر اجرای محصول freeze کند؛ پیاده‌ساز تا پس از freeze و ثبت hash خروجی را نبیند؛
- خطای schema پیش از scoring، هر اصلاح و هر replay به‌صورت append-only حفظ شود؛ پس از مشاهدهٔ خروجی، مجموعه دیگر untouched نامیده نشود.

این حداقل یک confirming set فنی است، نه تصویب label یا threshold. داوری خبرهٔ relevance/critical و تصمیم کیفی همچنان لازم است و این گزارش آستانه‌ای تصویب نمی‌کند.

## ۶. فرمان‌ها، شمار و زمان

فرمان‌های محوری (مقادیر DB فقط مصنوعی):

```text
git rev-parse HEAD
git diff --name-only 79519bb..d351892 -- backend frontend
python3 docs/experience-complete/tech-evidence-01-independent/independent_verify.py
docker exec invest-expit-db-1 createdb -U postgres evidence_ind_20261120_1252
docker compose -p invest-expit -f .tools/expit/compose.yaml run --rm \
  -e DATABASE_URL=postgresql://postgres:synthetic@db:5432/evidence_ind_20261120_1252 \
  test /app/.venv/bin/python manage.py migrate --noinput
docker compose ... test /app/.venv/bin/python manage.py shell \
  -c "exec(open('/independent/development_replay.py').read())"
docker run --rm -e PRODUCT_URL=http://host.docker.internal:3118 \
  mcr.microsoft.com/playwright:v1.65.1-noble ... playwright test
```

نتایج و شمار یکتا:

- verifier مستقل: ۳۰ کنترل؛ ۲۶ قبول و ۴ رد متناظر با چهار یافته.
- oracle: ۸۰ سناریوی یکتا/۴۸۰ زوج تحویلی و ۸۰ ترتیب top-5؛ یک mutation مصنوعی رد شد.
- اجرای تازه development: ۳۲ سناریوی یکتا/۱۹۲ زوج/۱۶۰ top-5؛ یک rerun فقط برای اصلاح metadata hash، نه شمار آزمون جدید.
- طراحی: ۴۸ جایگاه یکتای مشاهده‌شده در ۱۲ گروه×۴ عرض؛ ۹ row پرریسک اضافی با هم‌پوشانی، جدا باز شد؛ چهار آزمون مرورگر یکتای library در چهار عرض. اجرای نهایی مرورگر ۴/۴ قبول بود.
- تلاش‌های محیطی ناموفق و خارج شمار قبول: اتصال in-app browser به علت SIGABRT محیط Node؛ ورود role-based runtime موجود بدون navigation؛ هیچ‌یک نتیجهٔ محصول اعلام نشد.
- validate تحویلی ۲۸/۲۸ سبز بود، ولی پذیرش مستقل بر آن متکی نیست.

زمان‌های دیواری تقریبی و جداشده: آماده‌سازی/مطالعه/نسخه ۱۰ دقیقه؛ verifier و DB حدود ۹ دقیقه؛ مشاهدهٔ بصری و مرورگر حدود ۹ دقیقه؛ تحلیل و گزارش/اعتبارسنجی حدود ۱۲ دقیقه. build یا نصب مجدد انجام نشد.

## ۷. محدودیت‌ها و قدم بعدی

- runtime دقیق چهار capture تازه با digest قابل اثبات نبود؛ role-panelها مستقلاً بازاجرا نشدند.
- این مأموریت pixel-perfect کل محصول، ۱۴ row دور بعد، پذیرش انسانی، ممیزی تخصصی طراحی، داوری کیفی D28، threshold، COMP-AI یا production readiness را پوشش نمی‌دهد.
- سبز بودن oracle فرمول موجود را تأیید می‌کند، نه کیفیت رتبه‌بندی برای کاربر.

قدم بعدی پیشنهادی: مالک فنی بسته، بدون تغییر فرمول محصول، چهار نقص شواهد را در یک مأموریت محدود اصلاح کند: فرصت‌های تکراری را با پروفایل‌های معنایی تازه جایگزین و دوباره freeze کند؛ دو ردیف unit-basis را به مصرف واقعی یا N/A مستدل وصل کند؛ ۹ جایگاه نماینده را capture/بازطبقه‌بندی کند؛ و digest runtime را به manifest بیفزاید. پس از بازآزمایی مستقل این اصلاحات، بسته برای جلسهٔ مالک محصول و آماده‌سازی held-out تازه تحویل شود. شروع آن مأموریت یا داوری انسانی نیازمند دستور جداست.
