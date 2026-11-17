# نگاشت محدود و ظرفیت

منبع فقط `.tools/reference/advisor` تطبیق‌داده‌شده با ZIP اصلی است؛ مسیرهای زیر مسیر داخل ZIP هستند. namespace مقصد از معنای دقیق داده آمده، نه نام شبیه. نسخه تمام تعاریف۱ است. تمام مبالغ ورودی رشته با۹اعشار؛ داخلی تا۲۴رقم صحیح و۹اعشار، غیرمنفی؛ مقدار قطع نمی‌شود. در نمونه‌های مرجع مبالغ میلیاردی مانند minCapital=1000 و2500 و میلیون‌های monthlyRent=120 با این ظرفیت پوشش می‌یابند؛ سقف ظرفیت فنی، حد انتشار یا پیشنهاد مالی نیست.

| namespace.key | منبع و محل | معنا / واحد ورودی | قرارداد و محدودیت |
|---|---|---|---|
| invest.opportunity.project.min_capital | src/types/index.ts:41–42، src/lib/listings.ts:20–21/37 | حداقل سرمایه ورود، میلیارد تومان | money، BILLION_TOMAN@1→TOMAN@1؛ null=unknown؛ صفر به معنی رایگان نیست |
| invest.opportunity.project.budget | src/types/index.ts:43–44، src/lib/listings.ts:20–21 | نیاز مالی کل طرح، میلیارد تومان | money؛ جای min_capital نیست؛ source fallback نمایش به alias تبدیل نشد |
| invest.opportunity.project.monthly_rent | src/types/index.ts:81–82 | اجاره ماهانه، میلیون تومان | money؛ هزینه دوره‌ای، نه ودیعه یا قیمت کل؛ مقدار سالانه ساخته نمی‌شود |
| invest.opportunity.fund.minimum_investment | src/types/index.ts:95–98، src/lib/listings.ts:55–57 | حداقل ورود صندوق، میلیون تومان | money؛ namespace جدا از پروژه؛ forecast درصد، اصل سرمایه نیست |
| invest.opportunity.project.execution_months | src/types/index.ts:45، src/lib/listings.ts:26–27 | مدت اجرا، ماه | quantity MONTH؛ ۰..ظرفیت فنی،۹اعشار؛ مبنای شروع در منبع معلوم نیست، unspecified و غیرقابل مقایسه تا تعیین آن |
| invest.opportunity.project.payback_years | src/types/index.ts:46، src/lib/listings.ts:24–25 | دوره بازگشت، سال | quantity YEAR؛ مدت بازگشت≠IRR؛ بدون تبدیل سال/ماه/روز |
| invest.opportunity.sale.area | src/types/index.ts:103–104 و src/lib/listings.ts:70–90 | مساحت، مترمربع در نمایش مورد فروش | quantity SQUARE_METRE؛ با «مساحت عرصه» فیلتر src/data/fields.ts:57 هم‌نام‌سازی نمی‌شود |
| invest.opportunity.project.irr | src/types/index.ts:86–87 و src/data/fields.ts:24–26 | IRR اعلام‌شده، درصد؛ project/equity basis جدا | return PERCENT و return_type=irr؛ نرخ ساده زیر این فیلد رد می‌شود؛ بازه فنی signed،۹اعشار؛ منبع فاقد تاریخ/observation/source و افق کامل است؛ known ناقص رد می‌شود، این metadata جعل نمی‌شود و IRR تولید نمی‌گردد |

required به حضور عضو در type مرجع اشاره دارد، نه الزام UI آینده: minCapital/paybackYears کلید لازم ولی nullable؛ بقیه اختیاری. همه unknown/not_applicable را صریح پشتیبانی می‌کنند؛ شرایط مسیر و نمایش فعلی فقط metadata است، تصمیم فرم S05 نیست.

Unit registry علاوه بر این موارد DAY، KILOGRAM و ITEM و USD را فقط برای قرارداد صریح نوع مقدار/ارز دارد؛ در این بسته فیلد خدمت برای آن‌ها نگاشت نشده. ITEM صحیح است، USD پایه مستقل بدون نرخ؛ واحد ناشناخته/نسخه دیگر حدس زده نمی‌شود. default unit فیلد صریح است ولی API حذف unit را نمی‌پذیرد.

کنترل ظرفیت روی fixture نسخه‌دار مشتق از همان مرجع: minCapital تا۴۰۰۰ میلیارد، budget تا۵۶۰۰ میلیارد، monthlyRent=۱۲۰میلیون، حداقل صندوق تا۵۰میلیون، اجرا تا۳۶ماه، بازگشت تا۱۱سال و مساحت تا۸۰۰۰مترمربع؛ همگی بدون اعشار در رکوردهای حاضر. این شاهد نمونه‌هاست، نه نگاشت کامل یا حد تجاری. فایل source-capacity.json در شواهد تحویل، شمار هر مقدار را نگه می‌دارد.
