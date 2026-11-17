# تصمیم‌های فنی

- Decimal با localcontext بزرگ و trap عملیات نادقیق، ورودی خارجی فقط string؛ ظرفیت۲۴رقم صحیح+۹اعشار. رد مقدار خارج از حد، نه تغییر آن. اندازه‌های نمونه میلیارد/میلیون و مدت/مساحت در mapping ثبت می‌شوند؛ این ظرفیت از نمونه‌ها بزرگ‌تر است و قاعده تجاری تازه نیست.
- PostgreSQL numeric(p,s) می‌تواند ورودی را به scale گرد کند؛ numeric بدون typmod همراه CHECK(scale≤9 و حدود) برای رد مقدار اضافه انتخاب شد. Django custom field فقط db_type را تغییر می‌دهد؛ اعتبارسنجی رشته و مدل مستقل می‌مانند.
- UnitDefinition و FieldDefinition append-only، مقادیر snapshot واحد/عامل دارند؛ تاریخچه با تغییر ضریب تفسیر نمی‌شود. ماه/سال/روز پایه‌های مستقل و ارز خارجی بدون FX.

منابع رسمی: https://www.postgresql.org/docs/17/datatype-numeric.html ؛ https://docs.djangoproject.com/en/5.2/howto/custom-model-fields/ ؛ https://docs.python.org/3.14/library/decimal.html . کتابخانه/سرویس تازه لازم نیست؛ پژوهش مستقل یا delegation لازم نیست.
