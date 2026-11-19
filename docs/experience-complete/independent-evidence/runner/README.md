# بازتولید مستقل

این runnerها متعلق به TEST-EXPERIENCE-COMPLETE-01 هستند؛ انتظار تست‌های شکست‌خورده برای سبزشدن تغییر داده نشده است. فایل test_experience_independent.py یک سطح بالاتر قرار دارد.

## محیط

از imageهای ثبت‌شده در گزارش، شبکه Docker مستقل و PostgreSQL17.12 با داده مصنوعی استفاده کنید. DB فعال پروژه را هدف نگیرید. تنظیمات expit_settings.py فقط timeout محیط آزمون را۳۰ثانیه می‌کند. `DJANGO_SECRET_KEY` تصادفی جدید را خارج مخزن تولید کنید؛ مقدار runtime یا فایل .env واقعی را کپی نکنید.

mountها: backend جاری→`/src:ro`، runner→`/checks:ro`، پوشه شواهد تازه→`/evidence:rw`، وابستگی Playwright1.65.1→`/pw:ro`؛ `PYTHONPATH=/checks:/src:/app`، `DJANGO_SETTINGS_MODULE=expit_settings`، `INVEST_ENV=test`. سرویس backend به DB synthetic و hostname `backend`، web هم‌نسخه به backend همین شبکه وصل باشد. proxy.cjs پورت۳۱۰۹ داخل container مرورگر را به web:3000 وصل می‌کند و Origin را حفظ می‌کند. CSRF_TRUSTED_ORIGINS باید همین مبدأ آزمون را بپذیرد.

فرمان‌های محصول:

```sh
/app/.venv/bin/pytest -q tests/test_identity.py tests/test_identity_races.py tests/test_core.py --create-db --junitxml=/evidence/existing.xml
/app/.venv/bin/pytest -q /evidence/test_experience_independent.py --create-db --junitxml=/evidence/independent.xml
/app/.venv/bin/pytest -q tests/test_services.py -k report_escape_and_current_authority --create-db
```

runnerهای DB را هم‌زمان با نام DB یکسان اجرا نکنید. تست مستقل از helperهای fixture پروژه استفاده می‌کند ولی انتظار inactive/HTML/مالکیت را خود تعیین می‌کند.

برای مرورگر، پس از seed کامل شش فرصت و پنج نقش مصنوعی، `node /checks/proxy.cjs` و سپس `node /pw/node_modules/@playwright/test/cli.js test --config=/checks/playwright.config.cjs` اجرا شوند؛ `NODE_PATH=/pw/node_modules`. suiteهای saved و profile باید ترتیبی اجرا شوند تا اسم نمایشی مصنوعی/داده قبلی باعث ابهام نشود. local-role انتخاب بر مبنای role است؛ نام نمایشی ممکن است توسط خود آزمون تغییر کند.

تست تاریخی `frontend/tests/browser/experience-complete.spec.ts` بدون تغییر assertion اجرا شد؛ تنها مسیر evidence در کپی موقت به `/evidence/existing-browser` تغییر کرد. آن کپی تکراری اینجا ثبت نشده است. دو مورد ابتدایی قبل از تکمیل seed شکست خوردند و فقط همان دو مورد دوباره اجرا شدند.

## مرجع و تصاویر

آرشیو هم‌هش را فقط زیر .tools باز کنید؛ `npm ci --ignore-scripts` و اجرای مستقیم `node node_modules/next/dist/bin/next dev --hostname 0.0.0.0 --port 3107` در container دارای تنها mount همان کپی. نام شبکه‌ای مرجع در runner `expit-reference` است. source دستور اجرایی پروژه نیست. فونت، reducedMotion، viewport و حالت خالی در مقایسه‌ها کنترل شده‌اند؛ image مرجع dev است و نشان dev، اختلاف محصول محسوب نمی‌شود.

full-page ممکن است پیش از تکمیل schema یا در RTL اندازه متفاوت بدهد؛ تصاویر را علاوه بر viewport با گروه بارگذاری‌شده/networkidle کنترل کنید. clipping.spec.ts مستقل از screenshot، ancestor clip و hit-test و کلیک واقعی را می‌سنجد. report-view.cjs فقط HTML تازه دانلودشده را برای مشاهده بصری باز می‌کند؛ تست مستقل جدیدی به شمار نمی‌افزاید.

ردیابی علل خطاهای harness/محیط و تست‌های بازآزمایی‌شده در گزارش اصلی است. traceهای خام شامل نشست مصنوعی ممکن است در working tree باشند، اما عمداً ignore و از commit حذف شده‌اند؛ برای بازتولید trace تازه بسازید.
