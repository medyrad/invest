# گزارش PROGRAMMER-EXPERIENCE-FIX-02

مأموریت: `PROGRAMMER-EXPERIENCE-FIX-02`؛ مبنای مستقل: `32b3410f14f2e679e03bd7b69e4f8051cedaa42b`؛ commit کد و تست: `18b6c6e15de5d52f3d803c6a5fdc36062f37b56f`؛ تاریخ: ۲۰۲۶/۱۱/۲۰. این سند گزارش اصلاح برنامه‌نویس است و پذیرش مستقل/انسانی، پایان کامل COMP-EXPERIENCE یا مجوز مرحله بعد نیست.

## علت و اصلاح EXP-IT-003

علت ریشه‌ای در `apps/core/reporting.py` بود: meta سند، route را با `str(route)` مستقیماً وارد HTML می‌کرد؛ در نتیجه preview و سند تازه عبارت داخلی `مسیر: investor` داشتند. وجود `investor` در واژه‌نامه عمومی TERMS این مسیر رندر را پوشش نمی‌داد.

واژه‌نامه منجمد `report-routes-v1.json` افزوده شد. مجموعه مجاز در startup از union فیلد `routes` قرارداد موجود `search_fields.json` استخراج می‌شود و باید دقیقاً با کلیدهای واژه‌نامه برابر باشد؛ در غیر این صورت backend بالا نمی‌آید. هر هشت مسیر `investor/fund/contractor/buyer/lessee/heritage/charity/operator` label فارسی نسخه۱ دارند. renderer فقط label نسخه‌دار را نمایش می‌دهد.

شناسه خارج قرارداد به route شناخته‌شده حدس زده نمی‌شود: عبارت «شناسه تاریخی ناشناخته: …» با escaping و بخش «محدودیت داده تاریخی» می‌آید. این رفتار برای داده تاریخی ناقص است، نه افزودن route تازه.

## preview، دانلود و سابقه

preview و ایجاد گزارش تازه همچنان از `report_snapshot` و renderer مشترک می‌آیند. گزارش تازه label فارسی را در snapshot نهایی دارد؛ دانلود اول و دریافت مجدد همان بایت را می‌دهند و پرونده تازه نمی‌سازند. تست Chromium علاوه بر assertion، هر دو سند را واقعاً render کرد و تصاویر بازبینی شدند.

HTML قالب۲ قبلی عمداً تغییر نمی‌کند. endpoint دریافت مجدد ابتدا `snapshot.rendered_html` را برمی‌گرداند؛ trigger PostgreSQL نیز history را immutable نگه می‌دارد. بنابراین گزارش قدیمی که پیش از این اصلاح `مسیر: investor` را freeze کرده، همان متن قدیمی را حفظ می‌کند؛ فقط preview و گزارش‌های تازه label نسخه۱ فارسی دارند. migration، backfill یا بازنویسی snapshot انجام نشد.

## اعتبارسنجی واقعی

محیط: compose مستقل `invest-expit`، PostgreSQL 17.12 روی tmpfs، داده مصنوعی، backend نهایی `sha256:b26f984ef72b1cc63895c7bca0f481d83030679a9270d7e17d9e07825205a7df` و frontend موجودِ اثبات‌شده `sha256:40072e8c08fd71658ff709b42aa3e46fa5e2050d7740397cdfdc3c7c5e307a49`. hash فایل‌های runtime renderer و vocabulary با checkout برابر است. endpoint نسخه به‌دلیل عدم تغییر بسته نسخه تاریخی، همان `S08-FIX-01-e47b3701a586` را نشان می‌دهد؛ digest image و source hash مشخصه دقیق این اصلاح‌اند.

- اجرای تجمیعی backend: ۲۱ node، ۲۱ قبول، ۰ رد در ۲۲٫۵۴ثانیه pytest و ۳۵٫۵۱ثانیه wall. ۲۰ سناریوی متمایز دارد؛ node مستقل investor با مورد پارامتری همان معنا هم‌پوشان است و دوباره به مخرج یکتا افزوده نشده است.
- پوشش: هشت route، برابری دقیق قرارداد/واژه‌نامه، unknown تاریخی و escaping، preview/دانلود اول/redownload، HTML قدیمی منجمد، دو شکل legacy، محتوای مؤثر، renderer operator و عدم ایجاد Case.
- آزمون مستقل قبلاً شکست‌خورده `test_report_route_enum_is_human_readable_persian`: در اجرای نهایی قبول؛ این اجرای برنامه‌نویس جای پذیرش مستقل را نمی‌گیرد.
- Chromium/Playwright 1.65.1: یک سفر واقعی preview → دانلود اول → صفحه پروفایل → دریافت مجدد، ۱/۱ قبول، ۲۱٫۱ثانیه test و ۳۶٫۱۱ثانیه wall؛ label فارسی دیده شد، raw enum غایب بود و دو فایل بایت یکسان داشتند.

فرمان نهایی backend همان node-idهای صریح هفت تابع گزارش در `test_experience_fix.py` (دو تابع پارامتری)، سه regression `test_core.py` و node مستقل read-only را با `--reuse-db --junitxml=/fix02/backend-final.xml` اجرا کرد. فرمان مرورگر کامل در README شواهد ثبت است. تست حساب، پروفایل و خدمات نامرتبط اجرا نشد.

## زمان، فایل و محدودیت

آماده‌سازی/خواندن اسناد stopwatch مستقل نداشت و زمان ساختگی گزارش نمی‌شود. build نهایی backend ۱۵٫۶۰ثانیه بود؛ build تشخیصی پیش از کنترل contract نیز ۱۶٫۳۱ثانیه و rerun محسوب می‌شود. frontend build صفر بود. اجرای نهایی backend ۳۵٫۵۱ثانیه و مرورگر ۳۶٫۱۱ثانیه wall بود. اجراهای تشخیصی browser که به CSRF origin غیرواقعی و selector بیش‌ازحد خاص خوردند، نتیجه محصول شمرده نشدند؛ runner نهایی روی secure-context localhost و selector معنایی بخش گزارش اجرا شد. زمان گزارش با بازبینی شواهد هم‌پوشان است و خالص ادعا نمی‌شود.

فایل‌های محصول: `backend/apps/core/reporting.py`، `report-routes-v1.json` و `backend/tests/test_experience_fix.py`. اسناد صاحب مسئله: plan/contracts/tasks ویژگی 009، stage-status، این گزارش و پوشه `fix-02-evidence`. manifest hashها و نسخه‌ها را ثبت می‌کند.

وضعیت برنامه‌نویس EXP-IT-003: **اصلاح‌شده و آماده بازآزمایی مستقل**. پذیرش مستقل و انسانی همچنان false است. تصمیم legacy، فرمول/وزن D28، شواهد تاریخی و انتظار مستقل تغییر نکردند. مانع فنی شناخته‌شده‌ای در دامنه محدود FIX-02 باقی نمانده؛ داده legacy واقعاً ذخیره‌نشده و HTML منجمد قدیمی مطابق تصمیم جاری دست‌نخورده می‌مانند. push، deploy و بسته بعدی انجام نشد.
