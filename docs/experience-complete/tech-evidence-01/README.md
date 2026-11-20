# شواهد فنی TECH-EXPERIENCE-EVIDENCE-01

این مسیر فقط fixture، harness و شواهد فنی مأموریت است. داده‌ها مصنوعی‌اند، وارد کاتالوگ عمومی نمی‌شوند و هیچ رأی انسانی در آن‌ها ثبت نمی‌شود.

- `d28_prepare.py`: ساخت deterministic ورودی و freeze پیش از اجرای محصول.
- `d28_run.py`: اجرای جداگانهٔ development یا held-out روی PostgreSQL ایزوله و مقایسه با oracle مستقل.
- `build_manifest.py`: بازسازی deterministic فهرست فایل‌ها، اندازه و SHA-256 پس از اعتبارسنجی نهایی.
- `d28-inputs.json` و `d28-input-freeze.json`: ورودی منجمد و hash.
- `d28-*-results.json`: خروجی واقعی هر split؛ نتیجه نامطلوب نیز بازنویسی نمی‌شود.
- `design-slot-matrix.csv`: تعیین تکلیف ۱۰۴ جایگاه طراحی.
- `interaction-evidence.csv`: نگاشت تعامل‌های واقعی و محدودیت شاهد.
- `manifest.json`: منشأ، نسخه، شمار و hash تحویل.

فرم‌های رأی در بسته‌های انسانی جدا هستند و باید کاملاً خالی بمانند.
