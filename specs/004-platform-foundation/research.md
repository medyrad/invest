# پژوهش S02 — ۲۰۲۶/۱۱/۱۷

نسخه دقیق در [dependencies.json](../../docs/stage2/dependencies.json) ثبت است. پژوهش دو عامل خواندنی طبق speckit-plan انجام و با metadata رجیستری/manifest تصویر کنترل شد؛ نصب/build/تست gate بعدی است.

| تصمیم | دلیل | جایگزین |
|---|---|---|
| Django5.2 LTS/DRF/PostgreSQL17 و Python3.14.10 | حفظ جهت مهندسی مصوب؛ patchهای جاری | Python3.13 security-only؛ Python3.14 با smoke واقعی Gunicorn انتخاب شد چون classifier Gunicorn هنوز تا3.13 است |
| Node24.22.3 و npm11.19.1، Next16.4.6/React19.3.1 | حفظ فناوری UI مرجع و patch جاری | framework تازه/کپی UI ham وارد نمی‌شود |
| TS6.0.3 و ESLint10 با JS/TS/Next plugin مستقیم | parser فعلی TS<6.1؛ config-next بعضی peerهای ESLint10 ناسازگار دارد | ESLint9 EOL و force/legacy-peer-deps انتخاب نشد؛ TS7 تنها به‌علت parser فعلاً نیست |
| User موبایل canonical از migration اول | جلوگیری از جابه‌جایی مدل حساب پس از ساخت جداول وابسته | account پایه اکنون؛ OTP/نقش محصولی در S03 |
| اتصال هم‌مبدأ با rewrite ثابت Next | یک مبدأ مرورگر و backend صاحب مجوز | مقصد rewrite در build تثبیت می‌شود؛ در runtime وعده تغییر مقصد نمی‌دهیم؛ export استاتیک نامناسب |
| public fail-closed و حفاظت CSRF صریح برای ناشناس | DRF SessionAuthentication فقط برای authenticated CSRF enforce می‌کند | اعتماد صرف به AllowAny/middleware کافی نیست |
| imageهای رسمی Docker Library در ECR با digest linux/amd64 | Docker Hub در این محیط RBAC denied؛ mirror عمومی رسمی قابل خواندن است | سرویس/تصویر پروژه‌های دیگر تغییر نمی‌کند |
| uv.lock و package-lock مستقل، CI با SHA Action | نصب ثابت و حداقل دسترسی workflow | patch خودکار بی‌ردیابی انجام نمی‌شود |

منابع اولیه: [Django پشتیبانی](https://www.djangoproject.com/download/)، [Python سازگار](https://docs.djangoproject.com/en/5.2/faq/install/)، [User اولیه](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project)، [CSRF](https://docs.djangoproject.com/en/5.2/howto/csrf/)، [DRF session](https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication)، [deployment](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)، [PostgreSQL](https://www.postgresql.org/support/versioning/)، [pg_isready محدودیت](https://www.postgresql.org/docs/17/app-pg-isready.html)، [Gunicorn](https://gunicorn.org/install/).

[Node24.22.3](https://nodejs.org/en/blog/release/v24.22.3)، [Next support](https://nextjs.org/support-policy)، [rewrites](https://nextjs.org/docs/app/api-reference/config/next-config-js/rewrites)، [standalone](https://nextjs.org/docs/app/api-reference/config/next-config-js/output)، [ESLint](https://eslint.org/version-support/)، [parser](https://typescript-eslint.io/users/dependency-versions/)، [Playwright CI](https://playwright.dev/docs/ci).

Actionها: checkout v7.0.1 SHA 3d3c42e5aac5ba805825da76410c181273ba90b1؛ setup-node v7.1.0 SHA 949feb2413d6458794dcd2491c4babbbce0c15c1؛ setup-uv v10.3.3 SHA 68559e99cc807c1eb7e9238fd43a15bba460eec2؛ از release/tag رسمی و git ls-remote بررسی شدند. runner hosted با node24؛ اجرای واقعی GitHub فقط پس از اتصال مخزن/ارسال خواهد بود، در این مرحله کنترل‌های معادل محلی اجرا می‌شوند.

هیچ ابهام بیزینسی S02 باقی نیست. مقادیر فنی timeout و محیط محلی در plan تعریف‌اند و SLA مشتری نیستند. public HTTPS/HSTS واقعی، پیامک و AI گیت عرضه خود را دارند.

شاهد نصب: مسیر uv python install برای3.14.10 در فهرست این نسخه uv موجود نبود؛ Python image رسمی3.14.10 نصب/build/اجرای Gunicorn را گذراند. دستور uv sync --locked داخل image اجرا می‌شود؛ setup-uv Action در workflow نهایی استفاده نشده است. upload-artifact v7.0.2 با SHA cf430e030ddbb5b0abf93d22962f4752f3646cd9 از git ls-remote رسمی قفل شد. آزمون‌های مرورگر package-local هستند. CDN bundled Chromium159 در محیط محلی403 داد؛ Chrome151 نصب‌شده با executablePath صریح شاهد محلی است و اجرای bundled در CI هنوز ادعا نمی‌شود. [پیکربندی Python در uv](https://docs.astral.sh/uv/reference/settings/) فقط منبع بررسی گزینه نصب بود؛ مسیر نصب نهایی Docker است.
