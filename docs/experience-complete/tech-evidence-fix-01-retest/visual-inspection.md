# ثبت مشاهدهٔ بصری مستقل

تاریخ: ۲۰۲۶-۱۱-۲۰

همهٔ ۱۳ تصویر اصلاح تحویلی با viewer تصویر باز شدند. علاوه بر آن capture مستقل proposal در مرورگر واقعی گرفته و باز شد. این ثبت، مشاهدهٔ فنی route/state است و امضای انسانی طراحی یا pixel-perfect محسوب نمی‌شود.

| شاهد | مشاهدهٔ route/state | نتیجه |
|---|---|---|
| `design-proposal-summary-360.png` | proposal، جمع‌بندی | مطابق |
| `design-proposal-summary-768.png` | proposal، جمع‌بندی | مطابق |
| `design-foreign-investment-step1-360.png` | foreign-investment، گام اول | مطابق |
| `design-foreign-investment-step1-390.png` | foreign-investment، گام اول | مطابق |
| `design-foreign-investment-step1-768.png` | foreign-investment، گام اول | مطابق |
| `design-ma-renewal-step1-360.png` | ma-renewal، گام اول | مطابق |
| `design-ma-renewal-step1-768.png` | ma-renewal، گام اول | مطابق |
| `design-charity-summary-390.png` | charity، جمع‌بندی | مطابق |
| `design-charity-summary-768.png` | charity، جمع‌بندی | مطابق |
| `design-library-360.png` | library، همهٔ accordionها بسته | **نامطابق با metadata `accordion-open`** |
| `design-library-390.png` | library، همهٔ accordionها بسته | **نامطابق با metadata `accordion-open`** |
| `design-library-768.png` | library، همهٔ accordionها بسته | **نامطابق با metadata `accordion-open`** |
| `design-library-1440.png` | library، همهٔ accordionها بسته | **نامطابق با metadata `accordion-open`** |
| `independent-proposal-summary-360.png` | proposal، جمع‌بندی؛ دادهٔ مصنوعی مستقل | مطابق اجرای تازه |

علت قابل بازتولید چهار مورد library در runner تحویلی نیز دیده می‌شود: accordion نخست پیش از capture باز است، runner آن را click می‌کند و پس از بسته‌شدن تصویر می‌گیرد، اما state ثابت `topic-index;accordion-open` را در metadata می‌نویسد. ماتریس نیز state ردیف را `list;search;empty` و evidence state را `topic-index;accordion-open` ثبت کرده است؛ بنابراین هم پیوند row→evidence و هم ادعای state خود capture ناسازگار است.
