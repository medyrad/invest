# داده
User: role، auth_epoch؛ تغییر اختیار با قفل و افزایش epoch.
LoginFlow: digest، created/expires، user/epoch، completed، intent snapshot/time/account/session/consumed؛ اتصال نشست پس از verify یا هنگام ایجاد نیت واردشده تثبیت می‌شود.
OTPChallenge: UUID، flow، شماره از user، nonce، code_digest، issued/expires، attempts، state، delivery، operation_key یکتا در flow.
IssueEvent: flow/user/ip_digest/time؛ فقط پذیرش صدور.
CheckEvent: user/time/allowed و failed؛ محدودیت از پنجره خطا و آخرین مجاز.
AuthSession: digest، user/epoch، created/last_activity، sensitive، assurance، reauthenticated، revoked؛ absolute مستقل از token rotation.
AuditEvent: kind/user UUID/time؛ شکست ثبت به معنی شکست mutation.

حالت challenge: active→consumed/replaced/cancelled؛ expired/exhausted/revoked برآورد جاری سروری مقدم بر فعال است. تمام‌شدن جریان مانع صدور تازه است ولی retry رسید قبلی وضعیت consumed برمی‌گرداند. expired flow همیشه410 حتی با key قدیمی. نیت از ایجاد۱۰دقیقه اعتبار دارد، جایگزین/لغو/مصرف حالت پایانی‌اند.
