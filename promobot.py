import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
import re
from emojis import keyword_to_emoji, default_emoji

# Configurações do bot do Telegram
bot_token = 'TOKEN DO BOT'
chat_id = 'ID DO CHAT'

bot = telegram.Bot(token=bot_token)

# Lista de URLs das páginas com promoções
urls = [
    'https://www.promobit.com.br/promocoes/recentes/',
    'https://www.promobit.com.br/promocoes/loja/amazon/',
    'https://www.promobit.com.br/promocoes/loja/pichau/',
    'https://www.promobit.com.br/promocoes/loja/wine/',
    'https://www.promobit.com.br/promocoes/loja/kabum/',
    'https://www.promobit.com.br/promocoes/loja/magazine-luiza/',
    'https://www.promobit.com.br/promocoes/loja/aliexpress/',
    'https://www.promobit.com.br/promocoes/loja/terabyteshop/',
    'https://www.promobit.com.br/promocoes/informatica/',
    'https://www.promobit.com.br/promocoes/loja/mercado-livre/'
]

# Conjunto para armazenar URLs de promoções já enviadas
promo_set = set()

async def extract_deals():
    try:
        while True:
            for url in urls:
                # Refresh da página a cada iteração
                soup = refresh_page(url)

                # Verifica se houve mudanças no conteúdo da página
                if has_changes(soup, url):
                    # Extrai as promoções da página
                    deal_elements = soup.find_all(class_=re.compile('^font-sans text-neutral-low-100 whitespace-pre-wrap text-base'))[:5]

                    for deal in deal_elements:
                        title = deal.text.strip()
                        price_element = deal.find_previous('span', class_='font-sans text-base font-bold lg:text-xl whitespace-nowrap text-primary-500 dark:text-primary-100')
                        price = price_element.text.strip() if price_element else 'Preço não encontrado'
                        previous_price_element = price_element.find_previous('span', class_='font-sans text-sm whitespace-nowrap text-neutral-low-100 dark:text-neutral-high-100 line-through')
                        previous_price = previous_price_element.text.strip() if previous_price_element else 'Valor anterior não encontrado'
                        url_element = deal.find_previous('a', href=True)
                        product_url = f'https://www.promobit.com.br{url_element["href"]}' if url_element else 'URL não encontrada'

                        # Verifica se o URL do produto já foi enviado anteriormente
                        if product_url not in promo_set:
                            # Adiciona o URL ao conjunto de promoções enviadas
                            promo_set.add(product_url)

                            # Encontra a URL da imagem
                            image_url = None
                            if product_url != 'URL não encontrada':
                                product_page_response = requests.get(product_url)
                                product_page_soup = BeautifulSoup(product_page_response.content, 'html.parser')
                                img_element = product_page_soup.find('img', alt=re.compile(title))
                                if img_element:
                                    image_url = img_element['src']

                            # Adiciona emojis ao título com base nas palavras-chave
                            emoji_added = False
                            for keyword, emoji in keyword_to_emoji.items():
                                if keyword in title.lower():
                                    title = f'{emoji} {title}'
                                    emoji_added = True
                                    break

                            if not emoji_added:
                                title = f'{default_emoji} {title}'

                            await send_message(title, price, previous_price, product_url, image_url)
                            
                            # Aguarda 2 segundos entre cada mensagem enviada
                            await asyncio.sleep(2)

            # Aguarda 2 segundos antes de verificar novamente
            await asyncio.sleep(2)

    except requests.Timeout:
        print("O servidor não respondeu a tempo. Tentando novamente em alguns segundos...")
        await asyncio.sleep(2)
        await extract_deals()

def refresh_page(url):
    """
    Simula um refresh na página retornando o novo conteúdo da página.
    """
    response = requests.get(url)
    return BeautifulSoup(response.content, 'html.parser')


def has_changes(new_soup, url):
    """
    Verifica se houve mudanças no conteúdo da página comparando com a última vez que foi verificada.
    Retorna True se houver mudanças, False caso contrário.
    """
    # Aqui você pode implementar a lógica para verificar se há mudanças no conteúdo da página
    # Comparando com a última vez que foi verificada. Isso pode incluir comparação de elementos HTML
    # Ou outras técnicas dependendo da estrutura da página.

    # Por enquanto, vamos apenas retornar True sempre, para forçar a extração de promoções em todas as iterações.
    return True

async def send_message_with_photo(title, price, previous_price, url, image_url):
    try:
        # Baixa a imagem
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            # Salva a imagem localmente
            with open('temp_image.jpg', 'wb') as image_file:
                image_file.write(image_response.content)

            # Abre a imagem salva localmente
            with open('temp_image.jpg', 'rb') as image_file:
                # Envia a imagem como anexo junto com a mensagem
                await bot.send_photo(chat_id=chat_id, photo=image_file, caption=f'<b>{title}</b>\n\n💵 De: {previous_price} por {price}\n\n🛒 Ver Produto: {url}', parse_mode='HTML')
        else:
            print("Erro ao baixar a imagem. Status code:", image_response.status_code)
    except Exception as e:
        print("Erro ao enviar a mensagem com a imagem:", e)

async def send_message(title, price, previous_price, url, image_url):
    # Verifica se a URL do produto é válida
    if 'promobit.com.br/oferta/' in url:
        try:
            # Extrai o ID do URL original
            product_id = url.split('-')[-1]
            product_id = product_id[:-1] if product_id.endswith('/') else product_id
            # Cria o novo URL com o formato desejado
            redirect_url = f'https://www.promobit.com.br/Redirect/to/{product_id}/'

            # Verifica se a imagem está disponível
            if image_url:
                await send_message_with_photo(title, price, previous_price, redirect_url, image_url)
            else:
                # Se não houver imagem, envia apenas a mensagem
                message = f'<b>{title}</b>\n\n💵 De: {previous_price} por {price}\n\n🛒 Ver Produto: {redirect_url}'
                await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
        except Exception as e:
            print("Erro ao processar o URL do produto:", e)
    else:
        print("URL do produto inválido:", url)

# Inicia o loop de eventos do asyncio e executa a função extract_deals() em segundo plano
asyncio.run(extract_deals())