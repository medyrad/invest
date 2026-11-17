# راه پذیرش S02

راهنمای نهایی فرمان‌ها در [docs/development.md](../../docs/development.md) همراه کد تکمیل شده است. ابتدا env خصوصی ساخته شود؛ Compose فقط project invest و پورت‌های55432/3108، بدون down -v. نسخه‌ها از lock و image digest.

پذیرش ترتیب: تنظیم/نصب ثابت → PostgreSQL تازه و migrate → pytest روی PostgreSQL و کنترل public → lint/typecheck/build فرانت → مرورگر روی standalone و API هم‌مبدأ → build/up تصویرها → smoke داده/health، قطع/بازگشت DB و restart پایدار → check قرارداد و manifest. فرمان و نتیجه هر run در docs/stage2/verification.json ثبت شود. برای شکست، همان دامنه اصلاح و تکرار شود؛ پاس شدن اسناد شاهد runtime نیست.

فرانت مرحله S02 پوسته است؛ هیچ screenshot به‌عنوان تطابق صفحه اصلی سرمایه‌گزین یا پذیرش B08 معرفی نشود. تست‌های OTP، AI، فایل مشتری و گردش پرونده متعلق به این مرحله نیستند.
