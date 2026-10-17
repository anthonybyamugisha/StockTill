from uuid import uuid4

import pytest

from accounts.infrastructure.audit_repository import DjangoAuditRepository
from shared.infrastructure.audit import AuditEntry, build_audit_recorder


def _entry(**overrides):
    defaults = {
        "id": uuid4(),
        "user_id": uuid4(),
        "action": "sale.voided",
        "entity_type": "sale",
        "entity_id": "ST-2026-000001",
        "before": {"status": "completed"},
        "after": {"status": "voided"},
    }
    defaults.update(overrides)
    return AuditEntry(**defaults)


@pytest.mark.django_db
def test_save_persists_entry():
    repo = DjangoAuditRepository()
    entry = _entry()
    repo.save(entry)

    entries = repo.list_entries()
    assert len(entries) == 1
    assert entries[0].id == entry.id
    assert entries[0].action == "sale.voided"
    assert entries[0].entity_type == "sale"
    assert entries[0].entity_id == "ST-2026-000001"
    assert entries[0].before == {"status": "completed"}
    assert entries[0].after == {"status": "voided"}
    assert entries[0].timestamp is not None


@pytest.mark.django_db
def test_entries_are_ordered_newest_first():
    repo = DjangoAuditRepository()
    repo.save(_entry(action="product.created"))
    repo.save(_entry(action="product.deactivated"))

    actions = [e.action for e in repo.list_entries()]
    assert actions == ["product.deactivated", "product.created"]


@pytest.mark.django_db
def test_list_filters_by_action_entity_and_user():
    repo = DjangoAuditRepository()
    user_id = uuid4()
    repo.save(_entry(user_id=user_id, action="sale.voided", entity_type="sale"))
    repo.save(_entry(action="product.created", entity_type="product"))

    assert len(repo.list_entries(action="sale.voided")) == 1
    assert len(repo.list_entries(entity_type="product")) == 1
    assert len(repo.list_entries(user_id=user_id)) == 1
    assert len(repo.list_entries(entity_type="customer")) == 0


@pytest.mark.django_db
def test_supports_entries_without_a_user():
    repo = DjangoAuditRepository()
    repo.save(_entry(user_id=None, action="system.startup"))

    entries = repo.list_entries()
    assert entries[0].user_id is None


@pytest.mark.django_db
def test_build_audit_recorder_writes_to_database():
    recorder = build_audit_recorder()
    recorder.record(
        user_id=None,
        action="auth.login",
        entity_type="user",
        entity_id="someone@shop.com",
        after={"result": "success"},
    )

    entries = DjangoAuditRepository().list_entries()
    assert len(entries) == 1
    assert entries[0].action == "auth.login"
    assert entries[0].after == {"result": "success"}
