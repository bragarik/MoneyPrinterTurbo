"""Pasta e monitor de arquivos compartilhados com qualquer IA CLI."""

from pathlib import Path
from threading import Lock, Timer
from uuid import uuid4

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


WORKSPACE_NAME = "MoneyPrinterTurbo-CLI"
FIELD_FILES = ("tema.txt", "roteiro.txt", "palavras_chave.txt")
AGENT_INSTRUCTIONS = """# MoneyPrinterTurbo — IA CLI genérica

Esta pasta fica no home do usuário e é o ponto de troca entre o MoneyPrinterTurbo
e a IA CLI escolhida pelo usuário.
Você está preparando estes arquivos para serem lidos automaticamente pelo fork:
https://github.com/bragarik/MoneyPrinterTurbo
Como referência alternativa, o projeto original está em:
https://github.com/harry0703/MoneyPrinterTurbo
Consulte o repositório quando precisar entender exatamente como o aplicativo usa
os campos. Consulte primeiro o fork, pois ele contém esta integração por arquivos,
mas trabalhe nesta pasta apenas nos arquivos descritos abaixo.
O usuário pode pedir a geração ou a revisão de um ou mais destes campos:

- Tema do vídeo: `tema.txt`
- Roteiro do vídeo: `roteiro.txt`
- Palavras-chave do vídeo (opcional): `palavras_chave.txt`, uma por linha,
  sempre em inglês

O MoneyPrinterTurbo grava o arquivo correspondente quando o usuário define ou
altera tema, roteiro ou palavras-chave na interface. Leia esses arquivos como o
estado atual. O usuário também pode pedir que você gere ou revise qualquer campo;
nesse caso, sobrescreva somente o arquivo do campo solicitado.

Se o pedido não deixar claro quais campos o usuário quer gerar ou alterar, pergunte
antes de escrever qualquer arquivo. Por exemplo: "Você quer que eu gere o tema,
o roteiro, as palavras-chave do vídeo ou mais de um deles?" Aguarde a resposta.

Quando o pedido mencionar vários campos, produza um arquivo para cada campo pedido.
Não gere campos que o usuário não solicitou. Para uma revisão, leia os arquivos
existentes e use o pedido atual junto com esse contexto. Sobrescreva o arquivo do
campo alterado com o resultado completo; não acrescente uma segunda versão.

Escreva sempre as palavras-chave em inglês, mesmo se o tema, o roteiro ou a
conversa estiverem em português ou outro idioma. O campo é opcional: se o usuário
não o pedir, não crie nem altere `palavras_chave.txt`.

Você é responsável por manter o contexto das alterações ao longo da sessão. Antes
de cada nova resposta, consulte os arquivos existentes nesta pasta para recuperar
o estado atual, inclusive quando uma nova sessão de IA for iniciada. Se faltar
contexto para uma revisão, pergunte ao usuário em vez de adivinhar.

O usuário pode apagar ou esvaziar um arquivo por acidente e depois pedir para
refazê-lo. Você é responsável por lembrar a última versão conhecida durante a
sessão e, quando solicitado, reescrever o conteúdo completo no arquivo correto.
Se não tiver memória ou contexto suficiente para recuperar essa versão, explique
isso e pergunte ao usuário o que deve ser reconstruído antes de escrever.

Escreva apenas o conteúdo final de cada campo nos arquivos correspondentes, em
UTF-8, sem comentários sobre o processo. Não altere o código do MoneyPrinterTurbo.
"""


def workspace_path() -> Path:
    # Path.home() usa o home do sistema em que o aplicativo está rodando.
    return Path.home() / WORKSPACE_NAME


def ensure_workspace() -> Path:
    folder = workspace_path()
    folder.mkdir(parents=True, exist_ok=True)
    instructions = folder / "AGENTS.md"
    try:
        # Nunca substituímos instruções que o usuário já tenha ajustado.
        with instructions.open("x", encoding="utf-8") as output:
            output.write(AGENT_INSTRUCTIONS)
    except FileExistsError:
        pass
    # Os arquivos já ficam disponíveis para a IA desde a confirmação do modo.
    # O modo exclusivo não altera nem mesmo a data de um arquivo já existente.
    for filename in FIELD_FILES:
        try:
            (folder / filename).touch(exist_ok=False)
        except FileExistsError:
            pass
    return folder


def write_field(filename: str, value: str) -> Path:
    # Campos editados na WebUI entram no mesmo contrato de arquivos usado pela IA.
    if filename not in FIELD_FILES:
        raise ValueError(f"unsupported AI CLI field: {filename}")
    folder = ensure_workspace()
    field_file = folder / filename
    # A troca atômica impede que o monitor leia um arquivo pela metade.
    temporary = folder / f".{filename}.{uuid4().hex}.tmp"
    try:
        temporary.write_text(value.strip() + "\n", encoding="utf-8")
        temporary.replace(field_file)
    finally:
        temporary.unlink(missing_ok=True)
    return field_file


def write_subject(subject: str) -> Path:
    return write_field("tema.txt", subject)


_monitor_lock = Lock()
_monitor: "WorkspaceMonitor | None" = None


class _WorkspaceEventHandler(FileSystemEventHandler):
    def __init__(self, monitor: "WorkspaceMonitor"):
        self.monitor = monitor

    def on_any_event(self, event):
        # A escrita pode disparar vários eventos; só recalculamos o arquivo afetado.
        if event.is_directory:
            return
        paths = [Path(event.src_path)]
        if hasattr(event, "dest_path") and event.dest_path:
            paths.append(Path(event.dest_path))
        for path in paths:
            if path.parent == self.monitor.folder and path.name in FIELD_FILES:
                # Editores podem emitir um evento após truncar e outro após gravar.
                # A pequena espera impede que o vazio intermediário apague a tela.
                self.monitor.schedule_refresh(path.name)


class WorkspaceMonitor:
    def __init__(self, folder: Path):
        self.folder = folder
        self._lock = Lock()
        self._ready = {filename: False for filename in FIELD_FILES}
        self._contents: dict[str, str | None] = {
            filename: None for filename in FIELD_FILES
        }
        self._refresh_timers: dict[str, Timer] = {}
        for filename in FIELD_FILES:
            self.refresh(filename)
        self._observer = Observer()
        self._observer.schedule(_WorkspaceEventHandler(self), str(folder), recursive=False)
        self._observer.start()

    def schedule_refresh(self, filename: str) -> None:
        with self._lock:
            previous_timer = self._refresh_timers.get(filename)
            if previous_timer is not None:
                previous_timer.cancel()
            timer = Timer(0.1, self._run_scheduled_refresh, args=(filename,))
            timer.daemon = True
            self._refresh_timers[filename] = timer
            timer.start()

    def _run_scheduled_refresh(self, filename: str) -> None:
        self.refresh(filename)
        with self._lock:
            self._refresh_timers.pop(filename, None)

    def refresh(self, filename: str) -> None:
        field_file = self.folder / filename
        try:
            content = (
                field_file.read_text(encoding="utf-8").strip()
                if field_file.is_file()
                else None
            )
        except (OSError, UnicodeError):
            content = None
        with self._lock:
            self._contents[filename] = content
            self._ready[filename] = bool(content)

    def snapshot(self) -> dict[str, bool]:
        # A interface lê este estado em memória; ela não consulta os arquivos.
        with self._lock:
            return dict(self._ready)

    def contents(self) -> dict[str, str | None]:
        # O fragment recebe uma cópia consistente dos textos após cada evento.
        with self._lock:
            return dict(self._contents)


def get_monitor() -> WorkspaceMonitor:
    global _monitor
    folder = workspace_path()
    with _monitor_lock:
        if _monitor is not None and _monitor.folder == folder and _monitor._observer.is_alive():
            return _monitor
        # Só ao iniciar ou recuperar o observador tocamos na pasta novamente.
        folder = ensure_workspace()
        _monitor = WorkspaceMonitor(folder)
        return _monitor
