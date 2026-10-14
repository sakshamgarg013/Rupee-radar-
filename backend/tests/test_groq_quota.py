from pathlib import Path

import app.services.groq_client as groq_service


def test_quota_reserve_rejects_over_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(groq_service.settings, "GROQ_MAX_RPM", 1)
    monkeypatch.setattr(groq_service.settings, "GROQ_MAX_TPM", 150)
    monkeypatch.setattr(groq_service.settings, "GROQ_MAX_RPD", 2)
    monkeypatch.setattr(groq_service.settings, "GROQ_MAX_TPD", 200)

    quota = groq_service.GroqQuotaCoordinator(db_path=str(tmp_path / "quota.json"))
    assert quota.reserve(100) is True
    assert quota.reserve(100) is False

    snapshot = quota.get_usage_snapshot()
    assert snapshot["rpm"] == 1
    assert snapshot["tpm"] == 100
    assert snapshot["rpd"] == 1

    quota.reconcile(100, actual_tokens=120, status_ok=True)
    snapshot = quota.get_usage_snapshot()
    assert snapshot["tpd"] == 120


def test_quota_persists_daily_usage_across_restarts(tmp_path, monkeypatch):
    monkeypatch.setattr(groq_service.settings, "GROQ_MAX_RPM", 5)
    monkeypatch.setattr(groq_service.settings, "GROQ_MAX_TPM", 500)
    monkeypatch.setattr(groq_service.settings, "GROQ_MAX_RPD", 10)
    monkeypatch.setattr(groq_service.settings, "GROQ_MAX_TPD", 5000)

    db_path = tmp_path / "quota.json"
    quota = groq_service.GroqQuotaCoordinator(db_path=str(db_path))
    assert quota.reserve(250) is True

    restarted = groq_service.GroqQuotaCoordinator(db_path=str(db_path))
    snapshot = restarted.get_usage_snapshot()
    assert snapshot["rpd"] == 1
    assert snapshot["tpd"] == 250


def test_quota_reconcile_rolls_back_failed_request(tmp_path, monkeypatch):
    monkeypatch.setattr(groq_service.settings, "GROQ_MAX_RPM", 3)
    monkeypatch.setattr(groq_service.settings, "GROQ_MAX_TPM", 300)
    monkeypatch.setattr(groq_service.settings, "GROQ_MAX_RPD", 4)
    monkeypatch.setattr(groq_service.settings, "GROQ_MAX_TPD", 3000)

    quota = groq_service.GroqQuotaCoordinator(db_path=str(tmp_path / "quota.json"))
    assert quota.reserve(150) is True
    quota.reconcile(150, status_ok=False)

    snapshot = quota.get_usage_snapshot()
    assert snapshot["rpm"] == 0
    assert snapshot["tpm"] == 0
    assert snapshot["rpd"] == 0
