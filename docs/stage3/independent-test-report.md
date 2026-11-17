# گزارش مستقل TEST-S03-02

تاریخ: ۲۰۲۶/۱۱/۱۷. **نتیجه: نیازمند اصلاح.** سه ایراد مشاهده شد؛ هیچ دورزدن احراز، دسترسی حساب دیگر یا مصرف مضاعف کد در آزمون‌های اجراشده مشاهده نشد. این نتیجه پذیرش نهایی S03 یا تأیید انسانی طراحی نیست.

## نسخه و محیط

- تمام **۱۱۰ فایل** تحویل با `docs/stage3/evidence/artifact-manifest.json` تطبیق داشتند؛ بررسی نهایی نیز اختلاف نداشت. شاهد: [version.json](independent-evidence/version.json)، [بررسی نهایی](independent-evidence/final-delivery-check.json).
- کد فعال بک‌اند روی `3108`: تطبیق ۲۳ فایل اجرایی با workspace، بدون اختلاف. image: `sha256:6ae9137490d77c617eaddc2dd013835036e27d8d4bb6f7ff422934e5d799b05d`.
- web فعال: image `sha256:0197aa3c9099bc704a7bfd6720e1a2efb080a7f52f43ce8d13907784ee168039`؛ build ID برابر `WVfAwNWeqFt0YD4q3IIWw`. تمام ۲۲ فایل مشترک static/public با build تازه یکسان بودند. سه manifest زیر پوشه build ID متفاوت نام داشتند؛ این اختلاف ناشی از شناسه build جداست و اختلاف محتوای bundle مشترک مشاهده نشد. [تطبیق فرانت](independent-evidence/frontend-image-comparison.json).
- image آزمون و browser-api نیز جدا تثبیت شدند: ۳۴ فایل Python در هرکدام با workspace یکسان بود. مقصد browser-api فقط `invest_browser` و حالت `test/notification` بود. [runtime](independent-evidence/runtime.json)، [image آزمون](independent-evidence/test-image.json)، [image مرورگر](independent-evidence/browser-image.json).
- Python 3.14.10، Django 5.2.19، psycopg 3.3.9، PostgreSQL 17.12؛ Node 24.22.3 و Chrome 151.0.7922.137. Git commit قابل استناد موجود نبود؛ مبنا hash فایل و image است.
- سفر نسخه تحویلی روی `http://127.0.0.1:3108` انجام شد. آزمون‌های گسترده مرورگر روی standalone تازه `3109` و DB مصنوعی جدا اجرا شدند؛ آن‌ها شاهد داده DB برنامه نیستند.

## آنچه اجرا شد

| فرمان / مجموعه | نتیجه اجرای مستقل | شاهد |
|---|---|---|
| `make test` | **۹۳ موفق، صفر ناموفق**؛ PostgreSQL واقعی، DB آزمون | [خروجی](independent-evidence/existing-backend.txt) |
| `PATH="$PWD/.tools/runtimes/node-v24.22.3-linux-x64/bin:$PATH" make check` | Ruff، format، migration drift، Django check، ESLint و TypeScript موفق | [خروجی](independent-evidence/existing-quality.txt) |
| `python3 docs/stage3/independent-tests/run-existing-browser.py` | **۲۸ موفق، صفر ناموفق**؛ تست‌های تحویلی بدون تغییر، چهار عرض | [خروجی](independent-evidence/existing-browser.txt)، [JSON](independent-evidence/existing-browser-results.json) |
| `docker compose --env-file .env -f deploy/compose.yaml run --rm -v "$PWD/docs/stage3/independent-tests:/independent:ro" test /app/.venv/bin/pytest -c /app/pyproject.toml /independent/test_independent_identity.py -q --tb=short` | **۳۰ موفق، صفر ناموفق** | [خروجی](independent-evidence/independent-backend.txt) |
| `python3 docs/stage3/independent-tests/run-independent-browser.py`؛ با standalone فعال روی3109 | **۱۰ موفق، ۲ ناموفق**؛ IT-001 و IT-002 | [خروجی](independent-evidence/independent-browser.txt)، [JSON](independent-evidence/independent-browser.json) |
| `node docs/stage3/independent-tests/browser-boundaries.cjs` با Node قفل‌شده | **۳ موفق، ۱ ناموفق**؛ IT-003 | [خروجی](independent-evidence/browser-boundaries.txt)، [JSON](independent-evidence/browser-boundaries.json) |
| `node docs/stage3/independent-tests/proxy-log-probe.cjs` | دو مشتری واقعی HTTP روی3108؛ هر دو صدور/ورود200؛ IP مشترک؛ header جعلی بی‌اثر؛ صفر افشای مقدار از۸ مقدار محرمانه بررسی‌شده در log همان بازه | [شاهد](independent-evidence/proxy-log-probe.json) |
| `node docs/stage3/independent-tests/visual-independent.cjs` | capture تازه مرجع3107 و تحویل3108 با مرورگر/viewport/حالت یکسان | [شاهد](independent-evidence/visual-comparison.json) |
| `docker compose --env-file .env -f deploy/compose.yaml exec -T backend /app/.venv/bin/python manage.py migrate --check` | موفق | [خروجی](independent-evidence/migration-check.txt) |

جمع مجموعه‌های دارای نتیجه pass/fail: **۱۶۵ موفق و ۳ ناموفق، در۱۶۸ مورد**. quality، probe و capture به این شمار افزوده نشده‌اند. اعداد از اجرای خود تستر هستند. هنگام ساخت ابزار مستقل، انتظار ناهمگام Escape/Back و انتخابگر عمومی alert اصلاح شدند؛ یک تلاش مقدماتی نیز به خطای route در ابزار ختم شد. این تلاش‌ها شاهد باگ محصول محسوب نشده‌اند؛ جدول، اجرای نهایی ابزار اصلاح‌شده را گزارش می‌کند.

### پوشش رفتار

- قالب‌های09/+98/0098، ارقام فارسی/عربی، فاصله/خط تیره؛ رد حروف، bidi، newline و طول اضافه، بدون مصرف سهمیه شماره برای ورودی نامعتبر.
- کد صحیح/غلط، پنج خطا و سپس رد کد صحیح همان challenge؛ کد واقعاً تولیدشده با صفر ابتدایی روی PostgreSQL، بدون patch مولد کد؛ paste واقعی clipboard در Chrome.
- **گذشت واقعی۱۲۰ثانیه**: حذف اعلان کد و غیرفعال‌شدن ورود در UI، پاسخ سرور410 `challenge_expired`، سپس resend و ورود موفق با کد تازه در عرض390. مرزهای دقیق سرور علاوه بر این با ساعت کنترل‌شده روی PostgreSQL آزموده شدند.
- دو حساب/جریان، اتصال کد به جریان، استقلال دستگاه‌ها؛ آخرین ظرفیت شماره و مصرف هم‌زمان با connectionهای متفاوت PostgreSQL؛ حداکثر یک مصرف موفق و یک نشست.
- retry صدور پس از انقضا/مصرف/جایگزینی/لغو/خروج/ابطال/انقضای جریان؛ نبود صدور یا TTL تازه و نبود اعلان کد در رسیدهای نهایی. گم‌شدن پاسخ صدور اولیه با همان کلید بازیابی شد.
- گم‌شدن پاسخ verify با cookie دریافت‌شده در مجموعه تحویلی؛ نبود cookie در آزمون مستقل با حذف پاسخ Set-Cookie از مسیر شبیه‌سازی شد: نشست قابل بازیابی نبود و جریان تازه لازم شد. replay نشست تازه نساخت.
- ورود، reload، خروج و cookie قدیمی روی3108 موفق؛ Escape، focus trap/return، کندی شبکه و منع submit مضاعف؛ ویرایش شماره، بستن/بازکردن و refresh.
- quota جریان/شماره/IP، مرز لغزان و عدم تمدید انتظار با درخواست ردشده؛ محدودسازی خطا و خروج دقیق از پنجره. رقابت ابطال با verify و سلب نقش با عملیات حساس، با قفل و connection واقعی PostgreSQL.
- CSRF مهمان و واردشده، رد فیلدهای role/assurance/sensitive/owner؛ جداسازی حساب؛ رد شاهد آزمایشی برای عملیات حساس. حالت public و provider نامشخص/نامتاح با تنظیمات موقت آزمون و adapter شبیه‌سازی‌شده بررسی شدند؛ سرویس یا env برنامه تغییر نکرد.
- no-store، نبود اسرار در audit/خطاهای بررسی‌شده و log بازه probe؛ بررسی storage مرورگر. این نمونه‌برداری ادعای نبود افشا در تمام رخدادهای ممکن نیست.

## باگ‌های مشاهده‌شده

### S03-IT-001 — زیاد — پاسخ گم‌شده resend از UI قابل بازیابی نیست

- **نیازمندی:** mission بخش۳ و FR-005؛ retry همان عملیات نباید صدور/سهمیه تازه بسازد و باید وضعیت همان challenge را بدهد.
- **پیش‌شرط:** مرحله کد فعال؛۶۰ثانیه واقعی گذشته و دکمه «دریافت کد تازه» فعال است.
- **بازتولید:** resend را بزنید؛ اجازه دهید پاسخ200 سرور ثبت شود ولی پاسخ به مرورگر نرسد؛ پس از خطای اتصال همان دکمه را دوباره بزنید.
- **انتظار:** retry همان کلید صدور پذیرفته‌شده را به کار ببرد و رسید/اعلان challenge تازه را بازیابی کند.
- **واقعیت:** کلیک دوم UUID تازه می‌سازد؛ سرور429 می‌دهد. UI رسید و اعلان قبلی را نگه داشته، درحالی‌که آن کد در سرور جایگزین شده است. مشتری کد تازه پذیرفته‌شده را نمی‌بیند و دوباره منتظر می‌ماند.
- **اثر:** اختلال مسیر ورود پس از خطای شبکه و مصرف بیهوده فرصت ورود. در این بازتولید، درخواست سوم صدور تازه نساخت؛ نباید این ایراد را ارسال سه پیامک یا نشست مضاعف نامید.
- **شاهد:** case `resend-lost-response-keeps-idempotency-key` و observation `same_key:false, retry_status:429` در [JSON](independent-evidence/independent-browser.json)؛ [تصویر](independent-evidence/lost-resend-retry.png).
- **پیشنهاد اصلاح/بازگشت:** کلید عملیات resend تا تعیین تکلیف همان عملیات حفظ شود؛ آزمون قطع پاسخ پس از پذیرش سرور، بازیابی همان challenge و ثابت‌ماندن تعداد IssueEvent انجام شود. کد محصول تغییر داده نشد.

### S03-IT-002 — متوسط — تب دوم پس از خروج هویت خصوصی کهنه نشان می‌دهد

- **نیازمندی:** سفر خروج و پاک‌شدن وضعیت خصوصی کلاینت؛ بررسی دو تب در مأموریت مستقل.
- **پیش‌شرط:** دو تب از همان browser context، هر دو وضعیت ورود یک حساب را نشان می‌دهند.
- **بازتولید:** در تبA خروج بزنید؛ به تبB برگردید؛ بدون reload وضعیت حساب را ببینید و `GET /auth/me` را فراخوانی کنید.
- **انتظار:** با فعال‌شدن دوباره تب، وضعیت ورود و نمایش شماره با نشست باطل‌شده همگام شود.
- **واقعیت:** me برابر `authenticated:false` است، ولی تبB همچنان «وارد شده‌اید»، شماره و دکمه «خروج» را نشان می‌دهد. reload وضعیت را اصلاح می‌کند.
- **اثر:** هویت خصوصی روی نمایشگر باقی می‌ماند و کاربر درباره حساب فعال گمراه می‌شود. دسترسی سروری برقرار نمانده و دورزدن logout مشاهده نشده است.
- **شاهد:** case `two-tabs-logout-clears-displayed-private-identity` در [JSON](independent-evidence/independent-browser.json)؛ [تصویر masked](independent-evidence/two-tabs-stale-identity.png).
- **پیشنهاد اصلاح/بازگشت:** رویداد همگامی بدون حمل secret و/یا بازبینی me هنگام بازگشت focus؛ همان آزمون دو تب بدون reload سبز شود. این بازبینی خودکار نباید idle را تمدید کند.

### S03-IT-003 — متوسط — وعده مطلق استفاده از شماره با D26 سازگار نیست

- **نیازمندی:** D26 و اصل اول constitution؛ تصمیم بیزینسی بر متن متعارض مرجع مقدم است.
- **بازتولید:** دیالوگ ورود را در هر عرض باز کنید و یادداشت پایین فرم را بخوانید.
- **انتظار:** متن، انتقال تماس با رضایت مستقل به گیرنده نام‌برده و استثنای محدود امنیت/پشتیبانی حساب را نفی نکند.
- **واقعیت:** متن بی‌قید «شماره شما فقط برای ورود استفاده می‌شود.» همچنان نمایش داده می‌شود.
- **اثر:** انتظار نادرست درباره کاربرد شماره. در S03 انتقال تماس اجرا نشده و هیچ افشای تماس در این آزمون مشاهده نشد؛ ایراد، صداقت وعده نمایش‌داده‌شده در نسبت با تصمیم مصوب است.
- **شاهد:** case `privacy-copy-compatible-with-D26` در [نتیجه](independent-evidence/browser-boundaries.json) و [crop تازه تحویل](independent-evidence/visual-invest-1440.png).
- **پیشنهاد اصلاح/بازگشت:** متن با تصمیم مصوب سازگار و به‌عنوان اختلاف مشخص متنی ثبت شود؛ آزمون محتوایی و تصویر تازه دیالوگ بازبینی شوند. مسیر واقعی D26 همچنان متعلق به S06 است.

## دو نقطه مشخص تحویل

**proxy و IP:** دو مشتری مستقل روی3108 با XFFهای متفاوت هر دو صدور و ورود200 گرفتند؛ دو IssueEvent مربوط به آن‌ها فقط یک `ip_digest` داشتند و هیچ‌کدام با header جعلی برابر نبود. رفتار با REMOTE_ADDR مصوب سازگار است. اثر محلی: بودجه۳۰صدور/۱۵دقیقه میان همه مشتریان این proxy مشترک است؛ فشار یک مشتری می‌تواند صدور مشتری دیگر را عقب بیندازد. در محیط آزمون، عبور از سقف فقط صدور تازه را محدود کرد و بررسی کد صادرشده موفق ماند. این موضوع به‌تنهایی دلیل رد تحویل آزمایشی نیست؛ استخراج IP از proxy واقعاً مورد اعتماد و ظرفیت/سیاست شبکه مشترک، گیت پیش از عرضه است. اعتماد به XFF دلخواه پیشنهاد نمی‌شود.

**فعالیت نشست:** در مرورگر، reload و استفاده معمول پوسته فقط me را فراخواندند و activity نداشتند؛ کلیک صریح «بررسی و تمدید نشست» activity را فراخواند. روی PostgreSQL، me و خواندن منبع خصوصی `last_activity` را تغییر ندادند؛ activity موفق تغییر داد و سقف مطلق حفظ شد. در آزمون HTTP جدا نیز تکرار me، هدر prefetch، health و ادعای `user_active=true` زمان فعالیت را عوض نکرد و نشست روی مرز۲۴ساعت منقضی شد؛ پس این درخواست‌ها نشست را نامحدود تمدید نمی‌کنند. بااین‌حال، **اتصال به کار طبیعی محصول اثبات نشده است**: پوسته فعلی سفر خصوصی دیگری ندارد و تنها عامل تمدید همان دکمه است. این محدودیت مشاهده‌شده است، نه ادعای باگ جدید برخلاف قرارداد «فقط activity». با اضافه‌شدن تعامل‌های مراحل بعد، اتصال آن‌ها و تفکیک polling/prefetch باید آزموده شود؛ وجود دکمه، شاهد آن پذیرش آینده نیست.

## UI و مرز پذیرش

- در۳۶۰،۳۹۰،۷۶۸ و۱۴۴۰، ورود با clipboard واقعی، صفحه‌کلید، focus، Escape و پیمایش انجام شد. در موبایل اعلان قابل مشاهده و ورودی/ورود با scroll و کلیک عادی قابل استفاده بودند؛ resend پس از انتظار واقعی و انقضا نیز اجرا شد. این‌ها صرفاً screenshot نبودند. [تصاویر چهار عرض](independent-evidence/independent-code-360.png)، [۳۹۰](independent-evidence/independent-code-390.png)، [۷۶۸](independent-evidence/independent-code-768.png)، [۱۴۴۰](independent-evidence/independent-code-1440.png).
- مقایسه تازه دسکتاپ با مرجع در۱۴۴۰×۱۰۰۰، فونت آماده، تصویر اول office، مرحله شماره خالی و reduced motion انجام شد؛ پس‌زمینه S04 خارج crop بود. [مرجع](independent-evidence/visual-reference-1440.png)، [تحویل](independent-evidence/visual-invest-1440.png).
- bounding box هر دو۹۶۰×۵۷۸ بود؛ ولی فایل crop مرجع۹۶۱ و تحویل۹۶۰پیکسل عرض دارد. هم‌پوشانی تصاویر pixel-identical نیست: حدود۳۹٫۳۴٪ پیکسل‌ها مقداری تفاوت و۳٫۹۳٪ اختلاف کانالی بیش از۱۶ دارند؛ متن آزمایشی نیز عمداً متفاوت است. [تحلیل خام](independent-evidence/visual-pixel-analysis.json). این اعداد معیار مصوب پذیرش نیستند؛ از ابعاد یا چند CSS، برابری کامل تصویر نتیجه نمی‌شود. هویت کلی حفظ‌شده دیده شد؛ تأیید انسانی همه حالات و طرح موبایل باز است.
- شش خانه، متن‌های آزمایشی و حالت‌های عملیاتی اختلاف مأموریت‌اند؛ اصلاح IT-003 نیز باید جدا ثبت شود. هیچ `human_visual_approved` یا وضعیت پذیرشی علامت زده نشد.

**پیش از پذیرش فنی S03:** اصلاح IT-001 تا IT-003 و اجرای بازگشت‌های مرتبط، سپس بازبینی انسانی تصاویر طبق گیت موجود. **وابسته به عرضه/مراحل بعد:** SMS و روش واقعی نقش حساس، ظرفیت و حمله توزیع‌شده، retention/بازیابی عملیاتی، S05 نمایندگی، S06 مسیر D26 و S07 ذخیره پایدار؛ نبود اجرای آن‌ها علت نتیجه «نیازمند اصلاح» این مأموریت نیست.

## فایل‌های افزوده، حفاظت از محیط و محدودیت‌ها

فقط همین گزارش اصلی، پوشه `docs/stage3/independent-evidence/` و این هفت فایل آزمون/اجرا افزوده شدند:

1. `independent-tests/test_independent_identity.py`
2. `independent-tests/browser-independent.cjs`
3. `independent-tests/browser-boundaries.cjs`
4. `independent-tests/proxy-log-probe.cjs`
5. `independent-tests/visual-independent.cjs`
6. `independent-tests/run-existing-browser.py`
7. `independent-tests/run-independent-browser.py`

مسیر این فهرست نسبت به `docs/stage3/` است؛ فهرست دقیق شواهد و hash افزوده‌ها در `independent-evidence/added-files.json` ثبت می‌شود. ابزارهای موقت/سرور مرجع و خروجی‌های مقدماتی زیر ignored `.tools/test-s03-02/` نگه داشته شدند. کد محصول، env، اسناد مصوب، گزارش و شواهد پروگرمر و وضعیت مجوز/پذیرش تغییر نکردند. برای جلوگیری از بازنویسی تصاویر تحویلی، تست‌های موجود با cwd خروجی جدا اجرا شدند.

ابزار reset قبل از استفاده خوانده شد؛ مقصد حل‌شده با assertion دقیق `test + invest_browser` کنترل شد. فقط DB مصنوعی مرورگر بین مجموعه‌ها بازسازی شد؛ pytest از DB آزمون خود استفاده کرد. سرورهای موقت مرجع3107 و standalone3109 و سرویس آزمون browser-api پس از بررسی متوقف شدند؛ نسخه اصلی3108 فعال ماند. DB برنامه و volume حذف/بازنشانی نشدند؛ داده‌های افزوده به اجرای3108 مصنوعی‌اند. به سرویس‌های پروژه‌های دیگر دست زده نشد. پیامک واقعی، اتصال پولی، deploy و push اجرا نشدند.

Chrome نصب‌شده و viewportهای شبیه‌سازی آزموده شدند؛ دستگاه فیزیکی، Safari/Firefox، مرورگر bundled، CI خارجی، تست بار عرضه و قابلیت واقعی provider اجرا نشدند. حالت public و خطای provider فقط در آزمون جدا شبیه‌سازی شدند. تست‌های clock-controlled از انتظار واقعی۱۲۰ثانیه جدا گزارش شدند. هیچ نگرانی صرفاً حاصل از خواندن کد به‌عنوان باگ مشاهده‌شده در فهرست سه‌گانه ثبت نشد.

قدم بعدی برای هماهنگ‌کننده: ارجاع سه باگ به برنامه‌نویس و پس از تحویل اصلاح، مأموریت بازگشت محدود به تغییرات و سفرهای متاثر. این مأموریت پس از گزارش متوقف می‌شود؛ اصلاح محصول و پذیرش نهایی انجام نشده‌اند.
