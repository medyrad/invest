"""Only the tester's isolated, explicitly synthetic local-role user."""
from apps.core.models import Personal
from apps.core.models import Saved

for personal in Personal.objects.filter(profile__local_role=True, user__role="user"):
    personal.profile = {**personal.profile, "name": "مشتری مصنوعی"}
    personal.save(update_fields=["profile"])

# Exact residual target documented by the tester's historical late-handoff.json.
Saved.objects.filter(
    user__core_personal__profile__local_role=True,
    user__role="owner",
    opportunity_id="d2fa266e-a44f-4c22-9ec3-9cfb7181ae94",
).delete()
