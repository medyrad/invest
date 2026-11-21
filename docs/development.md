# اجرای محلی invest — محصول تا S08

این راهنما زیرساخت مشترک محصول تا S08 را اجرا می‌کند. مسیرهای فرصت، پیش‌نویس، انتشار، کشف، مقایسه، منتخب، پرونده و خدمات تخصصی حاضرند؛ OpenAI/S09، اتصال بیرونی F40 و عرضهٔ عمومی حاضر نیستند. گزارش‌های جاری در [هسته](core-delivery/report.md) و [S08](stage8/report.md) هستند. همه فرمان‌ها از ریشه مخزن هستند. Docker Engine/Compose و Python3 برای ساخت فایل env لازم‌اند؛ اجرای بک‌اند به Python میزبان وابسته نیست. imageها برای Linux/amd64 قفل شده‌اند؛ پشتیبانی معماری دیگر آزموده نشده است.

## شروع از محیط خالی

```sh
python3 scripts/dev_runtime.py up --build
```

`dev_runtime.py` در اجرای اول `dev_env.py` را برای ساخت رازهای تصادفی با مجوز 0600 فراخوانی می‌کند و در اجراهای بعد فقط سه مقدار عمومی `WEB_PORT`، `DJANGO_ALLOWED_HOSTS` و `CSRF_TRUSTED_ORIGINS` را همگام می‌کند؛ هیچ راز یا مقدار خصوصی چاپ نمی‌شود. برای پورت دیگر، مثلاً `WEB_PORT=43108 python3 scripts/dev_runtime.py up`، دقیقاً originهای `localhost:43108` و `127.0.0.1:43108` تولید و در startup بک‌اند دوباره اعتبارسنجی می‌شوند. wildcard و origin سوم رد می‌شود. بدون تغییر image از `python3 scripts/dev_runtime.py up` یا `make up` استفاده کنید.

این مسیر DB و scanner محلی را تا سلامت آماده، سپس migration، catalog نسخه‌دار و seed مصنوعی چندشهری را پیش از بالا آوردن backend/web/worker اجرا می‌کند. seed فقط در development/test مجاز، idempotent و مبتنی بر همان گردش draft، بررسی مستقل و publication است. UI فقط `/api/v1/core/opportunities` را به‌عنوان منبع فرصت می‌خواند؛ endpoint قدیمی fixture preview حذف شده است. فایل واقعی `.env` را commit یا در خروجی اشکال‌زدایی چاپ نکنید. شروع عمومی با مقادیر نمایشی، debug یا OTP نمایشی رد می‌شود و `PUBLIC_LAUNCH_ENABLED=true` مجاز نیست.

پوستهٔ اصلی development در http://127.0.0.1:3108 و http://localhost:3108 و API در همان مبدأ `/api/v1/health/live`، `/health/ready`، `/auth/csrf` و `/schema` است. هر دو alias در یک پورت دقیق برای CSRF معتبرند؛ origin دیگر 403 با کد `csrf_failed` و راهنمای امن تازه‌سازی/نشانی رسمی می‌گیرد. DB فقط localhost55432؛ backend فقط شبکه داخلی؛ volume پروژه `invest_pgdata`. Composeهای پروژه‌های دیگر مستقل می‌مانند.

نام پروژه `invest` و پورت را پیش از اجرا با محیط خود تطبیق دهید؛ ابزار runtime همگامی port/origin را انجام می‌دهد و ابزار smoke فعلاً پورت پیش‌فرض 3108 را می‌آزماید. `docker compose config` می‌تواند مقادیر خصوصی را چاپ کند؛ برای بررسی ساختار از `config --quiet` استفاده کنید.

## آزمون بک‌اند و migration

```sh
docker compose --env-file .env -f deploy/compose.yaml run --rm test
docker compose --env-file .env -f deploy/compose.yaml run --rm test /app/.venv/bin/ruff check . --no-cache
docker compose --env-file .env -f deploy/compose.yaml run --rm test /app/.venv/bin/ruff format --check . --no-cache
docker compose --env-file .env -f deploy/compose.yaml run --rm backend /app/.venv/bin/python manage.py makemigrations --check --dry-run
docker compose --env-file .env -f deploy/compose.yaml run --rm backend /app/.venv/bin/python manage.py migrate --check
docker compose --env-file .env -f deploy/compose.yaml run --rm backend /app/.venv/bin/python manage.py check
```

pytest روی PostgreSQL واقعی و DB جدا `test_invest` اجرا می‌شود. نقش محلی ایجاد DB آزمون را دارد؛ این تنظیم نقش دیتابیس، الگوی مجوز production نیست. test image شامل وابستگی توسعه است؛ runtime فقط وابستگی‌های اجرا را دارد. پس از تغییر کد، image مربوط را rebuild کنید. `uv sync --locked` داخل build با lock ناسازگار شکست می‌خورد؛ `.python-version` نسخه داخل کانتینر را هم مستند می‌کند. فهرست داخلی uv0.11.32 در این میزبان Python3.14.10 را نداشت؛ به همین دلیل مسیر مستند و CI از image رسمی همان نسخه استفاده می‌کند.

برای تولید migration جدید بدون تغییر مالکیت فایل میزبان:

```sh
docker compose --env-file .env -f deploy/compose.yaml run --rm --user "$(id -u):$(id -g)" -v "$PWD/backend/apps:/app/apps" backend /app/.venv/bin/python manage.py makemigrations
```

## فرانت و مرورگر

### حالت توسعهٔ فرانت با HMR

```sh
make dev
```

این فرمان runtime اصلی را بالا می‌آورد، بک‌اند را با `deploy/compose.dev.yaml` فقط روی `127.0.0.1:8018` منتشر می‌کند، کانتینر `web` را متوقف می‌کند و `next dev` را روی `WEB_PORT` (پیش‌فرض 3108) به همان بک‌اند اجرا می‌کند. تغییرات فرانت بدون build دوباره دیده می‌شوند. Ctrl+C فقط `next dev` را می‌بندد؛ برای توقف بقیه `make stop` و برای بازگشت به وب build‌شده `make up`.

کارهایی که خودکار انجام می‌شوند:

- اگر Node نصب‌شده با `.nvmrc` یکی نباشد، پیش از هر کار کند با راهنمای نصب متوقف می‌شود.
- اگر پورت وب اشغال باشد (مثلاً `make dev` دیگری باز است)، در چند ثانیه با پیام روشن متوقف می‌شود.
- اگر پورت DB (`POSTGRES_PORT`) را برنامهٔ دیگری گرفته باشد، اولین پورت آزاد بعدی در `.env` ثبت و اعلام می‌شود.
- اگر کد بک‌اند از آخرین build تغییر کرده باشد، image بک‌اند دوباره build می‌شود. برای build اجباری: `make dev BUILD=1`.
- اگر `package-lock.json` تغییر کرده یا اجرای اول باشد، `npm ci` اجرا می‌شود.
- اگر پورت 8018 اشغال باشد، با پورت دیگر اجرا کنید: `make dev BACKEND_DEV_PORT=8028`.

### راه‌اندازی در Windows با WSL

همه چیز داخل WSL اجرا می‌شود، نه در PowerShell یا CMD. این مسیر روی Windows واقعی هنوز آزموده نشده است.

1. WSL 2 و Ubuntu را نصب کنید (`wsl --install` در PowerShell با دسترسی Administrator، سپس راه‌اندازی دوبارهٔ سیستم).
2. Docker Desktop را نصب کنید و در Settings → Resources → WSL integration گزینهٔ Ubuntu را روشن کنید. در ترمینال Ubuntu باید `docker compose version` کار کند.
3. در ترمینال Ubuntu ابزارها را نصب کنید:

```sh
sudo apt update && sudo apt install -y make git python3
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
```

ترمینال را ببندید و دوباره باز کنید، سپس:

```sh
nvm install 24.22.3
```

4. مخزن را داخل فایل‌سیستم WSL clone کنید، مثلاً `~/invest`، نه زیر `/mnt/c/...`. مسیر Windows کند است و بازخوانی خودکار فرانت در آن قابل اعتماد نیست.
5. از ریشهٔ مخزن `make dev` را اجرا کنید و http://localhost:3108 را در مرورگر Windows باز کنید. اجرای اول به دلیل ساخت imageها چند دقیقه طول می‌کشد.



Node24.22.3 و npm11.19.1 را مطابق `.nvmrc` نصب کنید؛ engine-strict نسخه دیگر را رد می‌کند. بک‌اند probe فقط در profile آزمون و روی localhost8008 فعال می‌شود. URLConf آزمون از production جداست و فقط INVEST_ENV=test را می‌پذیرد.

```sh
docker compose --env-file .env -f deploy/compose.yaml stop browser-api
docker compose --env-file .env -f deploy/compose.yaml run --rm browser-api /app/.venv/bin/python -m tests.prepare_browser_db
docker compose --env-file .env -f deploy/compose.yaml run --rm browser-api /app/.venv/bin/python manage.py migrate --noinput
docker compose --env-file .env -f deploy/compose.yaml up -d browser-api
cd frontend
npm ci
npm run lint
npm run typecheck
npm run build
npx playwright install --with-deps chromium
npm run test:e2e
```

Playwright سرور standalone را خودش روی3109 آغاز و متوقف می‌کند؛ این runtime ایزولهٔ test است، نه runtime اصلی 3108. مقصد rewrite هنگام build تثبیت می‌شود: build محلی `http://127.0.0.1:8008` و Docker `http://backend:8000`. تغییر env پس از build مقصد را عوض نمی‌کند. API مرورگر هم‌مبدأ است؛ CSRF token از bootstrap body به X-CSRFToken می‌رود، چون cookie HttpOnly است. اعتبار Origin/Referer مطابق سیاست Django است؛ HTTP بدون Origin همچنان به cookie/token معتبر نیاز دارد.

نسخهٔ build در `/core-version.json` و نسخه/نوع runtime بک‌اند در `/api/v1/core/version` دیده می‌شود. پاسخ دوم `environment` و یکی از `primary-development`، `isolated-test` یا `public` را هم برمی‌گرداند؛ بنابراین اجرای evidence روی 3118/3120 یا test روی 3109 با اجرای اصلی اشتباه نمی‌شود.

در شبکه فعلی CDN مرورگر با403 محدودیت محل پاسخ داد. آزمون محلی با Chrome151.0.7922.137 نصب‌شده انجام شد:

```sh
PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/google-chrome npm run test:e2e
```

CI مرورگر بسته Playwright را نصب می‌کند؛ اجرای GitHub و همسانی آن مرورگر هنوز تأیید نشده‌اند. تصویرهای `docs/stage2/evidence/foundation-*.png` فقط پوسته S02 هستند، نه تأیید طراحی صفحات محصول. فونت محلی Vazirmatn33.0.3 و مجوز OFL از مرجع اصلی آمده‌اند.

## ماندگاری و بازیابی

پس از نصب مثبت وابستگی‌های فرانت، `python3 scripts/check_lock_drift.py` روی کپی‌های موقت بررسی می‌کند که uv و npm با manifest/lock ناسازگار شکست بخورند. به فایل‌های واقعی دست نمی‌زند؛ Node صحیح باید در PATH باشد. همین کنترل در CI نیز هست.

```sh
python3 scripts/foundation_smoke.py
```

فقط سرویس‌های invest restart/stop/start می‌شوند. این آزمون دو حساب ساختگی ایجاد می‌کند، ماندگاری آن‌ها پس از restart را می‌سنجد، DB را موقتاً متوقف می‌کند و در finally برمی‌گرداند. live باید200، ready هنگام قطعی503 در کمتر از۸ثانیه و پس از بازگشت200 باشد. هم‌زمان با این آزمون pytest یا کار دیگری روی DB پروژه اجرا نکنید. این آزمون برای محیط محلی است و داده ساختگی را نگه می‌دارد.

```sh
docker compose --env-file .env -f deploy/compose.yaml --profile test stop
```

این فرمان volume را حذف نمی‌کند. `down -v` برای توقف روزمره استفاده نشود. برای شروع مجدد `make up` کافی است. میان‌برهای `make build/check/test/browser/smoke/stop` همین مسیرها را اجرا می‌کنند؛ Node صحیح باید در PATH باشد.

## مرز عرضه

سیاست public و secure cookie به‌صورت مثبت/منفی آزموده شده؛ HTTPS، دامنه، reverse proxy مورداعتماد، HSTS، پشتیبان‌گیری/بازیابی عملیاتی، نقش محدود DB، SMS واقعی و کلید OpenAI هنوز گیت مراحل وابسته هستند. `check --deploy` در پیکربندی public تنها هشدار HSTS را مجاز می‌داند؛ HSTS بدون دامنه/TLS واقعی در S02 فعال نمی‌شود. S02 انتشار عمومی نیست.


## استفاده از ورود آزمایشی S03

در http://127.0.0.1:3108 «ورود به حساب» را باز کنید؛ شماره مصنوعی ایران بدهید و کد شش‌رقمی اعلان همان پنجره را وارد کنید. reload وضعیت را از سرور می‌خواند؛ «خروج» نشست جاری را باطل می‌کند. این محیط پیامک نمی‌فرستد و مالکیت واقعی شماره را تأیید نمی‌کند. کد و token در localStorage/sessionStorage ذخیره نمی‌شوند. نمایش کد پس از انقضا حذف می‌شود.

`make browser` فقط دیتابیس مصنوعی `${POSTGRES_DB}_browser` را آماده/پاک‌سازی می‌کند؛ به DB برنامه دست نمی‌زند. API مرورگر localhost8008 و DB مرورگر از اجرای محلی مستقل‌اند. آزمون‌های بک‌اند همچنان روی `test_invest` اجرا می‌شوند. از داده واقعی در DB آزمون استفاده نکنید. پس از تغییر backend/test کد، image مربوط باید rebuild شود.

شواهد تازه در docs/stage3/evidence هستند؛ گزارش‌ها و تصاویر S02 تاریخی باقی‌اند. آزمون مرورگر چهار عرض۳۶۰/۳۹۰/۷۶۸/۱۴۴۰ دارد. انقضای UI با ساعت مرورگر جلو برده می‌شود؛ مرز انقضای سرور جداگانه روی PostgreSQL آزموده است. paste از clipboard واقعی Chrome استفاده می‌کند. این بررسی دستگاه فیزیکی موبایل نیست.

فقط POST /api/v1/auth/activity موفق مهلت بی‌فعالیتی را تمدید می‌کند و در پوسته دکمه صریح دارد؛ me و polling و health خیر. راهنمای API، بازیابی پاسخ گم‌شده، نیت ادامه و قیود امنیتی در specs/005-identity-session/contracts/api.md است. روش واقعی ورود حساس، SMS، ظرفیت، نگهداری/بازیابی عملیاتی و پذیرش انسانی طراحی همچنان گیت جدا دارند.
