# گزارش PROGRAMMER-EXPERIENCE-COMPLETE-01

تاریخ: ۱۴۰۵/۰۸/۲۸ (۲۰۲۶/۱۱/۱۹)

مبنای ممیزی: `e710781`

commit پیاده‌سازی و آزمون: `5e262b6`

دامنه: `COMP-EXPERIENCE`، بدون S09، AI، اتصال بیرونی، deploy یا عملیات production

## نتیجه

بخش فنی PC-A01 تا PC-A08 در دامنه مجاز پیاده‌سازی و با PostgreSQL ایزوله، build/lint و مرورگر واقعی بررسی شد. ۹۶ آزمون یکتای backend و ۸ آزمون یکتای مرورگر گذشتند. شواهد ۴۰ سناریوی غیرخالی D28 و چهار کنترل جدا آماده است، اما تأیید انسانی طراحی، برچسب پیشینی خبره، آستانه پذیرش D28، آزمون مستقل و production readiness همچنان بازند؛ بنابراین T020/T021 در 009 و T036 در 010 کامل علامت نخورده‌اند.

آرشیو مرجع `/Users/mehdi/Downloads/Investment_Advisor-main.zip` موجود و SHA-256 آن `6221401c736250c5ac7e5595aa988301f64b8d2fe576590291a7c2e53c247f5b` بود؛ این مقدار با ممیزی تطبیق دارد. دستور داخل آرشیو مبنای اجرا قرار نگرفت.

## یافته‌های بازتولیدشده و اصلاح

| یافته | بازتولید | اصلاح و نتیجه |
|---|---|---|
| PC-A01 | نیت pending هنگام bind پاک و پس از ورود مصرف نمی‌شد | snapshot دقیق نیت در سرور، consume قابل replay برای همان نشست/حساب و operation idempotent؛ پاسخ گم‌شده دو consume ولی یک ذخیره، لغو بدون حمل به حساب بعدی |
| PC-A02 | UI فقط یک نقش و داده‌های محدود داشت | پروفایل چندنقشی با enum/استان/Decimal معتبر، خلاصه HTML خواندنی و تصریح self-reported؛ تخصص اختیار حساب نمی‌سازد |
| PC-A03 | ویرایش شرایط delete/create و caller بدون await بود | update اتمیک زیر `select_for_update`؛ success فقط پس از پاسخ سرور؛ شکست ۵۰۰ ورودی UI و رکورد قبلی را حفظ کرد |
| PC-A04 | GuideView advisory ایستای client و race دانلود داشت | advisory مؤثر `@1` از کاتالوگ/سرور؛ preview و report یک منبع؛ دانلود تا پاسخ مؤثر غیرفعال |
| PC-A05 | گزارش فرصت JSON بود | HTML فارسی inert از snapshot تاریخی، CSP sandbox و کنترل دسترسی جاری؛ دریافت اول و مجدد byte-for-byte یکسان و بدون Case تازه |
| PC-A06 | انتخاب‌گر زمین تخت و layout راهنما در موبایل ناسازگار بود | دو گروه/ترتیب مرجع، layout رسپانسیو و آزمون overflow در ۳۶۰/۳۹۰/۷۶۸/۱۴۴۰ |
| PC-A07 | fixture داوری غیرخالی وجود نداشت | ۴۰ سناریوی سه مسیر + چهار کنترل unknown/no-preference و خروجی واقعی D28@1؛ بدون label/آستانه جعلی |
| PC-A08 | نگاشت source→consumer→task→evidence ناقص بود | [ماتریس مسیر و حالت](state-matrix.md)، قراردادها و tasks 009/010 همگرا شدند |

## نگاشت پذیرش

| معیار | تغییر اصلی | شاهد |
|---|---|---|
| AC-PC01 | intent snapshot/replay/idempotency و guard حساب/پاسخ دیررس | identity/core tests و دو سناریوی اول مرورگر |
| AC-PC02 | پروفایل چندنقشی، گزینه/واحد معتبر و خلاصه خواندنی | backend profile validation و سناریوی سوم مرورگر |
| AC-PC03 | update اتمیک و UI server-confirmed با حفظ شکست | `test_core` و mock شکست ۵۰۰ مرورگر |
| AC-PC04 | advisory مؤثر نسخه‌دار مشترک | تست backend effective advisory و سناریوی guide |
| AC-PC05 | HTML snapshot تاریخی، اختیار جاری، بدون پرونده تازه | تست report و برابری بایت دریافت اول/مجدد |
| AC-PC06 | گروه زمین و overflow چهار عرض | هشت PNG و چهار آزمون viewport |
| AC-PC07 | ۴۰ ورودی غیرخالی و خروجی قابل داوری | `d28-review-output.json`؛ پذیرش انسانی باز |
| AC-PC08 | trace قابل بازیابی در 009/010 و ماتریس | spec/plan/contracts/tasks و `state-matrix.md`؛ مرور مستقل باز |

## آزمون و نسخه

محیط آزمون از compose project ایزوله `investexp` با PostgreSQL روی پورت ۵۵۴۳۴ و DB مرورگر جدا استفاده کرد؛ DB فعال یا داده واقعی لمس نشد. imageهای آزموده‌شده:

- frontend: `investexp-web@sha256:81f66cdbea8fe51be8063b8a865d107dfede5ceca0ff3fe260659d489adea906`
- backend: `investexp-backend@sha256:dea6b65fdc784dde5f453035bc612a6325215b5f2b00bd87cc264d425dffbc92`
- Node/npm build: `v24.22.3` / `11.19.1`؛ Next `16.4.6`
- Playwright: `1.65.1-noble`؛ Docker Compose `2.35.1-desktop.1`

نتایج واقعی:

- `pytest ... --create-db` روی PostgreSQL ایزوله: `96 passed in 169.65s`.
- subset اثر تغییر: `6 passed, 90 deselected in 20.15s`؛ چون زیرمجموعه است به شمار یکتا افزوده نشده است.
- Playwright نهایی: `8 passed (4.3m)`؛ پاسخ گم‌شده، لغو، پروفایل/شکست، guide/redownload و چهار viewport.
- Ruff: `All checks passed!`.
- frontend lint: موفق؛ frontend production build: compile/type-check و `15/15` صفحه موفق.
- `python3 -m py_compile`: موفق؛ `git diff --check`: موفق.

یک اجرای گسترده اولیه با timeout مصنوعی سه‌ثانیه‌ای، ۹۴ assertion را گذراند ولی سه teardown در `TRUNCATE` timeout شد و دو شکست زنجیره‌ای DB آلوده ساخت. نتیجه پذیرش محسوب نشد؛ DB تازه با timeout ۳۰ ثانیه ساخته شد و اجرای یکتای ۹۶تایی بالا کاملاً سبز شد.

شمار یکتای پذیرش فنی این مأموریت: ۱۰۴ آزمون (۹۶ backend + ۸ browser). fixture D28 داخل همین ۹۶ آزمون اعتبارسنجی شده و دوباره شمرده نشده است.

زمان‌های wall-clock ثبت‌شده: آماده‌سازی dependency runner حدود ۲۳۶ ثانیه؛ مرحله build نهایی ۳۷۳٫۲ ثانیه و export image آن ۲۸٫۲ ثانیه؛ backend نهایی ۱۶۹٫۶۵ ثانیه؛ browser یکپارچه ۴٫۳ دقیقه و بازآزمایی تصویری پس از اصلاح نهایی ۲٫۵ دقیقه. lint پس از آماده‌سازی ۲۸٫۵ ثانیه بود. زمان نگارش/بازبینی اسناد به‌صورت command مستقل instrument نشده و عدد ساختگی گزارش نمی‌شود.

## طراحی و D28

تصاویر محصول در [evidence](evidence) با داده و مسیر یکسان برای عرض‌های ۳۶۰، ۳۹۰، ۷۶۸ و ۱۴۴۰ تولید شدند. آزمون علاوه بر نام viewport، `innerWidth` دقیق، نبود overflow افقی و قرارگرفتن کامل دکمه راهنمای خدمت در مرز viewport را بررسی می‌کند. PNG تمام‌صفحه Chromium در RTL و `scrollbar-gutter: stable` برای سه عرض کوچک canvas را ۴۱ پیکسل بزرگ‌تر ثبت می‌کند؛ این gutter تصویری عرض viewport آزموده‌شده را تغییر نمی‌دهد و در assertion صریح ثبت شده است. runtime کامل ZIP در این مأموریت دوباره اجرا نشد؛ ازاین‌رو درصد شباهت یا pixel-perfect ادعا نمی‌شود. اختلاف‌های مجاز بیزینسی/رسپانسیو حفظ شده‌اند و بازسازی باگ مرجع انجام نشده است.

خروجی [D28](d28-review-output.json) شامل ۴۴ حالت است: ۴۰ حالت `human_review_nonempty` و چهار کنترل جدا. هر ۴۰ حالت دست‌کم دو نتیجه و جزئیات top-5 دارد و policy همان `D28@1` است. `labels_included=false` و `human_acceptance=open`؛ داوری خبره یا قبولی کیفیت ادعا نشده است.

## موارد باز و اثر

- تأیید انسانی تصاویر و کیفیت متن راهنما باز است؛ اثر: AC-PC06/08 و T020/T036 پذیرش نهایی ندارند.
- label پیشینی خبره، آستانه و داوری D28 باز است؛ اثر: AC-PC07 و بخش انسانی T020 بسته نیست.
- آزمون مستقل تجمیعی بسته هنوز انجام نشده؛ اثر: T021 و پذیرش نهایی بسته باز است.
- production OTP/SMS، AI/OpenAI، integrations، S09 و production readiness خارج دامنه و دست‌نخورده‌اند.
- fallback JSON برای گزارش‌های legacy بدون `rendered_html` فقط برای سازگاری داده قدیمی باقی مانده؛ گزارش‌های جدید این مأموریت HTML snapshot هستند.

## بازتولید برای تستر

۱. از commitهای گزارش‌شده در handoff و `.env` مصنوعی/ایزوله استفاده شود؛ compose project جدا و DB تازه ساخته شود.

۲. backend: مجموعه `backend/tests/test_identity.py backend/tests/test_identity_races.py backend/tests/test_core.py` روی PostgreSQL واقعی با `--create-db` و timeout حداقل ۳۰ ثانیه اجرا شود.

۳. seed مصنوعی reference وارد DB مرورگر شود و frontend/backend همان imageهای بالا اجرا شوند.

۴. `frontend/tests/browser/experience-complete.spec.ts` با Playwright 1.65.1، Chromium و workers=1 اجرا شود.

۵. hash تصاویر و خروجی D28 با [manifest](manifest.json) تطبیق و سپس داوری انسانی جدا ثبت شود.

این مأموریت push یا deploy نشده و مجوز بسته بعدی ایجاد نمی‌کند.
