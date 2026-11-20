# برنامه هسته

## اصلاح مجاز PROGRAMMER-EXPERIENCE-FIX-01

مبنای مستقل c7ac09b؛ push/deploy ممنوع. LoginOperation کلید handoff را به AuthSession و payload دقیق متصل می‌کند؛ لغو/انقضا و نشست جاری در همان ترتیب قفل identity→user بررسی می‌شوند. profile patch به‌جای replacement و base برای تشخیص تعارض داده متفاوت است؛ تعارض409 ورودی را حفظ می‌کند و سیاست merge بیزینسی تازه‌ای نمی‌سازد. search_update همان رکورد و کلید پایدار retry را حفظ می‌کند. فرم عمومی professional را نمی‌فرستد؛ refresh فرم dirty را جایگزین نمی‌کند.

report_snapshot و reporting.render منبع مشترک preview و دریافت هستند؛ قالب۲ همراه labels و action_steps در snapshot ثبت می‌شود. دریافت legacy فقط داده تاریخی + تعاریف ایستای نسخه۱ را می‌خواند؛ مقدار زنده برای پرکردن سابقه ممنوع است. فقدان گام/نام مکان تاریخی باید در محدودیت گزارش شود، نه ساخته شود. JSON جای متن فارسی نیست. آزمون معنایی بخش‌ها علاوه بر ثبات بایت و مجوز جاری لازم است.

واژه‌نامه legacy نسخه۱ در `apps/core/guide-fields-v1.json` کنار renderer منجمد است و import طرح‌واره زنده ندارد. شکل‌های تاریخی دارای/فاقد `report_id` و دارای پاسخ خام بدون `effective_advisory` جدا آزموده می‌شوند. قرارداد ۲۰ زمینه در `dynamic-context-contract.json`، alias منبع به فیلد جاری، اثر یا context-only بودن و سناریوی پذیرش هر زمینه را به runtime متصل می‌کند.

برای گزارش‌های تازه، مجموعه مسیرها از union نسخه جاری `apps/core/search_fields.json:routes` استخراج و پوشش دقیق آن با واژه‌نامه منجمد `report-routes-v1.json` در startup کنترل می‌شود. مقدار خارج از این قرارداد در بازنمایی تاریخی به مسیر شناخته‌شده نگاشت نمی‌شود و همراه محدودیت صریح می‌آید. HTML قالب۲ که قبلاً ذخیره شده همچنان منبع دریافت مجدد است و با تغییر واژه‌نامه migrate یا بازنویسی نمی‌شود.

مخرج route/state در fix-01-evidence/route-state-denominator.csv و نگاشت۲۰زمینه در catalog صاحب مسئله تکمیل می‌شود؛ شکاف شاهد فنی با امضای انسانی فرق دارد. تسک‌های اصلاح تا نتیجه واقعی بسته نمی‌شوند.

Django/DRF/PostgreSQL و Next/React موجود، بدون تعویض زیرساخت. افزودن apps.core برای گردش، انتشار، پرونده و فضای شخصی؛ گسترش schema A1 با kind پایدار و schema مخصوص هر نوع؛ catalog append-only با migration تازه. عملیات با قفل تراکنشی و key/fingerprint، snapshot immutable در DB، کنترل دسترسی جاری در هر بار دریافت. DTO عمومی whitelist از effective snapshot، فایل فقط مشتق صریح تأییدشده. مدل role از حساب سرور؛ ابزار محلی جدا و ممنوع در public.

تطبیق با Decimal و وزن سیاست D28@1، بدون حذف ترجیحی؛ cursor امضاشده شامل معیار/زمان/نسخه. تقویم مصنوعی نسخه‌دار و deadline پایدار؛ jobs زمان‌پذیر. Case/assignment/consent/message با قفل واحد پرونده؛ اعلان در همان تراکنش. گزارش snapshot ثابت و بدون شماره.

تکمیل COMP-EXPERIENCE روی ownerهای موجود انجام می‌شود: LoginFlow.intent برای handoff immutable؛ Operation هسته برای once-only؛ `search_update` زیر `select_for_update`؛ profile در Personal با اعتبارسنجی سرور؛ Report با شناسه operation و `rendered_html` ثابت. advisory گزارش از Subtype نسخه‌دار catalog به raw_id معتبر نگاشت و در سرور دوباره ارزیابی می‌شود. UI دانلود تا پاسخ مؤثر قفل است. آزمون اثر شامل race/replay احراز، PostgreSQL واقعی، مرورگر journey و چهار عرض است؛ suite کامل S08 دوباره اجرا نمی‌شود.

فرانت: اجزای مرجع Results/Detail/Compare/Saved/Guide، adapter داده API و store حساب سروری؛ حفظ LoginShell و الگوی stale-response guards. پنل‌های مالک/ادمین/کارشناس با اجزای برند؛ مسیرهای واقعی جایگزین catch-all.

برش‌ها: (۱) اسناد و schema سه نوع؛ (۲) بررسی/انتشار/سازمان؛ (۳) پرونده/رضایت/مهلت؛ (۴) discovery و فضای شخصی؛ (۵) UI/seed و نقش‌های محلی؛ (۶) آزمون یکپارچه و تطبیق مرجع/گزارش. تست انتخابی هر برش، build هنگام استفاده و یک regression نهایی. rollback مخرب فقط DB آزمون.

گیت constitution: منبع، دقت، مجوز سرور، سابقه و دامنه حفظ؛ پذیرش طراحی جدا. ریسک‌ها: اتصال UI مرجع به DTO، هم‌زمانی publication/assignment، مبنای بازده. با آزمون‌های منفی/مثبت و PostgreSQL پوشش داده می‌شوند.

## برنامه اصلاح CORE-FIX-01

Migration افزایشی catalog0010 برای تعریف دوره operator؛ schema و کنترل واحد صریح، بدون تغییر معنای مدت‌های قبلی. parser کنترل عضو قبل lookup؛ مقایسه با metadata گروه/ترتیب مرجع و رندر بخش‌های مستقل و anchor قابل صفحه‌کلید. تست‌های تاریخی دست‌نخورده؛ اجرای ترتیبی pytest مرتبط، سفر operator و مقایسه سه نوع دسکتاپ/موبایل. build متأثر پس از تثبیت و اجرای3108؛ گزارش، manifest، commit و push معمول origin.

## مسیر جایگزین مصوب — PC-FALLBACK-01

مصوبه legacy با منبع پیام PRODUCT-EXPERIENCE-FALLBACK-01 ثبت شد؛ قواعد renderer/immutability بالا تغییر نمی‌کنند. نبود داور، توسعه غیرعمومی با مجوز جدا را مسدود نمی‌کند؛ طراحی تخصصی، D28 خبره و production گیت عرضه‌اند. [بسته هماهنگی](../../docs/experience-complete/fallback-gates-plan.md) جزئیات شاهد/مخرج و پرامپت را دارد؛ مالک اجرا همین plan/tasks است.

ترتیب T030 و010/T041، سپس T031/T032 و T033 در TECH-EXPERIENCE-EVIDENCE-01 اجرا شد؛ شواهد و fixture در `docs/experience-complete/tech-evidence-01/` و گزارش تجمیعی ثبت‌اند. تصمیم‌های COMP-AI همچنان مرحله و مجوز جدا می‌خواهند و در این اجرا آغاز نشدند.

مجموعه۶فرصتی قدیم فقط calibration باقی است. حجم مصوب۸۰سناریو/۹۶فرصت در هشت مسیر با split۳۲/۴۸ ساخته شد؛ oracle عددی از تابع D28 مستقل و وزن/فرمول/label انسانی دست‌نخورده‌اند. نخستین held-out به‌علت basis ناقص fixture پیش از scoring شکست و حفظ شد؛ اجراهای اصلاح‌شده regression هستند و کورسازی مطلق ادعا نمی‌شود. این تحویل فقط fixture/harness/evidence/docs است؛ Constitution II/III/V/VI/VII و گیت‌های انسانی T020 برقرارند.

## اصلاح شواهد PROGRAMMER-EXPERIENCE-EVIDENCE-FIX-01

بدون تغییر کد محصول یا D28، canonical signature از route/kind/snapshot مؤثر ساخته می‌شود و شناسه/title/split/metadata در یکتایی نقشی ندارند. پروفایل‌های boundary با حفظ unknown/known-zero از زمینه مؤثر متفاوت استفاده می‌کنند. route×unit/basis فقط وقتی applicable است که criteria عددی یا return، unit/basis و check متناظر oracle وجود داشته باشد؛ operator و charity طبق قرارداد واقعی N/A هستند.

captureهای اصلاحی از imageهای برچسب‌دار checkout مبنای مستقل، BUILD_ID و hash سورس/runtime به metadata هر تصویر وصل می‌شوند. development روی DB تازه و held-out فقط regression اجرا می‌شود؛ تلاش‌های تاریخی، replay و فرم‌های انسانی بازنویسی نمی‌شوند. validatorهای مستقل mutation موقت، route/state و provenance را بررسی می‌کنند و خروجی به manifest متصل است.
