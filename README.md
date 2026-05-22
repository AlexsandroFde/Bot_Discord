# Bot Discord — Sayoko

Bot do Discord escrito em Python com a biblioteca [discord.py](https://discordpy.readthedocs.io/),
focado em moderação, caos divertido e um soundpad de áudios na call.

## Funcionalidades

### 🎵 Áudio
- **Soundpad** (`/play`) — entra na call e abre um painel interativo com a biblioteca de áudios.
  - Paginação para bibliotecas com mais de 25 áudios.
  - Botões de volume (🔉 🔊), aleatório (🔀), parar (⏹) e atualizar (🔄).
  - O painel sobrevive a reinícios do bot.
- **`/play <áudio>`** — toca um áudio direto, com autocomplete por nome.
- **Jukebox** (`/jukebox`) — toca áudios aleatórios da biblioteca em loop.
- **YouTube** (`/youtube <link ou busca>`) — toca o áudio de um vídeo do YouTube na call.
- **`/add_audio`**, **`/del_audio`**, **`/rename_audio`** — gerenciam a biblioteca de áudios.
- **`/top`** — ranking dos áudios mais tocados.
- **`/sair`** — tira o bot da call.
- Normalização de loudness (todos os áudios saem num volume parecido) e auto-desconexão
  quando a call fica vazia ou ociosa.

### 🛡️ Moderação
- **Spam de mensagens** e **spam em call** — envia mensagens em massa / move usuário entre calls.
- **`/stop`** — interrompe o spam em andamento.
- **Limpeza de mensagens** — apaga mensagens de um usuário ou do próprio bot.
- **Envio de mensagens** pelo bot.
- **Mute / desmute** de usuários nos canais de voz.
- **Ditadura / Democracia** — bloqueia ou libera o envio de mensagens no servidor.

### ℹ️ Outros
- **`/info`** — informações sobre a Sayoko.

## Requisitos

- **Python 3.12+**
- **FFmpeg** instalado e disponível no `PATH` (necessário para reproduzir áudio).
- Dependências Python:
  ```bash
  pip install -U discord.py python-dotenv PyNaCl yt-dlp
  ```
  - `discord.py` — biblioteca do bot.
  - `python-dotenv` — carrega o token do arquivo `.env`.
  - `PyNaCl` — suporte a voz.
  - `yt-dlp` — comando `/youtube` (opcional; sem ele apenas o `/youtube` fica indisponível).

## Configuração

Crie um arquivo `.env` na raiz do projeto com o token do seu bot:

```env
DISCORD_TOKEN=seu_token_aqui
```

## Execução

```bash
python main.py
```

Na primeira inicialização o bot sincroniza os slash commands com os servidores.
Reinicie o bot sempre que adicionar ou alterar comandos.

## Estrutura

```
Bot_Discord/
├── assets/              # biblioteca de áudios (.mp3, .wav, .ogg, .m4a)
├── bot/
│   ├── client.py        # cliente, command tree e tratamento de erros
│   ├── commands/        # comandos (audio, moderation, mute, spam, info)
│   ├── events/          # handlers de eventos
│   └── utils/           # helpers: voz, estatísticas, etc.
├── main.py              # ponto de entrada
└── .env                 # token (não versionado)
```

## Contribuição

Sinta-se à vontade para abrir uma issue ou enviar um pull request.
