# گزارش PROGRAMMER-EXPERIENCE-EVIDENCE-FIX-01

تاریخ: ۲۰۲۶/۱۱/۲۰

مبنای مستقل: `0380bbf3cdcf00f6997b060a7d43a1ad980dc56c`

تحویل اولیه: `d351892`
دامنه: فقط fixture، harness، شواهد و اسناد EVID-IT-001..004؛ کد رفتاری backend/frontend، فرمول/وزن/threshold D28، رأی انسانی، COMP-AI و deploy تغییر نکردند.

## نتیجه

هر چهار یافته از دید برنامه‌نویس اصلاح و بسته برای بازآزمایی مستقل آماده است. این عبارت به معنی قبول مستقل، قبول طراحی یا قبول کیفی D28 نیست. خروجی فعلی ۹۶ امضای معنایی یکتا، ۶۴ ردیف route×axis مستدل، ۱۳ capture تازه متصل به source/runtime و ۴۸۰ مقایسه oracle بدون mismatch دارد. held-out پس از اصلاح fixture فقط **regression** است و شاهد confirming/generalization یا کورسازی تازه محسوب نمی‌شود.

## EVID-IT-001 — تمایز معنایی فرصت‌ها

- علت ریشه‌ای: indexهای ۴ و ۵ در هر هشت route بین development و held-out، پس از حذف UUID/title/revision/split/metadata، snapshot مؤثر یکسان داشتند؛ بنابراین ۱۶ جفت cross-split و فقط ۸۰ امضای واقعی وجود داشت.
- اصلاح: حالت unknown و known-zero حفظ شد، اما province/group/risk/contract مؤثر held-out به ترکیب قراردادی متفاوت تغییر کرد. seed، شناسه‌ها، ۸ route، ۸۰ سناریو، ۹۶ فرصت، شش نامزد و top-5 ثابت ماندند.
- آزمون بازگشت: `validate_d28_evidence.py` canonical signature را فقط از route/kind/snapshot می‌سازد، یکتایی درون و بین split را الزام می‌کند و در کپی موقت یک duplicate معنایی می‌سازد؛ mutation با موفقیت رد شد.
- نتیجه: ۴۸ امضای یکتا در development، ۴۸ در held-out و ۹۶ در کل؛ duplicate صفر. هش ورودی منجمد جدید `89af376235955201ad0fc698a3090883bedda6a969954b12bac06b677e64fe6b` است.

## EVID-IT-002 — unit/basis بدون مصرف‌کننده

- علت ریشه‌ای: matrix صرف حضور route را برای unit/basis کافی می‌دانست، درحالی‌که operator و charity در قرارداد `search_fields.json`/`discovery.py` معیار budget/return مصرف‌شونده ندارند.
- اصلاح: دو ردیف `operator×unit-basis` و `charity×unit-basis` به `N/A` تغییر کردند؛ scenario ساختگی ندارند و دلیل/contract reference صریح دارند. پوشش unit/basis فقط از routeهای دارای budget یا return واقعی می‌آید.
- آزمون بازگشت: applicable=yes باید criteria عددی/return، TOMAN@1 یا basis و check واقعی `amount|returns` در oracle داشته باشد. mutation موقت operator را applicable می‌کند و validator آن را رد می‌کند.
- نتیجه: validator مستقل ۸/۸؛ matrix همچنان ۶۴ ردیف دارد و هیچ field/criteria/return ساختگی اضافه نشده است.

## EVID-IT-003 — route/state شواهد طراحی

نه جایگاه زیر با capture واقعی همان route/state به `capture-needed→new-evidence` منتقل شدند:

| ردیف | حالت | عرض‌ها | نتیجه |
|---|---|---|---|
| DES-003 `/tools/proposal` | `summary` | ۳۶۰، ۷۶۸ | capture دقیق و provenance معتبر |
| DES-009 `/tools/foreign-investment` | `step1` | ۳۶۰، ۳۹۰، ۷۶۸ | capture دقیق و provenance معتبر |
| DES-014 `/tools/ma-renewal` | `step1` | ۳۶۰، ۷۶۸ | capture دقیق و provenance معتبر |
| DES-021 `/tools/charity` | `summary` | ۳۹۰، ۷۶۸ | capture دقیق و provenance معتبر |

چهار library در ۳۶۰/۳۹۰/۷۶۸/۱۴۴۰ نیز روی runtime معتبر دوباره گرفته شد. ماتریس نهایی ۱۰۴ slot دارد: ۱۳ شاهد تازه، ۴۹ reuse معتبر، ۶ representative همان route/state با قرارداد صریح و ۳۶ reference-component-only. validator یک representative را در کپی موقت cross-route می‌کند و رد آن را ثابت می‌کند. index/gallery فقط برای همین ۱۳ slot همگام شد و همه فیلدهای verdict خالی‌اند. مشاهده مستقیم نمونه‌های proposal، foreign، renewal، charity و library انجام شد؛ این مشاهده تأیید انسانی طراحی نیست.

## EVID-IT-004 — اتصال source به runtime

زنجیره ماشین‌خوان در `tech-evidence-fix-01/runtime-provenance.json` ثبت شد:

- checkout: `0380bbf3cdcf00f6997b060a7d43a1ad980dc56c`؛ diff محصول نسبت به baseline محصول `79519bb8e88cbf6c0bcf7614c63b3737cc668a70` خالی؛
- frontend image: `sha256:7287a4565a5009804135d718f1685ca38c43adc207c5c33f5b1f965fdac0840a`؛ source tree hash: `cc270663d1abc0161a49f502f91ff1a9316b2445a46800b019def015e1fe03cc`؛
- backend image: `sha256:66d9622b61ba649030b770b68aed625224d503d0150b1160ddb8e09753b6feb7`؛ source tree hash: `701b2ba699e709f1ee725104f89f4e85686cfeeeb9c73d44d2e6229c896b0d06`؛
- frontend BUILD_ID: `myZDM7kEa-Q6fjMutJW5o`؛ bundle/server file hashها ثبت شده و ۱۴۸ فایل tracked backend با `/app` برابر بودند؛
- هر capture شامل URL، route، state، identity، seed، UTC time، viewport/canvas، font-ready، reduced-motion، Chrome/Playwright و SHA-256 تصویر است.

نتیجه provenance: ۱۰/۱۰ کنترل و ۱۳/۱۳ capture معتبر. رشته product_version به‌تنهایی معیار قرار نگرفت.

## اجرای D28 و حفاظت تاریخچه

development روی DB تازه `evidence_fix_dev_20261120` اجرا شد: ۳۲ سناریو، ۴۸ فرصت، ۱۹۲ candidate pair، ۱۶۰ top-5 pair و صفر mismatch. held-out روی DB تازه و جدا `evidence_fix_heldout_20261120` اجرا شد: ۴۸ سناریو، ۴۸ فرصت، ۲۸۸ candidate pair، ۲۴۰ top-5 pair و صفر mismatch؛ نقش آن فقط regression-after-fixture-correction است.

در مجموع ۸۰ ترتیب و ۴۸۰ زوج oracle بررسی شد. oracle مستقل از scorer محصول باقی ماند. ۴۰۰ ردیف relevance و critical-review یکتا و کاملاً خالی‌اند؛ reviewer input فاقد score/coverage/matching/system rank است. فرمول و وزن‌ها تغییر نکردند. `fixture-change-log.json` برابری byte-for-byte سیزده artifact تاریخی، شامل attemptهای قبلی، `heldout-first-attempt.json` و `leak-replay-log.json`، با commit مستقل را اثبات می‌کند.

## آزمون مرورگر

- اجرای آمادگی اول: ۱۳ error پیش از بازشدن صفحه به‌علت نبود Chromium revision مورد انتظار Playwright؛ محصول اجرا نشد (`browser-attempt-1.xml`).
- اجرای تشخیصی دوم با Chrome سیستم: ۹ pass و ۴ fail؛ دو علت harness/environment بودند: import نشدن reference catalog در DB تازه و focus target بدون scroll در summary (`browser-attempt-2.xml`).
- rerun هدفمند پس از اصلاح آماده‌سازی/harness: ۴/۴ pass، ۳۱٫۶ ثانیه (`browser-targeted.xml`).
- اجرای تجمیعی یکتای نهایی، retries=0 و worker=1: ۱۳/۱۳ pass، ۵۴٫۶ ثانیه (`browser-results.xml`).

هیچ نقص رفتاری تازه محصول در این دامنه مشاهده نشد. diagnostic rerunها در شمار یکتای ۱۳ تست نهایی محاسبه نشده‌اند.

## فرمان‌های بازتولید و نتیجه واقعی

```sh
python3 docs/experience-complete/tech-evidence-01/d28_prepare.py

# برای هر split یک DB تازه ساخته و migrate شود، سپس:
docker compose -f .tools/expit/compose.yaml run --rm \
  -e DATABASE_URL=postgresql://postgres:synthetic@db:5432/<fresh_db> \
  -e EVIDENCE_DIR=/tech-evidence -e D28_SPLIT=<development|held-out> \
  -e RUNTIME_SOURCE=0380bbf3cdcf00f6997b060a7d43a1ad980dc56c \
  -v "$PWD/docs/experience-complete/tech-evidence-01:/tech-evidence" \
  test /app/.venv/bin/python manage.py shell \
  -c "exec(open('/tech-evidence/d28_run.py').read()); main()"

python3 docs/experience-complete/tech-evidence-01/build_d28_package.py
python3 docs/experience-complete/tech-evidence-fix-01/validate_d28_evidence.py
python3 docs/experience-complete/tech-evidence-01/build_design_index.py
python3 docs/experience-complete/tech-evidence-fix-01/validate_design_evidence.py
python3 docs/experience-complete/tech-evidence-01/validate.py

cd docs/experience-complete/tech-evidence-fix-01
npx playwright test -c playwright.config.cjs
```

نتایج نهایی: D28 validator برابر ۸/۸، design validator برابر ۸/۸، runtime provenance برابر ۱۰/۱۰، aggregate validation برابر ۳۴/۳۴ و مرورگر ۱۳/۱۳ است. PostgreSQL 17 در tmpfs پروژه ایزوله استفاده شد؛ DB فعال، داده واقعی، سرویس پروژه دیگر یا secret واقعی لمس نشد.

## زمان‌ها

زمان‌های دقیق runner از خروجی خود ابزار و زمان‌های دیگر از ثبت اجرای shell تفکیک شده‌اند:

- آماده‌سازی/خواندن/کنترل نسخه: حدود ۱۸ دقیقه؛
- اصلاح fixture، matrix و validatorها: حدود ۲۲ دقیقه؛
- build/runtime ایزوله و import داده: حدود ۴ دقیقه (buildها cache-hit ولی image digest/label تازه و قابل محاسبه بود)؛
- capture نهایی یکتا: ۵۴٫۶ ثانیه؛ diagnosticهای مرورگر: ۱۶٫۲ + ۹۵٫۳ + ۳۱٫۶ ثانیه؛
- migration و اجرای development/held-out و validation D28: حدود ۷۵ ثانیه؛
- همگام‌سازی اسناد، گزارش و manifest: حدود ۱۸ دقیقه.

## فایل‌ها و ردیابی

- fixture/harness اصلی: `docs/experience-complete/tech-evidence-01/`؛
- شواهد اصلاح: `docs/experience-complete/tech-evidence-fix-01/`؛
- index/gallery: فقط ۱۳ slot متأثر در `human-design-review/`؛
- owner docs: plan/tasks ویژگی‌های 009 و 010 و `docs/stage-status.json`؛
- کد رفتاری `backend/` و `frontend/`: بدون تغییر.

T034–T037 در 009 و T042 در 010 با شاهد فنی بسته شدند. T020 در 009 و T036 در 010، تأیید انسانی طراحی، داوری کیفی D28، production readiness، COMP-AI و deploy بازند. بازآزمایی مستقل این بسته هنوز انجام/ثبت نشده است.

## محدودیت و handoff

- held-out به‌سبب اصلاح fixture پس از مشاهده گزارش مستقل، فقط regression است.
- تصاویر و hit-test/focus خودکار، جای ممیزی تخصصی طراحی نیستند.
- label انسانی، آستانه قبولی یا رأی useful/irrelevant/critical تولید نشده است.
- بسته از دید برنامه‌نویس آماده `TEST-EXPERIENCE-EVIDENCE-FIX-01` است؛ اجرای آن مجوز این مأموریت نیست.
