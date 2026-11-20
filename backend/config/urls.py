from django.urls import path

from apps.assistant.api import AssistantAPI
from apps.catalog.api import Geography, NormalizeValue, Taxonomy, ValueDefinitions
from apps.core.api import CoreAPI
from apps.identity.api import AuthAPI
from apps.services.api import ServicesAPI
from apps.workspace.api import WorkspaceAPI
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
    path("api/v1/catalog/value-definitions", ValueDefinitions.as_view()),
    path("api/v1/catalog/values/normalize", NormalizeValue.as_view()),
]


for suffix, action in [
    ("schema", "schema"),
    ("owners", "owners"),
    ("drafts", "drafts"),
    ("organizations", "organizations"),
    ("files/reserve", "reserve"),
]:
    urlpatterns.append(
        path("api/v1/workspace/" + suffix, WorkspaceAPI.as_view(), {"action": action})
    )
for suffix, action in [
    ("drafts/<uuid:id>", "draft"),
    ("drafts/<uuid:id>/delete", "delete"),
    ("drafts/<uuid:id>/restore", "restore"),
    ("organizations/<uuid:id>", "organizations"),
    ("files/<uuid:id>/content", "content"),
    ("files/<uuid:id>/download", "download"),
    ("files/<uuid:id>/retry", "retry"),
    ("files/<uuid:id>/delete", "file-delete"),
    ("files/<uuid:id>/restore", "file-restore"),
]:
    urlpatterns.append(
        path("api/v1/workspace/" + suffix, WorkspaceAPI.as_view(), {"action": action})
    )


urlpatterns.append(path("api/v1/core/<path:path>", CoreAPI.as_view()))
urlpatterns.append(path("api/v1/assistant/<path:path>", AssistantAPI.as_view()))


urlpatterns.append(path("api/v1/services/<path:path>", ServicesAPI.as_view()))
