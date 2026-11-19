# قرارداد هسته v1

تمام APIها /api/v1/core؛ خطا envelope استاندارد با پیام فارسی/fields/request_id؛ private no-store، CSRF برای mutation. زمان ISO؛ مقدار اعشاری رشته‌ای. key UUID و version برای تغییر وضعیت؛ retry همان ورودی/کلید همان رسید و بدون اثر مجدد. replay نیز اختیار جاری می‌خواهد.

عمومی: opportunities (kind/route/q/criteria/cursor)، opportunities/:id (فقط public_revision)، compare (۲–۴ هم‌نوع)، library. خصوصی: dashboard، submit/:draft، review/:revision، organization/:request، availability/:opportunity، cases و cases/:id/actions، saved، searches، profile، notifications، reports. درخواست‌ها actor از session؛ نقش از payload پذیرفته نیست.

revision شامل snapshot مؤثر و file refs ثابت؛ تصمیم/تاریخچه جدا و append-only. public_revision در قفل opportunity عوض می‌شود. مالک فقط pause؛ admin با دلیل approve/reject/changes_requested/suspend/reactivate. انتشار سازمانی نیازمند اختیار فعال و پایان معتبر. بررسی مدارک و منبع مستقل و منع self-approval.

پرونده: customer و expert جاری و admin عملیاتی؛ owner خودکار عضو نیست. تماس endpoint جدا فقط با grant همان recipient، پس از revoke/assignment مجدد بسته. answered نیازمند متن انسانی و next_action؛ customer confirm یا job هفت‌روز بدون پیام تازه closes. پیام پس از terminal با اقدام صریح follow-up پرونده مرتبط تازه می‌سازد. SLA مصنوعی نسخه۱ هدف داخلی، نه وعده عرضه.

ذخیره و گزارش پرونده ایجاد نمی‌کنند؛ compare مبنای ناسازگار را غیرقابل‌مقایسه برمی‌گرداند. profile هرگز role نمی‌پذیرد.

افزوده در مقابله D25: action پرونده `next_followup_at` صریح (ISO با timezone یا null) دارد؛ answer/awaiting_user تاریخ آینده لازم دارند. terminate به دلیل مستقل و دسته duplicate/abuse/withdrawn نیاز دارد. وضعیت جاری فرصت و تاریخچه در DTO خصوصی پرونده دیده می‌شوند. تعلیق ادمین محتوای عمومی را پنهان و توقف مالک آن را عوض نمی‌کند. بدون مهلت و زمان آخرین بازبینی در DTO عمومی صریح‌اند. intake در public تا گیت عرضه بسته است؛ seed و ابزار نقش در public مسدودند. وجود پرونده فعال با `existing=true` و توضیح «متن تازه ارسال نشده» بازمی‌گردد؛ این رسید، ارسال پیام جدید محسوب نمی‌شود.

احراز ادعای تضمین بانکی فقط در تأیید مستقل ادمین، با منبع/نتیجه و ارجاع مدرک پاک همین نسخه ثبت می‌شود؛ owner مقدار verified نمی‌سازد. ReviewEvidence ثابت است. DTO عمومی فقط وضعیت احراز را می‌گیرد، نه شناسه/محتوای مدرک یا یادداشت خصوصی. هر revision تازه نیازمند بررسی تازه است. احراز سند، تضمین سود یا مجوز جذب سرمایه معرفی نمی‌شود.

پرونده، شناسنامه مؤثر زمان درخواست و شناسه revision را برای اعضای مجاز حفظ و نمایش می‌دهد؛ بعد از توقف یا اصلاح عمومی، این snapshot عوض نمی‌شود. صاحب فرصت صرف رضایت تماس، عضو گفتگو یا خواننده snapshot پرونده نیست.

## اصلاح CORE-FIX-01

operator_work_period در namespace invest.opportunity.project، نسخه۱، Quantity غیرمنفی با دقت۹ و حد۲۴+۹، واحد صریح DAY/MONTH/YEAR@1 و start_basis طبق D29. required فقط هنگام operator؛ raw inactive محفوظ و snapshot مؤثر آن را حذف می‌کند. سوابق قبلی بازنویسی نمی‌شوند. criteria.important آرایه رشته از محورهای D28 است؛ عضو تو‌در‌تو/غیررشته/نامجاز پیش از lookup با۴۰۰ و مسیر criteria.important.N رد می‌شود. preferences/conditions نیز ساختار کنترل‌شده دارند.

## قرارداد COMP-EXPERIENCE

`POST /auth/intent` یک `destination=/saved` و snapshot نسخه۱ شامل operation دقیق `save-listing` یا `save-criteria` و UUID عملیات می‌پذیرد. consume برای همان session/account handoff ثابت را در retry برمی‌گرداند؛ اثر در `POST /core/personal` با همان UUID idempotent است. cancel/expiry handoff نمی‌دهد. تعویض حساب یا پاسخ نسل قبلی در client پذیرفته نمی‌شود.

`POST /core/personal` action=`search_update`، id موجود و value کامل `{name,criteria}` می‌خواهد و اتمیک است. action=`profile` در `professional` JSON نقش‌های چندگانه مجاز، entity، نام استان catalog، Decimal غیرمنفی سرمایه و validity enum را کنترل می‌کند؛ profile هرگز role/authority حساب را تغییر نمی‌دهد. پاسخ موفق تنها مبنای success UI است.

action=`report` با key UUID، opportunity عمومی و `{criteria,guide_context}` گزارش opportunity می‌سازد. `guide_context.advisory_version=1` و پاسخ‌ها/تیک‌ها محدود و ساختاری‌اند؛ subtype سلسله‌مراتبی فقط از catalog به advisory raw_id نگاشت می‌شود و guidance/check مؤثر در snapshot سرور ثبت می‌شود. `GET /core/reports/:id` پس از کنترل اختیار جاری همان `rendered_html` فارسی تاریخی را با `text/html` و CSP sandbox برمی‌گرداند؛ legacy بدون HTML فقط fallback JSON دارد و دریافت هیچ Case تازه‌ای ایجاد نمی‌کند.
