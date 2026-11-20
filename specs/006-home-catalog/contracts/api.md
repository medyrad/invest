# قرارداد کاتالوگ

GET /api/v1/catalog/taxonomy → {version,groups:[{id,name,icon,image,fullNames,subtypes:[{id,name,examples,sources,includes,image}]}]}.
GET /api/v1/catalog/geography → {version,provinces:[{id,name,counties:[{id,name,cities:[{id,name}]}]}]}؛ شهرستان با شهر یکی نیست؛ cities ناقص منبع صریح است.
منبع یکتای فرصت برای UI، `GET /api/v1/core/opportunities` و فقط revision منتشرشدهٔ سرور است. قرارداد قدیمی `/api/v1/catalog/preview` و fixture آن در مأموریت `PROGRAMMER-RUNTIME-HOME-LOADING-FIX-01` بازنشسته شد تا fallback پنهان یا دو منبع حقیقت وجود نداشته باشد. دادهٔ مصنوعی development/test نیز از draft، بررسی و publication واقعی عبور می‌کند و در public فیلتر می‌شود.

انتخاب‌ها client memory و فقط از DTO مجاز؛ parent تغییر کند child نامعتبر پاک شود. مقصدهای /opportunities و /assistant و /compare و /saved و /tools هنوز وابستگی مراحل بعدند؛ صفحات واضح موقت، بدون ذخیره/امتیاز یا ادعای ارسال.
