# قرارداد

GET /api/v1/catalog/value-definitions: version=invest-values-v1، units و fields با refs نسخه‌دار و حدود اعشاری رشته‌ای.
POST /api/v1/catalog/values/normalize (CSRF موجود): {field:{namespace,key,version},unit:{code,version},status,source_value:string|null,basis:object|null}. همه کلیدها لازم، کلید اضافه رد می‌شود. خروجی: همین فیلد/واحد/وضعیت و source_value canonical، value:string|null، base_unit، base_version، conversion_factor:string، contract_version=1 و basis. هیچ نوشتن عمومی انجام نمی‌شود. server عامل را از تعریف می‌گیرد؛ عامل ورودی یا مقدار نهایی جعلی پذیرفته نمی‌شود.

خطای400 envelope موجود با code، message فارسی و fields؛ نسخه ناشناخته/واحد نامجاز/بیش‌دقت/ابهام/مبنای ناقص جدا. مبنای Return شامل version=1، metric_type=irr|simple_rate|effective_rate، period=annual|monthly|total، horizon={value:string,unit:{code:DAY|MONTH|YEAR,version:integer}}، basis_date=YYYY-MM-DD، price_basis=nominal|real، scope=project|investor، observation=forecast|observed|claimed، source متن غیرخالی. horizon تبدیل تقویمی ندارد.

S04-04: هر متن دارای NUL با code=nul_not_allowed و fields[مسیر دقیق مانند field.namespace یا basis.horizon.unit.code] پیش از lookup، HTTP400 می‌گیرد. ورودی معتبر و بدون ذخیره بودن normalize تغییر نمی‌کند. قواعد basis این قرارداد در مرز INSERT/UPDATE دیتابیس نیز لازم‌اند؛ پول/Quantity غیرمدت null، مدت start_basis لازم و canonical، Return غیرknown null یا basis کامل؛ Return known فقط basis کامل.
