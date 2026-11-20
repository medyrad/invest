# گزارش TECH-EXPERIENCE-EVIDENCE-01

تاریخ: ۲۰۲۶/۱۱/۲۰
مبنای برنامه: `79519bb8e88cbf6c0bcf7614c63b3737cc668a70`
مبنای قبول فنی مستقل محصول: `8c327ec`
مرجع طراحی: `Investment_Advisor-main.zip` با SHA-256 برابر `6221401c736250c5ac7e5595aa988301f64b8d2fe576590291a7c2e53c247f5b`
دامنه: فقط fixture/harness/evidence/docs؛ **صفر تغییر کد رفتاری محصول، صفر تغییر وزن/فرمول/threshold D28، صفر رأی انسانی، صفر COMP-AI و صفر deploy**.

## نتیجه اجرایی

- 009/T030–T033 و 010/T041 از نظر فنی انجام شدند. 009/T020 و 010/T036 عمداً بازند، چون رأی طراحی و داوری انسانی D28 جزو این مأموریت نیست.
- هر **۲۶/۲۶ ردیف primary** در چهار عرض تعیین تکلیف شد: **۱۰۴/۱۰۴ slot**؛ ۴۹ reuse معتبر، ۱۵ نماینده مستدل، ۳۶ مقایسه فقط با جزء مرجع برای صفحه‌های فاقد مرجع کامل و ۴ شکاف capture که با شاهد تازه بسته شد.
- capture تازه برای جزئیات fund/sale، library، گزارش FIX02 و workspace/drafts/requests/admin/expert در ۳۶۰/۳۹۰/۷۶۸/۱۴۴۰ ثبت شد. در پنل‌های نقش، font-ready، focus واقعی، hit-test مرکز کنترل و نبود overflow بررسی شد.
- مجموعه D28 مصوب ساخته شد: **۸ route × ۱۰ سناریو = ۸۰ سناریو** و **۸ route × ۱۲ فرصت = ۹۶ فرصت مصنوعی یکتا**. در هر route دو pool متمایز development/held-out با ۶ فرصت وجود دارد؛ صرف UUID متفاوت معیار تمایز نبود.
- split نهایی: development برابر۳۲ سناریو/۴۸ فرصت و held-out برابر۴۸ سناریو/۴۸ فرصت. در هر سناریو ۶ نامزد مجاز و top-5 واقعی وجود دارد.
- اجرای نهایی فنی: development با۱۹۲ زوج نامزد/۱۶۰ top-5 و held-out با۲۸۸ زوج نامزد/۲۴۰ top-5؛ **اختلاف oracle صفر**. cursor کنترل سراسری در هر split با۴۸ نتیجه، ۱۲+۱۲ نتیجه در دو صفحه و overlap صفر گذشت.
- فرم relevance و critical برای تمام۴۰۰ زوج top-5 کاملاً خالی است. فایل reviewer هیچ score/coverage/matching/system rank ندارد؛ خروجی فنی و کلید هماهنگ‌کننده جدا هستند.
- هیچ نقص رفتاری تازه محصول اثبات نشد. دو نقص fixture و یک نقص selector harness پیدا، اصلاح و با سابقه حفظ شدند؛ جزئیات پایین.

## مسیر طراحی و شواهد

[ماتریس ۱۰۴ جایگاه](tech-evidence-01/design-slot-matrix.csv) برای هر slot شناسه/گروه، route/state، نقش، عرض و ارتفاع viewport، canvas، داده مصنوعی، نسخه محصول، hash مرجع، font/motion، زمان capture، طبقه‌بندی و محدودیت را ثبت می‌کند. [فهرست تعامل](tech-evidence-01/interaction-evidence.csv) تصویر ثابت را از شاهد انتخاب/بازگشت، focus، لمس/کلیک، ورود→ذخیره، error/retry و redownload جدا می‌کند.

| طبقه‌بندی | تعداد | تفسیر مجاز |
|---|---:|---|
| `reuse-valid` | ۴۹ | شاهد هم‌نسخه یا بدون تغییر مؤثر با منشأ مشخص |
| `representative-covered` | ۱۵ | component، breakpoint، state و ریسک مشترک صریح؛ محتوای اختصاصی در عرض مستقیم نیز شاهد دارد |
| `reference-component-only` | ۳۶ | صفحه کامل در ZIP وجود ندارد؛ فقط پوسته/کارت/کنترل مشترک و تصمیم مصوب قابل مقایسه است |
| `capture-needed→new-evidence` | ۴ | شکاف قبلی library در چهار عرض با capture جاری بسته شد |

گالری۱۲گروهی و `evidence-index.csv` به واقعیت تازه وصل شدند. تمام فیلدهای رأی `group-verdicts.csv` خالی‌اند. ۱۴ ردیف secondary/۵۶ slot خارج دور اول حذف یا قبول اعلام نشده‌اند و در گالری تاریخی باقی‌اند. capture موفق، نبود overflow یا مشاهده چشمی ایجنت **قبول طراحی، pixel-perfect یا ممیزی تخصصی نیست**.

بررسی چشمی مستقیم روی نمونه‌های workspace موبایل، admin دسکتاپ، expert موبایل و detail fund انجام شد. پنل‌های بدون مرجع کامل pair جعلی نگرفتند. full-page detail در موبایل canvas بلند دارد؛ این واقعیت در PNG باقی است و به‌تنهایی شکست طراحی یا قبول آن اعلام نشده است.

## D28: قرارداد، ساخت و استقلال

ورودی نهایی در [d28-inputs.json](tech-evidence-01/d28-inputs.json) با seed ثابت و SHA-256 برابر `4f74b92e2cf72aaed04311cbd43470e6930f25710c967f7b2be137ca5160294f` پیش از اجرای نهایی freeze شد. مبلغ‌ها `TOMAN@1` و بازده‌ها `PERCENT@1` با basis کامل نسخه۱ هستند. داده مصنوعی است و هیچ ادعای بازار واقعی ندارد.

[ماتریس route×axis](tech-evidence-01/d28-route-axis-coverage.csv) ۶۴ ردیف دارد. amount برای operator/charity و return/risk برای routeهای فاقد آن‌ها در `search_fields.json` صریحاً N/A است؛ برای پرکردن جدول فیلد ساختگی اضافه نشد و سناریوی همان جایگاه با شرط واقعی route مانند `experience` یا `charity_type` اجرا شد.

oracle در `d28_run.py` تابع `discovery.score` را برای انتظار محاسباتی import نمی‌کند؛ وزن/مخرج/score/coverage را از ورودی frozen و D28 مستقل محاسبه می‌کند و سپس با خروجی محصول مقایسه می‌شود. کنترل‌های نهایی شامل این موارد‌اند:

- ریاضی score/coverage و تفکیک آن دو؛
- W=0→null/null و W>0,K=0→0/0 با insufficient-data؛
- صفر معلوم در coverage و تمایز unknown/NA؛
- واحد و basis کامل و عدم مقایسه basis ناهمسان؛
- هشدار شرط مهم برای unknown/unmet؛
- عدم وزن مضاعف conditions و سقف مجموع وزن محور؛
- عدم بهترشدن score با پنهان‌کردن داده؛
- باقی‌ماندن هر شش فرصت، top-5 از رقابت بیش از۵، ترتیب تکرارشونده و cursor بدون افتادگی/تکرار.

این oracle «مفیدبودن توصیه»، رتبه مطلوب انسانی یا نبود خطر بحرانی را تعیین نمی‌کند. معیار۸۰٪/صفر بحرانی همچنان فقط پیشنهاد پایلوت است.

## شکست‌های حفظ‌شده و وضعیت held-out

نخستین development روی hash اولیه موفق بود، اما نخستین اجرای held-out پیش از scoring با خطای قرارداد `return.basis` متوقف شد. [رکورد دقیق](tech-evidence-01/heldout-first-attempt.json) و ورودی/نتیجه attemptها حفظ شده‌اند. پس از تکمیل basis، ممیزی route×field نیز استفاده معنایی نامعتبر return/risk برای بعضی routeها و سپس نبود unit صریح در fixture را کشف کرد. هیچ‌یک نقص محصول نبود و هیچ رفتار محصولی تغییر نکرد.

طبق پروتکل مأموریت، held-out پس از این مشاهده/اصلاح‌ها دیگر «confirming untouched holdout» نیست؛ خروجی نهایی آن فقط **regression فنی** است. [leak/replay log](tech-evidence-01/leak-replay-log.json) همه hashها و replayها را ثبت می‌کند و کورسازی مطلق ادعا نشده است. برای شاهد held-out تأییدی تازه، مجموعه مستقل جدید و مجوز/بازآزمایی جدا لازم است؛ نتیجه نامطلوب قبلی پاک یا موفق بازنام‌گذاری نشده است.

در capture نیز اجرای نخست پنل‌ها به‌علت دو fixture کارشناس و selector strict شکست؛ XML همان تلاش حفظ شد. selector فقط با `.first()` دقیق شد و چهار سناریوی پنل بدون retry خودکار دوباره اجرا و قبول شدند. این شکست harness بود، نه نقص UI.

## آزمون‌ها و نتایج واقعی

محیط: compose مستقل `invest-expit`، PostgreSQL 17 روی tmpfs، databaseهای تازه و مجزا؛ runtime محصول روی۳۱۱۸ و مرجع جدا. DB فعال پروژه، داده واقعی، پروژه‌های دیگر و secret استفاده نشدند. image محصول rebuild نشد، چون کد محصول تغییر نکرد و source/runtime موجود با مبنای قبول سازگار بود.

فرمان‌های اصلی قابل بازتولید:

```sh
python3 docs/experience-complete/tech-evidence-01/d28_prepare.py

docker compose -f .tools/expit/compose.yaml run --rm \
  -e DATABASE_URL=postgresql://postgres:synthetic@db:5432/<fresh_db> \
  -v "$PWD/docs/experience-complete/tech-evidence-01:/tech-evidence" \
  test /app/.venv/bin/python manage.py migrate --noinput

docker compose -f .tools/expit/compose.yaml run --rm \
  -e DATABASE_URL=postgresql://postgres:synthetic@db:5432/<fresh_db> \
  -e EVIDENCE_DIR=/tech-evidence -e D28_SPLIT=development \
  -e RUNTIME_SOURCE=79519bb8e88cbf6c0bcf7614c63b3737cc668a70 \
  -v "$PWD/docs/experience-complete/tech-evidence-01:/tech-evidence" \
  test /app/.venv/bin/python manage.py shell \
  -c "exec(open('/tech-evidence/d28_run.py').read()); main()"

# همان فرمان با DB تازه و D28_SPLIT=held-out؛ خروجی این تحویل regression است.
python3 docs/experience-complete/tech-evidence-01/build_d28_package.py
python3 docs/experience-complete/tech-evidence-01/build_design_index.py
python3 docs/experience-complete/tech-evidence-01/validate.py
python3 docs/experience-complete/tech-evidence-01/build_manifest.py
```

capture مرورگر با Playwright 1.65.1، `workers=1` و `retries=0` اجرا شد. اجرای اولیه ۸ سناریو: ۴ detail قبول و ۴ panel به selector harness خطا؛ rerun هدفمند panel: **۴/۴ قبول در ۵۱٫۷۲ثانیه**؛ library/report: **۴/۴ قبول در ۱۵٫۳۲ثانیه**. چهار detail قبول اولیه **۵۴٫۳ثانیه** زمان آزمون داشتند. در مجموع **۱۲ سناریوی مرورگر یکتا قبول**؛ ۴ rerun اصلاح harness جدا گزارش شده و به شمار یکتا افزوده نشده است.

D28 نهایی: **۸۰ سناریوی یکتا، ۹۶ فرصت یکتا، ۴۸۰ زوج نامزد و ۴۰۰ top-5**؛ ۲۸ کنترل ساختار/مخرج/لینک/فرم/oracle در `validation.json` همگی قبول. manifest نیز ۸۳ فایل تحویل را با اندازه و SHA-256 ثبت می‌کند و بازبینی مستقل hash آن‌ها صفر اختلاف داشت. rerunهای fixture در شمار۸۰ سناریوی یکتا دوباره شمرده نشده‌اند.

زمان‌ها بر پایه wall-clock و زمان runner: مطالعه/آماده‌سازی و ممیزی قرارداد حدود۱۴دقیقه؛ ساخت fixture/harness و اصلاح‌های داخلی حدود۱۸دقیقه؛ capture مرورگر حدود۳دقیقه زمان runner؛ build محصول **صفر دقیقه**؛ migration و اجرای نهایی D28 حدود۱٫۵دقیقه (کل اجراهای تشخیصی/regression حدود۶دقیقه)؛ گزارش/manifest/همگرایی حدود۱۵دقیقه. این اعداد زمان انسانی داوری نیستند.

## وضعیت گیت‌ها و موارد باز

| مورد | وضعیت |
|---|---|
| اصلاح/تکمیل فنی توسط برنامه‌نویس | انجام‌شده در دامنه شواهد؛ آماده بازآزمایی مستقل تجمیعی |
| قبول مستقل این بسته تازه | ثبت نشده؛ لازم است |
| رأی مالک محصول روی۱۲گروه | خالی |
| قبول متخصص طراحی | باز و گیت عرضه |
| relevance/critical review خبره D28 | ۴۰۰ فرم خالی؛ باز و گیت عرضه |
| held-out تأییدی untouched | موجود نیست؛ held-out فعلی regression است |
| ۱۴ ردیف secondary طراحی | خارج دور اول؛ حذف نشده و برای ممیزی نهایی باز |
| production readiness / عرضه | خارج دامنه و باز |

قدم بعدی پیشنهادی، نه مجازشده: بازآزمایی مستقل تجمیعی همین بسته با بررسی hash، replay محدود development، اعتبار matrix/link/form و تأیید اینکه held-out به‌اشتباه «تأییدی» نامیده نشده است. سپس رأی‌های انسانی فقط توسط افراد تعیین‌شده انجام شوند. COMP-AI، deploy یا مرحله بعد در این مأموریت آغاز نشده است.
