# تحویل PROGRAMMER-S04-03

**آماده آزمون مستقل**؛ نسخه **S04-VALUES-41a4dee62c26**. [مشخصات/طرح/تسک](../../specs/007-exact-values/spec.md)، [تحلیل پیش از کد](values-pre-code-analysis.md) و [manifest کد/image](values-evidence/manifest.json). دو اصلاح قبلی طبق [TEST-S04-02](retest-report.md) قبول فنی و بسته‌اند؛ تأیید انسانی و پذیرش کل S04 باز است.

MoneyValue، Quantity، ReturnMetric و تعریف نسخه‌دار Unit/Field در catalog اجرا شدند. تعاریف با namespace و نسخه append-only هستند؛ API اعشاری رشته‌ای، ذخیره PostgreSQL دقیق و source_value/واحد/عامل صریح است. پول داخلی TOMAN؛ USD با مقدار و واحد خودش و بدون FX نگه داشته می‌شود، نه تبدیل حدسی به تومان. numeric بدون typmod و CHECK دقت، مانع گردکردن پنهان SQL است.

ظرفیت فنی: **۲۴رقم صحیح و۹اعشار**؛ پول/مقدار غیرمنفی، بازده signed و ITEM صحیح. حدود قابل تنگ‌ترشدن در FieldDefinition است؛ این‌ها سقف انتشار یا قانون سرمایه‌گذاری نیستند. فارسی/عربی/لاتین و ممیزهای صریح پشتیبانی می‌شوند؛ جداکننده مبهم، number/float، بیش‌دقت، مقدار خارج از حد و نسخه/واحد ناشناخته با خطای فارسی رد می‌شوند. صفر معلوم، unknown و not_applicable مستقل‌اند. مقایسه فقط برای فیلد، نسخه، واحد و مبنای سازگار نتیجه دارد؛ IRR از نرخ سود یا دوره بازگشت ساخته نمی‌شود و فیلد `irr` نرخ ساده نمی‌پذیرد.

**۸فیلد از مرجع**، با معنا/مسیر/قرارداد و **۱۱واحد نسخه۱** ثبت شدند: سرمایه ورود، نیاز مالی کل، اجاره ماهانه، حداقل صندوق، مدت اجرا، دوره بازگشت، مساحت فروش و IRR. [نگاشت دقیق](../../specs/007-exact-values/mapping.md)، [ظرفیت نمونه‌های منبع](values-evidence/source-capacity.json). minCapital/budget و rent/deposit هم‌معنا نشده‌اند؛ مبنای ناقص بازده منبع جعل نمی‌شود. Quantity مدت با start_basis=unspecified قابل مقایسه نیست؛ روز/ماه/سال پایه‌های مستقل‌اند.

APIهای واقعی `/api/v1/catalog/value-definitions` و `/api/v1/catalog/values/normalize` اضافه شدند؛ POST فقط اعتبارسنجی/تبدیل یک مقدار است و ذخیره عمومی ندارد. مصرف‌کنندهٔ فرم آینده می‌تواند DTO را با `from_payload` اعتبارسنجی و ذخیره کند. [اجرای image محلی3108](values-evidence/runtime.json): **۱٫۵میلیارد و۱۵۰۰میلیون هر دو رشتهٔ 1500000000**؛ تعداد رکوردهای۱۴جدول قبلی حفظ شد؛ فقط تعاریف۱۱/۸ افزوده شدند و جدول‌های مقدار خالی‌اند.

| فرمان | نتیجه |
|---|---|
| `docker compose --env-file .env -f deploy/compose.yaml build backend test` | موفق؛ [build](values-evidence/build-final.txt) |
| `… run --rm test /app/.venv/bin/pytest -q tests/test_values.py tests/test_catalog.py tests/test_contract.py --tb=short` | **۱۰۶ موفق در۳٫۷۲ثانیه**؛ [خروجی](values-evidence/tests-final.txt) |
| Ruff check و format برای catalog، urls و test_values | موفق؛ [کیفیت](values-evidence/quality.txt)، [format](values-evidence/format-check.txt) |
| `… run --rm backend /app/.venv/bin/python manage.py makemigrations --check --dry-run` و `check` | بدون drift/خطا؛ [migration check](values-evidence/migration-check.txt)، [Django](values-evidence/django-check.txt) |
| migration۰۰۰۲/۰۰۰۳ و رفت‌وبرگشت واقعی PG | تست forward/backward و حفظ taxonomy، round-trip هر سه نوع، SQL بیش‌دقت/عامل/وضعیت، immutable تعریف موفق؛ [اعمال افزایشی محلی](values-evidence/migrate-live.txt) |

دو شکست اجرای اول از اشتراک دیکشنری واحدِ ورودی و خروجی بود؛ snapshot مستقل شد و همان سناریوها سبز شدند. [شاهد قبلی](values-evidence/tests-first.txt) حفظ است. کدهای اصلی: `backend/apps/catalog/{models,decimal_field,values,schemas,api}.py`، migrationهای۰۰۰۲/۰۰۰۳، `backend/config/urls.py`، `contracts/openapi.yaml` و `backend/tests/test_values.py`؛ فهرست و hash کامل در manifest است.

زمان دیواری از۱۵:۳۶:۱۱UTC: آماده‌سازی/SpecKit **274.0ثانیه**؛ پیاده‌سازی/build/چرخه آزمون **1068.8ثانیه**؛ بررسی اجرای محلی و گزارش تا ثبت شاهد **252.9ثانیه**. [جزئیات](values-evidence/timing.json).

تست مرورگر/OTP و build فرانت تکرار نشدند؛ فایل‌های frontend و image آن دقیقاً حفظ شدند. env و گزارش‌ها/شواهد/ابزار مستقل قبلی دست‌نخورده‌اند. فقط backend محلی با image همین کد اجرا شد؛ deploy عمومی یا push انجام نشد.

**باقی‌مانده:** نگاشت تمام فیلدها/خدمات، شرط‌های واقعی UI/سرور فرم و پذیرش حذف اثر فیلد پنهان در S05 و مراحل مربوط باقی است؛ metadata `inactive_effect=exclude` اثبات اجرای آن‌ها نیست. فرم، فرم‌ساز، محاسبات خدمات، snapshot گزارش خدمات و S05 ساخته نشده‌اند. T009/T011 پایه با توضیح پوشش جزئی بدون تیک کامل باقی ماندند. بازبینی پایانی SpecKit/converge برای۸FR،۳SC،۳داستان،۱۰تسک و۷اصل، کار ساختنیِ مجاز جامانده‌ای نیافت؛ گیت‌های آینده و انسانی جدا هستند. قدم بعد با دستور کاربر: آزمون مستقل همین بسته؛ پس از گزارش توقف.
