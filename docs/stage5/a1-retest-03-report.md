# TEST-S05-A1-03

**قبول فنی در دامنه A1.** ایراد **S05-A1-IT-002 رفع‌شده** است و الزام مدت بر مسیر lessee با UI و missing سرور هماهنگ است. مانع فنی باز در دامنهٔ تحویل آزموده‌شده مشاهده نشد. تأیید انسانی طراحی و پایان کل S04/S05 باز می‌مانند؛ این پذیرش مجوز عرضه یا A2/B/C نیست.

## نسخه و دامنه

محصول `39ebcff62ebc62c7972d72f392993b87c0dddbce`، نسخه `S05-A1-FIX-02-a8a919a8e751`؛ HEAD شروع `94db317` شامل دستور بازآزمایی بود. تمام hashهای source/artifact manifest و هر هفت image موجود تطبیق داشتند؛ rebuild انجام نشد. hash دو فایل schema داخل backend فعال و API ایزوله نیز با workspace برابر بود. [نسخه](a1-retest-03-evidence/version.json)، [diff و تطبیق runtime](a1-retest-03-evidence/scope.json).

backend/API مرورگر: `sha256:72578c07538c98eca05e2840e25dbaf7eff06079367d1e82a363867736c4ce40`؛ web اصلی/مرورگر: `sha256:ef95ce1c0b2d5e075ad36cd400efd06d0386baab1ce21437738756fad20e4147`؛ test: `sha256:3d4b30728d5f479ab9bca04fd5d88106a865a6fc3d9e4ce9292683c73ad1f831`.

diff از e1d1443 تا39ebcff خوانده شد: در schema فقط required مدل و required/required_routes مدت تغییر کرده؛ active-set و قرارداد عدد/واحد حفظ شده‌اند. UI فقط نشان تکمیل را با همان metadata و مسیر جاری تعیین می‌کند. schema_version=1 و داده‌های قبلی بدون migration معتبر می‌مانند. service/files/models، اعتبارسنجی007 و مسیر API/پنل فایل و assertion مستقل قبلی بدون تغییرند؛ نیازی به تکرار بررسی‌های پذیرفته‌شدهٔ rollback، اختیار، scanner و پاسخ دیررس نبود.

## نتیجهٔ رفتار

| محور | نتیجهٔ تازه |
|---|---|
| model_id | assertion مستقل اصلی بدون تغییر موفق؛ نبود و حذف در missing، unknown/not_applicable و متن معتبر رفع نقص حضور، رد ورودی نامعتبر با حفظ نسخه/مقدار سالم قبلی. ایجاد و ذخیره پیش‌نویس ناقص۲۰۰ می‌ماند؛ نشان تکمیل UI و نقص سرور هماهنگ‌اند و HTML required افزوده نشده است. |
| مدت مشروط | investor/heritage بدون lessee: قابل نمایش و اختیاری؛ lessee و ترکیب‌های دارای آن: الزام حضور. حالت غیرفعال، صفر معتبر، وضعیت‌های صریح، null/حذف، تزریق inactive و بازگشت مقدار خام مستقل بررسی شدند. نسخه۱ مقدار و schema حفظ شدند. |
| استقلال شروط | heritage_years در فقط fee غیرفعال است و با lease دوباره نقص حضور دارد؛ execution_months در مسیرهای قبلی برقرار است. UI پیش از ذخیره نشان مدت را با تغییر مسیر عوض می‌کند؛ پس از ذخیره با missing برابر است. draft به ارسال/انتشار تبدیل نشده است. |

کد و assertionهای مجموعهٔ هدفمند خوانده شدند؛ خلأ مشخصی که نیاز به آزمون تازهٔ تکراری داشته باشد در همین دامنه یافت نشد. تصاویر کنترل مدت الزامی اجاره و اختیاری مشارکت نیز مستقیم بازبینی شدند؛ [تصاویر تازه](a1-retest-03-evidence/screenshots/duration-required-lessee.png) و [مدت اختیاری](a1-retest-03-evidence/screenshots/duration-optional-investor.png) شاهد همین کنترل‌اند، نه تأیید انسانی کل طرح.

## فرمان‌ها و شمار

از ریشه، با پیشوند `docker compose --env-file .env -f deploy/compose.yaml`:

`run --rm -v "$PWD/docs/stage5/a1-retest-tests:/independent:ro" test /app/.venv/bin/pytest -c /app/pyproject.toml -q tests/test_workspace.py tests/test_workspace_required.py 'tests/test_workspace_acceptance.py::test_every_project_widget_contract_roundtrip[model_id]' 'tests/test_workspace_acceptance.py::test_every_project_widget_contract_roundtrip[duration_years]' /independent/test_conditions.py --tb=short`

**۵۶ مورد یکتا موفق،۱٫۹۲ثانیه؛ یک اجرا، بدون rerun.** [خروجی تازه](a1-retest-03-evidence/backend.txt).

از frontend با Node قفل‌شده و dependency موجود: `node node_modules/@playwright/test/cli.js test -c playwright.workspace-required.config.ts`؛ متغیرهای صرفاً مسیر خروجی `A1_REQUIRED_EVIDENCE` و `A1_RESULTS_FILE` به همین پوشهٔ شواهد هدایت شدند. **۲ سناریوی یکتا موفق،۵٫۴ثانیه؛ یک اجرا، بدون rerun.** [خروجی](a1-retest-03-evidence/browser.txt)، [نتیجه ماشین‌خوان](a1-retest-03-evidence/browser.json). fixture مرورگر به محیط test و DB `_browser` مقید بود؛ token/cookie در شواهد ذخیره نشد.

## زنجیرهٔ پذیرش و محدودیت

- [TEST-S05-A1-01](a1-independent-test-report.md): سفر ذخیره/ادامه و دستگاه دوم، رقابت/مجوز/فایل واقعی/نگهداری، UI چهار عرض و scanner؛ ایراد rollback باقی بود. این‌ها **تاریخی** هستند، اجرای تازه حساب نشده‌اند.
- [TEST-S05-A1-02](a1-retest-report.md): رفع rollback با داده/guard، تکمیل شاهد ردیفی۶۹فیلد و شروط، نماینده فعال در UI و شش حالت پاسخ خصوصی دیررس تأیید شدند؛ اختلاف model_id و ابهام مدت باز ماندند. آن بخش‌های کد حفظ شده‌اند.
- همین TEST-S05-A1-03: اختلاف model_id و الزام شرطی مدت طبق روشن‌سازی مأموریت رفع و مستقل بازآزمایی شدند؛ با اتکا به زنجیرهٔ بالا **پذیرش فنی A1** تعیین شد، نه صرفاً از تعداد آزمون‌ها.

گیت‌های انسانی، داده واقعی/نگهداری سوابق B، عرضه و SMS واقعی همچنان جدا هستند. همهٔ گزینه‌های واژه‌نامه به‌صورت تعامل مجزا دوباره کلیک نشدند؛ تطبیق منبع و widget و شروط قبلی مبناست. هیچ آزمون بار عرضه، suite کامل۴۴۶/۳۳۱، rollback یا scanner دوباره اجرا نشد.

زمان‌ها در [timing](a1-retest-03-evidence/timing.json) جداست: آماده‌سازی از marker تثبیت نسخه، اجرا شامل runner و بازبینی شواهد، و تهیه گزارش. مطالعهٔ اولیهٔ مأموریت پیش از marker انجام شد و مدت دقیق آن اندازه‌گیری نشد؛ زمان کل از اولین مطالعه ادعا نمی‌شود. build و برنامه‌نویسی آزمون تازه صفر است. [کنترل حفظ فایل‌های موجود و env](a1-retest-03-evidence/preservation.json).

فقط گزارش و شواهد تازه پس از بررسی diff محلی کامیت می‌شوند؛ محصول، env، stage-status و شواهد تاریخی تغییر نمی‌کنند. قدم بعد صرفاً با دستور کاربر؛ پس از این تحویل توقف و بدون push.
