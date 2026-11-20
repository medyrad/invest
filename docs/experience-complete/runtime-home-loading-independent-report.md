# گزارش مستقل TEST-RUNTIME-HOME-LOADING-01

تاریخ: ۲۰۲۶-۱۱-۲۰

نسخه‌های هدف: `24ebb1f` (محصول/runtime) و `67a4d74` (شواهد EVID-IT-004)

دامنه: فقط runtime اصلی، ورود/origin، seed و نقشه، loading/Lottie و چهار شاهد library. ممیزی کامل محصول، D28، pixel-perfect کل صفحات و production readiness اجرا یا قبول نشده‌اند.

## نتیجهٔ نهایی

| بخش | وضعیت مستقل | دلیل |
|---|---|---|
| ۱. منشأ runtime | **مسدود محیطی** | checkout روی `67a4d74` و imageهای موجود با شناسه‌های تحویلی منطبق بودند، اما `dev_runtime.py up` در ساخت container موقت migration بیش از پنج دقیقه در حالت `Created` ماند؛ ۳۱۰۸ باز نشد و version endpoint زنده قابل بررسی نبود. |
| ۲. ورود و امنیت origin | **مسدود محیطی** | سیاست ایستا exact و بدون wildcard و پیام `csrf_failed` امن است، اما ورود کامل روی دو alias، cookie زنده و Origin منفی به‌علت نبود runtime اجرا نشد. |
| ۳. seed و نقشه | **مسدود محیطی** | کد و تست هدفمند بررسی شدند، اما اجرای دوباره seed، PostgreSQL هدفمند و مشاهده نقشه/لینک/حرکت در مرورگر ممکن نشد. |
| ۴. Loading و Lottie | **مسدود محیطی** | مسیرهای محلی JSON/WASM، hash و SOURCE معتبرند؛ رفتار skeleton، stale data، retry، reduced-motion، fallback asset و منع درخواست CDN در runtime اجرا نشد. |
| ۵. EVID-IT-004 | **رد — نقص شواهد** | چهار تصویر و metadata از نظر state/viewport/hash/image digest درست‌اند و validation برابر ۸/۸ است، ولی recapture به commit `24ebb1f` متصل نشده است؛ provenance اصلی هنوز checkout قدیمی `0380bbf` را ثبت می‌کند. |

نتیجهٔ تجمیعی این تحویل **قابل قبول نیست**: چهار بخش محصول به‌علت مانع Docker آزموده‌نشده‌اند و EVID-IT-004 نیز یک نقص provenance باز دارد. این نتیجه شکست رفتار محصول را ادعا نمی‌کند، اما کمبود اجرا یا شواهد را قبولی محسوب نمی‌کند.

## نسخه و محیط

- `git rev-parse HEAD`: `67a4d741cfb467ef52fecbd2c677b330038fabdb`؛ parent محصول `24ebb1f` است و diff `24ebb1f..67a4d74` فقط شواهد/ماتریس/وضعیت مرحله را تغییر می‌دهد.
- worktree پیش از آزمون تمیز بود.
- image موجود frontend: `sha256:99d983e464848619f88ecb4ef5009aca081ded85f41b6ddbe264a45f8365ae98`.
- image موجود backend: `sha256:5a27cb247f9cdc04e9e6a25fae0d9e511e58cca96727ebef68135f4aaa4904a5`.
- image test موجود: `sha256:f79d0cf45835dc485946c87e77df2377a4b53972967ced838f1d9f8c0a73f8a3`.
- فایل‌های نسخه frontend/backend هر دو `RUNTIME-HOME-LOADING-FIX-01` را ثبت می‌کنند، اما endpoint زنده دریافت نشد.
- runtimeهای evidence جدا روی ۳۱۱۸ و ۳۱۲۰ روشن بودند و با primary اشتباه نشدند. primary web روی ۳۱۰۸ خاموش ماند.
- هیچ build یا نصب مجدد انجام نشد.

## مانع محیطی

فرمان الزامی `python3 scripts/dev_runtime.py up` بدون `--build` اجرا شد. DB و scanner سالم شدند، سپس `docker compose run --rm backend ... migrate` container با نام `invest-backend-run-f5e150164327` را ساخت، ولی container بیش از پنج دقیقه در state `Created` باقی ماند. اجرای زنجیره متوقف شد و build/retry انجام نشد.

یک تلاش مستقل برای pytest هدفمند نیز container `invest-test-run-82be7daf9902` را فقط در state `Created` گذاشت و هیچ test process آغاز نشد. برای تفکیک port-forward، start مستقیم web container موجود یک بار امتحان شد و Docker socket خطای start داد. بنابراین:

- آزمون backend «fail» نیست؛ **اجرا نشده بر اثر مانع محیطی** است.
- مجموعه `runtime-home.core.spec.ts` اجرا نشد، زیرا ۳۱۰۸ در دسترس نبود.
- این مانع محدود به ادعای محصول نیست: create/start در backend، test و web همگی متوقف بودند.

## کنترل‌های ایستای محدود

این کنترل‌ها جای آزمون runtime شمرده نشده‌اند:

- تنظیم development فقط دو Origin دقیق `localhost:<port>` و `127.0.0.1:<port>` را می‌پذیرد؛ hostها دقیق‌اند و wildcard رد می‌شود.
- پیام `csrf_failed` علت داخلی را افشا نمی‌کند و تازه‌سازی و نشانی رسمی را پیشنهاد می‌دهد.
- تنظیمات public، `SESSION_COOKIE_HTTPONLY=true` را در آزمون هدفمند الزام می‌کنند.
- route قدیمی `/api/v1/catalog/preview` از URLConf حذف شده و قرارداد آن ۴۰۴ می‌خواهد.
- seed فقط development/test را می‌پذیرد و مسیر Draft → Submission → Review → publication را به‌کار می‌گیرد؛ اجرای واقعی آن در این مأموریت ممکن نشد.
- Lottie از `/animations/invest-analysis.json` و `/animations/dotlottie-player.wasm` استفاده می‌کند. SHA-256 واقعی به‌ترتیب `7a90bc9c...` و `70c460be...` است و با SOURCE برابر است. منبع و مجوز asset و dependency ثبت شده‌اند.

## EVID-IT-004

چهار تصویر `design-library-{360,390,768,1440}.png` مستقیماً مشاهده شدند. در هر چهار تصویر accordion نخست واقعاً باز و متن آن قابل مشاهده است. metadata نیز `state=topic-index;accordion-open` و `expanded_accordions=1` دارد. hash تصویر و metadata برای هر چهار مورد با `runtime-provenance.json` برابر است؛ viewportها و frontend/backend image digest و BUILD_ID نیز منطبق‌اند. `validate_design_evidence.py` یک بار اجرا و ۸/۸ قبول شد.

بااین‌حال معیار commit عبور نکرد: `runtime-provenance.json.checkout_commit` همچنان `0380bbf3...` و source fingerprintهای همان بسته تاریخی را نگه می‌دارد. بخش `runtime.current_recapture` image digestها، BUILD_ID و mission را دارد، اما commit `24ebb1f` یا source hash متناظر با آن را ثبت نمی‌کند. رشتهٔ mission یا زمان ساخت image جای اتصال محاسبه‌پذیر commit به runtime نیست.

## یافته

### RHL-IT-001 — شدت متوسط — recapture کتابخانه به commit هدف متصل نیست

- اثر مشتری/پذیرش: خطای مستقیم محصول ثابت نشد، اما مالک محصول نمی‌تواند مستقلاً اثبات کند تصاویر اصلاح‌شده دقیقاً از کد `24ebb1f` تولید شده‌اند؛ EVID-IT-004 و بستهٔ شواهد قابل بستن نیست.
- پیش‌شرط: checkout `67a4d74` و فایل `docs/experience-complete/tech-evidence-fix-01/runtime-provenance.json`.
- مراحل بازتولید:
  1. `checkout_commit` و `source` بالای provenance را بخوانید؛ مقدار `0380bbf3...` است.
  2. `runtime.current_recapture` و چهار capture library را بخوانید.
  3. image digest و BUILD_ID وجود دارند، اما commit `24ebb1f` و source/runtime hash متناظر وجود ندارند.
- انتظار: هر recapture دارای commit دقیق و زنجیرهٔ محاسبه‌پذیر commit → source hash/image → container/BUILD_ID → capture باشد.
- نتیجه واقعی: زنجیره از image به capture معتبر است، ولی حلقهٔ commit هدف به image وجود ندارد و top-level به commit تاریخی دیگری اشاره می‌کند.
- شاهد: `runtime-provenance.json`؛ چهار `capture-library-*.json`؛ خروجی ۸/۸ validator و مشاهده مستقیم تصاویر.
- آزمون بازگشت پیشنهادی: برای recapture جاری، commit، tree/source hashهای frontend/backend و hash runtime affected files را جدا ثبت کنید؛ validator باید mismatch یا نبود commit را fail کند. پس از اصلاح metadata/provenance، همان چهار تصویر موجود کافی‌اند و capture تازه لازم نیست مگر hash یا runtime تغییر کند.

## فرمان‌ها و نتایج

```text
git rev-parse HEAD
docker image inspect invest-web
docker image inspect invest-backend
python3 scripts/dev_runtime.py up
curl http://127.0.0.1:3108/api/v1/core/version
docker compose --env-file .env -f deploy/compose.yaml run --rm test \
  /app/.venv/bin/pytest -q backend/tests/test_settings.py \
  backend/tests/test_catalog.py::test_catalog_api_matches_fixture_and_preview_contract_is_retired \
  backend/tests/test_core.py::test_synthetic_seed_is_multicity_idempotent_and_forbidden_in_public
python3 docs/experience-complete/tech-evidence-fix-01/validate_design_evidence.py
```

نتایج:

- build: صفر.
- primary runtime/version endpoint: اجرا نشد؛ ۳۱۰۸ قابل اتصال نبود.
- backend هدفمند: process آزمون شروع نشد؛ صفر pass/fail، مسدود محیطی.
- مرورگر: صفر تست اجراشده؛ مسدود محیطی.
- probe ایستای مستقل: origin policy، بازنشستگی preview، hash assetهای محلی و hash/state/viewport تصاویر قبول؛ این‌ها جای runtime نیستند.
- design validation: ۸/۸ قبول.
- مشاهده تصویر: ۴/۴ با accordion باز.

زمان تقریبی: مطالعه و تطبیق نسخه ۱۲ دقیقه؛ تلاش runtime و تشخیص مانع ۸ دقیقه؛ آزمون backend/مرورگر ۲ دقیقه (آغاز نشدند)؛ EVID و probeهای ایستا ۶ دقیقه؛ گزارش و اعتبارسنجی ۸ دقیقه. مجموع حدود ۳۶ دقیقه.

## اجرا‌نشده‌ها و مرز پذیرش

- دو ورود OTP زنده، Origin منفی و cookie نشست؛
- اجرای دوباره seed و بررسی DB واقعی/عمومی؛
- نقشه در ۳۹۰/۱۴۴۰، motion/reduced-motion، لینک واقعی، console و overflow؛
- loading خانه/نقشه/results/saved/report، stale data، retry و asset-failure fallback؛
- درخواست‌های شبکه واقعی Lottie/CDN؛
- سه آزمون backend هدفمند و مجموعه مرورگر تعیین‌شده.

full backend، historical/core suite، D28، capture تازه و ماتریس کامل طراحی مطابق دامنه اجرا نشدند. تأیید انسانی طراحی و production readiness همچنان بازند.

قدم بعدی مشخص: پس از رفع مشکل Docker Desktop، همین مأموریت محدود یک بار روی ۳۱۰۸ اجرا شود و هم‌زمان provenance recapture با commit/source hash هدف تکمیل گردد؛ تا آن زمان نتیجه فنی این تحویل مسدود و EVID-IT-004 رد است. شروع آن کار نیازمند دستور بعدی کاربر است.

---

# بازآزمایی مستقل FIX-02 — TEST-RUNTIME-HOME-LOADING-FIX-02

تاریخ: ۲۰۲۶-۱۱-۲۰
نسخه‌ها: محصول `24ebb1fcacb7782a6e1526e906ffed5f3514bea5`، اصلاح provenance روی HEAD برابر `8f11989853e1a19d89de2a93ebccb9fb9d4f7e59`، گزارش مسدود تاریخی `ada2b45`.

## نتیجه

| بخش | وضعیت مستقل | نتیجهٔ بازآزمایی |
|---|---|---|
| ۱. منشأ runtime و RHL-IT-001 | **قبول** | هر دو alias نسخهٔ `primary-development` را برگرداندند؛ containerها دقیقاً imageهای ثبت‌شده را اجرا می‌کنند؛ commit/tree/fingerprint/BUILD_ID و چهار capture به هم متصل‌اند؛ validator برابر ۱۰/۱۰ و mutationهای commit و fingerprint هر دو مردود شدند. **RHL-IT-001 بسته شد.** |
| ۲. backend هدفمند و seed | **قبول** | اجرای یکتای PostgreSQL برابر ۲۰/۲۰ بود. probe مستقیم DB، شش publication ثابت، idempotency، چندشهر/چنداستان، نبود مقدار صریح `unknown` و منع seed در public را تأیید کرد. |
| ۳. ورود و Origin | **قبول** | ورود OTP واقعی روی هر دو `localhost` و `127.0.0.1`، cookie نوع HttpOnly، reload نشست و logout موفق بود. Origin نامجاز 403 و `csrf_failed` فارسی و قابل اقدام داد؛ علت داخلی افشا نشد. |
| ۴. نقشه | **قبول** | مرورگر واقعی در ۳۹۰ و ۱۴۴۰، motion و reduced-motion را پوشش داد: چهار نقطه، کارت/حالت ثابت، لینک معتبر، نبود overflow و خطای شبکه/console غیرمنتظره. |
| ۵. Loading و Lottie | **قبول** | skeleton پیش از content، حذف دادهٔ موفق قبلی هنگام خطا، retry، preview واقعی گزارش، reduced-motion بدون shimmer و درخواست محلی JSON/WASM تأیید شد. abort مستقل JSON fallback قابل مشاهده نگه داشت و صفحه/preview بازیابی شد؛ درخواست CDN ثبت نشد. |

نتیجهٔ فنی محدود بستهٔ `RUNTIME-HOME-LOADING-FIX-01` پس از اصلاح provenance **قبول** است. یافتهٔ جدیدی با شناسه `RHL2-IT-xxx` ایجاد نشد. این نتیجه تأیید انسانی طراحی، D28، pixel-perfect جامع یا production readiness نیست و آن گیت‌ها باز می‌مانند.

## نسخه و زنجیرهٔ provenance

- endpoint هر دو `http://localhost:3108/api/v1/core/version` و `http://127.0.0.1:3108/api/v1/core/version` پاسخ یکسان `RUNTIME-HOME-LOADING-FIX-01 / development / primary-development` داد؛ runtime جداگانه‌ای روی ۳۱۱۸/۳۱۲۰ دست‌کاری نشد.
- web فعال: `sha256:47508d0bb685a9108ea8eff6395e9821b902b34080006581a3de4af2d736feb3`؛ backend فعال: `sha256:095fdd7a623ade56449a43b5b87ec2e7db58553b534ec99180764fec8de80460`. این دو دقیقاً با `current_recapture` برابرند.
- labelهای image شامل commit کامل `24ebb1f...`، tree برابر `468303589e836358afa2b353eb80dceecdab863c` و fingerprintهای frontend/backend به‌ترتیب `789d54ec...` و `7aead457...` بودند. diff کد محصول در `frontend/` و `backend/` نسبت به `24ebb1f` خالی است؛ تغییر بعدی فقط Dockerfileهای provenance را شامل می‌شود.
- BUILD_ID زنده `DFT9TLJgVRDglJ-Kvtsm3` و برابر provenance و هر چهار metadata بود.
- SHA-256 هر چهار PNG و هر چهار metadata مستقلاً محاسبه و با provenance برابر شد. تصاویر ۳۶۰، ۳۹۰، ۷۶۸ و ۱۴۴۰ مستقیماً دیده شدند و در همهٔ آن‌ها accordion نخست واقعاً باز و پاسخ آن قابل مشاهده بود.
- بخش `historical` صریحاً checkout `0380bbf...` را فقط شاهد تاریخی معرفی می‌کند؛ `current_recapture` محصول `24ebb1f...` را ثبت می‌کند. بنابراین منشأ تاریخی به‌عنوان recapture جاری مصرف نشده است.
- `validate_design_evidence.py` یک بار اجرا شد: ۱۰/۱۰. mutation فقط در temporary copy انجام شد و تغییر commit و تغییر fingerprint هرکدام قرارداد را fail کردند. هیچ فایل evidence واقعی دست‌کاری نشد.

## آزمون‌ها و probeهای مستقل

### PostgreSQL

فرمان هدفمند واحد:

```text
docker compose --env-file .env -f deploy/compose.yaml run --rm test \
  /app/.venv/bin/pytest -q \
  tests/test_settings.py \
  tests/test_catalog.py::test_catalog_api_matches_fixture_and_preview_contract_is_retired \
  tests/test_core.py::test_synthetic_seed_is_multicity_idempotent_and_forbidden_in_public
```

نتیجه: **۲۰ passed در ۳۲٫۳۲ ثانیه**. full suite اجرا نشد.

probe مستقل با `manage.py shell` seed را دوباره اجرا و snapshot شناسهٔ `public_revision` را پیش/پس مقایسه کرد: شش فرصت و revisionها ثابت ماندند؛ چهار شهر و چهار استان متمایز برای routeهای مکانی موجود بود و مقدار صریح `unknown` وجود نداشت؛ اجرای public با `CommandError: Synthetic seed is forbidden in public` رد شد. دو فرصت `fund` طبق schema فاقد فیلد مکان‌اند و به‌عنوان `unknown` جعل نشده‌اند.

نسخهٔ نخست probe فرض سخت‌گیرانه و نامعتبر «همهٔ kindها الزاماً city/province دارند» داشت؛ فقط یک بازآزمایی هدفمند انجام شد. پس از مشاهدهٔ `None`، دادهٔ هر شش snapshot مستقیم خوانده شد و روشن شد نبود مکان محدود به دو `fund` است، درحالی‌که project/saleها مکان معتبر و چندشهری دارند. این شکست harness به‌عنوان شکست محصول شمرده نشد.

### مرورگر و امنیت Origin

فرمان یکتای مجموعه:

```text
PATH=/Users/mehdi/.nvm/versions/node/v24.18.0/bin:$PATH \
CORE_URL=http://127.0.0.1:3108 \
PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
npx playwright test --config=core.playwright.config.ts
```

نتیجه: **۴/۴ passed در ۱٫۶ دقیقه**. ورود دو alias، چهار حالت نقشه (۳۹۰/۱۴۴۰ × motion/reduced-motion)، loading/error/retry خانه و loading گزارش با JSON/WASM محلی پوشش داده شد.

probe مستقل کوتاه:

- login → cookie HttpOnly → reload → logout در مرورگر واقعی موفق؛
- در عرض ۳۹۰ چهار نقطه و کارت واقعی دیده شد، overflow افقی، response غیرمنتظرهٔ 4xx/5xx و خطای console وجود نداشت؛
- با abort فایل `/animations/invest-analysis.json`، متن و گرافیک fallback قابل مشاهده ماند، صفحه crash نکرد و پس از آزادکردن پاسخ، preview واقعی گزارش نمایش داده شد؛ درخواست خارجی/CDN صفر بود؛
- اجرای نخست probe قبل از انتظار برای bootstrap نقشه، count صفر گرفت؛ harness اصلاح شد و تنها بازآزمایی هدفمند آن ۴ نقطه و کارت را تأیید کرد.

probe HTTP مستقل برای Origin نامجاز:

```text
curl -X POST -H 'Origin: http://evil.invalid' \
  -H 'Content-Type: application/json' --data '{}' \
  http://127.0.0.1:3108/api/v1/auth/issue
```

نتیجه: 403 با `code=csrf_failed` و پیام «صفحه را از نشانی رسمی همین محیط باز کنید، سپس تازه‌سازی و دوباره تلاش کنید»؛ wildcard یا جزئیات داخلی مشاهده نشد.

## شمار، زمان و محدودیت‌ها

- آزمون یکتای backend: ۲۰؛ مرورگر: ۴؛ کنترل validator: ۱۰؛ مشاهدهٔ تصویر: ۴؛ mutation مستقل validator: ۲.
- rerun آزمون موفق: صفر. یک بازآزمایی هدفمند probe DB برای رفع فرض harness و یک بازآزمایی هدفمند probe مرورگر برای افزودن انتظار bootstrap انجام شد؛ در شمار یکتا اضافه نشده‌اند.
- build، restart، capture و نصب dependency: صفر. runtime اصلی روشن reuse شد؛ ۳۱۱۸ و ۳۱۲۰ دست‌نخورده ماندند.
- زمان تقریبی: آماده‌سازی و نسخه/provenance ۹ دقیقه؛ PostgreSQL و probe DB چهار دقیقه؛ مرورگر و امنیت Origin شش دقیقه؛ گزارش و بازبینی هفت دقیقه؛ مجموع حدود ۲۶ دقیقه.
- اجرا‌نشده طبق دامنه: full backend، کل S08/COMP-EXPERIENCE، D28، تست‌های تاریخی، capture تازه، pixel-perfect جامع و هرگونه ارزیابی production.

قدم بعدی مشخص فقط گیت‌های جداگانهٔ ازپیش‌باز است: تأیید انسانی طراحی، داوری D28 و production readiness باید با مجوز مستقل خود انجام شوند؛ این گزارش مجوز شروع هیچ‌کدام نیست.
