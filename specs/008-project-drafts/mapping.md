# نگاشت تمام فیلدهای پروژه A1

مبنا بخش۳ PRODUCT-S05-01 و D29/D31؛ schema ثابت۱. مسیر پیش‌فرض منبع src/types/index.ts:Opportunity است، جز موارد صریح facts/تصمیم. کلید API snake_case با کلید منبع یکی فرض نشده است.

| منبع | معنا / واحد | schema/API key | widget / شرط | پذیرش |
| --- | --- | --- | --- | --- |
| title | عنوان پروژه / متن/شناسه | `title@1` | text / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| description | شرح پروژه / متن/شناسه | `description@1` | text / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| stage | مرحله اجرایی (اعلامی) / متن/شناسه | `stage@1` | text / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| model | مدل همکاری / متن/شناسه | `model@1` | text / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| modelId | شناسه مدل قرارداد / متن/شناسه | `model_id@1` | text / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| finance | روش تأمین مالی / متن/شناسه | `finance@1` | text / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| repay | بازگشت پول / متن/شناسه | `repay@1` | text / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| ownership | شرح حقوق / متن/شناسه | `ownership@1` | text / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| caution | هشدارها / متن/شناسه | `caution@1` | text / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| phase | وضعیت پیشرفت / متن/شناسه | `phase@1` | enum / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| owner | صاحب پروژه (بخش) / متن/شناسه | `sector@1` | enum / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| income | نوع درآمد / متن/شناسه | `income@1` | enum / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| risk | ریسک اعلامی / متن/شناسه | `risk@1` | enum / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| legalStatus | وضعیت حقوقی / متن/شناسه | `legal_status@1` | enum / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| revenues | منابع درآمد / متن/شناسه | `revenues@1` | multi / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| checks | بررسی‌های پروژه / متن/شناسه | `checks@1` | lines / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| steps | گام‌ها / متن/شناسه | `steps@1` | lines / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| province | استان / متن/شناسه | `province@1` | reference / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| کاتالوگ پذیرفته‌شده006 و D31؛ نوع افزوده نسبت به province/city منبع | شهرستان / متن/شناسه | `county@1` | reference / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| city | شهر / متن/شناسه | `city@1` | reference / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| group | حوزه / متن/شناسه | `group@1` | reference / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| subtype | زیردسته / متن/شناسه | `subtype@1` | reference / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| usage | کاربری / متن/شناسه | `usage@1` | enum / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| metric.label | عنوان ظرفیت / متن/شناسه | `metric_label@1` | text / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| metric.value/unit | مقدار ظرفیت / ITEM | `metric_quantity@2` | quantity / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| minCapital | حداقل سرمایه ورود / BILLION_TOMAN | `min_capital@1` | money / participation | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| budget | نیاز مالی کل / BILLION_TOMAN | `budget@1` | money / always | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| monthlyRent | اجاره ماهانه / MILLION_TOMAN | `monthly_rent@1` | money / lessee | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| terms.workingCapitalMin | نقدینگی اجرای پیمان / BILLION_TOMAN | `working_capital_min@1` | money / contractor | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| lib/facts.ts:109 عنوان قیمت عرضه + تفکیک D31 | قیمت خرید / BILLION_TOMAN | `purchase_price@1` | money / buyer | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| lib/facts.ts:113 عنوان ودیعه + تفکیک D31 | ودیعه / BILLION_TOMAN | `deposit@1` | money / lessee | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| terms.lumpRent | اجاره یکجای دوره / BILLION_TOMAN | `lump_rent@1` | money / lessee | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| executionMonths / terms.executionMonths | مدت اجرا / MONTH | `execution_months@1` | quantity / execution | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| paybackYears | دوره بازگشت / YEAR | `payback_years@1` | quantity / participation | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| paybackDownsideYears | بازگشت بدبینانه / YEAR | `payback_downside_years@1` | quantity / participation | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| lockupMonths | قفل سرمایه / MONTH | `lockup_months@1` | quantity / participation | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| firstIncomeMonths | اولین دریافت / MONTH | `first_income_months@1` | quantity / participation | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| durationYears | مدت کل طرح / اجاره / YEAR | `duration_years@1` | quantity / duration | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| heritageTerms.years | مدت بهره‌برداری میراث / YEAR | `heritage_years@1` | quantity / heritage_years | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| terms.partnerShare | سهم شریک / SHARE_PERCENT | `partner_share@1` | quantity / participation | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| terms.governmentShare | سهم دولت / SHARE_PERCENT | `government_share@1` | quantity / contractor | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| terms.irr / irrBasis / irrPrice | IRR اعلامی / PERCENT | `irr@1` | return / participation | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| terms.interventions | نوع مداخله دولت / متن/شناسه | `interventions@1` | multi / participation | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| terms.partnershipSettlements | نحوه تسویه سهم / متن/شناسه | `partnership_settlements@1` | multi / participation | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| terms.contractorSettlements | تسویه صورت‌وضعیت / متن/شناسه | `contractor_settlements@1` | multi / contractor | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| terms.acceptedGuarantees | تضمین قابل پذیرش / متن/شناسه | `accepted_guarantees@1` | multi / contractor | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| terms.salePayments | شرایط پرداخت خرید / متن/شناسه | `sale_payments@1` | multi / buyer | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| terms.transferRights | حق قابل انتقال / متن/شناسه | `transfer_rights@1` | multi / buyer | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| terms.leaseTypes | نوع اجاره / متن/شناسه | `lease_types@1` | multi / lessee | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| terms.leasePayments | نحوه پرداخت اجاره / متن/شناسه | `lease_payments@1` | multi / lessee | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| heritageTerms.returns | جبران هزینه مرمت / متن/شناسه | `heritage_returns@1` | multi / heritage | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| heritageTerms.uses | کاربری پس از مرمت / متن/شناسه | `heritage_uses@1` | multi / heritage | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| heritageTerms.payments | زمان دریافت قرارداد مرمت / متن/شناسه | `heritage_payments@1` | multi / heritage | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| terms.generalConditions | شرایط عمومی / متن/شناسه | `general_conditions@1` | text / execution | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| terms.specialConditions | شرایط تخصصی / متن/شناسه | `special_conditions@1` | text / execution | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| rights.subject | موضوع حق / متن/شناسه | `rights_subject@1` | text / rights | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| rights.titleParties | مالک عرصه / اعیان / متن/شناسه | `rights_title_parties@1` | text / rights | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| rights.holder | دارنده منافع / سرقفلی / حق کسب / متن/شناسه | `rights_holder@1` | text / rights | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| rights.originalLease | تاریخ رابطه اولیه و انتقال / متن/شناسه | `rights_original_lease@1` | text / rights | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| rights.regime | قانون حاکم و مستند / متن/شناسه | `rights_regime@1` | text / rights | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| rights.assignment | حق انتقال / رضایت / متن/شناسه | `rights_assignment@1` | text / rights | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| rights.keyMoney | شرح سرقفلی و دلیل پرداخت / متن/شناسه | `rights_key_money@1` | text / rights | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| rights.valuation | شرح ارزش مستقل حقوق / متن/شناسه | `rights_valuation@1` | text / rights | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| rights.permittedUse | کاربری و شغل مجاز / متن/شناسه | `rights_permitted_use@1` | text / rights | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| rights.renewal | شروط تمدید و تخلیه / متن/شناسه | `rights_renewal@1` | text / rights | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| rights.claims | دعاوی و حقوق ثالث / متن/شناسه | `rights_claims@1` | text / rights | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| rights.registration | نوع سند و ثبت / متن/شناسه | `rights_registration@1` | text / rights | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| rights.costs | هزینه انتقال و بدهی / متن/شناسه | `rights_costs@1` | text / rights | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |
| rights.occupancy | وضعیت تصرف / متن/شناسه | `rights_occupancy@1` | enum / rights | test_every_project_widget_contract_roundtrip؛ شروط در test_hidden_restore و heritage |

## اختلاف‌های مصوب و readonly
- owner منبع = بخش public/private، درAPI `sector`؛ مالک حساب/سازمان از نشست و انتخاب مجاز، با آن مخلوط نیست.
- terms.executionMonths و executionMonths: یک execution_months مؤثر؛ fallback یا دو مقدار متعارض نداریم. مدت، منبع شروع صریح می‌خواهد.
- minCapital زیرعنوان خرید/ودیعه در facts هم‌معنی نیست: purchase_price و deposit مستقل مصوب D31؛ اجاره ماهانه/lump مستقل.
- irrBasis/irrPrice در basis کامل007؛ irrCashflowsVerified قابل نوشتن نیست و ادعا خودتأیید نمی‌شود. IRR محاسبه نمی‌کنیم.
- usageLabel از برچسب واژه‌نامه؛ usage عنوان خام کاربری است، نه مقدار کمی. metric label + typed quantity با واحد صریح، ظرفیت بدون واحد معتبر نیست.
- id/version از سرور؛ publishedAt/expert/verified/public_revision درA1 قابل تعیین نیستند. image/guideFileUrl در فایل خصوصی image/document به جای URL دلخواه نگاشت شده‌اند.
- province/county/city روابط کاتالوگ؛ unknown مستقل؛ نبود شهر با شهرستان جایگزین نمی‌شود.
- phase/revenues/usage و سایر enumها عین واژه‌نامه مرجع از criteria/utils/provinces تثبیت می‌شوند؛ required از فرم ترجیحات متقاضی استخراج نشده است.
- صندوق/فروش A2؛ هیچ ردیف آن‌ها در این تحویل ادعای تکمیل ندارد. حقوق keyMoney/valuation صرفاً شرح مستند است و مبلغ محاسباتی نیست.

## ظرفیت نسخه۲
واحدهای metric.unit عین برچسب منبع نگاشت شدند؛ هر کد نسخه۱ و ضریب۱ با base مستقل است. تبدیل مگاوات/مگاولت‌آمپر، مسافر/نفر، اتاق/تخت یا طول/مساحت حدس زده نمی‌شود. تعریف نسخه۱ قبلی بدون تغییر حفظ و قابل خواندن است؛ widget جدید نسخه۲ را صریح می‌فرستد.

| منبع unit | کد نسخه۱ |
| --- | --- |
| اتاق | ROOM |
| ایستگاه | STATION |
| بشکه | BARREL |
| تخت | BED |
| تن | TONNE |
| جایگاه | STALL |
| خودرو | VEHICLE |
| راس | ANIMAL_HEAD |
| سایت | SITE |
| صندلی | SEAT |
| متر | METRE |
| مترمربع | SQUARE_METRE |
| مترمکعب | CUBIC_METRE |
| مسافر | PASSENGER |
| مگاوات | MEGAWATT |
| مگاولت‌آمپر | MEGAVOLT_AMPERE |
| میلیون مترمکعب | MILLION_CUBIC_METRE |
| نفر | PERSON |
| نقطه | POINT |
| هکتار | HECTARE |
| پایه | POLE |
| کیلومتر | KILOMETRE |
