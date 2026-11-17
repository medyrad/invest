# قرارداد API v1 — پیش‌نویس مرزها

این سند مسیر و رفتار پیشنهادی را مشخص می‌کند؛ OpenAPI ماشین‌خوان و schema دقیق هر فرم باید در تسک مقصد تولید و با آزمون قرارداد کنترل شود. وجود این فایل به معنی API پیاده‌شده نیست. B01–B04 در D25–D29 مصوب‌اند؛ B05–B08 و schema دقیق قبل از endpoint وابسته بسته می‌شوند.

## قواعد مشترک

- مبدأ مشترک `/api/v1`؛ JSON UTF-8؛ نشست سروری HttpOnly، CSRF برای تمام mutationها شامل OTP و ورود؛ احراز هویت جدا از مجوز موجودیت.
- خطا: `{ "error": { "code": "stable_code", "message": "متن فارسی", "fields": {}, "request_id": "opaque" } }`. شماره/OTP/کلید یا جزئیات خصوصی در خطا و log نباشد.
- 400 ورودی نامعتبر؛ 401 نشست لازم؛ 403 اختیار ناکافی؛ 404 منبع ناموجود یا غیرقابل مشاهده؛ 409 تعارض نسخه/کلید تکرار؛ 422 ترکیب بیزینسی نامعتبر؛ 429 سهمیه/تلاش همراه retry_after؛ 503 قطع سرویس قابل بازیابی.
- داده‌های عمومی فقط revision منتشرشده؛ اطلاعات خصوصی cache اشتراکی نشوند. تاریخ ISO8601 UTC؛ شناسه opaque؛ پاسخ‌های لیست `{items,next_cursor}` با ترتیب پایدار و tie-break شناسه. دادهٔ صفر و null یکی نیست.
- پول طبق D29: `{value: "15000000000", unit_code: "TOMAN", unit_definition_version: "toman-v1", status: "known"}` نمونهٔ شکل پیشنهادی؛ TOMAN کد داخلی برنامه است، نه ISO. مقدار دقیق و واحد ورودی/ضریب تبدیل ثبت شود؛ نام فیلد/نسخه قرارداد در مقصد قفل شود. `unknown/not_applicable` مقدار عددی ندارند؛ ارز متفاوت بدون تبدیل مصوب جمع یا رتبه‌بندی مالی نشود.
- ویرایش `If-Match` با version؛ ارسال پرونده/اقدام حساس `Idempotency-Key`. payload یکسان همان نتیجه و کلید با payload متفاوت 409؛ scope کلید حساب/عملیات. عمر کلید باید حداقل پنجره retry تعریف‌شده در spec قابلیت باشد.
- ورودی unknown field برای عملیات حساس رد شود؛ فیلد مالک/role/status/public_revision با patch عمومی تغییر نکند. شناسهٔ غیرقابل‌حدس جای مجوز نیست.

## endpointها و پذیرش

| روش و مسیر | ورودی/خروجی مهم | مجوز و تست مرزی |
|---|---|---|
| GET /auth/csrf | آماده‌سازی CSRF برای جریان ناشناس | cache عمومی نشست نشود |
| POST /auth/otp/challenges | mobile → challenge_id, expires_at؛ فقط test mode: delivery.code برای همان جریان | rate limit اتمیک؛ پاسخ عمومی OTP ندارد؛ login CSRF |
| POST /auth/otp/verify | challenge_id, code → session + user safe view | expiry/attempt/replay و bind جریان؛ rotate session |
| POST /auth/logout و GET /me | پایان نشست؛ اطلاعات مجاز حساب | CSRF خروج؛ نشست باطل‌شده کار نکند |
| POST /organizations و /organizations/{id}/representation-submissions | مشخصات و attachment refs → pending review | نماینده/مدرک خودش؛ draft بدون approval مجاز |
| POST /admin/representation-reviews/{id}/decision | approved/rejected, reason, expected_version | بررسی‌کننده؛ رقابت و تاریخچه |
| GET /catalog و /form-schemas/{kind} | گروه/شهر/schema_version/واحد/شرط | تعریف نسخه‌دار؛ تمام فیلدها نگاشت شوند |
| POST /owner/opportunities؛ PATCH /owner/revisions/{id} | owner, kind, schema_version, data → draft/version | مالک مرتبط؛ فرد/سازمان؛ public immutable |
| POST /owner/revisions/{id}/submit | expected_version → submitted | کامل‌بودن فرم؛ مجوز و تکرار امن |
| POST /admin/publication-reviews/{id}/decision | decision, reason, expected_version | نمایندگی و فرصت هر دو؛ تعویض اتمیک public_revision |
| GET /opportunities و /opportunities/{id} | cursor, criteria, sort → public revision + reasons | بودجه/مکان حذف نکنند؛ عدم افشای pending revision |
| POST /matching/evaluate | criteria, schema_version → policy_version, score, coverage, reasons, results | سرور امتیاز دهد؛ فرمول B02؛ unknown توضیح دارد |
| POST /comparisons | ids[2..4], criteria → kind, revisions, typed metrics, units, unknowns | رد mixed/duplicate/withdrawn؛ شاخص هر نوع جدا |
| POST /enquiries | نوع جریان، revision یا draft، snapshot_version، message، consent مستقل → receipt/id/status | explicit user action؛ no consent مجاز؛ stale revision و retry |
| GET /enquiries و /enquiries/{id} | پرونده‌های مجاز، snapshot، تاریخچه/پیام | صاحب فرصت خودکار مجاز نیست؛ phone حذف بدون consent |
| POST /admin/enquiries/{id}/assign | expert_id, expected_version | فقط ادمین؛ کارشناس قبلی دسترسی از دست بدهد طبق B01 |
| POST /enquiries/{id}/messages و /transitions | body/attachment یا action/version | اعضای مجاز و transition معتبر؛ owner injection رد |
| PUT /enquiries/{id}/contact-consent | recipient_scope, granted, text_version → وضعیت جاری | فقط subject؛ گیرنده نام‌برده و رضایت مستقل صاحب فرصت؛ لغو فوری دسترسی بعدی طبق D26؛ حفظ تاریخچه |
| GET/PUT/DELETE /workspace/{saved-listings,saved-searches,profile}/{id} | دادهٔ متعلق به حساب و timestamp | همگامی دو دستگاه، جداسازی حساب، پروفایل نقش نمی‌دهد |
| POST/PATCH /service-drafts/{kind}/{id} | schema_version, answers → draft/version | نوع/واحد/شرط معتبر؛ پنهان‌شدن فیلد اثر قبلی را رفع کند |
| POST /reports | draft/revision + snapshot → report id/download | دانلود ≠ ارسال؛ snapshot و تاریخ/واحد ثابت |
| POST /attachments و GET /attachments/{id}/content | upload metadata/content و download کنترل‌شده | B07 محدودیت؛ mime/content validation؛ عدم مسیر عمومی |
| GET /notifications و POST /notifications/{id}/read | لیست مخاطب و read_at | دیگری نتواند بخواند/علامت بزند؛ کانال B06 |
| POST /assistant/conversations و /assistant/conversations/{id}/messages | متن/criteria → پاسخ + references + quota | مهمان محدود/حساب بیشتر؛ داده مجاز؛ مدل هیچ submit tool ندارد |
| GET /assistant/usage و PUT /admin/assistant/policy | وضعیت مصرف و سیاست نسخه‌دار | سقف اتمیک، admin-only؛ مدل و اعداد B05 |

## قرارداد ابزار دستیار

ابزارها فقط normalize_criteria، search_public_opportunities، get_public_opportunity و compare_same_kind هستند. schema خروجی دارای revision_id و مقادیر سروری است. متن فرصت untrusted data است؛ نمی‌تواند دستور ابزار یا مجوز ایجاد کند. گزینهٔ ثبت درخواست در UI مسیر عادی POST /enquiries با اقدام صریح کاربر را باز می‌کند. شناسه‌های خصوصی، شماره تماس و اسناد سازمان وارد context عمومی نمی‌شوند. خطا/سهمیه مسیر فرم را حفظ می‌کند؛ streaming در صورت انتخاب باید قطع اتصال و تسویه مصرف را تعریف کند.

## قابلیت‌های غایب از این قرارداد

پرداخت/قرارداد درون سامانه و جست‌وجوی بیرونی AI خارج دامنه مصوب‌اند. API بازآفرینی بدون مستند قابل ادعا نیست. گردش بستن/پیگیری مطابق D25 است؛ سیاست مدارک/تغییر نماینده طبق D27 و نوع/حجم/نگهداری/حذف فایل تابع B07 است؛ نبودن schema نهایی در این سند نباید با کدنویسی حدسی پر شود.


## الحاق قرارداد گردش مصوب D25

- POST /owner/opportunities/{id}/pause: مالک مرتبط، توقف فوری پذیرش جدید؛ POST /owner/opportunities/{id}/request-republish درخواست بازنشر را ثبت کند و خودش public را فعال نکند. تصمیم republish/suspend/restore فقط endpoint ادمین با علت/نسخه و کنترل مجدد شرایط انتشار.
- POST /enquiries در توقف/انقضای فرصت، خطای opportunity_unavailable بدهد؛ GET و messaging پرونده‌های قبلی طبق مجوز همچنان فعال باشند. وضعیت فرصت در پرونده و snapshot زمان ارسال جدا نمایش یابند.
- POST /enquiries/{id}/transitions: actionهای answer/request_information/cancel/confirm_close/admin_terminate مطابق actor؛ answer باید شناسه پاسخ انسانی و اقدام بعد داشته باشد. admin_terminate علت متمایز لازم دارد و solved محسوب نشود. کارشناس نمی‌تواند به‌جای مشتری confirm_close بفرستد.
- POST /enquiries/{id}/follow-ups: فقط درخواست‌دهنده مجاز، related_enquiry_id سروری و idempotency؛ در closed/cancelled پیگیری جدید مرتبط با رسید. POST messages برای صفحهٔ کهنهٔ بسته‌شده باید پاسخ روشن requires_followup یا رسید پیگیری مرتبط بدهد؛ متن با خطای خام گم نشود. مسیر دقیق UX تبدیل/تأیید در spec تفصیلی پرونده تعیین و تست شود.
- POST assign: ارجاع اتمیک فقط ادمین، قطع دسترسی قبلی؛ دسترسی تماس گیرنده قبلی به حساب تازه منتقل نشود. بدون رضایت جدید شماره در response نباشد.
- GET /enquiries/{id}: due_at، first_human_response_at، next_followup_at و وضعیت تأخیر/بستن مطابق مخاطب؛ تغییر کارشناس موعد پاسخ اول را reset نکند. PUT /admin/operations/readiness تنظیم مسئول، کارشناس فعال، تقویم/تعطیلی و جانشین؛ فعال‌سازی پذیرش عمومی با تنظیم ناقص خطای operational_readiness_required.
- زمان‌بند b01-close فقط answered واجد هفت روز تقویمی بدون پیام تازه را ببندد؛ awaiting_user و بی‌پاسخ مشمول نیستند. تقویم روز کاری برای هدف پاسخ اول جدا از هفت روز تقویمی بستن است. worker/job و endpoint هر دو تراکنش و نسخه و تکرار امن لازم دارند.

این‌ها پیشنهاد قرارداد فنی برای اجرای قاعدهٔ مصوب‌اند؛ API یا تست runtime هنوز وجود ندارد.


## الحاق قرارداد تماس مصوب D26

- PUT /enquiries/{id}/contact-consent: recipient_id/type، granted، text_version و expected_version؛ سرور هویت گیرندهٔ تعیین‌شده را بررسی کند. client نمی‌تواند شناسه آزاد یا شخص نامعلوم را مجاز کند. هر گیرنده رکورد/تاریخچه مستقل؛ تعویض کارشناس grant جدید لازم دارد.
- GET /enquiries/{id}/contact: فقط شمارهٔ subject با رضایت معتبر برای actor و همان پرونده/هدف؛ شماره در پاسخ عمومی GET enquiry یا snapshot جاسازی نشود. مجوز دریافت تماس به‌خودی‌خود مجوز مشاهدهٔ پیام/مدرک پرونده نیست؛ صاحب فرصت فقط همین endpoint محدود را در صورت رضایت مستقل می‌بیند.
- لغو رضایت با PUT granted=false از همان صفحه، کنترل نسخه و حفظ تاریخچه؛ درخواست/خروجی جدید پس از لغو رد، پاسخ تماس private/no-store و لینک ثابت دورزننده مجوز ممنوع. دریافت قبلی داده قابل پس‌گرفتن نیست و UI این محدودیت را پیش از رضایت توضیح دهد.
- POST /account-support/contact-access: نقش مستقل مجاز امنیت/بازیابی حساب، target_user_id، purpose=security_incident/account_recovery، reason، شاهد احراز مجدد معتبر سرور؛ دسترسی از ادمین عملیاتی یا purpose پیگیری فرصت/بازاریابی رد شود. actor/target/purpose/time/result در audit و شماره از log عمومی حذف؛ هیچ grant به کارشناس یا تغییر ContactConsent ایجاد نشود.
- سناریوی خطا: recipient_not_assigned، consent_required/revoked، reauthentication_required و forbidden_purpose با envelope عمومی؛ پیام خطا نباید شماره هدف را لو بدهد. شماره در context AI/اعلان/خروجی پرونده بدون این قرارداد تزریق نشود.

مسیرها طراحی فنی پیشنهادی‌اند؛ خود سیاست D26 مصوب و تست‌های AC-D26 پیش‌نیاز پذیرش پیاده‌سازی‌اند.


## الحاق قرارداد نمایندگی مصوب D27

| عملیات پیشنهادی | ورودی/خروجی و کنترل سرور |
|---|---|
| POST /organizations/{id}/representation-submissions | نام رسمی/کشور/نوع/شناسه ثبت و refs خصوصی مدارک ثبت/اختیار امضا/معرفی‌نامه، حدود اختیار و تاریخ/اعتبار؛ متقاضی فقط درخواست/پیش‌نویس خودش را دارد و مالکیت سازمان موجود را تصاحب نمی‌کند |
| POST /admin/representation-reviews/{id}/decision | تصمیم و دلیل، شاهد مستقل با منبع/زمان/نتیجه، expected_version؛ نقص/تعارض مانع تأیید؛ self-review در سرور رد؛ مدرک با URL عمومی بازنگردد |
| POST /organizations/{id}/representation-changes | نامزد جانشین و refs خصوصی/دلیل، expected_version؛ تعویض عادی پرونده مستقل و نماینده فعلی تا تأیید معتبر است |
| POST /admin/representation-changes/{id}/decision | بررسی مستقل جانشین، expected_version؛ تأیید اتمیک، یک نماینده فعال، قطع اختیار قبلی و حفظ مالکیت/تاریخچه؛ تعارض هم‌زمان 409 |
| POST /admin/organizations/{id}/authority-holds | ثبت ادعای لغو/اختلاف با دلیل و شاهد؛ توقف اختیار نماینده و intake سازمان در تراکنش؛ رفع فقط با نتیجه رسیدگی ثبت‌شده و بازاعتبارسنجی اختیار |

هر فراخوانی مجوز نقش/سازمان را بررسی کند؛ جانشین pending به داده خصوصی قبلی دسترسی ندارد. فرصت active به‌تنهایی برای پذیرش درخواست کافی نیست: وضعیت اختیار سازمان هم بررسی شود. رفع توقف اختیار، انقضا/تعلیق مستقل فرصت را رفع نکند. پرونده قبلی و پیام کارشناس حفظ شوند. پاسخ عمومی فقط وضعیت لازم و نشان محدود نمایندگی دارد؛ مدارک، شواهد خصوصی یا ادعای تضمین مالی وارد payload عمومی/AI نشوند. رضایت شماره نام‌برده به جانشین منتقل نشود. مسیرهای فوق طراحی پیشنهادی‌اند؛ schema دقیق و نوع/حجم/نگهداری فایل در گیت مقصد تکمیل می‌شوند.


## الحاق قرارداد تطبیق مصوب D28

فهرست عمومی/ابزار search، دامنه مسیر و جست‌وجوی صریح عنوان/شناسه را از criteria اختیاری جدا بگیرند. نبود criteria مجاز است. سرور شرایط فعال و سهم وزن را تعیین می‌کند؛ score/وزن/وضعیت فرصتِ ارسالی کلاینت اختیار محاسبه یا انتشار نمی‌دهد. هیچ min_score یا strictLocation قدیمی موجب حذف فرصت مجاز نشود.

پاسخ پیشنهادی `{items,total_count,next_cursor,evaluation}`؛ evaluation شامل policy_version، criteria_hash، شرایط فعال/وزن و زمان مبناست. هر item شامل public_revision_id و match با score، coverage، status (no_preferences/insufficient_information/evaluated) و reasons با وضعیت met/unmet/unknown، وزن، مقدار/مبنای قابل‌مقایسه و علت است. شرط نامربوط به کل مسیر در evaluation روشن و قبل از محاسبه غیرفعال شود؛ برای یک رکورد مخرج کم نشود. W=0 مقادیر null؛ W>0 و K=0 مقادیر محاسباتی صفر و status اطلاعات ناکافی. نمایش درصد با برچسب میزان برآورده‌شدن ترجیحات و پوشش جدا، بدون ادعای احتمال سود.

cursor با نسخه سیاست، شرایط و زمان مبنا بسته شود؛ تغییر query با cursor قدیمی رد و بازاجرای روشن درخواست شود؛ نسخه‌ها خاموش مخلوط نشوند. روی داده ثابت ترتیب score دقیق نزولی، coverage نزولی، انتشار نزولی، شناسه ثابت بدون تکرار/افتادگی باشد. جزئیات انقضای cursor در قرارداد فنی مقصد تعیین شود؛ انقضای cursor مجوز تغییر خاموش مبنا نیست. ابزار AI همان خروجی سرور را مصرف و لینک ادامه نتایج را حفظ کند. شواهد کالیبراسیون/نمونه‌های بازبینی کارشناس و نگاشت واحد/معنای هر predicate پیش‌نیاز پذیرش‌اند؛ این outline جای schema نهایی نیست.


## الحاق قرارداد واحد و معنا مصوب D29

ورودی پول/کمیت دارای value رشته‌ای، status و واحد/تعریف نسخه‌دار باشد؛ known نیازمند مقدار و unknown/not_applicable فاقد مقدار عددی‌اند. واحد و ضریب تبدیل ورودی بدون حدس ثبت شوند. قرارداد دقیق دقت/حدود و normalization هر فیلد پیش از اجرای آن در schema نوشته شود؛ مقادیر مبهم/منفی غیرمجاز/بیش‌دقت رد، نه خاموش گرد شوند. نمایش میلیون/میلیارد مرجع از مقدار دقیق ساخته و تبدیل واحد آینده داده تاریخی را بازتفسیر نکند. بدون نرخ/منبع/تاریخ مصوب، مقایسه cross-currency نتیجه comparable=false با دلیل دهد؛ خود فرصت به این علت از دامنه جست‌وجو حذف نشود.

مقایسه بازده type/period/horizon/basis_date/nominal_or_real/project_or_investor/forecast_or_observed و منبع لازم دارد؛ نبود هم‌مبنایی، دلیل عدم مقایسه برگرداند و هیچ IRR ساختگی تولید نکند. فرم‌های خدمات schema_version داشته باشند؛ سرور شروط نمایش/کاربرد را مستقل از کلاینت محاسبه و پاسخ نامربوط را از effective_payload حذف کند. گزارش فقط snapshot واحد/داده/فرض/قاعده است و endpoint دانلود هیچ درخواست همکاری ثبت نکند.

اسکان دو مبلغ دقیق مستقل ودیعه برگشت‌پذیر و هزینه اجاره بدهد، نه مجموع با عنوان هزینه خالص. برآورد خیریه بدون source/date و هزینه/ظرفیت/دوره لازم، عدد نتیجه ندهد و needs_expert_estimate برگرداند؛ پیش‌نویس و درخواست صریح برای بررسی همچنان قابل انجام باشند. نام این فیلدها/وضعیت‌ها outline فنی است؛ D29 رفتار قطعی و schema هر خدمت در مقصد نهایی می‌شود.
