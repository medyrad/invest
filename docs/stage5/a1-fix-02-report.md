# PROGRAMMER-S05-A1-FIX-02

تاریخ: ۲۰۲۶/۱۱/۱۸؛ وضعیت: **آماده بازآزمایی مستقل**.
نسخه اجرا: **S05-A1-FIX-02-a8a919a8e751**؛ [manifest کد و imageها](a1-fix-02-evidence/manifest.json). مبنا `02a234e` و گزارش مستقل `ce565ac`؛ ایراد **S05-A1-IT-002**.

## علت و اصلاح

`model_id.required=false` برخلاف ردیف `stage, phase, model, modelId, owner, revenues` بخش۳ بسته محصول، پذیرفته‌شده با D31 بود. [بازتولید مستقل دست‌نخورده](a1-fix-02-evidence/reproduction.txt) شکست را نشان داد. اکنون نبود مدل قرارداد در `missing` می‌آید؛ `unknown`، `not_applicable` یا متن معتبر، نقص حضور را رفع می‌کنند؛ ورودی نامعتبر رد و داده قبلی حفظ می‌شود. ایجاد و ذخیره draft ناقص همچنان مجاز است.

طبق روشن‌سازی همین مأموریت، `durationYears` عمومی O و مدت اجاره شرطی S+U است. visibility قبلی `when=duration` تغییر نکرد؛ مقدار `required=false` و متادیتای کوچک `required_routes=['lessee']` افزوده شد. حضور هر مسیر این فهرست، در کنار required بدون شرط و فقط در active-set، الزام تکمیل را تعیین می‌کند. بنابراین در مشارکت/میراث بدون اجاره، مدت دیده می‌شود ولی نبودش نقص نیست؛ در lessee و ترکیب دارای lessee الزامی است. `heritage_years`، فقط fee میراث و `execution_months` مستقل باقی ماندند.

UI از همین متادیتا نشان «برای تکمیل اطلاعات» را در مسیر جاری می‌سازد؛ HTML required یا مانع ذخیره ناقص اضافه نشد. سرور `missing` را مستقلاً محاسبه می‌کند؛ هیچ وضعیت ارسال/انتشار ساخته نشده است. [قرارداد خواندنی schema](../../specs/008-project-drafts/contracts/api.md) و [ردیابی منبع](../../specs/008-project-drafts/mapping.md) هماهنگ شدند.

`schema_version=1` حفظ شد: شکل داده پیش‌نویس و اعتبار مقدار007 عوض نشده؛ `required_routes` افزوده اختیاری metadata در پاسخ schema است. مقدار، unit/basis و نسخه‌های قبلی007 معتبر مانده‌اند. migration، تبدیل یا پاک‌سازی داده لازم/انجام نشد.

## نتیجه تازه و حفظ محیط

| بررسی | نتیجه |
| --- | --- |
| workspace/readiness و قرارداد | **۵۶موفق،۱٫۷۴ثانیه**؛ شامل۳۹تست هدفمند جدید،۹تست workspace،۲ round-trip همین فیلدها و۶تست مستقل شامل assertion شکست‌خوردهٔ اصلی؛ [خروجی](a1-fix-02-evidence/backend-tests.txt) |
| مرورگر image نهایی، فقط همین قواعد | **۲موفق،۵٫۳ثانیه**؛ [نتیجه](a1-fix-02-evidence/browser-tests.json) |
| کیفیت | Ruff و ESLint فایل‌های متأثر موفق؛ TypeScript در build نهایی موفق؛ [backend](a1-fix-02-evidence/backend-quality.txt)، [frontend](a1-fix-02-evidence/frontend-quality.txt)، [build](a1-fix-02-evidence/build.txt) |
| نسخه و داده | imageهای backend/test/web پس از تثبیت یک بار ساخته شدند؛ تطبیق کد و image اجرای محلی/مرورگر ثبت شد. تمام۳۰جدول، migration record، guard و env قبلی برابرند؛ [حفظ داده](a1-fix-02-evidence/preservation.json)، [health](a1-fix-02-evidence/health.json) |

نبود/unknown/not_applicable/متن/ورودی نامعتبر مدل در API واقعی و UI بررسی شد. مدت در investor/heritage/lessee و ترکیب‌ها، صفر/وضعیت صریح، تغییر مسیر، مقدار inactive و تزریق مستقیم آزمون دارد. مرورگر الزام پویا پیش از ذخیره و هماهنگی با missing پس از ذخیره، بازگشت مقدار و fee میراث را بررسی کرد.

تصاویر هدفمند: [مدل ناقص](a1-fix-02-evidence/screenshots/model-id-missing.png)، [مدل unknown](a1-fix-02-evidence/screenshots/model-id-unknown.png)، [مدل نامربوط](a1-fix-02-evidence/screenshots/model-id-not_applicable.png)، [مدت الزامی اجاره](a1-fix-02-evidence/screenshots/duration-required-lessee.png)، [مدت اختیاری مشارکت](a1-fix-02-evidence/screenshots/duration-optional-investor.png). چیدمان/CSS خانه و ورود تغییر نکرد؛ تصاویر همین کنترل‌ها بازبینی شدند، نه چهار عرض یا پذیرش انسانی کل طرح.

تست/شواهد مستقل و migrationهای پذیرفته‌شده بدون تغییر حفظ شدند. rollback، scanner، پاسخ دیررس، OTP، چهار عرض و مجموعه‌های۴۴۶/۳۳۱ بازاجرا نشدند؛ قبولی‌های پیشین تاریخی‌اند. برای مرورگر نشست مصنوعی فقط با fixture مقید به محیط test و DB `_browser` ساخته شد. فقط backend/web اصلی و API/web ایزوله به image تازه منتقل شدند؛ scanner/jobs و سرویس پروژه‌های دیگر تغییر نکردند.

## فایل‌ها و بازتولید

کد: `backend/apps/workspace/schema.py`/`schema_data.json`؛ `frontend/src/components/workspace/field.tsx`/`types.ts`/`workspace.tsx`. تست: `backend/tests/test_workspace_required.py`، `frontend/tests/browser/workspace-required.spec.ts` و config محدودِ مشتق از Playwright موجود. اسناد feature008 و stage-status فقط همین اصلاح را ردیابی می‌کنند؛ feature تازه یا اسناد محصول موازی تولید نشد.

```bash
# از ریشه؛ فقط PostgreSQL مصنوعی pytest، بدون rollback:
docker compose --env-file .env -f deploy/compose.yaml run --rm -v "$PWD/docs/stage5/a1-retest-tests:/independent:ro" test /app/.venv/bin/pytest -c /app/pyproject.toml -q tests/test_workspace.py tests/test_workspace_required.py 'tests/test_workspace_acceptance.py::test_every_project_widget_contract_roundtrip[model_id]' 'tests/test_workspace_acceptance.py::test_every_project_widget_contract_roundtrip[duration_years]' /independent/test_conditions.py --tb=short
# از frontend با Node/dependency موجود و API مصنوعی invest-a1-browser-api روی3109:
npx playwright test -c playwright.workspace-required.config.ts
```

خروجی پیش‌فرض مرورگر در .tools است؛ شواهد تحویل را بازنویسی نمی‌کند. schema بقیه فیلدها، migrations، فایل مستقل و آثار قبلی با hash کنترل شدند.

## زمان و گیت‌ها

مطالعه اولیه پیش از marker مستقل آغاز شد و زمان دقیق آن جدا ثبت نشده است. از marker۱۱:۱۷:۴۷ تا تثبیت۱۱:۲۲:۱۶UTC، آماده‌سازی/ساخت آزمون/اصلاح۴دقیقه۲۹ثانیه ثبت شد. build سه image با cache موجود حدود۸٫۵ثانیه؛ اجرای نهایی backend+browser حدود۷ثانیه، جدا از اجرای توسعه و آماده‌سازی. گزارش/manifest از timestamp report_started تا reported_at در manifest ثبت است.

پذیرش مستقل این اصلاح، پذیرش کامل/انسانی A1 و S04/S05 باز می‌مانند. رفع مستقل rollback و پاسخ دیررس طبق TEST-S05-A1-02 تاریخی و حفظ‌شده است؛ این گزارش آن‌ها را آزمون تازه معرفی نمی‌کند. push، انتشار و A2/B/C انجام نشدند. قدم بعد: **بازآزمایی مستقل محدود همین نسخه**؛ پس از تحویل توقف.
