<div align="center">

# MoneyPrinterTurbo — IA CLI

Crie vídeos com o MoneyPrinterTurbo usando qualquer assistente de IA que consiga
ler e escrever arquivos locais e seguir instruções em um `AGENTS.md`.

[Projeto original](https://github.com/harry0703/MoneyPrinterTurbo) ·
[README original](README-ORIGINAL.md) ·
[Fork](https://github.com/bragarik/MoneyPrinterTurbo)

</div>

## Sobre este fork

Este projeto deriva do
[MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo), criado por
[harry0703](https://github.com/harry0703). Ele mantém o fluxo de criação de
vídeos do projeto original e acrescenta uma integração por arquivos para usar
uma IA executada por CLI na geração do tema, roteiro e palavras-chave.

O modo **Usar qualquer IA CLI com AGENTS.md** não depende de uma API de LLM para
gerar esses textos. Você pode usar o assistente de sua preferência, desde que
ele tenha acesso à pasta local e respeite o arquivo `AGENTS.md`.

Serviços escolhidos para buscar ou gerar materiais, sintetizar voz, criar
imagens ou executar outras etapas ainda podem exigir suas próprias chaves de
API. O modo CLI substitui especificamente a geração do conteúdo textual.

## Como funciona

Ao ativar e confirmar o modo de IA CLI nas configurações, o MoneyPrinterTurbo
cria esta pasta na home do usuário que está executando o aplicativo:

```text
~/MoneyPrinterTurbo-CLI/
├── AGENTS.md
├── tema.txt
├── roteiro.txt
└── palavras_chave.txt
```

No Windows, `~` normalmente corresponde a `C:\Users\SeuUsuario`. Em Linux e
macOS, corresponde ao diretório home do usuário.

O `AGENTS.md` explica à IA como tratar cada campo:

- `tema.txt`: tema do vídeo;
- `roteiro.txt`: texto completo da narração;
- `palavras_chave.txt`: palavras-chave em inglês, uma por linha.

O MoneyPrinterTurbo monitora esses arquivos e atualiza os campos da tela assim
que eles mudam. Se você editar um desses campos na interface e sair do campo, o
arquivo correspondente também será atualizado.

Quando um pedido não deixar claro se você quer gerar o tema, o roteiro ou as
palavras-chave, a IA deverá perguntar antes de escrever. Ela também pode gerar
os três arquivos em uma mesma solicitação e deve sobrescrever o arquivo
correspondente sempre que você pedir uma alteração.

## Usando uma IA CLI

1. Inicie o MoneyPrinterTurbo e abra **Ajustes**.
2. Entre em **Configurações do LLM**.
3. Marque **Usar qualquer IA CLI com AGENTS.md** e confirme.
4. Abra um terminal dentro de `~/MoneyPrinterTurbo-CLI`.
5. Inicie ali a IA CLI de sua preferência.
6. Peça explicitamente o tema, o roteiro, as palavras-chave ou uma combinação
   desses campos.
7. Confira os campos preenchidos automaticamente na interface.
8. Ajuste as demais opções e clique em **Gerar vídeo**.

No modo CLI, o botão **Gerar vídeo** usa os valores que já estão na tela. O
roteiro é obrigatório. As palavras-chave também são obrigatórias para fontes de
material não locais. Se estiverem ausentes, o aplicativo exibirá um erro em vez
de chamar silenciosamente uma API de LLM.

## Instalação

O projeto requer Python 3.11 ou mais recente e FFmpeg. O gerenciador
[uv](https://docs.astral.sh/uv/) é a maneira recomendada de instalar as
dependências.

```bash
git clone https://github.com/bragarik/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo
uv sync --frozen
```

Consulte a documentação do projeto original para detalhes adicionais sobre
FFmpeg, Docker, aceleração por GPU e provedores:

- [README original em chinês](README-ORIGINAL.md)
- [Documentação em inglês](README-en.md)
- [Documentação em japonês](README-ja.md)

## Executando

No Windows:

```bat
webui.bat
```

Em Linux ou macOS:

```bash
./webui.sh
```

O endereço padrão é <http://127.0.0.1:8501>. Se a porta estiver ocupada, o
inicializador escolherá automaticamente outra porta disponível entre 8502 e
8599 e mostrará o endereço correto no terminal.

## Recursos herdados

Além da integração com IA CLI, este fork conserva os recursos do
MoneyPrinterTurbo, incluindo composição automática de vídeo, legendas,
sintetização de voz, música de fundo, materiais locais e integração com fontes
externas. A disponibilidade de cada recurso depende da configuração e dos
serviços selecionados.

## Créditos e licença

Todo o crédito pelo projeto-base pertence aos autores e colaboradores do
[MoneyPrinterTurbo original](https://github.com/harry0703/MoneyPrinterTurbo).
Este fork é distribuído sob a mesma licença MIT, disponível em [LICENSE](LICENSE).
