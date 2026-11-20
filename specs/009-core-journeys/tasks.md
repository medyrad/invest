# تسک‌های اجرایی هسته

وضعیت جاری ۲۰۲۶/۱۱/۲۰: ده EXP قبول فنی مستقل در `8c327ec`؛ [گزارش](../../docs/experience-complete/fix-02-retest-report.md). قبول فنی T023/T027 شامل داده تاریخی موجود است، نه تصویب استثنای legacy. T020 و گیت‌های انسانی بسته نمی‌شوند؛ [بسته‌های داوری](../../docs/experience-complete/product-gates-report.md). مجوز اجرای قدیمی زیر، مجوز کدنویسی در مأموریت اسنادی جاری نیست.

مجوز کل بسته برقرار است؛ توقف پس از زیرمرحله لازم نیست. هر checkbox تنها پس از شاهد.

- [x] T001 تثبیت spec/plan/contracts و تحلیل سازگاری پیش از ساخت
- [x] T002 schema و field definitions صندوق/فروش، شرط‌ها، migration افزایشی و تست مقدار/ذخیره
- [x] T003 مدل snapshot immutable و بررسی/انتشار/توقف با مجوز جاری و آزمون رقابت
- [x] T004 بررسی سازمان، اسناد، جانشینی/اختلاف و آزمون چندحسابی
- [x] T005 پرونده، assignment، گفتگو/پیوست، consent و SLA/jobs با تست زمان و عدم نشت
- [x] T006 تطبیق D28، public DTO، cursor، مقایسه و fixtures مستقل
- [x] T007 منتخب/شرایط/پروفایل/اعلان/کتابخانه/گزارش snapshot و تست
- [x] T008 UI مرجع و پنل‌های متصل، ادامه ورود و حالت‌های خطا/دسترسی
- [x] T009 seed غیرمخرب سه نوع/سازمان و ابزار نقش محدود محلی؛ اجرای3108
- [x] T010 آزمون سفر یکپارچه PostgreSQL/مرورگر، چهار عرض و شاهد طراحی
- [x] T011 تحلیل پایان، پوشش۴۴قابلیت، guide/report/version/timings و commit تحویل


شاهد پایان: docs/core-delivery/report.md و evidence/manifest.json؛ ۶۲۸ آزمون PostgreSQL، هفت سفر مرورگر و دو regression نشست روی image نهایی. این تسک‌ها تحویل برنامه‌نویس همین بسته‌اند و به معنی پذیرش مستقل/انسانی نیستند. تسک‌های پایه چندمرحله‌ای تغییر نکردند.

## اصلاح تجمیعی CORE-FIX-01

- [x] T012 بازتولید سه ایراد و نگاشت source/قرارداد متأثر
- [x] T013 دوره operator از migration/schema/raw/effective/missing تا UI/انتشار/جزئیات/گزارش با آزمون مسیر
- [x] T014 اعتبارسنجی ساختار parser پیش از lookup و HTTP400 فارسی با تست منفی/مثبت
- [x] T015 گروه/ترتیب/ناوبری مقایسه سه نوع مطابق مرجع و آزمون DOM،۲تا۴، موبایل و صفحه‌کلید
- [x] T016 اجرای مرتبط ترتیبی، image نهایی3108، تصاویر، تحلیل سازگاری، گزارش/زمان و commit/push معمول

شواهد T012–T016 در docs/core-delivery/fix-01-report.md و fix-01-evidence/manifest.json؛ تحویل اصلاح با پذیرش مستقل/انسانی یکی نیست.


پذیرش T012–T016: [بازآزمایی مستقل هسته](../../docs/core-delivery/retest-01-report.md)، commit `8bfc727`. شاهد تحویل/اصلاح فوق تاریخی است؛ قبول انسانی از آن استنتاج نمی‌شود.

## مأموریت COMP-EXPERIENCE — PROGRAMMER-EXPERIENCE-COMPLETE-01

وضعیت تاریخی T017–T019 با گزارش مستقل c7ac09b نقض شده است؛ علامت‌های تحویل قبلی پذیرش جاری نیستند. اصلاح جاری در T022–T025 پیگیری می‌شود.

- [x] T017 بازتولید و تکمیل PC-A01: نیت ذخیره منتخب/شرایط پس از ورود با snapshot و یک‌بار اجرا؛ لغو/تعویض حساب/پاسخ دیررس، AC-PC01.
- [x] T018 تکمیل PC-A02/03: پروفایل چندنقشی و گزینه/واحد معتبر، جمع‌بندی/دریافت و ذخیره‌سازی صادقانه؛ تغییر شرایط ذخیره‌شده بدون حذف داده در شکست، AC-PC02/03.
- [x] T019 بستن PC-A04/05 همراه 010: راهنمای نسخه‌دار از پاسخ‌های مؤثر مشترک، دریافت مجدد HTML فارسی از snapshot و حفظ اختیار جاری، AC-PC04/05.
- [ ] T020 بستن PC-A06/07/08: بخش فنی ماتریس/مصرف‌کننده، اصلاح زمین/راهنما، چهار عرض و مجموعه۴۰سناریویی D28 آماده است؛ تأیید انسانی طراحی، label پیشینی خبره و پذیرش کیفی عمداً باز است، AC-PC06/07/08.
- [x] T021 تحویل جامع: regression اثرمحور، گزارش/شواهد/نسخه، اجرای تمام۱۲تست مستقل موجود توسط برنامه‌نویس و ثبت گیت‌های انسانی باز تکمیل شد؛ این علامت قبول مستقل نیست. شاهد: fix-01-report.md و fix-01-continuation-evidence.

منبع و معیار دقیق این تسک‌ها [ممیزی](../../docs/product-completion-audit.md) و دامنه/پایان بسته در [roadmap](../../docs/02-delivery-roadmap.md) است. تسک جدید به معنی بازشدن یافتهٔ بسته‌شدهٔ CORE-IT/S08-IT نیست.

## PROGRAMMER-EXPERIENCE-FIX-01

- [x] T022 EXP-IT-001/008/009/010: اتصال سروری کلید ادامه به نشست؛ ذخیره جزئی، حفظ dirty، retry ثابت و تعارض دو تب؛ آزمون واقعی PostgreSQL و مرورگر. شاهد: fix-01-evidence/backend-verified.xml، history-verified.xml، browser-final.xml و browser-targeted-rerun.xml؛ محدودیت مصرف‌کنندگان سریع در fix-01-report.md، بدون پذیرش مستقل.
- [x] T023 EXP-IT-002/003/004: محتوای مؤثر، متن فارسی و snapshot تاریخی؛ برابری معنایی preview/download، legacy بدون داده زنده و اختیار جاری. شاهد: continuation-evidence/backend-final-*.xml، actual-report و legacy-snapshot-shapes.md.
- [x] T024 EXP-IT-005/007: سبک فرم در همه مصرف‌کنندگان و hit-test/focus راهنمای موبایل در چهار عرض؛ شاهد هم‌شرایط مرجع. شاهد: continuation-evidence/browser-continuation.xml و تصاویر reference/product.
- [x] T025 EXP-IT-006: مخرج کامل route/state و نگاشت فیلدی۲۰زمینه؛ تفکیک شکاف فنی از داوری انسانی؛ گزارش تجمیعی، شمار یکتا و commit محلی. شاهد: continuation-evidence و commit کد `cb6aba7`؛ commit اسناد در تحویل نهایی گزارش می‌شود.

## Phase 1: Convergence

- [x] T026 CRITICAL تطابق جزئیات انتخاب‌گر نقش، پیشرفت، ترتیب و فاصله فرم حرفه‌ای در سه مصرف‌کننده با مرجع هم‌شرایط؛ حالت مهمان/حساب، خطای QuickProfile، focus و badge پس از font-ready در چهار عرض ثبت شد. منبع: continuation-evidence/browser-continuation.xml و تصاویر product/reference.
- [x] T027 بازسازی نسخه‌دار بخش‌های قابل بازیابی legacy و کارت‌بندی/محتوای سند تکمیل شد؛ نام/گام واقعاً ناموجود با محدودیت فیلدی و بدون lookup زنده ثبت می‌شود. منبع: continuation-evidence/legacy-snapshot-shapes.md، actual-report و backend-final-primary.xml.
- [x] T028 مخرج route/state و۲۰زمینه، aliasهای expectedReturn/fundReturnMin و fundRisk/risk و general/special/notes با خروجی و پذیرش ردیفی تکمیل شد. منبع: dynamic-context-contract.json، dynamic-context-review.csv و continuation-evidence/route-state-coverage.csv. گیت انسانی باز است.

## PROGRAMMER-EXPERIENCE-FIX-02

- [x] T029 EXP-IT-003: پوشش دقیق هر هشت route قرارداد با واژه‌نامه فارسی نسخه۱، نمایش صریح شناسه تاریخی ناشناخته، سازگاری preview/دانلود اول/دریافت مجدد و حفظ HTML منجمد قبلی؛ PostgreSQL ایزوله، آزمون مستقل و Chromium واقعی. شاهد: `docs/experience-complete/fix-02-report.md` و `fix-02-evidence/`. این علامت ادعای پذیرش مستقل یا انسانی نیست.

## Phase 2: Fallback evidence — TECH-EXPERIENCE-EVIDENCE-01

منبع: PC-FALLBACK-01 و [بسته هماهنگی](../../docs/experience-complete/fallback-gates-plan.md). PC-LEGACY-01 اکنون مصوب است؛ یادداشت ابتدای فایل وضعیت تاریخی قبل از پاسخ کاربر است. T020 باز می‌ماند و checkbox قبلی تغییر نمی‌کند.

- [x] T030 [US5] شواهد۲۶ردیف primary در چهار عرض با مخرج۱۰۴، reuse معتبر/نماینده مستدل/capture شکاف و گالری۱۲گروهی تکمیل شد؛ فرم مالک خالی و پنل بی‌مرجع فقط component/decision mapping دارد. شاهد: `docs/experience-complete/tech-evidence-01/design-slot-matrix.csv` و گالری جاری؛ همراه010/T041، نه رأی انسانی.
- [x] T031 [US3] حجم مصوب۸۰سناریو/۹۶فرصت در هشت route با seed/hash/freeze، دو pool واقعی۶تایی در هر route و split۳۲/۴۸ ساخته شد؛ route×axis و N/Aهای قراردادی ثبت و هیچ label انسانی تولید نشد. شاهد: `tech-evidence-01/d28-input*.json` و `d28-route-axis-coverage.csv`.
- [x] T032 [US3] harness روی PostgreSQL ایزوله با oracle حسابی مستقل، شش نامزد و top-5 واقعی، unknown/coverage/warning/tie/cursor اجرا شد؛ شکست نخست basis حفظ و held-out اصلاح‌شده صریحاً regression است. فرم‌های۴۰۰زوج top-5 کاملاً خالی و score/rank جداست؛ فرمول/وزن/کد محصول تغییر نکرد.
- [x] T033 تحویل جامع شواهد/fixture با manifest، محدودیت، نسخه/زمان و گزارش برای بازبینی مستقل تجمیعی آماده شد؛ لینک/مخرج/فرم خالی اعتبارسنجی و شواهد تاریخی حفظ شدند. commit/push در تحویل مأموریت ثبت می‌شود؛ نه رأی انسانی، نه COMP-AI یا عرضه.

تکمیل فنی این چهار تسک T020، گیت طراحی تخصصی، کیفیت انسانی D28 یا عرضه را خودکار نمی‌بندد. held-out نهایی به‌علت اصلاح fixture پس از نخستین تلاش، شاهد regression است و تأیید مستقل تازه هنوز لازم است.

## Phase 3: Evidence correction — PROGRAMMER-EXPERIENCE-EVIDENCE-FIX-01

- [x] T034 [US3] EVID-IT-001: پروفایل‌های unknown و known-zero با زمینه مؤثر متفاوت بازساخته شدند؛ validator مستقل ۹۶ امضای معنایی یکتا، ۴۸ در هر split و صفر duplicate را پس از حذف شناسه/metadata الزام می‌کند و mutation موقت را رد می‌کند.
- [x] T035 [US3] EVID-IT-002: محور unit/basis برای operator و charity به‌علت نبود مصرف‌کننده عددی در قرارداد route برابر N/A شد؛ مسیرهای عددی به criteria، unit/basis و check واقعی oracle متصل و false-applicable در mutation رد شد.
- [x] T036 [US5] EVID-IT-003/004 همراه 010/T042: نه slot دقیق route/state و چهار capture کتابخانه روی runtime منطبق recapture، به provenance محاسبه‌پذیر source→image→BUILD_ID/bundle→capture متصل و index/gallery فقط در همان ۱۳ slot همگام شد؛ هیچ verdict انسانی ثبت نشد.
- [x] T037 development روی PostgreSQL تازه و held-out فقط با نقش regression پس از اصلاح fixture اجرا شد؛ ۴۸۰ مقایسه oracle بدون mismatch، ۴۰۰ ردیف فرم داوری خالی، validation تجمیعی و گزارش/manifest برای بازآزمایی مستقل آماده شد. شواهد تاریخی/replay دست‌نخورده‌اند و این علامت پذیرش مستقل/انسانی نیست.

شاهد T034–T037: `docs/experience-complete/tech-evidence-fix-01/` و `tech-evidence-fix-01-report.md`. T020 و گیت‌های طراحی تخصصی/D28 انسانی/عرضه همچنان بازند.
