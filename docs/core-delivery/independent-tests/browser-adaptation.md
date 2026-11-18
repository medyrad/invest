# ابزار مرورگر TEST-CORE-COMPLETE

از ابزار و assertionهای موجود استفاده شد. نسخهٔ اجرایی در `.tools/test-core/browser` ساخته شد؛ کد محصول و فایل تاریخی تغییر نکردند. core.spec.ts فقط در import Playwright و مسیر evidence به پوشه تازه تطبیق یافت؛ config مستقل baseURL3108، همان Chrome، workers1، retries0 و trace خاموش داشت. auth-fixes.spec.ts فقط دو تست `delayed old me|cross-tab signals` انتخاب شد.

سناریوی پیوست در اجرای اول پیش از پایان POST رضایت تماس انتظار۲۰۰ داشت و۴۰۳ گرفت. نسخهٔ ابزار با انتظار رخداد واقعی اصلاح شد: پیش از کلیک رضایت `waitForResponse` برای POST مسیر `/core/cases/{caseId}` ساخته شد؛ پس از کلیک، status همان پاسخ۲۰۰ الزام شد و سپس GET contact اجرا شد. هیچ assertion رفتاری حذف نشد. فقط همین سناریو دوباره اجرا و کامل موفق شد؛ log اصلی و بازآزمایی جدا حفظ شده‌اند.

فرمان‌ها: `node frontend/node_modules/@playwright/test/cli.js test -c .tools/test-core/core.cjs`، config regression.cjs برای دو تست نشست و همان config core با `--grep 'private attachment'` برای بازآزمایی ابزار. Node قفل‌شدهٔ موجود از `.tools/runtimes/node-v24.22.3-linux-x64/bin/node` استفاده شد.
