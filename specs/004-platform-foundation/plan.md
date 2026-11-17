# Implementation Plan: زیرساخت S02

## Summary

دامنه مجاز: T003–T008 baseline؛ فقط foundation. spec/قرارداد/آزمون قبل از کد و تست واقعی PostgreSQL/production build. D01–D29 تغییر نمی‌کنند؛ OTP و صفحات محصول مرحله بعد هستند.

## Technical Context

Python3.14.10/uv0.11.32؛ Django5.2.19، DRF3.18.3، psycopg3.3.9، Gunicorn27.0.1؛ PostgreSQL17.12. Node24.22.3/npm11.19.1؛ Next16.4.6/React19.3.1/TS6.0.3. نسخه‌های lint/test و image digest در dependencies.json. هدف محلی و CI linux/amd64. lockهای جدا، بدون secret در build/repo.

Backend ماژولار `config` و `apps.identity`؛ مدل User پیش از نخستین migration. APIView پایه csrf_protect، session DB-backed/HttpOnly؛ default permission بسته، health/bootstrap صریح public. خطای یکنواخت برای DRF/CSRF/framework و request-id امن؛ لاگ بدون payload/کوکی/شماره/DSN. health live مستقل DB؛ ready با SELECT1 حساب واقعی، timeout3s و 503 بدون جزئیات.

چهار مسیر واقعی بدون slash پایانی: /api/v1/health/live، /api/v1/health/ready، /api/v1/auth/csrf، /api/v1/schema. مسیر CSRF آماده‌سازی است، نه ورود. GET/HEAD/OPTIONS مجاز؛ unsafe با CSRF معتبر هم روش نامجاز405 می‌دهد. test-only probe در backend/tests و URLConf جدا، فقط برای آزمون هم‌مبدأ در حالت test؛ در config.urls وجود ندارد.

Next output standalone و external rewrite ثابت build-time؛ مقصد build محلی127.0.0.1:8008، image مقصدbackend:8000. `skipTrailingSlashRedirect` و APPEND_SLASH=False، قرارداد URL بدون slash. هیچ NEXT_PUBLIC secret یا fetch از API بیرونی. public/fonts همان Vazirmatn مرجع با مجوز؛ پوسته فقط نام برند روی پایه همان رنگ/فونت، بدون صفحه جایگزین طراحی S04.

Docker Compose پروژه invest مستقل؛ PostgreSQL localhost55432، frontend localhost3108، backend فقط شبکه داخلی. تست مرورگر روی production build در localhost3109 و backend آزمون8008 در profile کانتینری test؛ به سرویس‌های موجود دست نمی‌زنیم. volume اختصاصی، stop/restart بدون حذف داده. backend migration با فرمان مستقل پیش از شروع، نه race چند worker. CI PostgreSQL واقعی، migrations/checks/pytest، lint/typecheck/build و Playwright؛ GitHub workflow با SHA و contents:read، اجرای remote ادعا نمی‌شود.

## Constitution Check

| اصل | پیش و پس طراحی |
|---|---|
| I | business/UI فقط advisor؛ ham فقط معماری/کیفیت |
| II | فقط پایه فونت/RTL/token؛ ادعای پذیرش صفحه وجود ندارد؛ S04 gate باقی |
| III | هر FR/SC به task و test وصل می‌شود |
| IV | حساب و CSRF در سرور، نه نقش کلاینت؛ session امن |
| V | حساب canonical احراز واقعی نیست؛ سیاست‌های پول خارج دامنه |
| VI | PostgreSQL واقعی، red/green، build واقعی و outage/restart |
| VII | دستور «برو قدم بعدی» S02 را مجاز کرد؛ S03/عرضه مجاز نیست |

قواعد مرزی انتخاب شده‌اند و ابهام مسدودکننده S02 باقی نیست؛ lint peer با plugin مستقیم حل شد، Gunicorn3.14 نیازمند smoke واقعی پذیرش است. چک‌لیست custom نیازمندی بازبین‌محور است؛ تأیید انسانی محصول ادعا نمی‌شود. دستور فعلی اجرای S02 و کنترل‌های همان مرحله را پوشش می‌دهد؛ تکرار درخواست اجازه برای کار داخلی لازم نیست.

## Project Structure

### Documentation (this feature)

spec.md، research.md، data-model.md، contracts/api.md، quickstart.md، test-plan.md، tasks.md، checklists/ و analysis.md؛ شواهد docs/stage2/.

### Source Code (repository root)

backend/{pyproject.toml,uv.lock,manage.py,config/,apps/identity/,tests/}؛ frontend/{package.json,package-lock.json,src/app/,public/fonts/}؛ contracts/openapi.yaml؛ deploy/{compose.yaml,backend.Dockerfile,frontend.Dockerfile}؛ scripts/{dev_env.py,foundation_smoke.py}؛ frontend/tests/browser/foundation.spec.ts؛ .github/workflows/ci.yml؛ docs/development.md.

## Complexity Tracking

صف/Redis/microservice/ورود/OTP یا عملیات فرصت اضافه نمی‌شود. middleware/helperها فقط قرارداد پایه را پوشش می‌دهند. probe آزمون در URLConf test جداست؛ نیاز به endpoint عملیاتی غیرمصوب نداریم. پذیرش S02 شامل ابزار آماده CI است؛ اجرا روی GitHub به اتصال/ارسال جدا وابسته است.

## اصلاحات اجرایی بر اساس شاهد

Python3.14.10 در image رسمی اجرا شد؛ فهرست دانلود uv میزبان این patch را ندارد، بنابراین نصب/آزمون backend و CI کانتینری است. آزمون مرورگر داخل frontend/tests/browser قرار گرفت تا از dependency همان package استفاده کند. نسخه محلی Chrome151 به دلیل محدودیت CDN استفاده شد؛ نسخه bundled در CI هنوز اجرا نشده است. If-Match عدد مثبت حداکثر۱۸رقم است؛ schema/helper یکسان‌اند.
