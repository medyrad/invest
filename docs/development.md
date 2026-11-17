# اجرای محلی invest — زیرساخت و ورود آزمایشی S03

ورود و خروج آزمایشی S03 به زیرساخت S02 اضافه شده است؛ گزارش و محدوده در [گزارش S03](stage3/report.md) است. صفحات کامل محصول، فرصت/پرونده و AI هنوز در این تحویل نیستند. همه فرمان‌ها از ریشه مخزن هستند. Docker Engine/Compose و Python3 برای ساخت فایل env لازم‌اند؛ اجرای بک‌اند به Python میزبان وابسته نیست. imageها برای Linux/amd64 قفل شده‌اند؛ پشتیبانی معماری دیگر آزموده نشده است.

## شروع از محیط خالی

```sh
python3 scripts/dev_env.py
docker compose --env-file .env -f deploy/compose.yaml build backend web test browser-api
docker compose --env-file .env -f deploy/compose.yaml up -d db
docker compose --env-file .env -f deploy/compose.yaml run --rm backend /app/.venv/bin/python manage.py migrate --noinput
docker compose --env-file .env -f deploy/compose.yaml up -d backend web
```

`dev_env.py` رازهای تصادفی را فقط در `.env` با مجوز0600 می‌نویسد؛ فایل موجود را تغییر نمی‌دهد. فایل واقعی را commit یا در خروجی اشکال‌زدایی چاپ نکنید. `.env.example` صرفاً الگو است. شروع عمومی با مقادیر نمایشی، debug یا OTP نمایشی رد می‌شود. `PUBLIC_LAUNCH_ENABLED=true` در S02 مجاز نیست.

پوسته در http://127.0.0.1:3108 و API در همان مبدأ `/api/v1/health/live`، `/health/ready`، `/auth/csrf` و `/schema` است. DB فقط localhost55432؛ backend فقط شبکه داخلی؛ volume پروژه `invest_pgdata`. Composeهای پروژه‌های دیگر مستقل می‌مانند. migration را پیش از شروع workerها با فرمان مستقل اجرا کنید.

نام پروژه `invest` و پورت‌ها را پیش از اجرا با محیط خود تطبیق دهید. تغییر WEB_PORT باید همراه CSRF_TRUSTED_ORIGINS باشد؛ ابزار smoke فعلاً پورت پیش‌فرض3108 را می‌آزماید. `docker compose config` می‌تواند مقادیر خصوصی را چاپ کند؛ برای بررسی ساختار از `config --quiet` استفاده کنید.

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

Playwright سرور standalone را خودش روی3109 آغاز و متوقف می‌کند. مقصد rewrite هنگام build تثبیت می‌شود: build محلی `http://127.0.0.1:8008` و Docker `http://backend:8000`. تغییر env پس از build مقصد را عوض نمی‌کند. API مرورگر هم‌مبدأ است؛ CSRF token از bootstrap body به X-CSRFToken می‌رود، چون cookie HttpOnly است. اعتبار Origin/Referer مطابق سیاست Django است؛ HTTP بدون Origin همچنان به cookie/token معتبر نیاز دارد.

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
