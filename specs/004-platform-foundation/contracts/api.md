# قرارداد پایه S02

مرجع اجرایی `contracts/openapi.yaml` در ریشه تولید می‌شود. URLها بدون slash پایانی، JSON UTF-8 و API /api/v1. تمام پاسخ‌ها X-Request-ID معتبر UUID و Cache-Control: no-store دارند. UUID ورودی معتبر حفظ و ورودی نامعتبر جایگزین شود. خطا `{error:{code,message,fields,request_id}}`؛ پیام فارسی و fields فقط خطای فیلد، هیچ traceback یا مقدار اتصال.

| مسیر | روش/نتیجه |
|---|---|
| /health/live | GET200 {status:ok} مستقل از DB |
| /health/ready | GET200 {status:ok} یا503 {status:unavailable}؛ اتصال SELECT1، بدون DSN/نسخه سرور |
| /auth/csrf | GET200 {csrfToken:string}، cookie CSRF HttpOnly/SameSite=Lax/Secure درpublic و Vary:Cookie؛ بدون session/login |
| /schema | GET200 schema ماشین‌خوان همان فایل قرارداد |

403 csrf_failed برای نبود/نامعتبر بودن token یا Origin؛ 405 method_not_allowed بعد از حفاظت درخواست unsafe؛ 404 not_found؛ 400 invalid_request/invalid_host/invalid_version/invalid_idempotency_key؛ 500 internal_error بدون جزئیات. healthready503 استثنای health-envelope و status-only است، خطای دامنه نیست. احراز در آینده SessionAuthentication ممکن است denial403 بدهد؛ 401 تنها وقتی قرارداد احراز آن را تعریف کند، نه جعل سراسری.

Cookie مسیر /، token از bootstrap در X-CSRFToken؛ حفاظت برای مهمان هم فعال. proxy باید method/body/query/status و Cookie/Set-Cookie را حفظ کند؛ Origin معتبر باید از allowlist صریح عبور کند. HTTPS proxy-header پیش‌فرض trusted نیست و در S11 topology واقعی تعریف می‌شود.

If-Match با قالب رشته نقل‌قول‌شده عدد مثبت حداکثر۱۸رقم؛ Idempotency-Key ASCII `[A-Za-z0-9._:-]` با طول1..128. helper اعتبارسنجی syntax و schema component آزموده می‌شوند؛ عملیات دامنه/ledger موجود نیست. قرارداد آینده: scope حساب+عملیات، payload یکسان همان رسید، متفاوت409، version stale409؛ window retry در feature مربوط مشخص می‌شود.
