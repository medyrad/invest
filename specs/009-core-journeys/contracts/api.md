# قرارداد هسته v1

تمام APIها /api/v1/core؛ خطا envelope استاندارد با پیام فارسی/fields/request_id؛ private no-store، CSRF برای mutation. زمان ISO؛ مقدار اعشاری رشته‌ای. key UUID و version برای تغییر وضعیت؛ retry همان ورودی/کلید همان رسید و بدون اثر مجدد. replay نیز اختیار جاری می‌خواهد.

عمومی: opportunities (kind/route/q/criteria/cursor)، opportunities/:id (فقط public_revision)، compare (۲–۴ هم‌نوع)، library. خصوصی: dashboard، submit/:draft، review/:revision، organization/:request، availability/:opportunity، cases و cases/:id/actions، saved، searches، profile، notifications، reports. درخواست‌ها actor از session؛ نقش از payload پذیرفته نیست.

revision شامل snapshot مؤثر و file refs ثابت؛ تصمیم/تاریخچه جدا و append-only. public_revision در قفل opportunity عوض می‌شود. مالک فقط pause؛ admin با دلیل approve/reject/changes_requested/suspend/reactivate. انتشار سازمانی نیازمند اختیار فعال و پایان معتبر. بررسی مدارک و منبع مستقل و منع self-approval.

پرونده: customer و expert جاری و admin عملیاتی؛ owner خودکار عضو نیست. تماس endpoint جدا فقط با grant همان recipient، پس از revoke/assignment مجدد بسته. answered نیازمند متن انسانی و next_action؛ customer confirm یا job هفت‌روز بدون پیام تازه closes. پیام پس از terminal با اقدام صریح follow-up پرونده مرتبط تازه می‌سازد. SLA مصنوعی نسخه۱ هدف داخلی، نه وعده عرضه.

ذخیره و گزارش پرونده ایجاد نمی‌کنند؛ compare مبنای ناسازگار را غیرقابل‌مقایسه برمی‌گرداند. profile هرگز role نمی‌پذیرد.

افزوده در مقابله D25: action پرونده `next_followup_at` صریح (ISO با timezone یا null) دارد؛ answer/awaiting_user تاریخ آینده لازم دارند. terminate به دلیل مستقل و دسته duplicate/abuse/withdrawn نیاز دارد. وضعیت جاری فرصت و تاریخچه در DTO خصوصی پرونده دیده می‌شوند. تعلیق ادمین محتوای عمومی را پنهان و توقف مالک آن را عوض نمی‌کند. بدون مهلت و زمان آخرین بازبینی در DTO عمومی صریح‌اند. intake در public تا گیت عرضه بسته است؛ seed و ابزار نقش در public مسدودند. وجود پرونده فعال با `existing=true` و توضیح «متن تازه ارسال نشده» بازمی‌گردد؛ این رسید، ارسال پیام جدید محسوب نمی‌شود.
