# شواهد TEST-EXPERIENCE-FIX-02-RETEST

این پوشه فقط شواهد تازه بازآزمایی مستقل `EXP-IT-003` را نگه می‌دارد. مبنای مستقل `32b3410`، commit کد `18b6c6e15de5d52f3d803c6a5fdc36062f37b56f` و commit تحویل `53af2c6931d06f28f284e1f0b7acae412b5f687e` است.

- `test_fix02_retest_independent.py`: ۱۴ سناریوی مستقل backend؛ قرارداد هشت route، fail صریح missing/extra، همه labelها، unknown، preview/download/redownload، اختیار، CSP، snapshot و HTML قدیمی منجمد.
- `independent-backend.xml`: نتیجه نهایی ۱۴/۱۴.
- `prior-failing-node.xml`: اجرای مستقل node قبلاً شکست‌خورده، ۱/۱؛ با سناریوی investor هم‌پوشان است و دوباره در شمار یکتا نیامده است.
- `product-regression.xml`: ۱۳/۱۳ node مستقیم محصول؛ شاهد کمکی رگرسیون است، نه مبنای پذیرش مستقل.
- `browser-report.spec.ts` و `browser-report.xml`: یک سفر واقعی Chromium از preview تا دانلود اول و دریافت مجدد.
- `browser-preview.png` و `browser-redownload.png`: مشاهده تازه قبل و بعد دریافت؛ تصویر به‌تنهایی امضای طراحی نیست.
- `fresh-report.html`: HTML مصنوعی تازه؛ route فارسی دارد و enum خام ندارد.
- `provenance.txt`: checkout، image، runtime hash، PostgreSQL و نتایج.

## فرمان‌های اصلی

```sh
docker compose -p invest-expit -f .tools/expit/compose.yaml run --rm \
  -v /Users/mehdi/Projex/invest/docs/experience-complete/fix-02-retest-evidence:/retest \
  test /app/.venv/bin/pytest -q /retest/test_fix02_retest_independent.py \
  --reuse-db --junitxml=/retest/independent-backend.xml
```

```sh
docker compose -p invest-expit -f .tools/expit/compose.yaml run --rm \
  -v /Users/mehdi/Projex/invest/docs/experience-complete/retest-01-evidence:/independent:ro \
  -v /Users/mehdi/Projex/invest/docs/experience-complete/fix-02-retest-evidence:/retest \
  test /app/.venv/bin/pytest -q \
  /independent/test_retest_independent.py::test_report_route_enum_is_human_readable_persian \
  --reuse-db --junitxml=/retest/prior-failing-node.xml
```

```sh
docker run --rm --network host \
  -e NODE_PATH=/repo/frontend/node_modules \
  -v /Users/mehdi/Projex/invest/frontend:/repo/frontend:ro \
  -v /Users/mehdi/Projex/invest/docs/experience-complete/fix-02-retest-evidence:/evidence \
  -w /repo/frontend mcr.microsoft.com/playwright:v1.65.1-noble \
  node node_modules/@playwright/test/cli.js test -c /evidence/playwright.config.cjs
```

اجرای نهایی مستقل backend پس از افزودن کنترل endpoint برای unknown یک بار بازاجرا شد. اجرای نخست backend فقط به دو اشکال harness (fixture بیرونی discover نشده و assertion بیش‌ازحد محدود درباره metadata واژه‌نامه) خورد. اجرای نخست مرورگر نیز به origin غیر secure harness خورد؛ اجرای نهایی با `--network host` و `127.0.0.1:3118` انجام شد. هیچ‌یک شکست محصول شمرده نشده است.

