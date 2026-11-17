# طرح اجرای S03

همان Django/DRF/PostgreSQL17 و Next16/React19 قفل‌شده S02؛ وابستگی جدید لازم نیست. بررسی اسناد رسمی در research.md. هیچ دستور آرشیو اجرا نمی‌شود.

## Constitution Check
I مرجع فقط advisor و مأموریت؛ II تصاویر دسکتاپ و موبایل و پذیرش انسانی باز؛ III FR→tasks→test؛ IV اختیار و سهمیه در تراکنش؛ V شاهد test جدا از احراز واقعی؛ VI PostgreSQL و build/browser واقعی؛ VII فقط این مأموریت. گیت پیش از کد برای دامنه آزمایشی قابل عبور است؛ تأیید محصول/عرضه نیست.

## ساختار و ترتیب
backend/apps/identity/{models,otp,sessions,api}.py و migration؛ tests/test_identity.py و test_identity_races.py؛ frontend/src/components/auth/login-dialog.tsx با CSS و asset محلی؛ frontend/tests/browser/auth.spec.ts؛ docs/stage3 شواهد/گزارش.

## قفل و مدل
برای نسخه آزمایشی یک pg_advisory_xact_lock سراسری مختص identity این دیتابیس به‌علاوه transaction.atomic؛ همه عملیات هویت و تغییر نقش/فعالیت مدل از همین قفل استفاده می‌کنند. زمان بعد از قفل خوانده می‌شود. راهکار عمداً ساده و چندworker-safe است؛ throughput به ترتیب‌سازی هویت محدود است و سنجش ظرفیت عرضه باقی است. تماس بیرونی زیر قفل انجام نمی‌شود؛ adapter فعلی محلی است. QuerySet.update برای تغییر اختیار ممنوع؛ service یا User.save لازم است.

رمز جریان و نشست تصادفی۲۵۶بیتی، ذخیره digest HMAC با کلید سرور. OTP فقط HMAC context-bound؛ اعلان آزمایشی از مشتق امن secret و nonce تصادفی challenge بازیابی می‌شود؛ هیچ OTP خام در DB/audit نیست. epoch حساب هنگام صدور ثبت می‌شود. نشست جدید cookie مجزا از sessionid پایه و از جریان مستقل است. نقش سروری و شاهد واقعی شرط sensitive است. route آزمایشی خصوصی فقط داده مصنوعی همان حساب را نشان می‌دهد.

## بازیابی و فعالیت
verify دوباره نشست صادر نمی‌کند. پاسخ گم‌شده با me و cookie دریافت‌شده بازیابی می‌شود؛ بدون cookie ورود تازه. فقط activity POST در UI با دکمه صریح واجد تمدید است. rotate token را عوض کرده، سقف ثابت؛ reauth با challenge تازه همان نشست و حساب، سقف ثابت. sensitive واقعی با test ممنوع.

## قرارداد
contracts/api.md به‌همراه contracts/openapi.yaml ریشه، مرجع endpoint، خطا، cookie و payload است؛ تست API مستقیم از قرارداد و FRها استفاده می‌کند. همه mutations CSRF دارند. نیت پس از اتصال به حساب به همان شناسه نشست هم متصل است تا تعویض و بازگشت حساب نیت قبلی را زنده نکند؛ چرخش token شناسه داخلی را عوض نمی‌کند. نیت مقصد allowlist /saved است؛ consume صرفاً handoff و destination validator فعلاً /saved را به‌عنوان قرارداد می‌پذیرد، ذخیره واقعی ندارد.
