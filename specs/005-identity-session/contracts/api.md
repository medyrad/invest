# قرارداد API S03

پیشوند /api/v1/auth؛ JSON، no-store، CSRF برای همه POST. فیلد اضافه رد400. flow_token فقط پاسخ ایجاد جریان و header X-Login-Flow؛ در memory تب، نه URL/localStorage/log. Cookie invest_session HttpOnly با عمر سقف مطلق و SameSite=Lax؛ response هرگز token نشست ندارد.

| مسیر | ورودی | خروجی/معنا |
|---|---|---|
| GET /csrf | ندارد | csrfToken |
| POST /flows | {} | flow_token، expires_at؛۳۰دقیقه |
| POST /issue | mobile، key UUID | challenge_id، state، expires_at، resend_at، delivery؛ فقط در test/development مجاز و active: notification.code |
| POST /edit | {} | لغو challenge جاری |
| POST /verify | challenge_id UUID، code رشته شش رقم | authenticated true و cookie تازه فقط اولین مصرف؛ retry بدون cookie recovery_required، با همان نشست موجود recovered true |
| GET /me | cookie | authenticated false یا user{id,mobile,role}, assurance؛ بدون تمدید idle |
| POST /logout | {} | ابطال جاری حتی با cookie قدیمی |
| POST /revoke-all | {} | epoch تازه، ابطال همه |
| POST /activity | {} | تمدید idle فقط در صورت موفقیت |
| POST /rotate | {} | cookie تازه، ساعت absolute ثابت |
| POST /reauth | challenge_id، code، flow header | همان حساب/نشست، سقف ثابت، test شاهد واقعی نمی‌شود |
| GET /private/<user_id> | cookie | داده مصنوعی فقط مالک |
| POST /sensitive | {} | نقش expert/admin، نشست حساس، assurance واقعی، freshness<۵دقیقه؛ test رد403 |
| POST /intent | destination=/saved، snapshot object | نیت ثابت و۱۰دقیقه؛ جایگزینی قبلی |
| POST /intent/cancel | {} | لغو |
| POST /intent/consume | {} | consumed/handoff بدون ذخیره؛ احراز همان حساب/نشست متصل، allowlist و freshness نیت بازبینی |

خطا: {error:{code,message,fields,request_id},retry_after?}؛400 invalid_mobile/invalid_code/invalid_request،403 csrf_failed/forbidden،409 payload_conflict/flow_completed/recovery_required/intent_unavailable،410 flow_expired/challenge_expired/challenge_replaced/challenge_cancelled/challenge_exhausted/challenge_revoked،429 rate_limited با Retry-After،503 delivery_unavailable؛ delivery unknown در رسید صدور صادقانه و بدون ارسال تازه در retry. بعد از انقضا/مصرف/جایگزینی اعلان کد برنگردد. مقدار resend_at فقط فاصله جریان است؛ سهمیه‌های دیگر با429 تعیین می‌شوند.

نسخه ماشین‌خوان سرویس: contracts/openapi.yaml؛ از GET /api/v1/schema هم قابل خواندن است. test_machine_contract_matches_implemented_trial_responses پاسخ واقعی را با schema همان سرویس می‌سنجد. جزئیات زمان/حالت/رقابت این سند و spec همچنان لازم‌اند.
