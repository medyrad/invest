# تحویل PROGRAMMER-S04-01

وضعیت: **آماده آزمون مستقل PROGRAMMER-S04-01**؛ نسخه **S04-f811d439b069**. خانه روی http://127.0.0.1:3108 قابل بررسی است. شناسهٔ دقیق کد، build و image در [manifest](evidence/manifest.json) و [اجرای واقعی](evidence/runtime.json) ثبت می‌شود. پذیرش انسانی S03/طراحی، پایان کل S04 و انتشار تأیید نشده‌اند.

اجرا: FR-001..008 و T001..T013 بستهٔ [006](../../specs/006-home-catalog/tasks.md). HeroCompass، هشت مسیر MainCategories، یازده حوزه Categories، شش کارت Featured، سه حالت HowItWorks، HelpCenter، Footer و برند فعال مرجع منتقل شدند. هدر و dropdown/منوی موبایل به ورود و نشست واقعی S03 متصل‌اند. انتخابگرهای دسته/زیردسته و استان/شهرستان/شهر، حذف/پاک‌کردن، پاک‌شدن فرزند با تغییر والد و وضعیت loading/خطا/خالی/retry از API کار می‌کنند. هویت localStorage، موتور تطبیق و قابلیت‌های آیندهٔ مرجع منتقل نشده‌اند.

کاتالوگ PostgreSQL: **۱۱ گروه،۷۸ زیردسته،۳۱ استان،۴۷۸ شهرستان و۲۲ پیوند شهر** عین دادهٔ منبع؛ منبع پوشش کامل شهرها ندارد. شناسه‌های گروه/نوع اصلی و namespace نسخهٔ ثابت استان/شهرستان حفظ می‌شوند. migration و import تراکنشی، تکرارپذیر و بدون delete است؛ تعارض هویت را رد می‌کند. APIهای خواندنی `/api/v1/catalog/{taxonomy,geography,preview}` نسخه و قرارداد ماشین‌خوان دارند. ۲۷۳ فرصت فقط fixture نمونهٔ توسعه/آزمون‌اند، رکورد فرصت واقعی seed نمی‌شود و پاسخ public همیشه بدون نمونه است. اطلاعات تماس نمونه از DTO عمومی حذف شده است.

فایل‌ها: `backend/apps/catalog/**` و `backend/tests/test_catalog.py`؛ تنظیمات/URL و `contracts/openapi.yaml`؛ `frontend/src/components/{home,brand,site,listing,ui}/**`، `lib/catalog-context.tsx`، `auth/login-dialog.tsx`، page/layout/CSS و دارایی‌های اصلی؛ آزمون‌های استاندارد browser، lockها، Makefile و seed کاتالوگ در CI. فهرست دقیق و hash تمام فایل‌های کد در manifest است. گزارش‌ها، ابزارهای مستقل و شواهد قبلی دست‌نخورده‌اند؛ ۲۸۱ فایل تاریخی با snapshot پیش از ویرایش کنترل می‌شوند.

## تفاوت‌های صریح با مرجع

- D28 و مرز S06: وعدهٔ تطبیق آماده در معرفی اصلاح شده؛ بودجه و مکان در روش کار ترجیح‌اند و شمار نمونه به‌واسطهٔ آن‌ها کاهش نمی‌یابد. حلقهٔ درصد «نامعلوم» است و چهار دلیلِ نمایشی محاسبه‌نشده‌اند؛ هیچ امتیاز حدسی اجرا نمی‌شود. مبلغ نمونه با واحد صریح میلیارد تومان است؛ ورودی پول ساختاریافته یا تبدیل مالی در این بسته وجود ندارد. متن آزاد دستیار به مقصد غیرفعال می‌رود و تفسیر/محاسبه نمی‌شود.
- D26: متن مصوب اشتراک شماره و رفتارهای اصلاح‌شدهٔ S03 حفظ شد. ورود/خروج در هدر واقعی انجام می‌شود؛ دکمهٔ خروج در منوی حساب است و بازخورد واقعی ورود/خروج و خطاهای نشست به‌صورت پیام قابل مشاهده زیر هدر نمایش می‌یابد.
- برچسب «نمونه» و توضیح صریح آمار/نقشه/Featured؛ بدون ادعای انتشار یا احراز. در public نقشهٔ پایه و پیام نبود داده جای نمونه‌ها را می‌گیرند.
- پنل انتخاب API زیر Categories افزوده شد؛ ارتفاع این بخش۳۴۶px بیشتر است. بقیهٔ ابعاد هفت بخش و فونت عنوان‌های دسکتاپ با مرجع سنجیده شده‌اند. موبایل همهٔ محتوا را با ستون‌بندی مناسب نگه می‌دارد؛ منوی تبلت تا۱۰۲۴px جمع می‌شود. کارت‌های نقشه در موبایل زیر نقشه در جریان معمول قرار می‌گیرند تا روی هم نیفتند؛ در دسکتاپ موقعیت اصلی حفظ است. حرکت چرخشی در reduced-motion متوقف، کارت‌های نقشه ثابت و محتوای روش کار با کنترل دستی قابل دسترسی است.

## شواهد و آزمون

| اجرا | نتیجه |
|---|---|
| تطبیق `.tools/reference/advisor` با ZIP | ۲۷۰ فایل src/public یکسان؛ [شاهد و hash آرشیو](evidence/reference-integrity.json) |
| `make check` با Node24.22.3 در PATH | Ruff، format، migration drift، Django check، ESLint و TypeScript موفق؛ [خروجی](evidence/quality.txt) |
| `make test` | ۹۷ آزمون PostgreSQL موفق؛ شامل import دوباره/حفظ داده سفارشی، rollback تعارض، FK/unique، تطابق منبع، قرارداد واقعی و منع preview عمومی؛ [خروجی](evidence/backend.txt) |
| Playwright استاندارد روی build تولیدی و DB مصنوعی `invest_browser` | **۵۹ آزمون موفق**؛ نتیجهٔ نهایی در [JSON](evidence/browser-delivery.json) و [خروجی](evidence/browser.txt)؛ خانه، API، لمس/صفحه‌کلید/focus/Escape، حرکت و احراز در چهار عرض |
| `npm run build` و `docker compose … build backend test browser-api web` | موفق؛ [build](evidence/build.txt)، [image](evidence/images.txt) |
| API روی image واقعی3108 | سلامت و شمارش واقعی کاتالوگ/fixture و بررسی مرورگر image در چهار عرض، ورود واقعی، Escape و بازگشت focus موفق؛ [مرورگر image](evidence/image-browser.json)، [runtime](evidence/runtime.json) |

شواهد شکست‌های میانی تصویر نیز نگه داشته شده‌اند: [ثابت‌سازی حالت کاهش حرکت](evidence/browser-mobile-capture-failure.json) و [انتقال افقی کارت موبایل](evidence/browser-mobile-overflow-failure.json). کاهش حرکت اکنون پیش از بارگیری انتخاب می‌شود و شرط عدم هم‌پوشانی/خروج محتوا حفظ است.

یک اجرای میانی هنگام انتظار resend با خروج۱۴۳ متوقف شد؛ علت قطعی مشخص نشد و [خروجی آن](evidence/browser-interrupted.txt) حفظ شد. اجرای کامل تازه جدا ثبت شده است.

بازگشت S03 در تست‌های استاندارد با هدر واقعی بررسی شد: پاسخ resend پذیرفته‌شده قطع می‌شود؛ همان کلید/ورودی، challenge و TTL بازیابی و IssueEvent دوباره مصرف نمی‌شود و ورود موفق است. خروج بین تب‌ها، پاسخ me دیررس، focus/visibility/pageshow بدون تمدید idle، مرجع‌بودن سرور و استقلال دستگاه دوم نیز بررسی شدند. انتخابگرهای آزمون استاندارد فقط با منوی حساب تطبیق یافتند؛ هیچ ابزار یا گزارش مستقل قبلی تغییر نکرد. قبول فنی مستقل پیشین در [TEST-S03-03](../stage3/retest-report.md) باقی است؛ تأیید انسانی از آن استنتاج نشده است.

تصاویر دسکتاپ برای **hero/main-categories/categories/featured/how/help/footer**، هرکدام reference و invest، با viewport۱۴۴۰×۱۰۰۰، فونت byte-identical Vazirmatn، زمان ثابت و دادهٔ نسخه‌دار در build تولیدی هر دو طرف ثبت شده‌اند؛ [اندازه‌ها و خطاهای مرورگر](evidence/section-comparison.json). تصویر golden قدیمی تغییر نکرد. hydration خطادار مرجع ثبت و target بدون خطای صفحه کنترل شده است. تصاویر ثابت جای آزمون حرکت نیستند. [موبایل۳۶۰](evidence/home-mobile-360.png)، [موبایل۳۹۰](evidence/home-mobile-390.png)، [تبلت۷۶۸](evidence/home-tablet-768.png)، [دسکتاپ۱۴۴۰](evidence/home-desktop-1440.png) و [متن ورود موبایل](evidence/auth/privacy-copy-mobile-360.png) برای بازبینی انسانی‌اند؛ برابری کامل پیکسلی یا تأیید انسانی ادعا نمی‌شود.

## مرز و بازتولید

مقصد `/opportunities` و جزئیات به S06، `/assistant` به S09، `/saved` و `/compare` به S07 و `/tools` و راهنماهای خدمات به S07/S08 وابسته‌اند. همگی صفحهٔ روشن «فعال نیست» و بازگشت به خانه دارند؛ لینک شکسته یا موفقیت جعلی ندارند. S05 ثبت/انتشار، S06 رتبه‌بندی، ابزارها، AI و اتصال پولی/پیامک واقعی ساخته نشده‌اند.

baseline: T009 فقط taxonomy/geography، T010 فقط fixture و جداسازی نمونه، T012 فقط خانه و حالت‌های همین بسته، T045 فقط اجزای فعال خانه پوشش یافتند؛ کل این تسک‌ها تیک نخورده‌اند. T011 و مدل‌های دقیق MoneyValue/Quantity/ReturnMetric و نگاشت‌های دیگر برای بستهٔ مربوط باقی‌اند. محدودیت شهرهای منبع و پذیرش انسانی موبایل/پنل جدید نیز باز است.

برای اجرا `make build` و `make up` (env موجود را حفظ می‌کند)؛ برای آزمون `make check` و `make test`. آماده‌سازی browser فقط DB با پسوند `_browser` را reset می‌کند: `prepare_browser_db`، سپس migrate و `import_reference` و اجرای browser-api. برای حفظ شواهد قدیمی، Playwright با config مطلق پروژه از cwd جدا در `.tools/s04/run/frontend` اجرا شد؛ `INVEST_S04_EVIDENCE`، `INVEST_FIX_EVIDENCE` و `PLAYWRIGHT_JSON_OUTPUT_FILE` به مسیر جدید stage4 اشاره می‌کنند. تصاویر section با `node scripts/capture_s04.mjs` و سرویس مرجع جدا3107 و image اصلی3108 (یا `INVEST_CAPTURE_ORIGIN` برای standalone آزمون3109) بازتولید می‌شوند؛ اجرای مرجع فقط زیر `.tools` است. `node scripts/verify_s04_image.mjs` کنترل خواندنی مرورگر روی image اصلی را تکرار می‌کند. `python3 scripts/manifest_s04.py` شناسهٔ کد/شواهد را بازتولید می‌کند. CI فقط تعریف و محلی معادل‌سازی شده؛ remote CI اجرا نشده است.

هیچ env یا DB اصلی reset نشد؛ migration افزایشی و import کاتالوگ اجرا شد. سرویس پروژه‌های دیگر دست‌نخورده‌اند. deploy/push انجام نشد. قدم بعد: آزمون مستقل همین مأموریت و بازبینی انسانی تصاویر، فقط با دستور بعدی کاربر؛ پس از این گزارش توقف.

بازبینی پایانی SpecKit/converge:۸ نیازمندی،۳ معیار،۳ داستان،۱۳ تسک و۷ اصل constitution با کد و شواهد سنجیده شدند؛ کار ساختنیِ مجازِ جامانده‌ای در این بسته یافت نشد. تسک‌های baseline و تأیید انسانی جدا باز مانده‌اند؛ برای آن‌ها تسک این بسته انجام‌شده معرفی نشده است.
