# مدل داده A1
- Organization: UUID، نام/کشور/نوع/شناسه ثبت؛ یکتایی کشور+ثبت.
- RepresentationRequest: سازمان، متقاضی، snapshot مشخصات و اختیار امضا/نام/حدود/تاریخ/پایان صریح؛ وضعیت pending/needs_info/rejected/approved. درخواست تأییدنشدهٔ خود یا اختیار فعال؛ approved در فهرست/دانلود به اختیار جاری وابسته است. هیچ endpoint تصویب وجود ندارد.
- Representation: سازمان/کاربر، وضعیت active/revoked/hold، پایان اختیاری؛ partial unique حداکثر یک active. اختیار هر درخواست مجدداً محاسبه می‌شود.
- Draft: UUID، creator، سازمان/درخواست اختیاری، schema1، version، routes و raw؛ deleted_at. مالک ثابت، state فقط draft. خام/inactive خصوصی و خروجی مؤثر مشتق سرور.
- DraftRevision: نسخه یکتا، raw و effective؛ DraftValue با یکی از FKهای MoneyValue/Quantity/ReturnMetric پذیرفته‌شده007، به تفکیک کلید.
- Operation: account+key یکتا، fingerprint و receipt؛ ورودی متفاوت همان کلید409، دریافت مجدد همان رسید. مرجع هدف برای بازبینی اختیار.
- PrivateFile: UUID، uploader، یکی از draft/request، kind، size/hash/extension، blob/derivative، state pending_check/clean/rejected/quarantined، timestamps/deleted/replaced/purged، replacement FK و incident owner/reason/review. محتوای کلاینت مسیر ذخیره نمی‌سازد؛ وضعیت‌ها از worker.
- Reservation حساب و موجودیت با SELECT FOR UPDATE: سایز قبل از stream رزرو؛ تمام blobهای purgeنشده در سقف‌اند. همان key/body همان رزرو؛ upload مجدد checksum یکسان مصرف دوباره ندارد.
- purge مرزهای۲۴ساعت/۷روز/۳۰روز، استثنا با هر سه جزء و زمان معتبر؛ فایل clean متصل زنده حذف نمی‌شود، فایل جایگزین هنوزمرجع‌دار حذف نمی‌شود. draft انقضای خودکار ندارد.
