# مدل محدود

UnitDefinition: code+version unique، kind، base_code/base_version، currency برای پول، factor دقیق مثبت و scale≤9. FieldDefinition: namespace+key+version unique، kind، واحد پیش‌فرض و refs مجاز، min/max، decimal_places، required/allow_unknown/allow_not_applicable، source_path/locator/meaning، visibility_rule توصیفی و inactive_effect=exclude. تعریف منتشرشده UPDATE/DELETE ندارد.

MoneyValue/Quantity/ReturnMetric: definition FK و unit FK با PROTECT، status، value/source_value nullable numeric، conversion_factor مثبت، base_code/base_version snapshot و basis nullable JSON. known دقیق و رابطه value=source×factor؛ غیرknown هر دو null. مقدار تا سقف۲۴+۹، شمارش scale0. Money بدون basis؛ Quantity مدت start_basis یا unspecified؛ Return basis version۱، metric_type/period/horizon/basis_date/price_basis/scope/observation/source، known فقط با کامل‌بودن. ثبت بازده، محاسبه IRR نیست.

نوع بازده return_type در تعریف فیلد ثبت می‌شود؛ فیلد project.irr فقط irr می‌پذیرد، نه نرخ ساده. واحد horizon نیز ref صریح code/version است. SQL ارتباط نوع/واحد/حدود و return_type رکورد known را کنترل می‌کند؛ اجرای شرط نمایش فرم آینده در این بسته نیست.
