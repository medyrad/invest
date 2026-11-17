# قرارداد کاتالوگ

GET /api/v1/catalog/taxonomy → {version,groups:[{id,name,icon,image,fullNames,subtypes:[{id,name,examples,sources,includes,image}]}]}.
GET /api/v1/catalog/geography → {version,provinces:[{id,name,counties:[{id,name,cities:[{id,name}]}]}]}؛ شهرستان با شهر یکی نیست؛ cities ناقص منبع صریح است.
GET /api/v1/catalog/preview → {version,synthetic:true,enabled,listings:[Listing]}؛ enabled فقط test/development؛ public همیشه false/[] حتی اگر fixture در image باشد. readonly، no-store و خطای استاندارد API. رکورد فرصت واقعی ایجاد نمی‌شود.

انتخاب‌ها client memory و فقط از DTO مجاز؛ parent تغییر کند child نامعتبر پاک شود. مقصدهای /opportunities و /assistant و /compare و /saved و /tools هنوز وابستگی مراحل بعدند؛ صفحات واضح موقت، بدون ذخیره/امتیاز یا ادعای ارسال.
