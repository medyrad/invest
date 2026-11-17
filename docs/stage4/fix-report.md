# اصلاح محدود PROGRAMMER-S04-02

وضعیت: **آماده بازآزمایی محدود**؛ نسخه **S04-FIX-5d2794c593b5** روی http://127.0.0.1:3108. build: `cVZXosaS-HTzSbx2hjX64`؛ [شناسه کامل image و hash کد](fix-evidence/version.json). مرجع: [گزارش مستقل](independent-test-report.md).

| ایراد | اصلاح و شاهد |
|---|---|
| S04-IT-001 | عنوان «شهر»، پیام دقیق مصوب برای شهرستان فاقد شهر و راهنمای مشتری جای اصطلاحات استخراج داده را گرفتند. هوراند بدون شهر، تهران دارای شهر، حفظ شهرستان و پاک‌شدن فرزند با تغییر والد در چهار عرض موفق‌اند. شهر فرضی یا رابطه تازه اضافه نشد. |
| S04-IT-002 | favicon از **همان مسیر برداری نشان هدر** در `brand/algo-pattern.tsx` و رنگ موجود ساخته شد؛ favicon آرشیو کپی نشد. ICO شامل۱۶/۳۲/۴۸/۶۴px و metadata صریح است. HTTP روی image نهایی: **۲۰۰، image/x-icon،۶۰۱۴بایت**، header معتبر ICO؛ HTML نیست. decode در context تازه و نبود resource/page error نیز موفق است. [HTTP](fix-evidence/favicon-http.json) |

فایل‌های کد/دارایی: `frontend/src/components/home/catalog-selectors.tsx`، `frontend/src/app/layout.tsx`، `frontend/public/icons/brand-mark.svg` و `frontend/public/favicon.ico`. آزمون استاندارد `home.spec.ts` فقط نام کنترل شهر را دنبال می‌کند؛ `catalog-fixes.spec.ts` دو بررسی هدفمند دارد. ردیابی: T014/T015 در tasks موجود و وضعیت همین اصلاح در stage-status؛ spec/plan تازه تولید نشد.

فرمان‌های اجراشده:

- از `frontend`: `./node_modules/.bin/eslint src/components/home/catalog-selectors.tsx src/app/layout.tsx tests/browser/home.spec.ts tests/browser/catalog-fixes.spec.ts --max-warnings=0` — موفق؛ [کیفیت](fix-evidence/quality.txt).
- `docker compose --env-file .env -f deploy/compose.yaml build web` — **یک build فرانت** موفق، شامل بررسی TypeScript خود build؛ [خروجی](fix-evidence/build.txt). سپس فقط `up -d --no-deps web` برای اجرای image محلی.
- با Node قفل‌شده و Chrome موجود: `frontend/node_modules/.bin/playwright test --config=.tools/s04-fix/playwright.config.ts --workers=2` — **۸ موفق** روی image3108، شامل smoke شش بخش خانه و بازشدن ناوبری؛ [نتیجه](fix-evidence/browser.json)، [خروجی](fix-evidence/browser.txt). override همان تنظیم موجود Playwright است؛ [نسخه تنظیم اجرا](fix-evidence/runner-config.txt).
- درخواست HTTP مستقیم `/favicon.ico` و بررسی content-type، header، اندازه‌ها و hash — موفق. مجموعه PostgreSQL، OTP و مقایسه همه صفحات تکرار نشدند.

تصاویر ضروری: شهرستان فاقد شهر در [۳۶۰](fix-evidence/city-empty-mobile-360.png)، [۳۹۰](fix-evidence/city-empty-mobile-390.png)، [۷۶۸](fix-evidence/city-empty-tablet-768.png) و [۱۴۴۰](fix-evidence/city-empty-desktop-1440.png)؛ [شهر موجود](fix-evidence/city-available-desktop.png)؛ [راهنمای مشتری](fix-evidence/city-help-mobile.png). کلاس، فونت و چیدمان سایر بخش‌ها تغییر نکردند.

زمان دیواری از شروع ثبت‌شده UTC؛ جزئیات در [زمان‌سنجی](fix-evidence/timing.json): آماده‌سازی **93.4ثانیه**، build **27.1ثانیه**، آزمون و بازبینی **34.8ثانیه**، گزارش/ردیابی/نسخه **76.8ثانیه**. اجرای خود مرورگر۴٫۲ثانیه بود.

۴۴۱ فایل گزارش، شاهد تاریخی و ابزار مستقل بدون تغییر کنترل شدند. env، کد بک‌اند/API/احراز/قواعد و کانتینرهای backend/DB حفظ شدند؛ تنها web محلی جایگزین شد. مورد باز این مأموریت: بازآزمایی محدود مستقل؛ پذیرش انسانی و پایان کل S04 همچنان باز است. deploy عمومی و push انجام نشد. پس از گزارش توقف؛ قدم بعد با دستور کاربر، بازآزمایی همین دو شناسه است.
