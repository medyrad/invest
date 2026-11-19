# شواهد ادامه PROGRAMMER-EXPERIENCE-FIX-01

مبنا: `2affb4544f49f42a400f76ae2bb91d1d75c5148e`. همه اجراها روی compose ایزوله `invest-expit`، PostgreSQL tmpfs و داده مصنوعی انجام شده‌اند. سرویس فعال پروژه و داده واقعی لمس نشده است. گزارش/runner مستقل تاریخی overwrite نشده‌اند.

## نسخه اجراشده

- frontend image: `sha256:40072e8c08fd71658ff709b42aa3e46fa5e2050d7740397cdfdc3c7c5e307a49`
- Next BUILD_ID: `myZDM7kEa-Q6fjMutJW5o`
- backend image: `sha256:24149525c9843cc9bf520eb1ce8f83d3a34c53a2dfa401055d5ab5dace25988f`
- مرجع: `/Users/mehdi/Downloads/Investment_Advisor-main.zip` با SHA256=`6221401c736250c5ac7e5595aa988301f64b8d2fe576590291a7c2e53c247f5b`
- مرورگر: Playwright image `mcr.microsoft.com/playwright:v1.65.1-noble`؛ عرض‌ها ۳۶۰/۳۹۰/۷۶۸/۱۴۴۰، ارتفاع ۱۰۰۰، reducedMotion و انتظار `document.fonts.ready`.

## نتیجه یکتا

- PostgreSQL اصلی: `backend-final-primary.xml`، تعداد **۲۱ قبول** در ۴۴٫۸۰۴ثانیه؛ شامل تمام ۱۲ تست مستقل COMP-EXPERIENCE و ۹ رگرسیون جدید.
- PostgreSQL مکمل: `backend-final-supplement.xml`، تعداد **۱۳ قبول** در ۱۲٫۲۸۰ثانیه؛ union بک‌اند **۳۴ آزمون یکتا**.
- مرورگر تجمیعی: `browser-continuation.xml`، تعداد **۱۹ قبول** در ۲۱۴٫۳۳۹ثانیه؛ شامل ۴ مرجع هم‌شرایط، ۴ فرم حرفه‌ای، ۴ سفر سه‌مرحله‌ای زمین، ۵ خطای QuickProfile، یک کلیک واقعی منو هنگام refresh و یک گزارش واقعی.
- کیفیت: `ruff check --no-cache apps/core tests/test_experience_fix.py` قبول؛ `makemigrations --check --dry-run` بدون تغییر؛ frontend Docker build شامل TypeScript و static generation قبول.
- `backend-targeted.xml` و اجراهای هدفمند میانی rerun تشخیصی‌اند و به شمار یکتا افزوده نمی‌شوند. یک شکست تاریخی مکمل، نبود دو عنوان قراردادی قدیمی در طراحی تازه را آشکار کرد؛ عنوان‌ها حفظ و کل ۱۳تایی دوباره سبز شد.

## بازتولید

```sh
docker compose -f .tools/expit/compose.yaml -f docs/experience-complete/fix-01-continuation-evidence/runtime.override.yaml up -d db backend web

docker compose -f .tools/expit/compose.yaml run --rm \
  -v "$PWD/specs:/specs:ro" \
  -v "$PWD/docs/experience-complete/fix-01-continuation-evidence:/continuation-evidence" \
  -v "$PWD/docs/experience-complete/independent-evidence:/independent:ro" \
  test /app/.venv/bin/pytest -q \
  /independent/test_experience_independent.py tests/test_experience_fix.py \
  --create-db --junitxml=/continuation-evidence/backend-final-primary.xml

docker run --rm --network invest-expit_default \
  -v "$PWD/docs/experience-complete/fix-01-continuation-evidence:/checks:ro" \
  -v "$PWD/docs/experience-complete/independent-evidence/runner:/independent:ro" \
  -v "$PWD/docs/experience-complete/fix-01-continuation-evidence:/evidence" \
  -v "$PWD/.tools/pw-min:/pw:ro" -e NODE_PATH=/pw/node_modules \
  mcr.microsoft.com/playwright:v1.65.1-noble sh -c \
  'node /independent/proxy.cjs & node /pw/node_modules/@playwright/test/cli.js test --config=/checks/playwright.config.cjs'
```

فرمان مکمل دقیق node-idها در گزارش `fix-01-report.md` ثبت شده است. DB test هم‌نام را موازی اجرا نکنید. هر اجرای آینده باید مسیر خروجی جدید داشته باشد تا شواهد تاریخی و این بسته overwrite نشوند.

## زمان

- آماده‌سازی/ممیزی منبع و شکل legacy: stopwatch مستقل از ادامه قبلی حفظ نشده و صفر ادعا نمی‌شود؛ بازه قابل مشاهده از نخستین فایل تغییرکرده ۲۳:۴۷ تا ایجاد runner در ۰۰:۵۶ است و با پیاده‌سازی هم‌پوشان است.
- build: frontend نهایی حدود ۱۰۱ثانیه (compile حدود۴۲، TypeScript حدود۴۱)؛ backend build نهایی cache-warm حدود۱٫۱ثانیه. buildهای backend میانی ۴٫۵ و۲٫۰ثانیه rerun بوده‌اند.
- آزمون نهایی: ۲۷۱٫۴۲۳ثانیه مجموع زمان suiteهای یکتا (۴۴٫۸۰۴ + ۱۲٫۲۸۰ + ۲۱۴٫۳۳۹)، بدون جمع‌زدن rerunهای تشخیصی.
- گزارش/ردیابی: بازه قابل مشاهده ۰۰:۵۶ تا ۰۱:۴۲، با آزمون و بازبینی تصویر هم‌پوشان؛ زمان فعال خالص اندازه‌گیری نشده است.

تصاویر قبول فنی برنامه‌نویس‌اند، نه قبول طراحی انسانی. `actual-report.html` حاوی شناسه تاریخی `unknown` فقط در عبارت صریح «شناسه تاریخی» برای location بدون label منجمد است؛ آن مقدار جعل یا از داده زنده پر نشده و محدودیت همان سند آن را توضیح می‌دهد.
