# مدل داده و تنظیم S02

## User

نام جدول/مدل پیشنهادی `identity.User` با UUID primary key؛ `mobile` رشته حداکثر۱۶، قالب canonical `^\+[1-9][0-9]{7,14}$` و قید unique و check در PostgreSQL. S02 ورودی غیرcanonical را رد می‌کند؛ تبدیل شماره محلی فرم ورود در S03 تعریف می‌شود و کشور حدس زده نمی‌شود. `mobile_verified_at` nullable و پیش‌فرض null؛ ایجاد حساب یا regex اثبات مالکیت نیست. `is_active=True`، `is_staff=False` و `is_superuser=False`، created_at/updated_at؛ رمزِ ارائه‌نشده unusable است. مدیر ساخت superuser فقط ابزار داخلی و بدون API عمومی است. مدل در 0001_initial، AUTH_USER_MODEL قبل از migrate. ستون‌های مجوز Django مجوز نقش محصول از کلاینت نمی‌سازند.

## تنظیمات

INVEST_ENV یکی development/test/public؛ SECRET_KEY و DATABASE_URL لازم، PostgreSQL تنها موتور. connect_timeout=3 ثانیه و statement_timeout=3000ms؛ کنترل قطعی health حداکثر۸ ثانیه در آزمون محلی، نه SLA محصول. hostهای مجاز/مبدأهای CSRF صریح. public: DEBUG=False، secret حداقل۵۰ و غیرنمونه، HTTPS redirect، secure+HttpOnly cookies، OTP_DELIVERY_MODE=sms؛ PUBLIC_LAUNCH_ENABLED در S02 همیشه false. عدم config باید با نام متغیر و بدون مقدار secret شکست بدهد. HSTS/preload تابع دامنه/TLS واقعی S11 و پیش‌فرض غیرفعال؛ هشدار check--deploy ثبت شود.

## اطلاعات گذرا

شناسه درخواست UUID معتبرِ ورودی یا UUID تازه؛ رشته نامعتبر بازتاب داده نشود. Error: code/message/fields/request_id. health: status فقط ok/unavailable. CSRF token در پاسخ bootstrap و cookie HttpOnly؛ cache خصوصی no-store. نشست DB-backed است اما endpoint ورود/نشست کاربر این مرحله ساخته نمی‌شود.

## مرزهای آینده

If-Match نسخه صحیح مثبتِ نقل‌قول‌شده؛ کلید Idempotency-Key رشته ASCII غیرخالی حداکثر۱۲۸. helper فقط syntax را بررسی می‌کند؛ اثر تراکنشی/idempotency ledger و expected_version دامنه در S05/S06 ساخته می‌شوند. scope حساب/عملیات و hash payload، تکرار payload یکسان همان رسید و متفاوت409 در قرارداد ثبت است، نه رفتار عملیاتی موجود.
