# طرح اجرای مقدار دقیق

## خلاصه
همان Django5.2/DRF/PostgreSQL17 و Decimal داخلی؛ وابستگی تازه و تغییر frontend ندارد. numeric بدون typmod با check دقت/حدود، برای رد SQL بیش‌دقت به جای گردکردن PostgreSQL. API بدون ذخیره با CSRF موجود و خطای اختصاصی همین endpoint؛ احراز تغییر نمی‌کند.

## زمینه فنی
backend/apps/catalog/{values.py,schemas.py,models.py,decimal_field.py}؛ migration ساخت و seed واحد/فیلد نسخه۱، FK محافظ و unique(namespace,key,version). تعاریف immutable با save و trigger SQL، نسخه تازه رکورد تازه است. سه مدل مقدار مقدار/source/factor دقیق و snapshot واحد پایه دارند؛ save اعتبارسنجی کامل و constraints SQL؛ هیچ Opportunity/فرم ساخته نمی‌شود. normalize POST فقط یک مقدار را از ورودی به DTO نوع‌دار می‌برد؛ مقایسه helper داخلی بدون ranking/UI است.

## Constitution Check
I D29 و منبع واقعی؛ II frontend دست‌نخورده؛ III هشت FR→تسک/آزمون؛ IV اعتبارسنجی سرور+DB؛ V نامعلوم/واحد/مبنا صریح؛ VI PG/قرارداد/migration واقعی؛ VII فقط S04-03 و توقف. تعارض مسدودکننده صفر؛ فایل پنهان فرم آینده و نگاشت همه خدمات ادعا نمی‌شود.

## ساختار
اسناد همین specs/007-exact-values؛ mapping.md، research.md، data-model.md و contracts/api.md. backend/tests/test_values.py و contracts/openapi.yaml فقط قرارداد جدید. docs/stage4/values-report.md و values-evidence مسیر شاهد تازه؛ سوابق مستقل immutable.

## پیچیدگی
numeric سفارشی برای جلوگیری از silent rounding ضروری است؛ trigger برای ثبات دو جدول تعریف و کنترل ارتباط نوع/واحد/حدود مقدار در SQL است. بدون موتور فرم/محاسبات و بدون endpoint ذخیره عمومی. مدل‌های موجود taxonomy/geography حفظ می‌شوند.
