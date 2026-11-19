# ماتریس مسیر و حالت COMP-EXPERIENCE

مأموریت: `PROGRAMMER-EXPERIENCE-COMPLETE-01`؛ مبنا `e710781`. مرجع ZIP با SHA-256 برابر `6221401c736250c5ac7e5595aa988301f64b8d2fe576590291a7c2e53c247f5b` بررسی شد. این ماتریس شاهد فنی است و امضای انسانی طراحی نیست.

| مسیر/حالت | منبع مرجع یا تصمیم | مصرف‌کننده | اصلاح و شاهد | گیت باز |
|---|---|---|---|---|
| مهمان → ذخیره منتخب/شرایط → ورود موفق | تصمیم‌های D25/D28 و رفتار Saved مرجع | `store.ts`، `login-dialog.tsx`، identity intent، core personal | snapshot دقیق + key ثابت؛ replay پاسخ گم‌شده همان handoff و اثر idempotent؛ تست مرورگر PC-A01 و race PostgreSQL | احراز production خارج دامنه |
| لغو/خطا/تعویض حساب/پاسخ دیررس | مرز امنیتی مصوب | همان مصرف‌کنندگان | cancel flow، generation guard و عدم حمل نیت؛ تست لغو و تست‌های identity race | اتصال OTP واقعی خارج دامنه |
| پروفایل چندنقشی و جمع‌بندی | فرم پروفایل مرجع؛ اختیار فقط از D25/D27 | `profile.tsx`، `pro-profile.tsx`، Personal.profile | نقش‌های چندگانه، enum/استان/Decimal معتبر، HTML خواندنی، success پس از پاسخ؛ failure ورودی/داده قبلی را حفظ می‌کند | اعتبارسنجی مدرک واقعی/authority خارج دامنه |
| ویرایش شرایط ذخیره‌شده | Saved مرجع + AC-PC03 | `store.ts`، `personal.py` | `search_update` اتمیک زیر قفل، بدون delete/create؛ regression PostgreSQL | ندارد |
| پیش‌نمایش راهنما | `src/lib/guide.ts:1,43,50,87` و `components/guide/guide-view.tsx:2,49,54,66` | GuideView 009 + advisories 010 | پاسخ مؤثر نسخه۱؛ دانلود تا پاسخ سرور غیرفعال؛ preview از همان effective answers/questions/checks | تطابق کیفی متن نیازمند بازبینی انسانی |
| دریافت نخست/مجدد | همان doc-template؛ AC-PC05 | Report snapshot و `/core/reports/:id` | HTML فارسی ثابت، CSP sandbox، اختیار جاری، بدون Case؛ دریافت مجدد byte-for-byte همان snapshot | legacy JSON فقط fallback سابق است |
| زمین: گروه/ترتیب | `public/engine/advisor.html:45,1075` | ServiceEditor 010 | دو گروه دقیق مرجع، ترتیب انتخاب مشترک، بدون iframe؛ تصاویر چهار عرض | تأیید انسانی طرح باز است |
| راهنما/زمین در ۳۶۰ | هویت مرجع + mobile adaptation مصوب | GuideView و ServiceEditor | `guide-360.png`، `land-360.png`؛ بدون overflow | داوری انسانی |
| راهنما/زمین در ۳۹۰ | همان | همان | `guide-390.png`، `land-390.png`؛ بدون overflow | داوری انسانی |
| راهنما/زمین در ۷۶۸ | همان | همان | `guide-768.png`، `land-768.png`؛ بدون overflow | داوری انسانی |
| راهنما/زمین در ۱۴۴۰ | مرجع desktop | همان | `guide-1440.png`، `land-1440.png`؛ بدون overflow | داوری انسانی |
| D28: ۴۰ سناریوی غیرخالی | D28@1 بدون تغییر وزن | discovery API | `d28-human-review-inputs.json` و `d28-review-output.json`: سه مسیر، حداقل۲ نتیجه، top-5 موجود | label پیشینی خبره، آستانه و پذیرش PC-D05 باز |
| D28: no-preference/unknown | AC-D28/AC-PC07 | discovery API | چهار کنترل جدا؛ score/coverage و warning واقعی در خروجی | تفسیر کیفی انسانی باز |

## بازتولید یافته‌های ایستا پیش از اصلاح

- PC-A01: `bindAccount` نیت pending را پاک می‌کرد و consumer پس از ورود وجود نداشت؛ با تست پاسخ گم‌شده و شمار اثر سرور تأیید شد.
- PC-A02: UI فقط اولین role را مصرف می‌کرد؛ فرم چندنقشی و persistence واقعی بازتولید و اصلاح شد.
- PC-A03: ویرایش delete/create بود و caller پاسخ را await نمی‌کرد؛ شکست مصنوعی ۵۰۰ حفظ ورودی و رکورد قبلی را اکنون اثبات می‌کند.
- PC-A04: GuideView advisory ایستای client را مصرف می‌کرد و در اجرای نخست race دانلود قبل از advisory مؤثر دیده شد؛ دانلود اکنون تا پاسخ نسخه‌دار قفل است.
- PC-A05: endpoint گزارش opportunity JSON می‌داد؛ اکنون HTML snapshot تاریخی با اختیار جاری بازمی‌گردد.
- PC-A06: grid راهنما در موبایل، فهرست تخت زمین و بیرون‌زدگی منفی دکمه راهنمای خدمت با مرجع/رسپانسیو ناسازگار بود؛ تصاویر بالا حالت پس از اصلاح‌اند و assertion هندسی دکمه به آزمون افزوده شد. before تصویری تازه تولید نشد چون اجرای کد معیوب به‌عنوان محصول نهایی نگهداری نشد؛ محل و علت در diff و منبع قابل بازتولید است.
- PC-A07: فرمول D28 موجود بود ولی مجموعه داوری غیرخالی وجود نداشت؛ مجموعه آماده شد، پذیرش کیفیت انجام نشد.
- PC-A08: نگاشت source→consumer→task→evidence در همین ماتریس و tasks 009/010 ثبت شد.

محدودیت مقایسه: تصاویر محصول با شرایط یکسان viewport/data تولید شده‌اند؛ canvas تمام‌صفحه Chromium در RTL برای عرض‌های کوچک gutter اضافه دارد، اما `innerWidth` دقیق و مرز دکمه در آزمون assert شده است. runtime کامل ZIP در این مأموریت دوباره اجرا نشد، بنابراین درصد شباهت یا ادعای pixel-perfect ارائه نمی‌شود. تصاویر برای داوری انسانی آماده‌اند، جایگزین آن نیستند.
