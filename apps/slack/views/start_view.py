from apps.slack.views.schedule_setting_view import ScheduleSettingView


class StartView(ScheduleSettingView):
    """
    Handles the /start [hour] slash command.
    Sets or displays the user's schedule window start hour override.
    """

    setting_label = "Schedule start hour"
    default_setting = "SCHEDULE_START_HOUR"
    getter_attr = "schedule_start"
    setter_attr = "set_schedule_start"
