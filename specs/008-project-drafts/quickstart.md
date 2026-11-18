# بازتولید A1
از http://127.0.0.1:3108 وارد شوید؛ منوی حساب ← پیش‌نویس‌های من، مالک فردی یا درخواست سازمان، پروژه جدید. اطلاعات/مسیرها را تکمیل و «ذخیره پیش‌نویس» بزنید؛ رسید شناسه/نسخه. خروج و ورود مجدد یا دستگاه دوم همان پیش‌نویس را باز کند. پنل فایل رزرو/دریافت/بررسی را نشان می‌دهد؛ تنها clean قابل دریافت است. حذف/سطل حذف/بازیابی مستقل‌اند.
فرمان‌های واقعی و نسخه نهایی در docs/stage5/a1-report.md ثبت می‌شوند؛ pytest استاندارد backend/tests/test_workspace*.py روی DB آزمون PG؛ Playwright frontend/tests/browser/workspace.spec.ts؛ job: python manage.py workspace_jobs --once یا حلقه زمان‌بندی compose.
اطلاعات مصنوعی؛ ابزار اعطای نقش عمومی وجود ندارد. fixture تست درخواست approved و Representation می‌سازد. قطع scanner، متن را از ذخیره محروم نمی‌کند؛ فایل pending می‌ماند. صندوق/فروش، ارسال و انتشار فعال نیستند.


## فرمان‌های بازتولید
از ریشه پروژه، با env موجود و بدون چاپ مقادیر آن:

```bash
# فقط در محیط تازه: ابزار scanner و CVD معتبر را آماده کنید.
./deploy/prepare-scanner.sh
docker compose --env-file .env -f deploy/compose.yaml build backend web
docker compose --env-file .env -f deploy/compose.yaml up -d db scanner
docker compose --env-file .env -f deploy/compose.yaml run --rm backend /app/.venv/bin/python manage.py migrate --noinput
docker compose --env-file .env -f deploy/compose.yaml up -d backend web workspace-jobs
# pytest فقط test_ PostgreSQL؛ image تست در محیط تازه با lock جاری ساخته شود.
docker compose --env-file .env -f deploy/compose.yaml build test
docker compose --env-file .env -f deploy/compose.yaml run --rm test /app/.venv/bin/pytest -q tests/test_catalog.py tests/test_values.py tests/test_values_fixes.py tests/test_workspace.py tests/test_workspace_files.py tests/test_workspace_acceptance.py tests/test_workspace_concurrency.py
```

برای مرورگر، DB موجود invest_browser فقط مصنوعی است. آن را با profile browser-api و تنظیم tests.browser_settings، image همان invest-backend و migrate آماده کنید؛ overlay `deploy/compose.workspace-test.yaml` همان تنظیم آزمون نهایی است. کانتینر باید `invest-a1-browser-api` نام داشته باشد. برای frontend همان invest-web روی شبکه اختصاصی `invest-a1-review` با alias `backend` برای API و port3109 استفاده شود؛ env یا دادهٔ اصلی جایگزین نشود. نمونه فرمان‌های همین تحویل:

```bash
docker compose --env-file .env -f deploy/compose.yaml -f deploy/compose.workspace-test.yaml run --rm browser-api /app/.venv/bin/python manage.py migrate --noinput
docker compose --env-file .env -f deploy/compose.yaml -f deploy/compose.workspace-test.yaml run --rm -d --name invest-a1-browser-api --service-ports browser-api /app/.venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 40
docker network create invest-a1-review
docker network connect --alias backend invest-a1-review invest-a1-browser-api
docker run -d --name invest-a1-review-web --network invest-a1-review -p 127.0.0.1:3109:3000 invest-web
# از frontend با Node قفل‌شده و dependency موجود:
A1_RESTART=1 npx playwright test -c playwright.workspace.config.ts
A1_WIDTH=390 A1_SCREEN_PREFIX=mobile- npx playwright test -c playwright.workspace.config.ts --grep 'A1 journey'
```

در تحویل فعلی سرویس‌ها آماده‌اند؛ create/runهای کانتینر موجود تکرار نشوند. خروجی پیش‌فرض این config در .tools است و شواهد ثبت‌شده را بازنویسی نمی‌کند. تنها fixture امن EICAR استفاده می‌شود. تکرار زیاد ورود می‌تواند سقف واقعی۳۰صدور در۱۵دقیقه IP آزمون را پر کند؛ قواعد سهمیه تغییر نکنند. پاک‌سازی fixture فقط با assert نامDB آزمون و INVEST_ENV=test مجاز است؛ داده اصلی هرگز reset نشود.
