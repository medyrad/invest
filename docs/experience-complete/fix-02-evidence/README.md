# شواهد PROGRAMMER-EXPERIENCE-FIX-02

این پوشه فقط شواهد تازه EXP-IT-003 را نگه می‌دارد. مبنا `32b3410`، PostgreSQL ایزوله compose `invest-expit` و backend image با digest `sha256:b26f984ef72b1cc63895c7bca0f481d83030679a9270d7e17d9e07825205a7df` است. شواهد مستقل تاریخی فقط read-only mount شدند.

- `backend-final.xml`: اجرای تجمیعی ۲۱ node، ۲۱ قبول؛ شامل هشت route، برابری قرارداد/واژه‌نامه، unknown تاریخی، snapshot/download/redownload، rendererهای مرتبط و node مستقل قبلاً شکست‌خورده.
- `browser-report.xml`: یک سفر واقعی Chromium؛ preview، دانلود اول و دریافت مجدد با label فارسی و بایت یکسان، ۱ قبول.
- `browser-preview.png` و `browser-redownload.png`: مشاهده واقعی قبل و بعد دریافت؛ تصویر به‌تنهایی پذیرش طراحی نیست.
- `fresh-report.html`: سند مصنوعی تازه و بدون راز؛ snapshot قدیمی نیست.
- `runtime.override.yaml`: فقط جایگزینی backend در compose مستقل؛ frontend و DB بازسازی نشدند.

## بازتولید

از ریشه مخزن:

```sh
docker build --target runtime -f deploy/backend.Dockerfile -t investexpfix02-backend .
docker compose -p invest-expit -f .tools/expit/compose.yaml -f docs/experience-complete/fix-02-evidence/runtime.override.yaml up -d --no-deps backend
```

اجرای backend با mount فقط‌خواندنی شاهد مستقل و خروجی جدا:

```sh
docker compose -p invest-expit -f .tools/expit/compose.yaml run --rm -v /Users/mehdi/Projex/invest/docs/experience-complete/retest-01-evidence:/independent:ro -v /Users/mehdi/Projex/invest/docs/experience-complete/fix-02-evidence:/fix02 test /app/.venv/bin/pytest -q tests/test_experience_fix.py::test_report_semantic_sections_preview_download_and_history tests/test_experience_fix.py::test_report_document_design_and_effective_content_are_snapshot_only tests/test_experience_fix.py::test_report_uses_versioned_persian_label_for_every_contract_route tests/test_experience_fix.py::test_versioned_route_vocabulary_exactly_covers_existing_route_contract tests/test_experience_fix.py::test_unknown_historical_route_is_explicit_and_never_guessed tests/test_experience_fix.py::test_preview_first_download_and_redownload_share_label_but_old_html_stays_frozen tests/test_experience_fix.py::test_real_template_one_snapshot_shapes_are_readable_and_honest tests/test_core.py::test_saved_search_update_is_atomic_and_report_redownload_is_readable tests/test_core.py::test_personal_isolation_report_no_case tests/test_core.py::test_operator_work_period_roundtrip_hidden_restore_public_and_report /independent/test_retest_independent.py::test_report_route_enum_is_human_readable_persian --reuse-db --junitxml=/fix02/backend-final.xml
```

مرورگر:

```sh
docker run --rm --network host -e NODE_PATH=/repo/frontend/node_modules -v /Users/mehdi/Projex/invest/frontend:/repo/frontend:ro -v /Users/mehdi/Projex/invest/docs/experience-complete/fix-02-evidence:/evidence -w /repo/frontend mcr.microsoft.com/playwright:v1.65.1-noble node node_modules/@playwright/test/cli.js test -c /evidence/playwright.config.cjs
```

شبکه host فقط برای دسترسی Chromium ایزوله به localhost:3118 و secure-context لازم است؛ سرویس دیگری تغییر نمی‌کند.
