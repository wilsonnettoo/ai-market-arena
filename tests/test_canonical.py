import pytest

from arena.canonical import (
    GENESIS_PREV_HASH,
    assert_no_floats,
    canonical_bytes,
    sha256_hex,
)


def test_chaves_ordenadas_e_sem_espacos():
    assert canonical_bytes({"b": "2", "a": "1"}) == b'{"a":"1","b":"2"}'


def test_ordenacao_e_recursiva():
    obj = {"z": {"y": "1", "x": "2"}, "a": ["3", {"d": "4", "c": "5"}]}
    assert canonical_bytes(obj) == b'{"a":["3",{"c":"5","d":"4"}],"z":{"x":"2","y":"1"}}'


def test_acento_fica_literal_nao_escapado():
    assert canonical_bytes({"t": "ação"}) == '{"t":"ação"}'.encode()


def test_float_e_rejeitado_em_qualquer_profundidade():
    with pytest.raises(TypeError, match="float"):
        assert_no_floats({"a": [{"b": 1.5}]})
    with pytest.raises(TypeError, match="float"):
        canonical_bytes({"p": 0.62})


def test_int_e_bool_sao_permitidos():
    assert canonical_bytes({"n": 5, "ok": True}) == b'{"n":5,"ok":true}'


def test_hash_e_estavel_e_conhecido():
    # golden: se este valor mudar, a cadeia inteira ja publicada fica invalida
    assert sha256_hex({"a": "1"}) == (
        "9afeb0f2b203f254312ec8ded441d0318b7c34c57f8695ede42d2215a30c0960"
    )


def test_genesis_prev_hash():
    assert GENESIS_PREV_HASH == "0" * 64
