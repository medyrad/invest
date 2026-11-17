from django.urls import path

from apps.catalog.api import Geography, NormalizeValue, Preview, Taxonomy, ValueDefinitions
from apps.identity.api import AuthAPI
from config import views

urlpatterns = [
    path("api/v1/health/live", views.Live.as_view()),
    path("api/v1/health/ready", views.Ready.as_view()),
    path("api/v1/auth/csrf", views.Csrf.as_view()),
    path("api/v1/schema", views.Schema.as_view()),
]
for action in (
    "flows",
    "issue",
    "edit",
    "verify",
    "me",
    "logout",
    "revoke-all",
    "activity",
    "rotate",
    "reauth",
    "sensitive",
    "intent",
    "intent/cancel",
    "intent/consume",
):
    urlpatterns.append(path("api/v1/auth/" + action, AuthAPI.as_view(), {"action": action}))
urlpatterns.append(
    path("api/v1/auth/private/<uuid:owner>", AuthAPI.as_view(), {"action": "private"})
)

handler400 = "config.api.bad_request"
handler403 = "config.api.permission_denied"
handler404 = "config.api.not_found"
handler500 = "config.api.server_error"


urlpatterns += [
    path("api/v1/catalog/taxonomy", Taxonomy.as_view()),
    path("api/v1/catalog/geography", Geography.as_view()),
    path("api/v1/catalog/preview", Preview.as_view()),
    path("api/v1/catalog/value-definitions", ValueDefinitions.as_view()),
    path("api/v1/catalog/values/normalize", NormalizeValue.as_view()),
]
