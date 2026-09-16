"""Verifica a passagem dos eventos de arquivos para os campos da WebUI."""

import ast
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).parents[2]


class RerunRequested(Exception):
    pass


class FakeStreamlit:
    def __init__(self):
        self.session_state = {"video_subject": "", "video_script": "", "video_terms": ""}

    def fragment(self, **_kwargs):
        return lambda function: function

    def rerun(self, **_kwargs):
        raise RerunRequested

    def info(self, *_args, **_kwargs):
        pass

    def caption(self, *_args, **_kwargs):
        pass

    def warning(self, *_args, **_kwargs):
        pass


class FakeMonitor:
    def __init__(self):
        self.fields = {
            "tema.txt": "Tema da IA",
            "roteiro.txt": "Roteiro da IA",
            "palavras_chave.txt": "keyword one\nkeyword two",
        }

    def snapshot(self):
        return {name: bool(content) for name, content in self.fields.items()}

    def contents(self):
        return dict(self.fields)


def _load_ui_functions(streamlit, monitor):
    tree = ast.parse((ROOT / "webui" / "Main.py").read_text(encoding="utf-8"))
    names = {
        "FILE_CLI_FIELD_WIDGETS",
        "_apply_pending_file_cli_fields",
        "_collect_file_cli_changes",
        "_sync_file_cli_fields_before_widgets",
        "_render_file_cli_monitor_status",
    }
    nodes = [
        node
        for node in tree.body
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id in names
                for target in node.targets
            )
        )
        or isinstance(node, ast.FunctionDef) and node.name in names
    ]
    namespace = {
        "st": streamlit,
        "config": SimpleNamespace(app={"file_cli_enabled": True}),
        "file_cli_workspace": SimpleNamespace(
            workspace_path=lambda: Path("/tmp/generic-cli"),
            get_monitor=lambda: monitor,
        ),
        "tr": lambda key: key,
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(ROOT / "webui" / "Main.py"), "exec"), namespace)
    return namespace


def test_file_changes_fill_and_clear_matching_fields():
    streamlit = FakeStreamlit()
    monitor = FakeMonitor()
    ui = _load_ui_functions(streamlit, monitor)

    ui["_sync_file_cli_fields_before_widgets"]()
    assert streamlit.session_state["video_subject"] == "Tema da IA"
    assert streamlit.session_state["video_script"] == "Roteiro da IA"
    assert streamlit.session_state["video_terms"] == "keyword one\nkeyword two"

    monitor.fields["roteiro.txt"] = "Roteiro revisado"
    try:
        ui["_render_file_cli_monitor_status"]()
    except RerunRequested:
        pass
    else:
        raise AssertionError("changing a file should request a full UI rerun")
    ui["_apply_pending_file_cli_fields"]()
    assert streamlit.session_state["video_script"] == "Roteiro revisado"
    assert streamlit.session_state["video_subject"] == "Tema da IA"

    monitor.fields["roteiro.txt"] = None
    try:
        ui["_render_file_cli_monitor_status"]()
    except RerunRequested:
        pass
    else:
        raise AssertionError("deleting a file should update its field")
    ui["_apply_pending_file_cli_fields"]()
    assert streamlit.session_state["video_script"] == ""
