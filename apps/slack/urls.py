from django.urls import path

from apps.slack.views import (
    ActivateView,
    DeactivateView,
    DndView,
    EndView,
    ModeView,
    SlackEventView,
    StartView,
)

urlpatterns = [
    path("events/", SlackEventView.as_view(), name="slack-events"),
    path("commands/activate/", ActivateView.as_view(), name="slack-activate"),
    path("commands/deactivate/", DeactivateView.as_view(), name="slack-deactivate"),
    path("commands/mode/", ModeView.as_view(), name="slack-mode"),
    path("commands/dnd/", DndView.as_view(), name="slack-dnd"),
    path("commands/start/", StartView.as_view(), name="slack-start"),
    path("commands/end/", EndView.as_view(), name="slack-end"),
]
