# گزارش مستقل TEST-S04-01

تاریخ: ۲۰۲۶/۱۱/۱۷. **نتیجه: قبول با ایراد جزئی.** در دامنه خانه/ناوبری/کاتالوگ، مانع رفتاری، نقض جداسازی نشست یا تغییر نیمه‌کاره import مشاهده نشد. دو ایراد کم‌اهمیت زیر باز هستند. این نتیجه پایان کل S04، تأیید انسانی طراحی یا مجوز عرضه نیست.

## نسخه و اجرای واقعی

- نسخه **S04-f811d439b069**؛ هر۲۴۳ فایل کد،۵ سند بسته و۵۱ شاهد manifest تحویل تطبیق داشتند. imageهای backend/web/db فعال3108 با runtime اعلام‌شده یکسان بودند. [نسخه](independent-evidence/version.json)، [تطبیق کامل](independent-evidence/delivery-integrity.json).
- web فعال: `sha256:29f52e4a8cea2a4ab2a79053180dd0d000571f879bcd094469773b8965caf11d`؛ build ID برابر `wyi_ODna_cB3bUWbdOgFM`. build تازه مرورگر `q2OQrMNEIWgi0RuOdlUOy` بود؛ هر۱۰ فایل JS/CSS مشترک آن با image هدف یکسان بود. ۴۶ فایل Python/fixture در backend، browser-api و image آزمون نیز با workspace یکسان بودند. [bundle](independent-evidence/bundle-check.json)، [کد اجراشده](independent-evidence/runtime-sources.json).
- آزمون‌های مخرب فقط روی PostgreSQL آزمون و سفرهای مرورگر روی standalone3109 با `invest_browser` اجرا شدند. روی3108 فقط خواندن سلامت/کاتالوگ انجام شد. Chrome151 و Node24.22.3 قفل‌شده استفاده شدند.

| فرمان از ریشه | نتیجه خود تستر |
|---|---|
| `make test` | **۹۷ موفق** روی PostgreSQL؛ [خروجی](independent-evidence/existing-backend.txt) |
| `PATH="$PWD/.tools/runtimes/node-v24.22.3-linux-x64/bin:$PATH" make check` | Ruff، format، migration drift، Django check، ESLint و TypeScript موفق؛ [خروجی](independent-evidence/existing-quality.txt) |
| `python3 docs/stage4/independent-tests/run-existing-browser.py` | **۵۹ موفق**؛ مجموعه استاندارد یک بار، با تصاویر/JSON در مقصد جدا؛ [خروجی](independent-evidence/existing-browser.txt) |
| `python3 docs/stage4/independent-tests/extract-source.py` | استخراج مستقل مستقیم از ZIP؛ [خلاصه](independent-evidence/source-extraction.json) |
| `docker compose --env-file .env -f deploy/compose.yaml run --rm -v "$PWD/docs/stage4/independent-tests:/independent:ro" -v "$PWD/docs/stage4/independent-evidence:/evidence:ro" test /app/.venv/bin/pytest -c /app/pyproject.toml /independent/test_catalog_independent.py -q --tb=short` | **۱۰ موفق**؛ [خروجی](independent-evidence/independent-backend.txt) |
| `node docs/stage4/independent-tests/home-independent.cjs` و بازاجرای محدود `HOME_CASE=all-sections-navigation-and-layout-768` | **۱۱ سناریوی نهایی موفق**؛ [اصل](independent-evidence/home-independent.json)، [تبلت](independent-evidence/home-tablet-rerun.json) |
| `node docs/stage4/independent-tests/async-motion.cjs` و بازاجرای محدود `ASYNC_ONLY=mobile` | **۲ سناریوی نهایی موفق**؛ [پاسخ دیررس](independent-evidence/async-motion.json)، [حرکت موبایل](independent-evidence/motion-rerun.json) |
| `node docs/stage4/independent-tests/auth-regression.cjs` و بازاجرای محدود `RETEST_ONLY=affected RETEST_FIXTURE_SEED=700` | **۱۰ سناریوی نهایی موفق**؛ [اصل](independent-evidence/auth/targeted.json)، [بازگشت مسیر](independent-evidence/auth/IT001-rerun.json) |
| `node docs/stage4/independent-tests/controls.cjs` | **۲ موفق**؛ همه۱۱گروه، زیردسته مرزی هر گروه،۳مسیر و۶پاسخ راهنما؛ [نتیجه](independent-evidence/controls.json) |

`node` در فرمان‌ها همان runtime قفل‌شده است. جمع نهایی **۱۹۱ آزمون نام‌دار موفق** است؛ probeهای تشخیصی و capture تصویری به این شمار اضافه نشده‌اند. پنج نتیجه مقدماتی ابزار/محیط پنهان نشده‌اند: نبود hasTouch در fixture تبلت، reload پیش از تکمیل مسیریابی SPA، فرض نادرست تعداد ثابت دو کارت در حرکت عادی، انتخابگر چندعنصری screenshot و قطع سرور موقت با خروج۱۴۳. فقط موارد متأثر بازاجرا شدند؛ assertionهای رفتاری پس از اصلاح ابزار موفق‌اند. این موارد باگ محصول شمرده نشده‌اند. [جمع‌بندی](independent-evidence/summary.json).

## پوشش مستقل

**کاتالوگ:** آرشیو با hash `6221401c736250c5ac7e5595aa988301f64b8d2fe576590291a7c2e53c247f5b` مستقیم و بدون اجرای کد خوانده شد. تمام نام‌ها، شناسه‌ها و روابط۱۱گروه/۷۸زیردسته و۳۱استان/۴۷۸شهرستان/۲۲پیوند شهر با API آزمون و API واقعی3108 مقایسه شدند؛ صرف شمارش نبود. اولین/آخرین رکوردها و شهرستان بدون شهر نیز پوشش یافتند. source-id گروه/زیردسته و namespace نسخه‌دار مکان حفظ شده‌اند؛ شهرستان به شهر تبدیل نشده است. [انتظار مستقل](independent-evidence/source-expected.json)، [تطبیق runtime](independent-evidence/runtime-api-source-check.json).

import دوباره snapshot را عوض نکرد؛ داده مستقل و metadata آن ماند. تعارض شناسه در آخرین استان و خطای تزریق‌شده پس از۲۰۰ نوشتن شهرستان، تمام مدل‌ها را به snapshot قبلی برگرداندند. FK نامعتبر و یکتایی شهرستان/شهر/زیردسته روی PostgreSQL واقعی رد شدند. قرارداد ماشین‌خوان با پاسخ واقعی در مجموعه استاندارد بررسی و شکل/محتوای کامل API مستقلاً با منبع سنجیده شد.

**خانه و انتخاب:** هفت بخش در هر چهار عرض، منوی موبایل/تبلت، Escape و focus، مقصدهای مستقیم، refresh و Back بررسی شدند. لینک‌های اولیه و لینک‌های آشکارشده هر شش پاسخ راهنما پاسخ موفق داشتند؛ مقصدهای S06/S07/S08/S09 پیام غیرفعال و بازگشت به خانه داشتند. کنترل بی‌اثر یا پیام موفقیت ساختگی مشاهده نشد.

انتخاب/حذف/پاک‌کردن، لمس و صفحه‌کلید، تغییر سریع والد و پاک‌شدن فرزند آزموده شدند. تغییر نام دسته در پاسخ آزمایشی API واقعاً به UI رسید؛ کپی مخفی جایگزین نشد. قطع، تأخیر، پاسخ خالی و retry صادقانه بودند. پاسخ قدیمی عمداً پس از خروج از صفحه و بازگشت با پاسخ تازه تحویل شد؛ داده و انتخاب تازه را پس نگرفت.

**نمونه و public:** برچسب‌های نمونه، نبود درصد محاسبه‌شده، واحد مبلغ و نبود شماره تماس در DTO/صفحه بررسی شدند. یک backend جدا واقعاً با `INVEST_ENV=public`، SMS پیکربندی‌نشده و DB مصنوعی اجرا شد؛ API، `enabled:false` و آرایه خالی داد. فرانت همان bundle هدف با پاسخ واقعی این API از طریق پل شبکه آزمون رندر شد: هیچ عنوان نمونه از۲۷۳مورد، کارت Featured یا کارت نقشه باقی نماند. صرف خالی‌شدن API معیار نبود. فقط redirect به HTTPS برای انتقال HTTP روی loopback در settings آزمون غیرفعال شد؛ TLS یا عرضه عمومی آزموده نشده است. [public](independent-evidence/home-independent.json)، [تنظیم اجرا](independent-evidence/runtime-sources.json).

**بازگشت S03:** resend پذیرفته‌شده با پاسخ گم‌شده، همان key/payload/flow/challenge و TTL را بازیابی کرد؛ IssueEvent پس از صدور دوم روی۲ ماند و فقط یک نشست ساخته شد. کد قبلی در وضعیت نامعلوم نمایش داده نشد. خروج تبA هویت تبB را پاک کرد؛ پاسخ دیررس me آن را برنگرداند، پیام جعلی اختیار نداد، نشست دستگاه مستقل ماند و idle تمدید نشد. متن D26 در چهار عرض حفظ شد. ورود با خطا، ورود صحیح، reload، رفتن به `/saved`، بازگشت خانه و خروج نیز موفق بود. [probe مسیر با وضعیت سرور در هر گام](independent-evidence/navigation-auth-probe.json).

## ایرادهای مشاهده‌شده

### S04-IT-001 — کم — زبان انتخاب شهر به استخراج داده اشاره می‌کند

- **اثر:** هدف کنترل و راه ادامه هنگام نبود شهر، با اصطلاحات فنی بیان می‌شود؛ انتخابگر کار می‌کند، اما زبان آن برای مشتری روشن نیست. این ارزیابی زبانی است؛ مطالعه با مشتری واقعی انجام نشده است.
- **منبع:** بخش۷ مأموریت حاضر؛ FR-005/FR-008 بسته006.
- **بازتولید:** خانه → پنل انتخاب → استان آذربایجان شرقی → شهرستان هوراند؛ عنوان شهر و پیام زیر آن را بخوانید.
- **انتظار:** عنوان ساده «شهر» و توضیح روشنِ ناقص‌بودن فهرست، با حفظ تفکیک شهر/شهرستان و بدون ساخت شهر فرضی.
- **واقعیت:** «شهرهای پیوندخورده در منبع» و «برای این شهرستان پیوند شهری در منبع ثبت نشده است؛ نامی حدس زده نمی‌شود.» نمایش داده می‌شوند. این متن رابطه استخراج‌شده را شرح می‌دهد و اقدام بعدی مشتری را روشن نمی‌کند.
- **شاهد:** [تصویر](independent-evidence/city-copy.png)، مشاهده `language` در [نتیجه مرورگر](independent-evidence/home-independent.json).
- **پیشنهاد بازگشت:** پس از اصلاح متن، عنوان/پیام نبود شهر در چهار عرض بازبینی شود؛ شهر نامعتبر اضافه نشود و روابط API عوض نشوند.

### S04-IT-002 — کم — favicon پاسخ404 دارد

- **اثر:** آیکون برگه مرورگر فراهم نمی‌شود و در بارگذاری نخست یک خطای resource در console ثبت می‌شود؛ مسیرهای اصلی مختل نیستند.
- **بازتولید:** Chrome با context تازه → خانه؛ همچنین `GET http://127.0.0.1:3108/favicon.ico`.
- **انتظار:** درخواست آیکون برند پاسخ موفق بگیرد؛ خطای resource ناشی از دارایی خود برنامه ایجاد نشود.
- **واقعیت:** درخواست خودکار `/favicon.ico` روی standalone404 و همان مسیر روی image هدف3108 نیز404 است. جدیدبودن این ایراد نسبت به مرجع احراز نشده است؛ لینک اقدام مشتری شکسته نبود.
- **شاهد:** [URL خطای console و پاسخ image](independent-evidence/console-404-detail.json).
- **پیشنهاد بازگشت:** آیکون از هویت موجود تأمین و درخواست آن روی image ساخته‌شده کنترل شود؛ تصویر اصلی صفحه تغییر نکند.

## طراحی و محدودیت

مقایسه تازه production مرجع و هدف، هفت بخش را جدا با۱۴۴۰×۱۰۰۰، فونت یکسان، fixture یکسان، زمان ثابت و reduced-motion ثبت کرد. هر۲۷۰ فایل src/public مرجع مستقلاً با ZIP برابر بود. ابعاد شش بخش برابر و Categories دقیقاً **۳۴۶px بلندتر** بود؛ پنل انتخاب دسته/مکان افزوده است و تطابق عین مرجع یا طراحی تأییدشده محسوب نمی‌شود. اختلاف‌های متن D28، نمونه، امتیاز نامعلوم و D26 از حفظ طراحی جدا هستند. [تصاویر جفتی و اندازه‌ها](independent-evidence/visual/section-comparison.json)، [خلاصه](independent-evidence/visual/summary.json)، [اصالت مرجع](independent-evidence/reference-integrity.json).

موبایل/تبلت محتوای بخش‌ها را نگه داشتند؛ نقشه و کنترل‌ها در پیمایش واقعی قابل دسترس بودند. در حرکت عادی موبایل، هندسه کارت‌ها در۷نقطه با ساعت کنترل‌شده مرورگر بررسی و هم‌پوشانی/خروج از عرض دیده نشد؛ چرخش معمول و reduced-motion جدا آزموده شدند. در هدف خطای page/hydration مشاهده نشد؛ یک console404 بالا ثبت شد. خطاهای React418 مرجع نیز جدا در capture باقی‌اند. [console چهار عرض](independent-evidence/console-probe.json).

دستگاه فیزیکی، Safari/Firefox، CI خارجی، TLS/public عملیاتی، SMS، بار عرضه و قابلیت‌های واقعی مراحل بعد اجرا نشدند. تأیید انسانی desktop/mobile و پنل افزوده همچنان باز است. متن مستقیم مأموریت PROGRAMMER-S04-01 در تاریخچه در اختیار این اجرا نبود؛ دامنه از مأموریت حاضر و بسته006 گرفته شد، نه از سبز بودن گزارش پروگرمر.

فقط این گزارش، `docs/stage4/independent-tests/` و `docs/stage4/independent-evidence/` افزوده شدند؛ فهرست دقیق/hash در `independent-evidence/added-files.json` است. env، کد محصول، قواعد، وضعیت پذیرش و شواهد قبلی حفظ شدند. فقط DB مصنوعی مرورگر بازسازی شد؛ DB برنامه reset نشد. سرویس‌های موقت3107/3109/8011 و browser-api در پایان متوقف و3108 فعال ماند؛ deploy، push، پیامک و اتصال پولی انجام نشد.

قدم بعدی مشخص: ارجاع دو ایراد جزئی برای اصلاح محدود و بازبینی انسانی طراحی، به‌ویژه پنل جدید و موبایل. این مأموریت با گزارش متوقف می‌شود؛ مرحله بعد آغاز نشده است.
