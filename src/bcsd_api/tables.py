from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text

from .database import metadata

members = Table(
    "members", metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("email", String, nullable=False, unique=True),
    Column("department", String),
    Column("student_id", String),
    Column("school_email", String),
    Column("phone", String),
    Column("status", String, nullable=False, server_default="Beginner"),
    Column("track", String),
    Column("team", String),
    Column("role", String),
    Column("join_date", String),
    Column("payment_status", String, server_default="미납"),
    Column("grade", String),
    Column("last_updated", String),
)

fees = Table(
    "fees", metadata,
    Column("id", String, primary_key=True),
    Column("member_id", String, ForeignKey("members.id")),
    Column("amount", Integer),
    Column("paid_date", String),
    Column("payment_method", String),
    Column("notes", Text),
    Column("semester", String),
    Column("last_updated", String),
)

groups = Table(
    "groups", metadata,
    Column("id", String, primary_key=True),
    Column("name", String),
    Column("type", String),
    Column("parent_id", String),
    Column("size", Integer),
    Column("leader_email", String),
    Column("last_updated", String),
)

events = Table(
    "events", metadata,
    Column("id", String, primary_key=True),
    Column("title", String),
    Column("date", String),
    Column("type", String),
    Column("organizer", String),
    Column("attendees", Text),
    Column("notes", Text),
)

workflow_logs = Table(
    "workflow_logs", metadata,
    Column("timestamp", String, primary_key=True),
    Column("workflow_name", String, primary_key=True),
    Column("status", String),
    Column("input_data", Text),
    Column("output_data", Text),
    Column("error_message", Text),
)

links = Table(
    "links", metadata,
    Column("id", String, primary_key=True),
    Column("code", String, nullable=False, unique=True),
    Column("title", String, nullable=False),
    Column("description", Text),
    Column("url", Text, nullable=False),
    Column("creator_id", String, ForeignKey("members.id")),
    Column("created_at", String),
    Column("expires_at", String),
    Column("expired_at", String),
    Column("updated_at", String),
)

link_clicks = Table(
    "link_clicks", metadata,
    Column("id", String, primary_key=True),
    Column("link_id", String, ForeignKey("links.id", ondelete="CASCADE")),
    Column("clicked_at", String),
    Column("referer", Text),
    Column("user_agent", Text),
)

tracks = Table(
    "tracks", metadata,
    Column("name", String, primary_key=True),
)

statuses = Table(
    "statuses", metadata,
    Column("name", String, primary_key=True),
)

payment_statuses = Table(
    "payment_statuses", metadata,
    Column("name", String, primary_key=True),
)

recruitment_periods = Table(
    "recruitment_periods", metadata,
    Column("id", String, primary_key=True),
    Column("title", String, nullable=False),
    Column("type", String, nullable=False),
    Column("start_date", String, nullable=False),
    Column("end_date", String, nullable=False),
    Column("is_active", String, server_default="true"),
    Column("created_by", String, ForeignKey("members.id")),
    Column("created_at", String),
    Column("updated_at", String),
)

forms = Table(
    "forms", metadata,
    Column("id", String, primary_key=True),
    Column("title", String, nullable=False),
    Column("description", Text),
    Column("recruitment_id", String, ForeignKey("recruitment_periods.id")),
    Column("type", String, nullable=False),
    Column("is_active", String, server_default="true"),
    Column("created_by", String, ForeignKey("members.id")),
    Column("created_at", String),
    Column("updated_at", String),
)

form_questions = Table(
    "form_questions", metadata,
    Column("id", String, primary_key=True),
    Column("form_id", String, ForeignKey("forms.id", ondelete="CASCADE")),
    Column("label", String, nullable=False),
    Column("type", String, nullable=False),
    Column("options", Text),
    Column("required", String, server_default="true"),
    Column("sort_order", Integer, nullable=False),
    Column("created_at", String),
)

applications = Table(
    "applications", metadata,
    Column("id", String, primary_key=True),
    Column("form_id", String, ForeignKey("forms.id")),
    Column("member_id", String, ForeignKey("members.id")),
    Column("track", String),
    Column("status", String, nullable=False, server_default="pending_payment"),
    Column("submitted_at", String),
    Column("approved_at", String),
    Column("approved_by", String),
    Column("updated_at", String),
)

application_answers = Table(
    "application_answers", metadata,
    Column("id", String, primary_key=True),
    Column("application_id", String, ForeignKey("applications.id", ondelete="CASCADE")),
    Column("question_id", String, ForeignKey("form_questions.id")),
    Column("value", Text, nullable=False),
)

app_settings = Table(
    "app_settings", metadata,
    Column("key", String, primary_key=True),
    Column("value", String, nullable=False),
    Column("updated_at", String),
    Column("updated_by", String),
)
