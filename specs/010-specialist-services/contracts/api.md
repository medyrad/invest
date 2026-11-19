# قرارداد S08@1

همان /api/v1 و envelope خطای فارسی fields/request_id، no-store خصوصی، session/CSRF برای mutation. ورودی بدشکل قبل lookup رد می‌شود.

عمومی:
- GET /services/schema/<kind>: نام/گروه/مراحل/فیلد/گزینه/when/required/unit/version/منبع.
- POST /services/evaluate/<kind>: raw، schema_version=1؛ بدون ذخیره، effective/missing/assessment، مقادیر مشتق دقیق/واحد/فرض و guard scope.
- GET /services/advisories و POST /services/advisories/<id>: تمام۷۸شناسه شامل۶۱پیکربندی اصلی و۱۷تکمیلی، role/answers/funding؛ سؤال فعال و اثر/مرور/مانع و راهنما.

خصوصی:
- workspace/drafts موجود با kind خدمت و schema_version=1، owner شخصی/سازمانی؛ save دارای key/version/routes=[]/heritage_enabled=false/values. delete/restore و فایل همان قرارداد موجود.
- POST /services/drafts/<id>/report با key/version: snapshot ثابت در Report؛ بدون پرونده.
- GET /services/reports/<id>/download: گزارش HTML مستقل و escaped فقط با مجوز جاری.
- POST /services/drafts/<id>/submit با key/version/text/previous: نقص فعال یا فایل ناپاک ارسال را رد می‌کند؛ assessment block مانع انتخاب ساختار نهایی است، خودکار مانع درخواست بررسی نیست. نتیجه یک رسید، service_submission و case موجود هسته.
- cases/<id> و actions/contact/private-file موجود با subject.type=service و snapshot redacted عملیاتی. follow-up خدمت از service_submission/previous صریح، بدون ساخت فرصت.

Field refs نسخه‌دارند؛ مبلغ داخلی canonical TOMAN و ورودی/ضریب صریح؛ API اعشاری رشته‌ای. عدد ارزی {status,source_value,value,currency:{code,version}} مستقل، بدون نرخ/تبدیل/aggregate ناهم‌ارز. صفر/unknown/not_applicable جدا. ماه مدت تقویمی است و روزسازی نمی‌شود. بازه/دقت۲۴+۹ و مقدار count صحیح طبق catalog؛ درصد ساده خدمات ReturnMetric/IRR نیست.

شرط پنهان raw را در چهارچوب مجاز نگه و از effective/evaluation/submission/report کنار می‌گذارد. دریافت نتیجه retry همان key+همان payload همان اثر؛ key با payload متفاوت409. پاسخ قدیمی UI پس از تعویض حساب اعمال نمی‌شود.

اسکان: هر خانوار و ماه مبنای مستقل، دو مقدار deposit_total و rent_total رشته تومان؛ aggregate نقدینگی فقط با همه داده معلوم و با عنوان مستقل، نه هزینه خالص. خیریه بدون ضریب مستند، اثر needs_expert_estimate. proposal کسری اعلامی با منابع/نیاز مستقل؛ کمبود/مازاد محاسباتی فقط وقتی هر دو مقدار هم‌معنا معلوم‌اند.

## قرارداد تثبیت‌شده تحویل
namespace خدمت با snake_case است؛ نمونه invest.service.ma_renewal. currency@1 یکی از USD/EUR/CNY/AED/OTHER است؛ OTHER نام دقیق currency_name را لازم دارد. مبلغ ارزی به همان ارز باقی می‌ماند. ظرفیت غیرنقدی Quantity نسخه۱ و واحد مجاز صریح دارد؛ noncash_unit تعریف متنی ظرفیت است، ضریب تبدیل نیست. SERVICE_HOUR و SESSION واحد پایه مستقل‌اند. اعداد حداکثر۲۴رقم صحیح و۹رقم اعشار در واحد canonical؛ شمارهای integer بدون اعشار و درصدهای محدود طبق FieldDefinition هستند؛ بیش‌دقت/بازه رد می‌شود. report_version=1 و زمان/قاعده/قرارداد در snapshot ثابت‌اند. تغییر فایل بدون افزایش نسخه پیش‌نویس، برای ارسال تازه نسخه سابق409 می‌دهد؛ UI پیش از ارسال/بسته ذخیره می‌کند.

فایل گزارش HTML مستقل، escaped، با فونت و نشان محلی و CSP بدون اجرای script/شبکه خارجی است. سند تاریخچه دریافت‌شده با ویرایش بعدی عوض نمی‌شود. نمونه‌های بین‌المللی و الگوی سیروس۵ تاریخی‌اند، اعتبار جاری یا پذیرش مالی نیستند. کمک در این سامانه درخواست بررسی داخلی است؛ جای ثبت رسمی فراخوان یا انتقال پول نیست.

بسته دارای پیوست: پاسخ report، در صورت داشتن فایل، download را به `/services/reports/<id>/package` می‌دهد؛ HTML مستقل در `/download` باقی است. ZIP شامل report.html، manifest.json نسخه۱ و محتوای پاک/مجاز فایل‌ها با نام UUID امن است؛ نام اصلی فقط داده manifest است. در دریافت بسته، اختیار جاری و وضعیت clean دوباره بررسی می‌شوند؛ قرنطینه/فایل مفقود409 می‌دهد. بسته، درخواست ایجاد نمی‌کند و receipt آن از ارسال صریح جداست.

FIX-01: کنترل اختیار و تولید کامل HTML/ZIP در یک بخش تراکنشی سازمان→فایل سری می‌شوند؛ جانشینی زودتر،403 و فایل pending/قرنطینه/حذف نامجاز،409 می‌دهد. بایت پاسخ پیش از پایان این بخش در حافظه ساخته می‌شود و بعد ارسال می‌شود؛ streaming یا ابطال بایت ارسال‌شده وعده داده نمی‌شود. مقادیر boolean و شناسه ذخیره‌شده ثابت می‌مانند؛ برچسب مشتری بله/خیر و نام فارسی مرحله است.

COMP-EXPERIENCE: مصرف‌کننده راهنمای 009، `POST /services/advisories/:raw_id` را با role/funding/answers می‌خواند و تا پاسخ نسخه۱ دانلود را فعال نمی‌کند. preview و snapshot هسته از همان effective_answers/questions/guidance استفاده می‌کنند؛ JSON ضمیمه جای HTML خواندنی نیست. انتخاب‌گر `land-preparation.types` دو گروه مرجع «عملیات و مطالعات آماده‌سازی» و «توسعه زمین، خدمات مالکیتی و حفاظت ملک» دارد، ولی ترتیب انتخاب مؤثر واحد باقی می‌ماند.
