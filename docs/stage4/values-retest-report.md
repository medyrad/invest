# بازآزمایی TEST-S04-04

**قبول فنی بسته مبلغ و واحد با رفع دو ایراد**؛ IT-001 و IT-002 هر دو رفع‌شده‌اند. ایراد باقی‌مانده‌ای در دامنهٔ این بازآزمایی مشاهده نشد. تأیید انسانی طراحی و پایان کل S04 همچنان باز است؛ S05 یا عرضه آغاز نشده‌اند.

## نسخه

نسخهٔ `S04-VALUES-FIX-82f03c66ac3b` روی کامیت `c547a547f93b3d005d86efca59ed920ef2ef9b2a` آزموده شد. تمام **۵۹ فایل source و ۳۱ artifact** manifest برابر بودند؛ hash پانزده فایل Python بخش catalog داخل backend فعال نیز با کد تحویل تطبیق داشت.

- backend فعال: `sha256:76a571c71a1e824a07148b445f8532e210cf0530bbfa759e90fd9d2a99523818`
- image آزمون: `sha256:2da63c384a2616d368608fb34b911cb97ce6502ed8ca1ae442a7f586175416f1`
- PostgreSQL موجود و imageهای backend/web/test با manifest تطبیق داشتند؛ rebuild انجام نشد. [شاهد نسخه](values-retest-evidence/version.json).

## نتیجهٔ رفتار و migration

| محور | نتیجهٔ مشاهده‌شده |
|---|---|
| IT-001 | سه NUL در namespace/key/unit.code با همان assertionهای مستقل قبلی موفق شدند. روی endpoint فعال نیز این سه و مسیرهای horizon.unit.code، source و start_basis با ۴۰۰، code صحیح، پیام فارسی و fields مسیر درست رد شدند. surrogate نامعتبر در همین شش مسیر نیز کنترل شد. سه ورودی معتبرِ فارسی و Unicode شامل نویسهٔ خارج از BMP همچنان ۲۰۰ می‌دهند. [۱۵ probe فعال](values-retest-evidence/runtime-http.json). |
| بدون ذخیره | درخواست معتبر ۱۵۰۰ میلیون روی اجرای فعال، رشتهٔ `1500000000` برگرداند؛ تعداد رکوردهای هر سه جدول مقدار قبل و بعد برابر و صفر بود. ۱٫۵ میلیارد نیز در probe معتبر قبلی همین نتیجه را داد. [خواندن DB و HTTP](values-retest-evidence/active-db-readonly.json). |
| IT-002 | سه update شکست‌خوردهٔ قبلی اکنون رد می‌شوند. guard و منطق برنامه خوانده و با قرارداد basis تطبیق داده شدند: پول/مقدار غیرمدت null، مدت با شروع صریح، return known با مبنای کامل و return غیرknown با null یا مبنای کامل. INSERT/UPDATE مستقیم، هر سه وضعیت، SQL NULL/JSON null، انواع اعضا، کلید اضافی، نسخه، تاریخ، افق و نمونه‌های معتبر آزموده شدند؛ خواندن مجدد و full_clean نمونه‌های مجاز موفق بود. |
| migration 0004 | علاوه بر آزمون تحویل، در هر سه جدول جداگانه دادهٔ ناسازگار مصنوعی قرار گرفت؛ migration با IntegrityError متوقف شد، دادهٔ ناسازگار حذف/اصلاح نشد، رکورد migration ثبت نشد و validator/triggerهای بررسی‌شده نیمه‌نصب نماندند. پس از اصلاح فقط fixture مصنوعی، migration موفق شد؛ مقدار و snapshot معتبرِ پول، مدت و بازده هم‌زمان حفظ شدند و update نامعتبر دوباره رد شد. |
| DB فعال | فقط SELECT: migration۰۰۰۴ ثبت‌شده و هر سه guard فعال‌اند. اجرای migration/rollback/reset یا درج داده روی DB فعال انجام نشد؛ اثبات رفتاری نوشتن مربوط به PostgreSQL آزمون است، نه صرف وجود نام trigger. |

## اجراهای تازه

پیشوند همهٔ فرمان‌های container: `docker compose --env-file .env -f deploy/compose.yaml`. هیچ مقدار env، cookie یا CSRF در شواهد ثبت نشده است.

| فرمان پس از پیشوند | نتیجهٔ تازه |
|---|---|
| `run --rm -v "$PWD/docs/stage4/values-independent-tests:/independent:ro" test /app/.venv/bin/pytest -c /app/pyproject.toml /independent/test_values_independent.py -q --tb=short -k 'embedded_nul_reference or queryset_cannot_persist_basis'` | **۶ موفق، ۴۷ انتخاب‌نشده؛ ۱٫۱۷ثانیه**؛ اصل فایل و assertionها دست‌نخورده‌اند. [خروجی](values-retest-evidence/six-reproductions.txt). |
| `run --rm test /app/.venv/bin/pytest -q tests/test_values_fixes.py --tb=short` | **۲۲۹ موفق؛ ۲٫۰۲ثانیه**، فقط یک اجرا. [خروجی](values-retest-evidence/fixes-suite.txt). |
| `run --rm -v "$PWD/docs/stage4/values-retest-tests:/retest:ro" test /app/.venv/bin/pytest -c /app/pyproject.toml /retest/test_values_retest.py -q --tb=short` | **۱۴ موفق؛ ۱٫۰۹ثانیه**؛ شکاف‌های وضعیت غیرknown، INSERT با JSON null و preflight هر سه جدول/حفظ سه نوع. [خروجی](values-retest-evidence/independent-gaps.txt). |
| همان فرمان مستقل با `-k duration_requires_basis` | **۸ موفق، ۱۴ انتخاب‌نشده؛ ۰٫۴۸ثانیه**؛ موارد تازهٔ null در مدت unknown/not_applicable برای INSERT/UPDATE. موارد موفق قبلی تکرار نشدند. [خروجی و زمان](values-retest-evidence/missing-duration-nulls.txt). |
| `python3 docs/stage4/values-retest-tests/probe_runtime.py` و `python3 docs/stage4/values-retest-tests/probe_active_db.py` | **۱۶ درخواست normalize موفق طبق انتظار**؛ ۱۲ خطای کنترل‌شده و ۴ ورودی معتبر. |

جمع **۲۵۷ مورد pytest یکتا، همگی موفق**؛ ۱۶ probe HTTP جداست و در شمار pytest یا اجرای مجدد حساب نشده است. مجموعه‌های کامل ۱۰۶تایی و ۵۳تایی تکرار نشدند. اجرای برنامه‌نویس یا نتایج تاریخی به‌عنوان اجرای من شمرده نشده‌اند.

## محدودیت، زمان و تحویل

تمام نوشتن‌ها و rollbackهای آزمون در PostgreSQL واقعی با نام آغازشونده با `test_` و کنترل fixture انجام شدند. اختیار مالک DB برای حذف guard/TRUNCATE، مرورگر، OTP، build فرانت، فرم‌های آینده، پذیرش فیلدهای پنهان و بار عرضه خارج از دامنه‌اند. آزمون تازه صرفاً شکاف مشخص مجموعهٔ موجود را پوشش داد؛ محصول یا قواعد اصلاح نشدند.

زمان آماده‌سازی 8.41ثانیه، اجرا/بررسی شکاف‌ها 113.15ثانیه و گزارش تا ثبت شاهد 15.1ثانیه است؛ تفکیک در [timing.json](values-retest-evidence/timing.json) است؛ آماده‌سازی از شروع تثبیت نسخه اندازه‌گیری شد و خواندن اولیهٔ دستورها، اسناد و guard پیش از آن بود و زمان آن جدا اندازه‌گیری نشد. در logهای تازه فقط فاصلهٔ انتهای سطر و سطر خالی انتهایی حذف شده است. زمان خود pytest در logها جداست؛ build صفر است. [کنترل حفظ فایل‌های موجود و env](values-retest-evidence/preservation.json).

فقط گزارش، آزمون‌ها و شواهد تازهٔ همین مأموریت پس از بررسی diff کامیت می‌شوند؛ push انجام نمی‌شود. قدم بعد نیازمند دستور کاربر است؛ این مأموریت پس از تحویل متوقف می‌شود.
