# PROGRAMMER-CORE-FIX-01

وضعیت: **آماده بازآزمایی مستقل بسته اصلاح**. هر سه ایراد برای بازآزمایی تحویل شدند؛ پذیرش مستقل و تأیید انسانی بازند. نسخه نهایی **CORE-443ca1cbf0c7** روی [3108](http://127.0.0.1:3108/) اجراست. [manifest و imageها](fix-01-evidence/manifest.json)، [دوره کار نمونه منتشرشده](http://127.0.0.1:3108/opportunities/fff6a942-d395-4da3-86e1-e586f21f9aa8).

## اصلاح‌ها و علت

| ایراد | علت و اصلاح | فایل‌های اصلی و شاهد |
|---|---|---|
| CORE-IT-003 | مسیر operator دوره مستقل نداشت. Quantity نسخه۱ با انتخاب صریح DAY/MONTH/YEAR و start_basis افزوده شد؛ فقدان مقدار، پیش‌نویس ناقص را مجاز و ارسال را ناقص نگه می‌دارد. raw هنگام تغییر مسیر محفوظ و در effective/snapshot غیرفعال بی‌اثر است. unknown/not_applicable و صفر مستقل ماندند. | catalog/migrations/0010_operator_work_period.py، workspace/schema_data.json، workspace/field.tsx، core/exact-facts.tsx، lib/guide.ts؛ operator-journey.json و تصاویر فرم/جزئیات |
| CORE-IT-001 | عضو object/list در important پیش از کنترل نوع، وارد lookup دیکشنری وزن‌ها می‌شد. کنترل نوع و گزینه پیش از lookup، خطای۴۰۰ فارسی و مسیر criteria.important.N اضافه شد. preferences تو‌در‌تو و شناسه بدشکل مقایسه نیز پیش از استفاده رد می‌شوند. وزن‌ها، unknown و ورودی معتبر تغییر نکردند؛ catch عمومی اضافه نشد. | backend/apps/core/discovery.py و tests/test_core.py؛ مستقل تاریخی و http-probes.json |
| CORE-IT-002 | metadata گروه‌ها/ترتیب مرجع کنار گذاشته شده بود. گروه پول، زمان، ریسک و حقوق، پروژه و محل با ترتیب و عنوان مرجع، ردیف‌های متناسب، پیوندهای قابل صفحه‌کلید و نمایش راه‌های ورود برگشتند. صندوق چهار گروه متناسب و فروش پول/حقوق/دارایی و محل دارد؛ گروه زمانِ ساختگی ندارد. انتخاب/حذف/افزودن۲تا۴، تفاوت‌ها، مقدار دقیق و مبنای ناهمسان محفوظ‌اند. | frontend/src/lib/compare.ts، components/core/compare.tsx؛ تصاویر هر سه نوع۱۴۴۰/۳۹۰ و product-after-dom.json |

در سفر ناشناس مقایسه، خطای گذرای CSRF نیز با تأخیر کنترل‌شده بازتولید شد: load لغوشده هنوز درخواست می‌فرستاد و دو bootstrap اولیه cookie متفاوت می‌گرفتند. در reference-shell بار لغوشده پیش از درخواست متوقف شد و core-api فقط bootstrap درحال‌اجرا را مشترک می‌کند؛ token دائمی cache نمی‌شود و حفاظت سرور حذف نشده است. آزمون نهایی مقایسه تأخیر۲۰۰ms و نبود پاسخ خطای API را می‌سنجد. نمودار فقط برای مقادیر هم‌مبناست؛ مبدأ صفر حفظ می‌شود و نمودار زمان/IRR فرضی تولید نمی‌شود.

## نگاشت بهره‌برداری و سازگاری

منبع src/data/routes.ts:operator و routeSteps.operator، بهره‌برداری/نگهداری، شرح خدمت/حدود تعمیرات و تحویل/پایش را مشخص می‌کند. F09 دوره کار می‌خواهد؛ منبع واحد قطعی دوره ندارد. description همان شرح خدمت است؛ operator_work_period@1 در namespace invest.opportunity.project دوره ارائه خدمت است و با execution_months، payback یا افق IRR ادغام نشده است. حدود فنی غیرمنفی۲۴رقم صحیح و۹اعشار مطابق D29؛ قطع یا گردکردن پنهان ندارد.

MONTH در تعریف فقط anchor فنی است، نه واحد تخصیص‌یافته به سوابق یا انتخاب پیش‌فرض UI. کنترل با واحد خالی شروع می‌شود؛ کاربر واحد را انتخاب می‌کند. تعریف‌های پیشین تغییر نکردند و migration تنها تعریف جدید را افزود. سابقه قدیمی بازنویسی نشده است. snapshotهای قبلی فاقد این داده، همان سابقه قبلی‌اند؛ پیش‌نویس operator فاقد آن نقص صریح برای تکمیل دارد. بودجه سرمایه‌گذار اجباری نشده است. نمونه UI با ورودی فارسی۱۸٫۵ روز و «تحویل کارگاه» تا انتشار، نمایش عمومی و گزارش ثابت عبور کرد.

تعریف مصرف‌شده قابل rollback نیست و guard فعال می‌ماند؛ آزمون آن فقط DB ایزوله بود. migration روی DB برنامه افزایشی اعمال شد. hash و تعداد تمام Draft، PrivateFile، Submission و Report بلافاصله پیش/پس از migration برابر بودند؛ [شاهد بدون محتوا](fix-01-evidence/preservation.json). env طبق hash تغییر نکرد. داده‌های مرورگر فقط مصنوعی‌اند؛ reset/rollback DB برنامه یا دست‌کاری سرویس پروژه دیگری انجام نشد.

## آزمون و بازتولید

| بررسی | نتیجه |
|---|---|
| بازتولید مستقل پیش از اصلاح | سه شکست مورد انتظار و دو مورد کنترل موفق؛ reproduce.txt |
| مجموعه مرتبط core/workspace/required/acceptance/values و مستقل | **۳۰۶ موفق،۱۵٫۲۲ثانیه**؛ شامل۲۵ مورد تازه core و ماتریس فیلد جدید |
| مستقل تاریخی روی image نهایی | **۸ موفق**؛ زیرمجموعه همان۳۰۶، به شمار یکتا دوباره افزوده نشده است |
| مرورگر بسته اصلاح | ۴موفق،۲۹٫۹ثانیه؛ سفر واقعی operator تا گزارش و مقایسه هر سه نوع،۲/۳/۴ و افزودن/حذف، صفحه‌کلید و۳۹۰/۱۴۴۰؛ browser-delivery.txt |
| regression محدود فضای شخصی | ۱موفق،۶٫۵ثانیه؛ منتخب/شرایط/مقایسه/گزارش ثابت/خروج؛ personal-delivery.txt |
| GET واقعی نهایی | دو بازتولید object/list و دو عضو نامعتبر دیگر۴۰۰؛ important خالی۲۰۰؛ preferences بدشکل۴۰۰؛ جمع۶ probe |
| کیفیت و ساخت | ruff فایل‌های Python متأثر، eslint، tsc، build backend/test/web و migration drift موفق؛ فایل‌ها در manifest |

فرمان pytest از ریشه:

```sh
docker compose --env-file .env -f deploy/compose.yaml run --rm --no-deps --user 1000 -v "$PWD/backend:/src" -v "$PWD/contracts:/contracts:ro" -v "$PWD/docs/core-delivery/independent-tests:/independent:ro" -w /src test /app/.venv/bin/pytest -q tests/test_core.py tests/test_workspace.py tests/test_workspace_required.py tests/test_workspace_acceptance.py tests/test_values.py /independent/test_gaps.py --tb=short
```

از frontend با Node موجود پروژه در PATH:

```sh
npx playwright test --config=core-fix-01.playwright.config.ts
CORE_URL=http://127.0.0.1:3108 npx playwright test --config=core.playwright.config.ts --grep "personal saved"
```

runnerهای PostgreSQL ترتیبی بودند. suite کامل۶۲۸، نه سفر قبلی، scanner و انتظار OTP تکرار نشدند؛ اثر تغییر با مجموعه‌های بالا پوشش داده شد. تست‌ها و گزارش مستقل تاریخی تغییر نکردند. نخستین شکست ماتریس عمومی به نبود operator در routes fixture مربوط بود؛ مسیر جدید اضافه و assertion حفظ شد. ابزار مرورگر برای ادامه پس از reload واقعاً «ادامه ویرایش» را می‌زند و جدول جمع‌شده جزئیات را باز می‌کند؛ دریافت save نیز منتظر پاسخ POST است. شواهد شکست توسعه در .tools/core-fix-01 محفوظ‌اند.

## تصاویر، زمان و تحویل

[مرجع](fix-01-evidence/reference-1440.png)، [محصول قبل](fix-01-evidence/product-before-1440.png) و [محصول بعد](fix-01-evidence/product-after-1440.png) با همان دو عنوان و مقادیر عددی DEMO-01/02 در۱۴۴۰ ثبت شدند. reference-input.json فقط داده غیرتماسی fixture دارد و هر دو محصول از API واقعی ثبت/بررسی/منتشر شدند. عکس عمومی برند، برچسب مصنوعی و داده فاقد مبنای صریح با مرجع یکسان فرض نشده‌اند: در محصول، مبدأ مدتِ فاقد منبع unspecified است و نمودار معتبر زمان ساخته نمی‌شود. نبود دستیار متصل طبق مقصد S09 و تفاوت D26/D29 حفظ است. DOM چهار گروه/ترتیب ردیف‌ها ثبت و تصاویر desktop/mobile واقعاً بازبینی شدند؛ ادعای برابری پیکسلی همه حالات یا تأیید انسانی نیست.

زمان آغاز13:45:12 UTC روز2026-11-18 (17:15:12 تهران) است. آماده‌سازی/پیاده‌سازی تا build اول۷دقیقه۶ثانیه؛ buildهای cache‌شده۱۰،۸،۹،۸و۹ثانیه بودند، چهار build بعدی برای یافته واقعی عنوان دوره، رقابت مقایسه ، تکمیل نمایش مرجع و حذف بخش نامرتبط صندوق/فروش لازم شدند. زمان runnerها مستقل در manifest ثبت شده است؛ گزارش تا snapshot فعلی حدود 5.9دقیقه زمان داشت؛ کارهای هم‌زمان جمع‌پذیر نیستند. نصب مجدد انجام نشد.

کامیت‌های پیاده‌سازی 8b9dbc2 و178e555 هستند؛ hash کامیت تحویل در پاسخ نهایی ثبت می‌شود. push معمول origin روی main طبق مجوز کاربر انجام می‌شود و نتیجه remote در پاسخ تحویل اعلام خواهد شد. force push، انتشار عمومی و شروع بسته بعد انجام نمی‌شوند. قدم بعد، بازآزمایی مستقل همین سه ایراد است؛ وضعیت مستقل/انسانی تا گزارش نقش مربوط باز می‌ماند.
