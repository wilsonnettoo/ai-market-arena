from pathlib import Path

from arena.audit.chain import (
    append_entry,
    build_entry,
    file_sha256,
    last_hash,
    read_chain,
    verify_chain,
)
from arena.canonical import GENESIS_PREV_HASH, sha256_hex


def _dia(tmp: Path, chain: Path, dia: str, conteudo: str) -> Path:
    f = tmp / f"data/forecasts/{dia}.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(conteudo, encoding="utf-8")
    e = build_entry(dia, f"{dia}T20:15:00Z", [f], last_hash(chain), tmp)
    append_entry(chain, e)
    return f


def test_cadeia_vazia_devolve_genesis(tmp_path):
    assert last_hash(tmp_path / "CHAIN.jsonl") == GENESIS_PREV_HASH


def test_dois_dias_encadeiam_e_verificam(tmp_path):
    chain = tmp_path / "CHAIN.jsonl"
    _dia(tmp_path, chain, "2026-08-03", '{"a":"1"}')
    _dia(tmp_path, chain, "2026-08-04", '{"a":"2"}')
    assert verify_chain(chain, tmp_path) == []


def test_editar_arquivo_antigo_quebra_a_cadeia(tmp_path):
    chain = tmp_path / "CHAIN.jsonl"
    f = _dia(tmp_path, chain, "2026-08-03", '{"a":"1"}')
    _dia(tmp_path, chain, "2026-08-04", '{"a":"2"}')
    assert verify_chain(chain, tmp_path) == [], "pre-condicao: cadeia integra antes da fraude"
    f.write_text('{"a":"999"}', encoding="utf-8")  # a fraude
    erros = verify_chain(chain, tmp_path)
    assert any("sha256 divergente" in e for e in erros)


def test_remover_arquivo_quebra_a_cadeia(tmp_path):
    chain = tmp_path / "CHAIN.jsonl"
    f = _dia(tmp_path, chain, "2026-08-03", '{"a":"1"}')
    f.unlink()
    assert any("ausente" in e for e in verify_chain(chain, tmp_path))


def test_reescrever_linha_da_cadeia_quebra_o_elo(tmp_path):
    chain = tmp_path / "CHAIN.jsonl"
    _dia(tmp_path, chain, "2026-08-03", '{"a":"1"}')
    _dia(tmp_path, chain, "2026-08-04", '{"a":"2"}')
    linhas = chain.read_text(encoding="utf-8").splitlines()
    linhas[0] = linhas[0].replace('"2026-08-03"', '"2026-08-02"')
    chain.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    erros = verify_chain(chain, tmp_path)
    assert any("entry_hash" in e or "prev_hash" in e for e in erros)


def test_remover_entrada_do_meio_quebra_o_elo(tmp_path):
    """Cada entry_hash continua internamente valido; o que quebra e a LIGACAO.

    Sem este teste o check de prev_hash fica sem cobertura: um atacante que
    recompute os entry_hash corretamente e remova uma entrada nao seria pego.
    Descoberto por teste de mutacao — desligar o check de prev_hash nao
    quebrava nenhum teste da suite original.
    """
    chain = tmp_path / "CHAIN.jsonl"
    for dia, conteudo in (("2026-08-03", '{"a":"1"}'), ("2026-08-04", '{"a":"2"}'),
                          ("2026-08-05", '{"a":"3"}')):
        _dia(tmp_path, chain, dia, conteudo)
    assert verify_chain(chain, tmp_path) == []

    linhas = chain.read_text(encoding="utf-8").splitlines()
    del linhas[1]  # remove o meio, sem tocar em nenhum entry_hash
    chain.write_text("\n".join(linhas) + "\n", encoding="utf-8")

    erros = verify_chain(chain, tmp_path)
    assert any("prev_hash" in e for e in erros), erros
    assert not any("entry_hash divergente" in e for e in erros), (
        "os entry_hash continuam validos; so o elo quebrou"
    )


def test_reordenar_entradas_quebra_o_elo(tmp_path):
    chain = tmp_path / "CHAIN.jsonl"
    _dia(tmp_path, chain, "2026-08-03", '{"a":"1"}')
    _dia(tmp_path, chain, "2026-08-04", '{"a":"2"}')
    linhas = chain.read_text(encoding="utf-8").splitlines()
    chain.write_text("\n".join([linhas[1], linhas[0]]) + "\n", encoding="utf-8")
    assert any("prev_hash" in e for e in verify_chain(chain, tmp_path))


def test_primeira_entrada_forjada_nao_aponta_para_genesis(tmp_path):
    """Truncar o inicio da cadeia e a fraude mais barata: apaga o passado
    inconveniente e deixa o resto internamente consistente."""
    chain = tmp_path / "CHAIN.jsonl"
    _dia(tmp_path, chain, "2026-08-03", '{"a":"1"}')
    _dia(tmp_path, chain, "2026-08-04", '{"a":"2"}')
    linhas = chain.read_text(encoding="utf-8").splitlines()
    chain.write_text(linhas[1] + "\n", encoding="utf-8")  # descarta a primeira
    erros = verify_chain(chain, tmp_path)
    assert any("prev_hash" in e for e in erros), erros


def test_primeira_entrada_precisa_apontar_para_genesis(tmp_path):
    chain = tmp_path / "CHAIN.jsonl"
    _dia(tmp_path, chain, "2026-08-03", '{"a":"1"}')
    assert read_chain(chain)[0]["prev_hash"] == GENESIS_PREV_HASH
    assert verify_chain(chain, tmp_path) == []


def test_entry_hash_e_do_dict_sem_a_propria_chave(tmp_path):
    """Se entry_hash entrasse no calculo do proprio entry_hash, seria impossivel
    recomputa-lo — e o verificador do navegador nao conseguiria conferir nada."""
    chain = tmp_path / "CHAIN.jsonl"
    _dia(tmp_path, chain, "2026-08-03", '{"a":"1"}')
    entrada = read_chain(chain)[0]
    corpo = {k: v for k, v in entrada.items() if k != "entry_hash"}
    assert sha256_hex(corpo) == entrada["entry_hash"]


def test_append_nao_reescreve_linha_anterior(tmp_path):
    """Append-only de verdade: os bytes da primeira linha nao mudam."""
    chain = tmp_path / "CHAIN.jsonl"
    _dia(tmp_path, chain, "2026-08-03", '{"a":"1"}')
    primeira = chain.read_bytes()
    _dia(tmp_path, chain, "2026-08-04", '{"a":"2"}')
    depois = chain.read_bytes()
    assert depois.startswith(primeira)


def test_file_sha256_e_dos_bytes_em_disco(tmp_path):
    """Nao da forma canonica: o arquivo publicado pode ter qualquer formatacao,
    e o que a cadeia promete e que AQUELES bytes nao mudaram."""
    import hashlib

    f = tmp_path / "x.json"
    bruto = b'{ "a" : "1" }'  # espacos de proposito, nao e forma canonica
    f.write_bytes(bruto)
    assert file_sha256(f) == hashlib.sha256(bruto).hexdigest()


def test_arquivos_da_entrada_ficam_ordenados_por_path(tmp_path):
    chain = tmp_path / "CHAIN.jsonl"
    for nome in ("z.json", "a.json", "m.json"):
        (tmp_path / nome).write_text("{}", encoding="utf-8")
    e = build_entry(
        "2026-08-03",
        "2026-08-03T20:15:00Z",
        [tmp_path / "z.json", tmp_path / "a.json", tmp_path / "m.json"],
        last_hash(chain),
        tmp_path,
    )
    assert [d["path"] for d in e["files"]] == ["a.json", "m.json", "z.json"]
