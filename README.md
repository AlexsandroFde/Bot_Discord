# Bot Discord

Este é um bot Discord escrito em Python usando a biblioteca discord.py. O bot possui várias funcionalidades, incluindo:

- Spam de mensagens
- Movimentação de usuários entre canais de voz
- Comandos para interromper o spam
- Limpeza de mensagens
- Envio de mensagens
- Mute e desmute de usuários
- Implementação de uma "ditadura" para impedir mensagens

## Como usar

1. **Instalação das dependências:**
   Certifique-se de ter o Python e a biblioteca discord.py instalados. Você pode instalar a biblioteca discord.py usando o pip:
    ```bash
    pip install discord.py
    ```

2. **Configuração do token:**
   Antes de executar o bot, você precisará configurar o token do bot. Para fazer isso, defina a variável de ambiente `BOT_TOKEN` com o token do seu bot Discord. Você pode definir essa variável de ambiente no seu sistema operacional. No Windows, você pode seguir estas instruções: [Como definir uma variável de ambiente no Windows](https://www.architectryan.com/2018/08/31/how-to-change-environment-variables-on-windows-10/). Em sistemas Unix-like (Linux, macOS), você pode usar o comando `export` no terminal. Certifique-se de que o nome da variável seja `BOT_TOKEN` e o valor seja o token do seu bot.

3. **Execução do bot:**
    Execute o arquivo Python para iniciar o bot:

## Funcionalidades Principais

- **Spam de Mensagens:**
- O bot pode enviar várias mensagens para um usuário especificado.

- **Movimentação de Usuários:**
- O bot pode mover um usuário entre diferentes canais de voz.

- **Interromper o Spam:**
- Comando para interromper o spam em andamento.

- **Limpeza de Mensagens:**
- O bot pode limpar as mensagens de um usuário específico ou suas próprias mensagens no canal.

- **Envio de Mensagens:**
- Os usuários autorizados podem usar o bot para enviar mensagens.

- **Mute e Desmute de Usuários:**
- O bot pode mutar e desmutar usuários nos canais de voz.

- **Ditadura:**
- Implementação de uma "ditadura" para impedir que os usuários mandem mensagens.

## Contribuição
Se você quiser contribuir para este projeto, sinta-se à vontade para abrir uma issue ou enviar um pull request.
