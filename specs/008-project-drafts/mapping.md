# نگاشت تمام فیلدهای پروژه A1

مبنا جدول بخش۳ PRODUCT-S05-01، D29/D31؛ schema ثابت نسخه۱. همه widgetها در فرم واقعی /drafts ساخته می‌شوند؛ هر مقدار دقیق field namespace=invest.opportunity.project@1 و کلید زیر دارد. متن خام/enum طبقschema؛ آمادگی نقص است نه ارسال.

| منبع | معنا / واحد | schema/API key | widget / شرط | پذیرش |
| --- | --- | --- | --- | --- |
| src/types/index.ts:Opportunity.title | عنوان پروژه / متن یا شناسه | `title` | text / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.description | شرح پروژه / متن یا شناسه | `description` | text / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.stage | مرحله اجرایی (اعلامی) / متن یا شناسه | `stage` | text / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.model | مدل همکاری / متن یا شناسه | `model` | text / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.model_id | شناسه مدل قرارداد / متن یا شناسه | `model_id` | text / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.finance | روش تأمین مالی / متن یا شناسه | `finance` | text / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.repay | بازگشت پول / متن یا شناسه | `repay` | text / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.ownership | شرح حقوق / متن یا شناسه | `ownership` | text / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.caution | هشدارها / متن یا شناسه | `caution` | text / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.phase | وضعیت پیشرفت / متن یا شناسه | `phase` | enum / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.sector | صاحب پروژه (بخش) / متن یا شناسه | `sector` | enum / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.income | نوع درآمد / متن یا شناسه | `income` | enum / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.risk | ریسک اعلامی / متن یا شناسه | `risk` | enum / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.legal_status | وضعیت حقوقی / متن یا شناسه | `legal_status` | enum / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.revenues | منابع درآمد / متن یا شناسه | `revenues` | lines / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.checks | بررسی‌های پروژه / متن یا شناسه | `checks` | lines / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.steps | گام‌ها / متن یا شناسه | `steps` | lines / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.province | استان / متن یا شناسه | `province` | reference / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.county | شهرستان / متن یا شناسه | `county` | reference / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.city | شهر / متن یا شناسه | `city` | reference / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.group | حوزه / متن یا شناسه | `group` | reference / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.subtype | زیردسته / متن یا شناسه | `subtype` | reference / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.usage | کاربری / متن یا شناسه | `usage` | text / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.metric_label | عنوان ظرفیت / متن یا شناسه | `metric_label` | text / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.metric | مقدار ظرفیت / ITEM | `metric_quantity` | quantity / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.min_capital | حداقل سرمایه ورود / BILLION_TOMAN | `min_capital` | money / participation | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.budget | نیاز مالی کل / BILLION_TOMAN | `budget` | money / always | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.monthly_rent | اجاره ماهانه / MILLION_TOMAN | `monthly_rent` | money / lessee | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.working_capital_min | نقدینگی اجرای پیمان / BILLION_TOMAN | `working_capital_min` | money / contractor | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.purchase_price | قیمت خرید / BILLION_TOMAN | `purchase_price` | money / buyer | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.deposit | ودیعه / BILLION_TOMAN | `deposit` | money / lessee | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.lump_rent | اجاره یکجای دوره / BILLION_TOMAN | `lump_rent` | money / lessee | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.execution_months | مدت اجرا / MONTH | `execution_months` | quantity / execution | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.payback_years | دوره بازگشت / YEAR | `payback_years` | quantity / participation | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.payback_downside_years | بازگشت بدبینانه / YEAR | `payback_downside_years` | quantity / participation | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.lockup_months | قفل سرمایه / MONTH | `lockup_months` | quantity / participation | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.first_income_months | اولین دریافت / MONTH | `first_income_months` | quantity / participation | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.duration_years | مدت کل طرح / اجاره / YEAR | `duration_years` | quantity / duration | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.heritage_years | مدت بهره‌برداری میراث / YEAR | `heritage_years` | quantity / heritage_years | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.partner_share | سهم شریک / SHARE_PERCENT | `partner_share` | quantity / participation | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.government_share | سهم دولت / SHARE_PERCENT | `government_share` | quantity / contractor | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.irr | IRR اعلامی / PERCENT | `irr` | return / participation | US3، اعتبارسنجی/active-set و round-trip |
| src/data/source-terms.ts:interventionLabel; src/types/index.ts:ProjectTerms/heritageTerms | نوع مداخله دولت / متن یا شناسه | `interventions` | multi / participation | US3، اعتبارسنجی/active-set و round-trip |
| src/data/source-terms.ts:settlementLabel; src/types/index.ts:ProjectTerms/heritageTerms | نحوه تسویه سهم / متن یا شناسه | `partnership_settlements` | multi / participation | US3، اعتبارسنجی/active-set و round-trip |
| src/data/source-terms.ts:contractorSettlementLabel; src/types/index.ts:ProjectTerms/heritageTerms | تسویه صورت‌وضعیت / متن یا شناسه | `contractor_settlements` | multi / contractor | US3، اعتبارسنجی/active-set و round-trip |
| src/data/source-terms.ts:guaranteeLabel; src/types/index.ts:ProjectTerms/heritageTerms | تضمین قابل پذیرش / متن یا شناسه | `accepted_guarantees` | multi / contractor | US3، اعتبارسنجی/active-set و round-trip |
| src/data/source-terms.ts:salePaymentLabel; src/types/index.ts:ProjectTerms/heritageTerms | شرایط پرداخت خرید / متن یا شناسه | `sale_payments` | multi / buyer | US3، اعتبارسنجی/active-set و round-trip |
| src/data/source-terms.ts:transferRightLabel; src/types/index.ts:ProjectTerms/heritageTerms | حق قابل انتقال / متن یا شناسه | `transfer_rights` | multi / buyer | US3، اعتبارسنجی/active-set و round-trip |
| src/data/source-terms.ts:leaseTypeLabel; src/types/index.ts:ProjectTerms/heritageTerms | نوع اجاره / متن یا شناسه | `lease_types` | multi / lessee | US3، اعتبارسنجی/active-set و round-trip |
| src/data/source-terms.ts:leasePaymentLabel; src/types/index.ts:ProjectTerms/heritageTerms | نحوه پرداخت اجاره / متن یا شناسه | `lease_payments` | multi / lessee | US3، اعتبارسنجی/active-set و round-trip |
| src/data/source-terms.ts:heritageReturnLabel; src/types/index.ts:ProjectTerms/heritageTerms | جبران هزینه مرمت / متن یا شناسه | `heritage_returns` | multi / heritage | US3، اعتبارسنجی/active-set و round-trip |
| src/data/source-terms.ts:heritageUseLabel; src/types/index.ts:ProjectTerms/heritageTerms | کاربری پس از مرمت / متن یا شناسه | `heritage_uses` | multi / heritage | US3، اعتبارسنجی/active-set و round-trip |
| src/data/source-terms.ts:heritagePaymentLabel; src/types/index.ts:ProjectTerms/heritageTerms | زمان دریافت قرارداد مرمت / متن یا شناسه | `heritage_payments` | multi / heritage | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.general_conditions | شرایط عمومی / متن یا شناسه | `general_conditions` | text / execution | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.special_conditions | شرایط تخصصی / متن یا شناسه | `special_conditions` | text / execution | US3، اعتبارسنجی/active-set و round-trip |
| src/lib/facts.ts:134-146; Opportunity.rights.subject | موضوع حق / متن یا شناسه | `rights_subject` | text / rights | US3، اعتبارسنجی/active-set و round-trip |
| src/lib/facts.ts:134-146; Opportunity.rights.title_parties | مالک عرصه / اعیان / متن یا شناسه | `rights_title_parties` | text / rights | US3، اعتبارسنجی/active-set و round-trip |
| src/lib/facts.ts:134-146; Opportunity.rights.holder | دارنده منافع / سرقفلی / حق کسب / متن یا شناسه | `rights_holder` | text / rights | US3، اعتبارسنجی/active-set و round-trip |
| src/lib/facts.ts:134-146; Opportunity.rights.original_lease | تاریخ رابطه اولیه و انتقال / متن یا شناسه | `rights_original_lease` | text / rights | US3، اعتبارسنجی/active-set و round-trip |
| src/lib/facts.ts:134-146; Opportunity.rights.regime | قانون حاکم و مستند / متن یا شناسه | `rights_regime` | text / rights | US3، اعتبارسنجی/active-set و round-trip |
| src/lib/facts.ts:134-146; Opportunity.rights.assignment | حق انتقال / رضایت / متن یا شناسه | `rights_assignment` | text / rights | US3، اعتبارسنجی/active-set و round-trip |
| src/lib/facts.ts:134-146; Opportunity.rights.key_money | شرح سرقفلی و دلیل پرداخت / متن یا شناسه | `rights_key_money` | text / rights | US3، اعتبارسنجی/active-set و round-trip |
| src/lib/facts.ts:134-146; Opportunity.rights.valuation | شرح ارزش مستقل حقوق / متن یا شناسه | `rights_valuation` | text / rights | US3، اعتبارسنجی/active-set و round-trip |
| src/lib/facts.ts:134-146; Opportunity.rights.permitted_use | کاربری و شغل مجاز / متن یا شناسه | `rights_permitted_use` | text / rights | US3، اعتبارسنجی/active-set و round-trip |
| src/lib/facts.ts:134-146; Opportunity.rights.renewal | شروط تمدید و تخلیه / متن یا شناسه | `rights_renewal` | text / rights | US3، اعتبارسنجی/active-set و round-trip |
| src/lib/facts.ts:134-146; Opportunity.rights.claims | دعاوی و حقوق ثالث / متن یا شناسه | `rights_claims` | text / rights | US3، اعتبارسنجی/active-set و round-trip |
| src/lib/facts.ts:134-146; Opportunity.rights.registration | نوع سند و ثبت / متن یا شناسه | `rights_registration` | text / rights | US3، اعتبارسنجی/active-set و round-trip |
| src/lib/facts.ts:134-146; Opportunity.rights.costs | هزینه انتقال و بدهی / متن یا شناسه | `rights_costs` | text / rights | US3، اعتبارسنجی/active-set و round-trip |
| src/types/index.ts:Opportunity.rights_occupancy | وضعیت تصرف / متن یا شناسه | `rights_occupancy` | enum / rights | US3، اعتبارسنجی/active-set و round-trip |

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
