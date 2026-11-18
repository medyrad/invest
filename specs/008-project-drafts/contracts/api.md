# قرارداد خصوصی A1 — /api/v1/workspace
همه پاسخ‌ها no-store/private؛ نشست Cookie فعلی invest_session، درخواست‌های نوشتنی CSRF. JSON ناشناخته، NUL یا نسخه غلط400 با envelope error{code,message فارسی,fields,request_id}؛ بدون اختیار403/404، نسخه/idempotency409، سهمیه429. هیچ verified/status/public_revision/owner از payload ویرایش پذیرفته نمی‌شود.

| مسیر | روش / ورودی | خروجی |
| --- | --- | --- |
| schema | GET | schema_version1، fields، routes، source/unit refs |
| owners | GET | فرد، درخواست‌های خود و سازمان دارای اختیار جاری |
| organizations | POST {key,details} | درخواست pending؛ details نام رسمی، کشور، نوع، ثبت، اختیار امضا، نام/حدود/شروع و ends_on یا no_expiry صریح |
| organizations/{request_id} | POST {key,version,details} | تکمیل درخواست خود، بدون تصویب |
| drafts | GET ?trash=1 | فقط فهرست مجاز؛ deleted جدا |
| drafts | POST {key,kind:'project',schema_version:1,owner:{kind:'personal'} یا {kind:'organization',request_id}} | receipt شامل UUID/version؛ کلید ثابت |
| drafts/{id} | GET | raw خصوصی، effective فقط active، inactive keys، missing، version و files |
| drafts/{id} | POST {key,version,routes,heritage_enabled,values} | patch active فقط؛ values طبقschema، null حذف صریح فعال؛ مقادیر غیرفعال ورودی اثر ندارند، خام قبلی حفظ می‌شود |
| drafts/{id}/delete یا restore | POST {key,version} | حذف نرم/بازیابی۳۰روزه، اختیار فعلی |
| files/reserve | POST {key,target_type:'draft' یا 'request',target_id,kind:'image' یا 'document',name,size,sha256,replaces:null یا UUID} | reservation UUID؛ سقف پیش از stream |
| files/{id}/content | PUT application/octet-stream، بدنه bytes دقیق | receipt؛ checksum و سقف stream؛ تکرار همانbytes بی‌مصرف مضاعف |
| files/{id}/download | GET | فقط clean/متصل/مجوز جاری؛ تصویر derivative، PDF attachment، nosniff/no-store |
| files/{id}/{retry,delete,restore} | POST {} | وضعیت واقعی، مجوز جاری و محدودیت زمانی |

مقدار دقیق هر field payload همان007، field.namespace=invest.opportunity.project و کلید/نسخه ازschema؛ source_value string؛ basis کامل. متن حداکثر۴۰۰۰، لیست حداکثر۵۰عضو/enum؛ unknown/not_applicable گزینه صریح؛ متن خام بدون تغییر پنهان نگه داشته می‌شود. readonly سیستم از schema حذف است، نه قابل جعل.
تعارض409 شامل current نسخه و DTO سرور؛ کلاینت ورودی خود را حفظ و بازبینی/بارگیری نسخه سرور را انتخاب می‌کند. خطای شبکه result نامعلوم، retry همان key/body؛ تغییر ورودی تا تعیین نتیجه مسدود.

ظرفیت: schema.fields.metric_quantity نسخه۲ و unit_options را معرفی می‌کند؛ نسخه۱ قبلی با همان سه واحد قدیمی معتبر می‌ماند. واحدهای ظرفیت مرجع نسخه۱ با base مستقل‌اند و تبدیل طول/مساحت/حجم/توان/تعداد حدس زده نمی‌شود؛ mapping.md فهرست دقیق را دارد.
