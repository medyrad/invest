# برنامه هسته

Django/DRF/PostgreSQL و Next/React موجود، بدون تعویض زیرساخت. افزودن apps.core برای گردش، انتشار، پرونده و فضای شخصی؛ گسترش schema A1 با kind پایدار و schema مخصوص هر نوع؛ catalog append-only با migration تازه. عملیات با قفل تراکنشی و key/fingerprint، snapshot immutable در DB، کنترل دسترسی جاری در هر بار دریافت. DTO عمومی whitelist از effective snapshot، فایل فقط مشتق صریح تأییدشده. مدل role از حساب سرور؛ ابزار محلی جدا و ممنوع در public.

تطبیق با Decimal و وزن سیاست D28@1، بدون حذف ترجیحی؛ cursor امضاشده شامل معیار/زمان/نسخه. تقویم مصنوعی نسخه‌دار و deadline پایدار؛ jobs زمان‌پذیر. Case/assignment/consent/message با قفل واحد پرونده؛ اعلان در همان تراکنش. گزارش snapshot ثابت و بدون شماره.

فرانت: اجزای مرجع Results/Detail/Compare/Saved/Guide، adapter داده API و store حساب سروری؛ حفظ LoginShell و الگوی stale-response guards. پنل‌های مالک/ادمین/کارشناس با اجزای برند؛ مسیرهای واقعی جایگزین catch-all.

برش‌ها: (۱) اسناد و schema سه نوع؛ (۲) بررسی/انتشار/سازمان؛ (۳) پرونده/رضایت/مهلت؛ (۴) discovery و فضای شخصی؛ (۵) UI/seed و نقش‌های محلی؛ (۶) آزمون یکپارچه و تطبیق مرجع/گزارش. تست انتخابی هر برش، build هنگام استفاده و یک regression نهایی. rollback مخرب فقط DB آزمون.

گیت constitution: منبع، دقت، مجوز سرور، سابقه و دامنه حفظ؛ پذیرش طراحی جدا. ریسک‌ها: اتصال UI مرجع به DTO، هم‌زمانی publication/assignment، مبنای بازده. با آزمون‌های منفی/مثبت و PostgreSQL پوشش داده می‌شوند.

## برنامه اصلاح CORE-FIX-01

Migration افزایشی catalog0010 برای تعریف دوره operator؛ schema و کنترل واحد صریح، بدون تغییر معنای مدت‌های قبلی. parser کنترل عضو قبل lookup؛ مقایسه با metadata گروه/ترتیب مرجع و رندر بخش‌های مستقل و anchor قابل صفحه‌کلید. تست‌های تاریخی دست‌نخورده؛ اجرای ترتیبی pytest مرتبط، سفر operator و مقایسه سه نوع دسکتاپ/موبایل. build متأثر پس از تثبیت و اجرای3108؛ گزارش، manifest، commit و push معمول origin.
