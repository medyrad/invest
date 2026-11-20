# گزارش مستقل TEST-EXPERIENCE-EVIDENCE-FIX-01

تاریخ اجرا: ۱۴۰۵/۰۸/۲۹ (۲۰۲۶-۱۱-۲۰)

مبنای یافته‌ها: `0380bbf3cdcf00f6997b060a7d43a1ad980dc56c`

commit اصلاح: `f550645fa65f92c6f71ea156ae3e1f42bd36cf0c`

commit تحویل آزموده‌شده: `a742f709060198785f69eb4bc1fe97e70fd660ce`

دامنه: فقط بازآزمایی `EVID-IT-001..004` و رگرسیون مستقیم؛ بدون تغییر کد محصول، fixture تحویلی، ماتریس، رأی انسانی، stage-status، oracle یا شواهد تاریخی.

## نتیجهٔ اجرایی

| مورد | نتیجه مستقل | جمع‌بندی |
|---|---|---|
| EVID-IT-001؛ تمایز فرصت‌ها | **قبول** | ۹۶ امضای معنایی یکتا، ۴۸ در هر split؛ mutation تکرار معنایی رد شد و مخرج‌های ۸۰/۹۶/۴۸۰/۴۰۰ حفظ شدند. |
| EVID-IT-002؛ unit/basis | **قبول** | operator و charity واقعاً مصرف‌کنندهٔ عددی ندارند و N/A صحیح است؛ شش route قابل اعمال amount و سه route دارای return/basis به check واقعی actual/oracle وصل‌اند؛ mutation کاذب operator رد شد. |
| EVID-IT-003؛ نه جایگاه طراحی | **قبول** | هر ۹ تصویر route/state درست را نشان می‌دهد؛ شش representative باقی‌مانده همان route/state و قرارداد component/breakpoint صریح دارند؛ چهار مسیر یکتای مرورگر قبول شد. |
| EVID-IT-004؛ provenance | **رد — نقص شواهد** | commit/digest/BUILD_ID/hash/URL/identity/seed/viewport/browser/hash تصویر برای ۱۳ capture معتبر است، اما چهار capture library در تصویر accordion بسته دارند، metadata آن‌ها `accordion-open` می‌گوید و state ردیف ماتریس نیز `list;search;empty` است. |
| رگرسیون مستقیم D28 | **قبول** | oracle بدون تغییر، replay تازه development بدون اختلاف، فرم‌های انسانی خالی، کد رفتاری/فرمول/وزن/threshold و شواهد held-out تاریخی دست‌نخورده‌اند. |

نتیجهٔ تجمیعی: اصلاح fixture فنی D28 و ۹ جایگاه هدف طراحی قبول است، اما بستهٔ شواهد طراحی به‌سبب `EVID-IT-004` هنوز پذیرش فنی کامل ندارد. مورد بازمانده نقص محصول نیست؛ نقص اتصال state واقعی چهار تصویر library به metadata و ماتریس است. بنابراین بسته برای مرور محدود ۹ جایگاه اصلاح‌شده مفید است، ولی برای بستن مرور مالک محصول یا ادعای کامل‌بودن بسته کافی نیست.

## ۱. نسخه و منشأ runtime

- checkout هنگام آزمون دقیقاً `a742f709...` بود. تغییرات `0380bbf..a742f70` فقط اسناد، fixture، runner و شواهد است؛ diff رفتاری `backend/` و `frontend/` نسبت به مبنای محصول `79519bb8...` خالی است.
- frontend image: `sha256:7287a4565a5009804135d718f1685ca38c43adc207c5c33f5b1f965fdac0840a`؛ backend image: `sha256:66d9622b61ba649030b770b68aed625224d503d0150b1160ddb8e09753b6feb7`.
- image labelها runtime را به source `0380bbf3...` متصل می‌کنند. این مبنا برای محصول صحیح است، چون اصلاح حاضر کد محصول را تغییر نداده است.
- hash مستقل source frontend برابر `cc270663...` و backend برابر `701b2ba6...` بود و با labelها و provenance تحویل برابر شد. ۱۴۸ فایل tracked backend در `/app` و فایل‌های runtime frontend ثبت‌شده بدون mismatch بودند.
- frontend `BUILD_ID` برابر `myZDM7kEa-Q6fjMutJW5o` بود؛ containerهای فعال دقیقاً از imageهای فوق اجرا می‌شدند.
- manifest اصلاح ۵۵/۵۵ فایل را از نظر وجود، byte count و SHA-256 قبول کرد. hard-coded بودن `product_version` مبنای قبول نبود.
- build یا نصب مجدد انجام نشد؛ image سالم و منطبق reuse شد.

## ۲. EVID-IT-001 — قبول

verifier مستقل هیچ scorer یا validator برنامه‌نویس را import نکرد. canonical form فقط از `route`، `kind` و `snapshot` بدون `title` ساخته شد؛ UUID، revision، split و metadata اصلاً وارد امضا نشدند.

- ۹۶ رکورد به ۹۶ امضای معنایی تبدیل شد؛ development و held-out هرکدام ۴۸ امضای یکتا دارند و اشتراک تکراری ندارند.
- indexهای unknown و known-zero در هشت route بین splitها دست‌کم در فیلدهای مؤثر `group/province/risk/contract_mode` تفاوت دارند؛ تفاوت به عنوان یا شناسه محدود نیست.
- در کپی حافظه، snapshot یک فرصت held-out با development برابر و فقط title متفاوت شد؛ verifier duplicate معنایی را تشخیص داد. فایل تحویلی تغییر نکرد.
- ۸۰ سناریو، ۹۶ فرصت، شش نامزد یکتا برای هر سناریو، ۴۸۰ candidate pair و ۴۰۰ top-5 حفظ شدند.

شاهد: `tech-evidence-fix-01-retest/independent-validation.json`، کنترل‌های `evid_it_001_96_semantic_unique`، `unknown_zero_not_cosmetic`، `semantic_duplicate_mutation_rejected` و `d28_denominators_preserved`.

## ۳. EVID-IT-002 — قبول

- قرارداد واقعی route از `search_fields.json` همراه با محدودیت‌های مصرف‌کننده بررسی شد. operator و charity هیچ فیلد عددی واحددار/بازده قابل مصرف ندارند؛ فیلد عمومی `area` برای این دو route مصرف نمی‌شود. N/A این دو ردیف صحیح است.
- همهٔ ۱۵ scenario پیوندشده به unit-basis بررسی شدند. amount با `TOMAN@1` و check محور `amount` برای investor/fund/buyer/lessee/contractor/heritage وجود دارد. return/basis و check محور `returns` برای investor/fund/heritage در خروجی تاریخی regression موجود است.
- این بررسی held-out را دوباره اجرا نکرد؛ فقط fixture و خروجی موجود را در برابر قرارداد و oracle پذیرفته‌شده خواند.
- mutation موقت `operator applicable=yes` با scenario فاقد budget/return رد شد. صرف route یا field ساختگی پوشش محسوب نشد.

oracle `d28_run.py` byte-for-byte با `0380bbf` برابر و SHA-256 آن `ce182269...` بود. چون منشأ و عدم تغییر ثابت شد، محاسبهٔ کامل ۴۸۰ زوج تکرار نشد؛ نمونه‌های amount/return و checkهای مرزی مستقل بررسی شدند.

شاهد: `independent-validation.json`، کنترل‌های `evid_it_002_contract_and_oracle_samples`، `false_applicable_mutation_rejected` و جزئیات `unit_basis_*`.

## ۴. EVID-IT-003 — قبول

هر ۹ تصویر اصلاح‌شده مستقیماً باز و با ماتریس تطبیق داده شد:

- proposal summary: عرض‌های ۳۶۰ و ۷۶۸؛
- foreign-investment step1: عرض‌های ۳۶۰، ۳۹۰ و ۷۶۸؛
- ma-renewal step1: عرض‌های ۳۶۰ و ۷۶۸؛
- charity summary: عرض‌های ۳۹۰ و ۷۶۸.

نام فایل به‌تنهایی معیار نبود؛ عنوان، فیلدها و summary/step واقعی در تصویر دیده شد. شش representative باقی‌مانده فقط compare project/fund/sale در عرض‌های ۳۶۰ و ۷۶۸ هستند و route/state و قرارداد component/breakpoint مشترک صریح دارند.

مشاهدهٔ تازه با Chromium واقعی:

- proposal summary در ۳۶۰؛
- foreign-investment step1 در ۳۹۰؛
- ma-renewal step1 در ۳۶۰؛
- charity summary در ۳۹۰.

چهار مسیر font-ready، reduced motion، نبود overflow افقی، focus و hit-test را قبول کردند. یک capture تازه proposal summary نیز گرفته، باز و به همان image digest/BUILD_ID متصل شد. این capture آزمون pixel-perfect یا امضای طراحی محسوب نمی‌شود.

اجرای نخست مرورگر دو مسیر step1 را قبول کرد و دو summary به‌علت origin نامنطبق runner Docker با CSRF runtime به summary نرسیدند. proxy محدود فقط origin را به `127.0.0.1:3120` منطبق کرد؛ انتظار یا دادهٔ آزمون تغییر نکرد. rerun هدفمند همان دو مسیر ۲/۲ قبول شد.

شاهد: `visual-inspection.md`، چهار `browser-*.json`، `browser-attempts.json`، `browser-results.xml` و `independent-capture-provenance.json`.

## ۵. EVID-IT-004 — رد؛ نقص شواهد بازمانده

### اثر و شدت

شدت **متوسط، نقص شواهد**. مشتری در runtime این مأموریت با خطای رفتاری تازه مواجه نشد، اما مالک محصول ممکن است state کتابخانه را بر پایهٔ شاهد نادرست بپذیرد و بستهٔ ۱۳ capture به‌اشتباه کامل اعلام شود.

### نیازمندی

هر capture باید commit، digest frontend/backend، BUILD_ID، hash source/runtime، URL، state، identity، seed، viewport، browser و SHA-256 تصویر معتبر و هم‌خوان با محتوای واقعی داشته باشد.

### پیش‌شرط و بازتولید

1. checkout تحویل `a742f70` و runtime imageهای ثبت‌شده را آماده کنید.
2. چهار فایل `design-library-{360,390,768,1440}.png` را باز کنید.
3. محتوای تصویر را با metadata `capture-library-*.json` و ردیف‌های DES-035 در `design-slot-matrix.csv` مقایسه کنید.
4. runner `capture-fixed-slots.spec.cjs` را بخوانید: accordion نخست ابتدا باز است، runner آن را click می‌کند و پس از بسته‌شدن capture می‌گیرد، ولی state ثابت `topic-index;accordion-open` می‌نویسد.

### انتظار و واقعیت

- انتظار: state تصویر، metadata و state/evidence_state ماتریس یکسان و قابل مشاهده باشد.
- واقعیت: هر چهار تصویر همهٔ accordionها را بسته نشان می‌دهد؛ metadata می‌گوید `accordion-open`؛ state اصلی ردیف ماتریس نیز `list;search;empty` و evidence_state برابر `topic-index;accordion-open` است.
- بخش پذیرفته‌شده: commit، دو image digest، BUILD_ID، source/runtime hashes، URL، identity، seed، viewport، browser و hash هر ۱۳ تصویر معتبرند؛ چهار تصویر library نیز واقعاً از runtime منطبق آمده‌اند.

شاهد: `independent-validation.json` با تنها کنترل ردشدهٔ `capture_state_matches_matrix` و چهار `capture_state_errors`؛ `visual-inspection.md`؛ تصاویر library و runner تحویلی.

آزمون بازگشت پیشنهادی: state را از DOM بعد از تعامل استخراج کنید، نه از رشتهٔ ثابت؛ validator باید `row.state == evidence_state == metadata.state` را الزام کند و assertion بصری/DOM برای `aria-expanded=true` داشته باشد. سپس فقط چهار capture library و metadata/matrix وابسته دوباره تولید شوند.

## ۶. replay محدود PostgreSQL و حفاظت تاریخچه

یک DB تازه به نام `evidence_fix_retest_20261120` در PostgreSQL ایزولهٔ `invest-evidencefix-db-1` ساخته و migrate شد. DB فعال reset/rollback نشد.

- ۳۲ سناریوی development، ۴۸ فرصت، ۱۹۲ candidate pair و ۱۶۰ top-5؛
- cursor: چهار صفحهٔ ۱۲تایی، ۴۸ شناسه و ۴۸ شناسهٔ یکتا؛
- ترتیب و matching همهٔ سناریوها با خروجی تحویلی منطبق؛ mismatch صفر؛
- هر scenario برای کنترل ثبات ترتیب یک بار داخلی تکرار شد، اما در شمار آزمون یکتا دوباره محاسبه نشد.

held-out اجرا نشد. فایل‌های نخستین شکست، attemptها و `leak-replay-log.json` byte-for-byte با `0380bbf` برابرند؛ held-out فعلی همچنان فقط regression است و با تکرار confirming نمی‌شود.

دو فرم relevance و critical-review هرکدام ۴۰۰ زوج یکتا و کاملاً خالی دارند. reviewer input فاقد score، coverage، matching و system rank است. diff کد رفتاری backend/frontend، فرمول، وزن و threshold صفر است.

## ۷. وضعیت نهایی اجزای بسته

| جزء | وضعیت پس از بازآزمایی |
|---|---|
| بستهٔ شواهد طراحی | **رد فنی**؛ ۹ جایگاه هدف درست‌اند، اما state چهار library نامعتبر است. |
| fixture فنی D28 | **قبول**؛ ۹۶ امضای واقعی و unit/basis مستدل. |
| oracle پذیرفته‌شده | **همچنان قبول**؛ hash و محتوا بدون تغییر، نمونه‌های مرزی منطبق. |
| development | **قبول تازه** روی PostgreSQL ایزوله. |
| held-out regression | **حفظ‌شده و فقط regression**؛ در این مأموریت اجرا نشد. |
| کفایت برای مرور مالک محصول | برای مرور محدود ۹ اصلاح **بله**؛ برای بستن بسته/دور **خیر**. |
| held-out تأییدی تازه | **وجود ندارد**؛ برای ادعای generalization همچنان لازم است. |
| گیت‌های انسانی | تأیید تخصصی طراحی، رأی مالک، labelهای خبره و داوری D28 **باز** هستند. |

## ۸. فرمان‌ها، شمار و زمان

فرمان‌های محوری:

```text
git rev-parse HEAD
git diff --name-only 79519bb..a742f70 -- backend frontend
python3 docs/experience-complete/tech-evidence-fix-01-retest/independent_verify.py
docker exec invest-evidencefix-db-1 createdb -U postgres evidence_fix_retest_20261120
docker compose -f .tools/evidencefix/compose.yaml run --rm ... manage.py migrate --noinput
docker compose -f .tools/evidencefix/compose.yaml run --rm ... manage.py shell -c "exec(open('/independent/development_replay.py').read())"
docker run --rm ... mcr.microsoft.com/playwright:v1.65.1-noble ... playwright test
```

شمارها:

- verifier مستقل: ۲۵ کنترل یکتا؛ ۲۴ قبول و ۱ رد؛
- mutation: دو مورد مستقل، هر دو به‌درستی رد شدند؛
- replay development: ۳۲ سناریوی یکتا، ۱۹۲ زوج و ۱۶۰ top-5؛ rerun سناریوی شکست‌خورده نداشت؛
- مرورگر: چهار route یکتا؛ دو rerun هدفمند summary پس از اصلاح محیط runner؛ نتیجهٔ معتبر ۴/۴؛
- مشاهدهٔ تصویر: ۱۳ capture تحویلی + یک capture مستقل؛
- build: صفر؛ held-out: صفر.

زمان دیواری جداشده، تقریبی مگر زمان runner:

- آماده‌سازی، مطالعه و تطبیق نسخه: حدود ۳۰ دقیقه؛
- DB، replay و verifier: حدود ۸ دقیقه؛ migration ۱۴٫۴ ثانیه، replay ۲۴٫۲ ثانیه و verifier نهایی ۲٫۶ ثانیه؛
- مرورگر و مشاهدهٔ بصری: حدود ۱۲ دقیقه؛ اجرای اول ۶۶ ثانیه و rerun هدفمند ۱۷٫۲ ثانیه؛
- گزارش و اعتبارسنجی نهایی: حدود ۱۵ دقیقه؛
- build/install: صفر.

محدودیت محیطی: browser integration داخلی محیط به‌علت خطای runtime Node قابل استفاده نبود؛ Chromium واقعی Playwright در container رسمی اجرا شد. این محدودیت شکست محصول محسوب نشد.

## ۹. نظر پذیرش و قدم بعد

`EVID-IT-001..003` از نظر فنی بسته‌اند. `EVID-IT-004` به‌سبب چهار شاهد library باز است؛ در نتیجه کل بستهٔ شواهد طراحی هنوز قابل پذیرش فنی کامل نیست. fixture، oracle پذیرفته‌شده و development مانع فنی دیگری در دامنهٔ این اصلاح ندارند. این نتیجه هیچ رأی طراحی، label خبره، threshold، production readiness یا مجوز COMP-AI ایجاد نمی‌کند.

قدم بعدی مشخص: در مأموریت جداگانه فقط چهار capture library، metadata و ردیف‌های وابستهٔ ماتریس با state واقعی همگام و سپس همین کنترل EVID-IT-004 هدفمند بازآزمایی شود. این گزارش مجوز آن اصلاح یا شروع مرحلهٔ بعد نیست.
