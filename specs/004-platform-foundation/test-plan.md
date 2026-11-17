# آزمون S02

| نیازمندی/داستان | شاهد مقصد |
|---|---|
| FR-001/002/003؛ US1 | lock frozen، migration DBخالی، User unique/check، دو حساب و restartvolume؛ backend/tests/test_accounts.py و scripts/foundation_smoke.py |
| FR-004/005/006؛ US2 | health DBواقعی/قطعی/بازیابی، خطای404/405/500 و UUID معتبر/نامعتبر بدونsecret؛ backend/tests/test_api.py و smoke |
| FR-007/008؛ US3 | APIClient(enforce_csrf_checks=True)، مهمان/واردشده، token/origin مثبت/منفی؛ settings public بدونsecret/debug/testOTP/HTTP و کنترل مثبت؛ backend/tests/test_security.py و test_settings.py |
| FR-009/010؛ US4 | Playwright 390/1440 روی standalone؛ RTL/font و GET/POST/query/body/cookie/status/CSRF با test-only URLConf؛ frontend/tests/browser/foundation.spec.ts |
| FR-011 | OpenAPI validator و response schema و header syntax؛ backend/tests/test_contract.py |
| FR-012/013 و SC-001..006 | CI و نصب frozen/build واقعی، checkdeploy با هشدارهای دامنه ثبت‌شده و docs/development.md و گزارش شواهد |

تست‌های پایه پیش از کد اجرا و شکست اولیه ثبت شوند. خطاهای قابل انتظار tests probe فقط تنظیم test دارند و در URLConf محصول نیستند. اندازه/بار/SLA مشتری این آزمون نیست. CI remote، پذیرش انسانی UI و عرضه ادعا نمی‌شوند.
