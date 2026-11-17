# بازبینی و بازتولید این گام

این راهنما برای اسناد/مرجع است؛ دستور اجرای invest هنوز وجود ندارد. cwd ریشهٔ invest و Python 3/Node لازم است. فایل‌های ZIP اصلی تغییر نمی‌کنند. `.tools` خروجی محلی و در gitignore است.

## بررسی اسناد و کاتالوگ

```sh
python3 scripts/catalog_sources.py --advisor /home/mehdirad/Documents/product-management/Investment_Advisor-main.zip --ham /home/mehdirad/Projects/company/hammahalle/ham.zip --check
node scripts/extract_dynamic_catalog.mjs --check
python3 scripts/validate_planning.py
python3 scripts/check_scoring_proposal.py
bash .specify/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks
```

استخراج AST از `.tools/reference/advisor/public/engine/advisor.html` می‌خواند و acorn@8.15.0 در `.tools/audit` لازم دارد؛ مسیر دقیق و روش در [گزارش](../../docs/stage1/dynamic-source-audit.md). dependencyهای ابزار audit برابر playwright@1.65.1 و acorn@8.15.0 هستند. نصب فقط در `.tools/audit`، نه dependencies محصول.

## بازتولید تصویر مرجع

در کپی دست‌نخوردهٔ `.tools/reference/advisor` با lock اصلی، `npm ci --ignore-scripts --no-audit --no-fund` و سپس `npm run dev -- --hostname 127.0.0.1 --port 3107` اجرا شود. در ریشه:

```sh
node scripts/capture_reference.mjs
```

Chrome در `/usr/bin/google-chrome` لازم است. ابزار تمام مقصدهای غیرمحلی را مسدود می‌کند، فقط state نمونهٔ ایزوله دارد و هیچ اتصال حساب/پیامک نمی‌سازد. اجرای دوباره تصاویر و manifest را عوض می‌کند؛ نسخهٔ مرورگر/زمان/animation را قبل از مقایسه بررسی کنید. این audit goldens تثبیت‌شدهٔ CI نیست. سرور مرجع پس از بررسی متوقف شود.

## ترتیب کار بعدی

۱. B01–B04 در D25–D29 ثبت و تحلیل شدند؛ [گزارش پایان جلسه](../../docs/stage1/clarification-report.md) و [دامنه S02](../../docs/stage1/next-step-s02.md) خوانده شوند.
۲. schema و نمونهٔ پذیرش موارد مربوط دقیق شوند؛ checklist بازبین و analyze تکرار شود.
۳. در انتهای گام، نتیجه و قدم بعد گزارش و برای دستور کاربر توقف شود.
۴. پس از دستور S02، نسخه‌های فنی قفل، پروژه ایجاد و اجرای تمیز/CI ثبت شود؛ پس از آن هر feature با spec تفصیلی خودش.

SpecKit 1.4.1 به‌صورت integration مهارت‌های Codex نصب شده؛ `$speckit-*` workflow عامل است، نه shell executable. bash helper فقط مسیر/template/prerequisite را فراهم می‌کند و کیفیت معنایی سند را تضمین نمی‌کند. `.specify/extensions.yml` موجود نیست؛ hook جانبی اجرا نشده است.
