from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class WeeklyReportResult:
    weekly_report_draft: str
    schedule_risk_report: str


class WeeklyReportService:
    def generate(
        self,
        *,
        project_id: str,
        week_start: date,
        week_end: date,
        as_of_timestamp: datetime,
    ) -> WeeklyReportResult:
        _ = (project_id, week_start, week_end, as_of_timestamp)
        # TODO: Fetch data from MariaDB + Qdrant and generate the draft/report.
        raise NotImplementedError("Weekly report generation is not implemented yet.")
