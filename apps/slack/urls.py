from django.urls import path

from apps.slack.views import ActivateView, DeactivateView, SlackEventView

urlpatterns = [
    path("events/", SlackEventView.as_view(), name="slack-events"),
    path("commands/activate/", ActivateView.as_view(), name="slack-activate"),
    path("commands/deactivate/", DeactivateView.as_view(), name="slack-deactivate"),
]
