import json

import pytest
from pydantic import ValidationError

from arena.canonical import canonical_bytes
from arena.contracts import (
    SCHEMA_VERSION,
    ForecastRecord,
    OutageRecord,
    Persona,
)


def _fc(**over):
    base = dict(
        schema_version=SCHEMA_VERSION,
        record_type="forecast",
        emitted_at_utc="2026-08-03T20:15:00Z",
        session_date="2026-08-03",
        resolution_session_date="2026-08-10",
        horizon_sessions=5,
        persona=Persona.AGRESSIVO,
        symbol="NVDA",
        claim="outperform_qqq",
        p_up="0.5600",
        rule_version="momentum-1.0.0",
        reference_close_raw="174.2000",
        reference_close_qqq_raw="480.1100",
        universe_snapshot_sha256="a" * 64,
        outcome="pending",
        resolved_at_utc=None,
    )
    base.update(over)
    return base


def test_forecast_valido_e_hasheavel():
    r = ForecastRecord.model_validate(_fc())
    assert len(r.sha256()) == 64
    assert r.canonical_dict()["p_up"] == "0.5600"


def test_p_up_float_e_rejeitado():
    with pytest.raises(ValidationError):
        ForecastRecord.model_validate(_fc(p_up=0.56))


def test_campo_desconhecido_e_rejeitado_nao_ignorado():
    with pytest.raises(ValidationError):
        ForecastRecord.model_validate(_fc(inventado="x"))


def test_timestamp_precisa_terminar_em_Z():
    with pytest.raises(ValidationError):
        ForecastRecord.model_validate(_fc(emitted_at_utc="2026-08-03T20:15:00-03:00"))


def test_p_up_fora_de_zero_um_e_rejeitado():
    with pytest.raises(ValidationError):
        ForecastRecord.model_validate(_fc(p_up="1.5000"))


def test_decimal_sem_ponto_e_rejeitado():
    with pytest.raises(ValidationError):
        ForecastRecord.model_validate(_fc(p_up="1"))


def test_hash_muda_quando_qualquer_campo_muda():
    a = ForecastRecord.model_validate(_fc()).sha256()
    b = ForecastRecord.model_validate(_fc(symbol="AAPL")).sha256()
    assert a != b


def test_registro_e_imutavel():
    r = ForecastRecord.model_validate(_fc())
    with pytest.raises(ValidationError):
        r.p_up = "0.9900"


def test_round_trip_json_valida_de_volta_em_strict():
    """O resolvedor e o painel LEEM o que foi publicado.

    Se persona voltar como a string "agressivo" e strict=True recusar,
    nada consegue reler o proprio registro. Este teste e o que garante
    que o registro publicado e legivel pelo sistema que o produziu.
    """
    original = ForecastRecord.model_validate(_fc())
    como_publicado = json.loads(canonical_bytes(original.canonical_dict()))
    relido = ForecastRecord.model_validate(como_publicado)
    assert relido == original
    assert relido.sha256() == original.sha256()
    assert relido.persona is Persona.AGRESSIVO


def test_canonical_dict_nao_contem_float():
    from arena.canonical import assert_no_floats

    assert_no_floats(ForecastRecord.model_validate(_fc()).canonical_dict())


def test_outage_record():
    o = OutageRecord.model_validate(
        dict(
            schema_version=SCHEMA_VERSION,
            record_type="outage",
            detected_at_utc="2026-08-03T20:15:00Z",
            session_date="2026-08-03",
            stage="ingest",
            reason="DATA_UNAVAILABLE",
            detail="HTTP 503 do provedor de barras",
        )
    )
    assert len(o.sha256()) == 64


def test_as_tres_personas_existem():
    assert {p.value for p in Persona} == {"agressivo", "equilibrista", "guardiao"}
