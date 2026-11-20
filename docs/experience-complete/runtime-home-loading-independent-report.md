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
