# شواهد اصلاح تجمیعی تجربه

مأموریت `PROGRAMMER-EXPERIENCE-FIX-01`، مبنا `c7ac09b`.
شواهد مستقل قبلی فقط خوانده می‌شوند. خروجی‌های بازتولید، regression و manifest تازه در همین پوشه ثبت می‌شوند؛ trace خام نشست وارد commit نمی‌شود.

## بازتولید در محیط مستقل آماده

فقط compose `invest-expit`، PostgreSQL tmpfs مصنوعی و پورت۳۱۱۸؛ نه compose فعال پروژه. تنظیمات آماده `.tools/expit` و وابستگی `.tools/pw-min` متعلق به آماده‌سازی مستقل تسترند. اگر موجود نیستند، همان تنظیمات runner مستقل را در محیط ایزوله بازسازی کنید؛ secrets محیط واقعی کپی نشوند.

```sh
docker build -f deploy/backend.Dockerfile --target runtime -t investexpfix-backend .
docker build -f deploy/frontend.Dockerfile -t investexpfix-web .
docker compose -f .tools/expit/compose.yaml -f docs/experience-complete/fix-01-evidence/runtime.override.yaml up -d db
docker compose -f .tools/expit/compose.yaml -f docs/experience-complete/fix-01-evidence/runtime.override.yaml run --rm -v "$PWD/docs/experience-complete/fix-01-evidence:/evidence" backend /app/.venv/bin/python manage.py migrate --noinput
docker compose -f .tools/expit/compose.yaml -f docs/experience-complete/fix-01-evidence/runtime.override.yaml run --rm -v "$PWD/docs/experience-complete/fix-01-evidence:/evidence" backend /app/.venv/bin/python manage.py shell -c "exec(open('/checks/seed.py').read())"
docker compose -f .tools/expit/compose.yaml -f docs/experience-complete/fix-01-evidence/runtime.override.yaml up -d --no-deps backend web
```

seed فقط روی DB تازه مصنوعی؛ scanner در fixture mock است. برای rerun بعد از آزمونی که نام مشتری را عوض می‌کند، فقط همان synthetic fixture را بازگردانید:

```sh
docker compose -f .tools/expit/compose.yaml -f docs/experience-complete/fix-01-evidence/runtime.override.yaml run --rm -v "$PWD/docs/experience-complete/fix-01-evidence:/evidence" backend /app/.venv/bin/python manage.py shell -c "exec(open('/evidence/restore-synthetic-name.py').read())"
```

### سرور

```sh
docker compose -f .tools/expit/compose.yaml run --rm -v "$PWD/docs/experience-complete/fix-01-evidence:/evidence" -v "$PWD/docs/experience-complete/independent-evidence:/independent:ro" test /app/.venv/bin/pytest -q /independent/test_experience_independent.py tests/test_experience_fix.py tests/test_core.py tests/test_identity.py tests/test_services.py -k 'personal or profile or report or intent or handoff or search_edit or inactive_answer or residential_presale or search_validation or concurrent_search or cancel_after_consume' --create-db --junitxml=/evidence/backend-verified.xml
docker compose -f .tools/expit/compose.yaml run --rm -v "$PWD/docs/experience-complete/fix-01-evidence:/evidence" -v "$PWD/docs/experience-complete/independent-evidence:/independent:ro" test /app/.venv/bin/pytest -q /independent/test_experience_independent.py -k history_other_session --reuse-db --junitxml=/evidence/history-verified.xml
docker compose -f .tools/expit/compose.yaml run --rm -v "$PWD/docs/experience-complete/fix-01-evidence:/evidence" test /app/.venv/bin/ruff check --no-cache apps/core apps/identity/otp.py tests/test_experience_fix.py
docker compose -f .tools/expit/compose.yaml run --rm -v "$PWD/docs/experience-complete/fix-01-evidence:/evidence" test /app/.venv/bin/python manage.py makemigrations --check --dry-run
```

### مرورگر و مرجع

مرجع موجود `expit-reference:3107` باید healthy و همان ZIP باشد؛ وابستگی آن قبلاً زیر `.tools` آماده شده است. دستور اجرا از این گزارش است، نه دستورهای آرشیو:

```sh
docker run -d --rm --name expit-reference --network invest-expit_default -v "$PWD/.tools/product-audit-osgcnW/Investment_Advisor-main:/reference" -w /reference mcr.microsoft.com/playwright:v1.65.1-noble node node_modules/next/dist/bin/next dev --hostname 0.0.0.0 --port 3107
docker run --rm --name invest-expfix-final --network invest-expit_default -v "$PWD/docs/experience-complete/fix-01-evidence:/checks:ro" -v "$PWD/docs/experience-complete/independent-evidence/runner:/independent:ro" -v "$PWD/docs/experience-complete/fix-01-evidence:/evidence" -v "$PWD/.tools/pw-min:/pw:ro" -e NODE_PATH=/pw/node_modules mcr.microsoft.com/playwright:v1.65.1-noble sh -c 'node /independent/proxy.cjs & node /pw/node_modules/@playwright/test/cli.js test --config=/checks/playwright.config.cjs'
```

اگر container مرجع موجود است دوباره ساخته نشود. آزمون ترتیبی workers=1 و بدون retries خودکار است. برای بازتولید تازه، خروجی را به زیرپوشه جدید بدهید؛ فایل‌های تحویل commit‌شده را overwrite نکنید. capture با قضاوت طراحی متفاوت است؛ شکاف‌ها در گزارش اصلی آمده‌اند.

برای اجرای اثرمحور نهایی همان فرمان مرورگر را با `--config=/checks/playwright-final-impact.config.cjs` اجرا کنید (۹سناریو: دانلود،۴انتخاب‌گر،۴capture پروفایل). آخرین تغییر فقط چیدمان پروفایل saved بود؛ `playwright-visual-rerun.config.cjs` چهار capture و شرط تک‌ستونه زیر۱۰۲۴ را دوباره می‌سنجد. runner اصلی مستقل و assertionهای آن تغییر نکرده‌اند؛ فهرست snapshotهای مرجع فقط پس از آماده‌شدن فرم capture می‌شود. build و ترتیب اجرا در manifest آمده است.

آزمون formatter متن با منبع واقعی فرانت:

```sh
docker run --rm --name invest-expfix-text --network invest-expit_default -v "$PWD/frontend:/source:ro" -v "$PWD/docs/experience-complete/fix-01-evidence:/checks:ro" -v "$PWD/docs/experience-complete/fix-01-evidence:/evidence" -v "$PWD/.tools/pw-min:/pw:ro" -e NODE_PATH=/pw/node_modules mcr.microsoft.com/playwright:v1.65.1-noble node /pw/node_modules/@playwright/test/cli.js test --config=/checks/playwright-text.config.cjs
```

آزمون‌های capture را هم‌زمان با runner دیگری که همان پوشه artifact را پاک/ایجاد می‌کند اجرا نکنید. گذر capture به معنی تطابق طراحی نیست؛ تفاوت‌های ثبت‌شده در گزارش همچنان بازند.
