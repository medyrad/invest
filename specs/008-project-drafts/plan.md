# Implementation Plan: پیش‌نویس پروژه A1

**Feature**: 008-project-drafts | ۲۰۲۶/۱۱/۱۷ | [spec](spec.md) | مبنا d713876

## Summary
Django app مستقل workspace؛ استفاده مجدد از نشست و catalog007 بدون تغییر رفتار آن‌ها. فرانت مسیر /drafts، اجزای برند موجود و فرم بخش‌بندی‌شده مبتنی بر schema ثابت نسخه۱ (فرم‌ساز عمومی نیست).

## Technical Context
Python3.14.10/Django5.2.19/DRF3.18.3/PostgreSQL17.12؛ Next16.4.6/React19.3.1، نسخه‌های قفل‌شده موجود. ابزار بررسی فایل در research.md قفل می‌شود. pytest و Playwright موجود، Chrome موجود؛ نصب چارچوب جدید ممنوع.
ذخیره خصوصی blob در PostgreSQL BinaryField: تراکنش سهمیه/فایل/ارجاع و purge یک مرز دارد؛ برای این محیط مصنوعی کم‌ظرفیت، هزینه backup/حجم از بهره‌برداری واقعی تفکیک است. هیچ مسیر public/media وجود ندارد.
حد مهندسی قابل تنظیم: حساب۵۰۰MiB کل دریافت موجود (pending/rejected/deleted نیز)، ۳۰ reservation و۶۰ تلاش دریافت (شامل retry/خطا) در ساعت و۱۰۰ draft؛ جلوگیری از دریافت بی‌حد، نه قاعده تجاری. D32: تصاویر۱۰MiB/۱۰عدد/۵۰MiB، اسناد۲۰MiB/۲۰عدد/۱۰۰MiB برای هر موجودیت. رزرو پیش از دریافت، قفل حساب و موجودیت؛ payload دریافت در chunk و حداکثر اندازه رزروشده، SHA256 برای retry. رزروهای موقت۲۴ساعت در بودجه می‌مانند.
worker همان image، job مدیریت Django با قفل skip_locked و parser در subprocess محدود CPU۲۰ثانیه، wall۳۰ثانیه، RAM۵۱۲MiB، خروجی تصویر۱۰MiB. Scanner جدا با INSTREAM و timeout۳۰ثانیه؛ قطع سرویس→pending با backoff حداکثر۱۵دقیقه. loop واقعی هر۵ثانیه بررسی و هر۶۰ثانیه purge؛ --once برای آزمون/عملیات. حداکثر یک فایل در هر worker؛ replica بیشتر با قفل ایمن. محدودیت اندازه stream در scanner هم برقرار.

## Constitution Check
پیش و پس از طراحی: I منبع/D31؛ II اجزای موجود و تصاویر چهارعرض، بدون ادعای تأیید؛ III mapping؛ IV اختیار جاری/قفل/CSRF؛ V007؛ VI PostgreSQL/مرورگر/scanner واقعی؛ VII فقطA1. هر هفت اصل پاس طراحی؛ شواهد اجرا جدا در گزارش. هیچ استثنای قانون اساسی نیست.

## Project Structure
backend/apps/workspace/{models,schema,service,api,files,inspect_file}.py و management/commands/workspace_jobs.py؛ migrations افزایشی workspace و catalog0005؛ backend/tests/test_workspace*.py.
frontend/src/app/drafts/page.tsx و components/workspace/ با CSS محدود به workspace؛ تغییر Header فقط پیوند پیش‌نویس‌های من.
specs/008-project-drafts/{spec,plan,research,data-model,mapping,quickstart,tasks}.md و contracts/api.md؛ docs/stage5/a1-evidence/ و a1-report.md.

## Phases / validation
۱ منبع/اسناد/تحلیل؛ ۲ تست و مدل/اختیار/نسخه؛ ۳ شروط/مقدار و UI؛ ۴ فایل/scanner/job/بازیابی؛ ۵ تست PG/مرورگر و regression متأثر؛ ۶ یک build نهایی هر image متأثر و manifest/کامیت. مدل جدید migration واقعی با بررسی حفظ داده. rollback تنها DB آزمون. هیچ seed واقعی یا endpoint اعطای نقش نیست.

## Complexity Tracking
blob داخلDB انتخاب آگاهانه برای یکپارچگی A1؛ مهاجرت storage برای مقیاس واقعی خارج دامنه و بدون وعده آمادگی production. نسخه خام هر ذخیره خصوصی و مقادیر دقیق typed ذخیره می‌شوند؛ مخفی‌شدن حذف نیست. کلید idempotency در client تا تعیین نتیجه ثابت و body ثابت؛ conflict هم receipt خطا ندارد و ورودی حفظ می‌شود.

پردازش scanner/parser خارج تراکنش موجودیت با lease۱۲۰ثانیه و بازبینی اتمیک پس از بررسی؛ قطعی سرویس قفل ذخیره متن را نگه نمی‌دارد. دریافت rate-admission جداگانه commit می‌شود تا خطای checksum نرخ را rollback نکند.

تکمیل ظرفیت: catalog0006 تعریف metric_quantity@2 و۲۱واحد افزایشی ایجاد می‌کند؛ base هر واحد مستقل و factor=1، بدون تبدیل حدسی. widget از واحدهای صریح schema می‌خواند؛ API مقدار قدیمی@1 را با allowlist همان تعریف حفظ می‌کند. شمار تعاریف نهایی۲۱فیلد/۳۳واحد است. build دوم صرفاً به علت این شکاف یافته‌شده در تطبیق نهایی مرجع لازم شد.

انتقال Next.js روی۲۱MiB محدود است تا مدرک۲۰MiB کامل عبور کند؛ نوع/حجم/سهمیه نهایی سمت سرور مستقل اعمال می‌شود. شکست واقعی مرز۲۰MiB دلیل build سوم فقط فرانت است.

## اصلاح rollback — A1-FIX-01
علت بررسی‌شده: constraint triggerهای FK ابتدا معوق‌اند؛ DELETE می‌تواند قبل از ALTER ENABLE رویداد معوق باقی بگذارد. reverseها در تراکنش اتمیک همان migration، پیش از ALTER، SET CONSTRAINTS ALL IMMEDIATE اجرا می‌کنند؛ خطای constraint پنهان نمی‌شود و mode با پایان تراکنش به پیش‌فرض برمی‌گردد. guardهای immutable فقط داخل همان تراکنش و فقط برای حذف تعریف همین نسخه موقتاً غیرفعال می‌شوند؛ شکست rollback داده/DDL همان migration را برمی‌گرداند. وابستگی FK/PROTECT و ارجاع allowed_units تعریف‌های باقی‌مانده مانع حذف واحدند. backward migration فقط روی test_ PostgreSQL، بدون fake/cascade یا دست‌زدن به DB اصلی. آزمون هدفمند catalog/value/reverse و build backend/test؛ فرانت/scanner/مرورگر بی‌تغییر.
