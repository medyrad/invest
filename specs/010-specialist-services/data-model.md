# داده و اختیار

Draft.kind افزایشی به۹خدمت گسترش می‌یابد؛ raw، effective، missing، history، مالک و فایل‌های خصوصی همان زیرساخت‌اند. فیلدها namespace/نسخه مشخص و metadata شرط/واحد دارند. فیلدهای عددی داخلی با MoneyValue/Quantity ذخیره و ردیابی می‌شوند. مبلغ ارزی فقط مبلغ دقیق و ارز صریح است؛ تبدیل ندارد.

ServiceSubmission: UUID، Draft، draft_version، service_kind، schema_version/rule_version، snapshot مؤثر، evaluation، file refs، submitted_by/at؛ immutable و unique(draft,draft_version). Case.service_submission/service_draft nullable، در برابر opportunity/submission دقیقاً یک موضوع معتبر؛ یک پرونده فعال برای یک draft خدمت. Case.customer actor تاریخی اولیه است؛ اختیار مشتری سازمانی از نماینده جاری می‌آید، نه بازنویسی actor.

Report.snapshot.subject.type=service و source_draft/kind/versions/fields/display/evaluation/assumptions/files. core.Report ثابت و صاحب حساب است؛ مجوز جاری سازمان نیز برای خواندن دوباره بررسی می‌شود. Report بدون Case معتبر است. وضعیت فایل/مجوز دریافت مستقل از وجود لینک است؛ فایل دارای reference پاک‌سازی نمی‌شود.

مقادیر contact خصوصی از snapshot عملیاتی کارشناس/ادمین حذف می‌شوند؛ شماره فقط contact endpoint و رضایت گیرنده جاری. خدمات فاقد فرصت منتشرشده صاحب فرصت ساختگی ندارند؛ رضایت صاحب فرصت در آن حالت نامربوط است، رضایت کارشناس اختیاری و معتبر است.
