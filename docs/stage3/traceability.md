# ردیابی مأموریت PROGRAMMER-S03-01

| نیازمندی | تسک | شاهد اجرا |
|---|---|---|
| FR-001 ورودی | T002/T004 | test_canonical_contract، test_zero_prefix_and_strict_otp، invalid mobile مرورگر |
| FR-002 چرخه کد | T003/T004/T007 | test_expiry_and_five_errors، test_clock_sampled_after_lock_wait، test_parallel_consumption_creates_exactly_one_session |
| FR-003 سهمیه | T004/T007 | test_flow_spacing_and_sliding_boundaries، test_phone_daily_cap_and_rejected_does_not_extend، test_parallel_last_phone_quota_and_same_idempotency_key |
| FR-004 خطای مشترک | T004/T007 | test_error_throttle_shared_and_sliding_exit، test_throttle_ends_when_errors_leave_window، test_ip_only_limits_new_issuance |
| FR-005 تکرار | T004/T007 | test_retry_current_state_and_payload، test_retry_expired_replaced_and_mode_change_never_exposes_code، lost verify body مرورگر |
| FR-006 تحویل | T004/T007 | test_provider_failure_unknown_and_public_no_disclosure، test_failed_delivery_consumes_quota_and_retry_does_not_refund_or_redeliver |
| FR-007 نشست | T008 | test_idle_absolute_rotation_and_activity در دو سطح، test_reauth_is_session_bound_and_cannot_refresh_real_assurance |
| FR-008 اختیار | T008 | test_two_accounts_and_sensitive_gate، test_sessions_logout_revoke_deactivate_and_role_changes، test_revocation_committed_first_blocks_waiting_verify، test_role_revoked_first_blocks_sensitive_action، test_trial_evidence_and_previous_code_are_unusable_in_public |
| FR-009 نیت | T009 | test_intent_snapshot_replacement_expiry_cancel_and_owner، test_parallel_intent_consumes_once، test_intent_cannot_revive_after_switching_away_and_back |
| FR-010 UI | T005/T006/T012 | ۲۸تست مرورگر شامل۸زیرساخت و۲۰هویت، چهار عرض، clipboard واقعی، focus و screenshot؛ visual-metrics.json؛ پذیرش انسانی باز |
| FR-011 اسرار/audit | T003/T008/T010 | test_api_csrf_payload_cookie_ip_and_logs، test_audit_failure_rolls_back_issuance_and_consumption، scripts/verify_identity_safety.py |

SC-001: مرورگر build واقعی؛ SC-002: ۹۳آزمون PostgreSQL شامل۵۷ آزمون قبلی و۳۶آزمون تازه؛ SC-003: گزارش و نگاشت F01..F12 در report.md. نام‌ها از خروجی pytest و تست موجود گرفته شده‌اند؛ آزمون داخلی سرویس از سفر مرورگر و اتصال واقعی provider جداست.

T013: قرارداد ماشین‌خوان سرویس به S03 همگام شد؛ test_machine_contract_matches_implemented_trial_responses نسخه تحویلی /schema و پاسخ‌های واقعی جریان/صدور/ورود/me را اعتبارسنجی می‌کند.
