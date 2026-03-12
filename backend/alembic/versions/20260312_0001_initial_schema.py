# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

"""initial schema"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260312_0001"
down_revision = None
branch_labels = None
depends_on = None


severity_enum = sa.Enum("low", "medium", "high", "critical", name="severitylevel")
rule_type_enum = sa.Enum(
    "threshold", "pattern", "sequence", "aggregation", name="ruletype"
)
alert_status_enum = sa.Enum(
    "new", "acknowledged", "investigating", "resolved", "false_positive", name="alertstatus"
)
case_status_enum = sa.Enum(
    "open", "in_progress", "escalated", "resolved", "closed", name="casestatus"
)
case_event_type_enum = sa.Enum(
    "comment",
    "status_change",
    "assignment",
    "alert_linked",
    "evidence_added",
    "playbook_step",
    "response_action",
    "escalation",
    name="caseeventtype",
)
response_action_type_enum = sa.Enum(
    "block_ip", "isolate_host", "disable_account", "custom", name="responseactiontype"
)
response_action_status_enum = sa.Enum(
    "pending", "running", "completed", "failed", name="responseactionstatus"
)
analyst_role_enum = sa.Enum(
    "soc_analyst", "vulnerability_analyst", "incident_commander", "admin", name="analystrole"
)


def upgrade() -> None:
    bind = op.get_bind()
    severity_enum.create(bind, checkfirst=True)
    rule_type_enum.create(bind, checkfirst=True)
    alert_status_enum.create(bind, checkfirst=True)
    case_status_enum.create(bind, checkfirst=True)
    case_event_type_enum.create(bind, checkfirst=True)
    response_action_type_enum.create(bind, checkfirst=True)
    response_action_status_enum.create(bind, checkfirst=True)
    analyst_role_enum.create(bind, checkfirst=True)

    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("source_ip", sa.String(length=64), nullable=True, index=True),
        sa.Column("dest_ip", sa.String(length=64), nullable=True, index=True),
        sa.Column("source_port", sa.Integer(), nullable=True),
        sa.Column("dest_port", sa.Integer(), nullable=True),
        sa.Column("protocol", sa.String(length=16), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=True),
        sa.Column("severity", severity_enum, nullable=False, server_default="medium"),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("source_system", sa.String(length=128), nullable=False),
        sa.Column("raw_log", sa.Text(), nullable=False),
        sa.Column("parsed_data", sa.JSON(), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_events_event_type_timestamp", "events", ["event_type", "timestamp"])
    op.create_index("ix_events_severity_timestamp", "events", ["severity", "timestamp"])

    op.create_table(
        "detection_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("rule_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", severity_enum, nullable=False),
        sa.Column("rule_type", rule_type_enum, nullable=False),
        sa.Column("rule_definition", sa.JSON(), nullable=False),
        sa.Column("mitre_tactic", sa.String(length=128), nullable=True),
        sa.Column("mitre_technique_id", sa.String(length=32), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cases",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("case_uid", sa.String(length=36), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", severity_enum, nullable=False),
        sa.Column("status", case_status_enum, nullable=False, server_default="open"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("assigned_to", sa.String(length=255), nullable=True),
        sa.Column("playbook_id", sa.String(length=128), nullable=True),
        sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("alert_uid", sa.String(length=36), nullable=False, unique=True),
        sa.Column("rule_id", sa.Integer(), sa.ForeignKey("detection_rules.id"), nullable=False),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("cases.id"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("severity", severity_enum, nullable=False),
        sa.Column("status", alert_status_enum, nullable=False, server_default="new"),
        sa.Column("source_ip", sa.String(length=64), nullable=True),
        sa.Column("mitre_tactic", sa.String(length=128), nullable=True),
        sa.Column("mitre_technique_id", sa.String(length=32), nullable=True),
        sa.Column("matched_events", sa.JSON(), nullable=False),
        sa.Column("assigned_to", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "case_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("event_type", case_event_type_enum, nullable=False),
        sa.Column("actor", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "case_alerts",
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("cases.id"), primary_key=True),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "case_evidence",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "response_actions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("cases.id"), nullable=True),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id"), nullable=True),
        sa.Column("action_type", response_action_type_enum, nullable=False),
        sa.Column("target", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            response_action_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "mitre_technique_coverage",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("technique_id", sa.String(length=32), nullable=False),
        sa.Column("tactic", sa.String(length=128), nullable=False),
        sa.Column("rule_id", sa.Integer(), sa.ForeignKey("detection_rules.id"), nullable=False),
        sa.Column("alert_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_alert_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_mitre_technique_coverage_technique_tactic",
        "mitre_technique_coverage",
        ["technique_id", "tactic"],
    )

    op.create_table(
        "analysts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=64), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("role", analyst_role_enum, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "system_config",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("config_key", sa.String(length=128), nullable=False, unique=True),
        sa.Column("config_value", sa.JSON(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("system_config")
    op.drop_table("analysts")
    op.drop_index("ix_mitre_technique_coverage_technique_tactic", table_name="mitre_technique_coverage")
    op.drop_table("mitre_technique_coverage")
    op.drop_table("response_actions")
    op.drop_table("case_evidence")
    op.drop_table("case_alerts")
    op.drop_table("case_events")
    op.drop_table("alerts")
    op.drop_table("cases")
    op.drop_table("detection_rules")
    op.drop_index("ix_events_severity_timestamp", table_name="events")
    op.drop_index("ix_events_event_type_timestamp", table_name="events")
    op.drop_table("events")

    bind = op.get_bind()
    analyst_role_enum.drop(bind, checkfirst=True)
    response_action_status_enum.drop(bind, checkfirst=True)
    response_action_type_enum.drop(bind, checkfirst=True)
    case_event_type_enum.drop(bind, checkfirst=True)
    case_status_enum.drop(bind, checkfirst=True)
    alert_status_enum.drop(bind, checkfirst=True)
    rule_type_enum.drop(bind, checkfirst=True)
    severity_enum.drop(bind, checkfirst=True)