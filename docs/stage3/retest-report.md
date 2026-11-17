# بازآزمایی مستقل TEST-S03-03

تاریخ: ۲۰۲۶/۱۱/۱۷. **نتیجه پذیرش فنی همین تحویل: قبول فنی؛ IT-001 تا IT-003 رفع‌شده‌اند.** تأیید انسانی طراحی، پذیرش نهایی مرحله و مجوز عرضه تغییر نکردند.

## نسخه دقیق

- هدف آزموده‌شده: **S03-FIX-5f377655f1f5**؛ hash کامل component برابر `5f377655f1f5592f1ed79c0a66deb50e53fe7107b339448e82da8aae85c88f52`.
- هر **۵۲ فایل** manifest اصلاح با workspace تطبیق داشت. image فعال3108 برابر `sha256:66051906086ef35de61214ae4e76c13ec25dd4ac74cd1a330d173d65a8a98a8a` و build ID برابر `SNrpyl-H1oIEP24eg8xPY` بود؛ هر دو با نسخه هدف یکسان‌اند. [تطبیق مستقل](retest-evidence/version-check.json).
- آزمون رفتار روی standalone3109 با build ID `NIgDNnYoKvyp0_OO0tKjC` و DB مصنوعی `invest_browser` انجام شد. bundle احراز `chunks/22z7mnh-qy4_q.js` در build آزمون و runtime3108، hash یکسان `038a2ea1e1032ecd891fce1fa725b1d327179335bdbf0c18234efe459cfe968a` داشت. rewrite آزمون به8008 بود؛ نتیجه به image قدیمی نسبت داده نشد. [شاهد](retest-evidence/browser-build-check.json).

## نتیجه سه باگ

| باگ | نتیجه مستقل و شاهد |
|---|---|
| **IT-001 — رفع‌شده** | پس از گذشت واقعی فاصله resend، سرور درخواست تازه را با200 پذیرفت و پاسخ به مرورگر قطع شد. retry همان key، payload و flow را فرستاد،200 و همان challenge را بازیابی کرد؛ `expires_at` و `resend_at` تغییر نکردند. شمار IssueEvent از۱ به۲ رسید و پس از بازیابی و ورود **۲ باقی ماند**؛ فقط دو challenge و یک نشست ساخته شد. در حالت نامعلوم اعلان کد قبلی حذف، مقدار ورودی پاک و ورود غیرفعال بود. کد بازیابی‌شده در UI با پاسخ پذیرفته‌شده برابر بود و ورود با آن موفق شد. [نتیجه کامل](retest-evidence/IT001-rerun.json)، [حالت نامعلوم](retest-evidence/IT001-unknown-hides-old-code.png)، [بازیابی](retest-evidence/IT001-recovered.png). |
| **IT-002 — رفع‌شده** | خروج تبA، هویت و شماره تبB را بدون reload پاک کرد؛ me نیز false بود. پاسخ authenticated قدیمی عمداً نگه داشته و پس از خروج تحویل شد؛ هویت برنگشت. focus، visibilitychange، pageshow و رفت‌وبرگشت واقعی تاریخچه بازبینی شدند. پیام واقعی فقط `{type:"session-invalidated"}` بود؛ پیام جعلی حاوی ادعای هویت/نقش نیز اختیار نداد و سرور مرجع ماند. `last_activity` نشست‌ها قبل/بعد برابر و درخواست activity صفر بود؛ نشست browser context مستقل دستگاه دوم برقرار ماند. [نتایج](retest-evidence/targeted.json)، [تب پاک‌شده](retest-evidence/IT002-cleared-tab.png). |
| **IT-003 — رفع‌شده** | وعده «فقط برای ورود» حذف شده است. قید رضایت/گیرنده مشخص، درباره اشتراک برای پیگیری فرصت است و استثنای امنیت/پشتیبانی D26 را نفی نمی‌کند. متن و شکست خطوط در۳۶۰/۳۹۰/۷۶۸/۱۴۴۰ خوانا بود؛ متن از کادر بیرون نزد و کنترل‌های شماره، دریافت کد، ورودی کد و ورود با scroll/click عادی قابل استفاده بودند. [نتایج چهار عرض](retest-evidence/targeted.json)، [۳۶۰](retest-evidence/IT003-privacy-360.png)، [۳۹۰](retest-evidence/IT003-privacy-390.png)، [۷۶۸](retest-evidence/IT003-privacy-768.png)، [۱۴۴۰](retest-evidence/IT003-dialog-1440.png). |

۱۳ فایل CSS/تصویر/آیکون و دو فایل فونت/مجوز نسبت به manifestهای تاریخی یکسان بودند. در crop هم‌شرایط۱۴۴۰، ستون تصویر با capture مستقل پیش از اصلاح دقیقاً یکسان بود؛ در ناحیه بالای فرم، خارج از یادداشت تغییرکرده، حدود۰٫۰۱۱۴٪ پیکسل‌ها اختلاف داشتند. تغییر بی‌دلیل دیگری در اجزای بررسی‌شده مشاهده نشد؛ این مقایسه، برابری کامل همه صفحات یا تأیید انسانی طراحی نیست. [فایل‌ها](retest-evidence/visual-assets.json)، [مقایسه ناحیه‌ها](retest-evidence/visual-comparison.json).

## ابزار و اجرای واقعی

اصل `independent-tests/browser-independent.cjs` و همه شواهد تاریخی حفظ شدند؛ hash ابزار اصلی همچنان با `tool-compatibility.json` یکسان است. کپی جدا در `retest-tests/browser-independent.cjs` ساخته شد:

- درخواست اولیه همچنان با «دریافت کد تازه» انتخاب می‌شود؛ فقط کلیک بازیابی به «تلاش دوباره برای دریافت نتیجه» تغییر کرد.
- مکث ثابت بازیابی با دریافت پاسخ واقعی و ظاهرشدن اعلان، و مکث تب دوم با شرط حذف هویت جایگزین شد. هیچ assertion قبلی حذف یا ضعیف نشد؛ پاسخ200 نیز صریح کنترل شد.
- فقط دو سناریوی مرتبط ابزار قدیمی اجرا شدند و مسیر خروجی تغییر کرد. آزمون تکمیلی `retest-tests/targeted.cjs` معیارهای قوی‌تر TTL، payload، PostgreSQL، پاسخ دیررس، دستگاه مستقل و چهار عرض را افزود. [diff دقیق ابزار](retest-evidence/tool-diff.patch)، [hash و شرح تغییر](retest-evidence/tool-change.json).

Node قفل‌شده از `.tools/runtimes/node-v24.22.3-linux-x64/bin/node` و Chrome151.0.7922.137 استفاده شد. پیش از اجرای زیر، standalone3109 و browser-api8008 طبق راهنمای پروژه برقرار شدند؛ ابزار reset خوانده و مقصد دقیق `test + invest_browser` با assertion کنترل شد. [آماده‌سازی](retest-evidence/setup.txt).

| فرمان از ریشه، با `node` قفل‌شده | نتیجه |
|---|---|
| `node docs/stage3/retest-tests/browser-independent.cjs` | **۲ موفق**؛ [خروجی](retest-evidence/compatibility.txt)، [JSON](retest-evidence/compatibility/independent-browser.json) |
| `node docs/stage3/retest-tests/targeted.cjs` | **۹ موفق**؛ اجرای IT-001 پیش از آماده‌شدن resend با بسته‌شدن غیرمنتظره مرورگر متوقف شد؛ علت قطعی این توقف مشخص نشد. [خروجی](retest-evidence/targeted.txt) |
| `RETEST_ONLY=IT001 RETEST_FIXTURE_SEED=200 node docs/stage3/retest-tests/targeted.cjs` | **۱ موفق**؛ تمام معیارهای IT-001، شامل شمارنده واقعی PostgreSQL و ورود نهایی. [خروجی](retest-evidence/IT001-rerun.txt) |

نتیجه نهایی **۱۲ بررسی موفق** است. دو تلاش مقدماتی جدا ثبت شده‌اند و پنهان نشده‌اند: توقف مرورگر بالا، و یک بازاجرای انتخابی که شماره مصنوعی اجرای قبلی را دوباره استفاده کرد و انتظار شمار۱ با مقدار۳ برخورد کرد. مورد دوم با fixture استفاده‌نشده، بدون تغییر assertion یا سهمیه، بازاجرا شد. این دو نتیجه به‌عنوان شکست رفتاری نسخه هدف معرفی نمی‌شوند؛ شواهدشان در [اجرای اولیه](retest-evidence/targeted.json) و [تداخل fixture](retest-evidence/attempts/fixture-collision.json) باقی است. [جمع‌بندی ماشین‌خوان](retest-evidence/summary.json).

سفر متأثر ورود → reload → خروج، رد cookie قدیمی، شماره نامعتبر و کد غلط نیز موفق بود. مجموعه گسترده بک‌اند، تست بار، SMS واقعی و مراحل S05/S06/S07 تکرار نشدند؛ هیچ شکست تازه‌ای اجرای آن‌ها را لازم نکرد.

## حفاظت و محدودیت

فقط همین گزارش، `docs/stage3/retest-tests/` و `docs/stage3/retest-evidence/` افزوده شدند؛ فهرست و hash در `retest-evidence/added-files.json` است. فایل محصول، قواعد، env، اسناد پذیرش و شواهد قبلی تغییر نکردند. DB برنامه بازنشانی یا برای سفر آزمون استفاده نشد؛ فقط DB مصنوعی مرورگر آماده شد. [کنترل حفظ فایل‌ها و env](retest-evidence/preservation-check.json).

مرورگر واقعی با viewport شبیه‌سازی‌شده آزموده شد؛ دستگاه فیزیکی، مرورگرهای دیگر و تضمین BFCache همه پلتفرم‌ها بررسی نشدند. شاخه‌های focus/visibility/pageshow با رخداد کنترل‌شده و بازگشت تاریخچه با مرورگر اجرا شدند. کدها در تصاویر mask شده‌اند. سرور موقت3109 و browser-api پس از آزمون متوقف و نسخه اصلی3108 فعال نگه داشته شد؛ سرویس دیگری، deploy یا push انجام نشد.

مورد باز در دامنه این سه اصلاح: **ندارد**. قدم بعدی برای هماهنگ‌کننده و کاربر، بازبینی انسانی طراحی و تصمیم پذیرش S03 است؛ این گزارش آن وضعیت‌ها را علامت نمی‌زند و مأموریت در همین‌جا متوقف می‌شود.
