# طرح بسته S04

Django/DRF/PostgreSQL فعلی و Next/React فعلی حفظ می‌شوند. Tailwind و Motion/Radix/Iconsax اجزای واقعی مرجع برای انتقال دقیق UI؛ نسخه‌ها از registry رسمی بررسی و دقیق قفل می‌شوند. منبع domain فقط advisor است.

Constitution Check: I ZIP و مأموریت؛ II همان JSX/asset/CSS فعال با اصلاح موبایل و اختلاف صریح قواعد؛ III FR→tasks→test؛ IV catalog سروری و auth S03 بدون تغییر قواعد؛ V نمونه/unknown واضح؛ VI تست PG/browser و تصویر section؛ VII همین بسته و توقف پس از گزارش. هیچ ابهام مسدودکننده این دامنه باقی نیست.

مدل: Group id منبع؛ Subtype id namespace گروه و raw_id؛ Province id از index فایل منبع ثابت v1؛ County id از شماره استان/ردیف مرجع ثابت v1؛ City فقط پیوندهای واقعی cities منبع. import روی source-id شناخته‌شده update، روی هویت متعارض reject و هرگز delete نمی‌کند. روابط FK/unique. JSON fixture نسخه‌دار از آرشیو کنترل‌شده، نه فهرست موازی frontend.

API /api/v1/catalog/{taxonomy,geography,preview}؛ فقط GET، version در پاسخ، نمونه فقط development/test. DTOهای frontend از API؛ حافظه موقت انتخاب‌ها، بدون persist هویت. S03 به AuthContext قابل استفاده مجدد تبدیل می‌شود؛ منطق OTP/نشست/پیام بین تب‌ها حفظ می‌شود.

اجزای HeroCompass/MapScene و بخش‌های sections، برند و کارت با وابستگی محدود از مرجع انتقال می‌یابند؛ heroهای جایگزین حذف از مسیر کد. matching مرجع منتقل نمی‌شود. نمایش روش کار مفهوم با امتیاز نامعلوم و ترجیح مکانی/بودجه است، نه قیف حذف بر مبنای آن دو. مقصدهای آینده صفحه شفاف وابستگی با برگشت خانه دارند؛ اجرای قابلیت آینده نیستند.

فایل‌ها: backend/apps/catalog و tests/test_catalog.py؛ frontend/src/components/home/site/brand/listing/ui و lib/catalog-context.tsx؛ tests/browser/home.spec.ts و auth موجود متناسب header. گزارش‌ها و شواهد قدیمی immutable، اجرای تست‌های تصویری قبلی در cwd جدا.
