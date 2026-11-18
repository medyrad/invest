# مدل داده هسته

Draft.kind افزایشی و پروژه‌های قبلی با project ادامه می‌یابند. FieldDefinitionهای صندوق/فروش append-only هستند؛ rollback این seed عمداً برگشت‌ناپذیر است تا تعریف مصرف‌شده حذف نشود. migrationهای پذیرفته‌شده پیشین دست‌نخورده‌اند.

Opportunity یک Draft و یک public_revision دارد؛ Submission داده مؤثر، نوع، مسیرها و ارجاع فایل را ثابت نگه می‌دارد. Review/Event/Message/Report نیز با trigger در PostgreSQL immutable هستند. Decision و availability جدا هستند. Receipt با user/key یکتا و fingerprint، اثر دوباره و replay با ورودی متفاوت را رد می‌کند؛ replay اختیار جاری را بررسی می‌کند.

Case به snapshot زمان درخواست و فرصت متصل است؛ یک کارشناس جاری، نسخه، سابقه، deadline اولیه و موعد پیگیری بعد دارد. Consent به case/recipient/kind متصل است؛ شماره تنها از endpoint کنترل‌شده و با audit خوانده می‌شود. Saved، Search، Personal، Notification و Report مالک سروری مستقل دارند. profile مجوز role نیست. Retention نسخه‌های ارسال‌شده/تصمیم‌ها/پرونده و مدارک مرجع در محیط مصنوعی حفظ می‌شود؛ policy داده واقعی باز است.
