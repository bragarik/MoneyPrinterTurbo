import time

from app.services import file_cli_workspace


def test_ensure_workspace_creates_contract_files_without_overwriting(monkeypatch, tmp_path):
    workspace = tmp_path / "MoneyPrinterTurbo-CLI"
    workspace.mkdir()
    existing_script = workspace / "roteiro.txt"
    existing_script.write_text("roteiro existente\n", encoding="utf-8")
    monkeypatch.setattr(file_cli_workspace, "workspace_path", lambda: workspace)

    result = file_cli_workspace.ensure_workspace()

    assert result == workspace
    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == (
        file_cli_workspace.AGENT_INSTRUCTIONS
    )
    assert existing_script.read_text(encoding="utf-8") == "roteiro existente\n"
    for filename in file_cli_workspace.FIELD_FILES:
        assert (workspace / filename).is_file()


def test_monitor_waits_until_file_write_is_stable(tmp_path):
    workspace = tmp_path / "MoneyPrinterTurbo-CLI"
    workspace.mkdir()
    script = workspace / "roteiro.txt"
    script.write_text("roteiro anterior", encoding="utf-8")
    monitor = file_cli_workspace.WorkspaceMonitor(workspace)
    try:
        # Simula um editor que trunca o arquivo antes de escrever o resultado.
        script.write_text("", encoding="utf-8")
        monitor.schedule_refresh("roteiro.txt")
        script.write_text("roteiro atualizado", encoding="utf-8")
        monitor.schedule_refresh("roteiro.txt")
        time.sleep(0.2)

        assert monitor.contents()["roteiro.txt"] == "roteiro atualizado"
    finally:
        monitor._observer.stop()
        monitor._observer.join(timeout=1)
