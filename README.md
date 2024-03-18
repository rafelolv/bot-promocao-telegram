# Bot de promoções para Telegram

Este é um bot do Telegram que envia promoções para um chat/grupo específico. Ele faz uso de web scraping para extrair informações sobre as promoções e as envia para o chat configurado.

## Configuração do Bot do Telegram

Para utilizar este bot, é necessário configurar um bot no Telegram e obter o token do bot e o ID do chat para onde as promoções serão enviadas. Substitua os valores das variáveis `bot_token` e `chat_id` com as suas próprias credenciais.

## Requisitos

- **Python 3.7 ou superior**
- Bibliotecas Python:
  - requests
  - BeautifulSoup
  - telegram
  - asyncio
  - emojis
  - datetime
  - os
  - re

Você pode instalar as dependências utilizando o comando pip:

**pip install requests beautifulsoup4 python-telegram-bot asyncio emojis datetime os re**

## Funcionamento

O bot verifica regularmente as páginas listadas na variável `urls` em busca de novas promoções. Se uma nova promoção for encontrada, o bot a envia para o chat especificado. As promoções são verificadas a cada 2 segundos (Não reduza para menos do que isso ou seu bot vai tomar timeout do Telegram por alguns minutos)

As promoções são extraídas da página utilizando web scraping com a lib BeautifulSoup. O bot verifica se houve mudanças no conteúdo das páginas para determinar se deve extrair novas promoções. Atualmente, a função `has_changes` sempre retorna True para forçar a extração de promoções em todas as iterações.

## Funcionalidades Adicionais

- O bot adiciona emojis aos títulos das promoções com base em palavras-chave. Caso deseje mudar o emote de acordo com o produto, acesse o arquivo "emojis.py" e altere da forma que desejar.
- As mensagens de promoção incluem informações sobre o preço atual, preço anterior (se disponível), URL do produto e uma imagem representativa (se disponível).

## Como Executar

1. Configure as variáveis `bot_token` e `chat_id` com as credenciais do seu bot Telegram.
2. Execute o script Python.
3. O bot começará a enviar as promoções para o chat configurado.

Certifique-se de manter o script em execução para continuar recebendo as promoções atualizadas.
