from apps.slack.views.schedule_setting_view import ScheduleSettingView


class EndView(ScheduleSettingView):
    """
    Handles the /end [hour] slash command.
    Sets or displays the user's schedule window end hour override.
    """

    setting_label = "Schedule end hour"
    default_setting = "SCHEDULE_END_HOUR"
    getter_attr = "schedule_end"
    setter_attr = "set_schedule_end"
