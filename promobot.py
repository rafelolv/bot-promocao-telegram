import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
import re
from emojis import keyword_to_emoji, default_emoji
import os
from datetime import datetime
from redirect_promobit import findLink

# Configurações do bot do Telegram
bot_token = '7032724196:AAGbIy3kafhyn4mljQZB9qcFNeb_JwhXOv0'
chat_id = '-1002106191183'

bot = telegram.Bot(token=bot_token)

# Lista de URLs das páginas com promoções
urls = [
    'https://www.promobit.com.br/promocoes/loja/amazon/',
    'https://www.promobit.com.br/promocoes/loja/magazine-luiza/',
    'https://www.promobit.com.br/promocoes/loja/casas-bahia/',
    'https://www.promobit.com.br/promocoes/loja/steam/',
    'https://www.promobit.com.br/promocoes/loja/samsung/',
    'https://www.promobit.com.br/promocoes/loja/mercado-livre/',
    'https://www.promobit.com.br/promocoes/loja/aliexpress/',
    'https://www.promobit.com.br/promocoes/loja/nuuvem/',
    'https://www.promobit.com.br/promocoes/loja/kabum/',
    'https://www.promobit.com.br/promocoes/loja/wine/',
    'https://www.promobit.com.br/promocoes/loja/pichau/',
    'https://www.promobit.com.br/promocoes/loja/terabyteshop/',
    'https://www.promobit.com.br/promocoes/loja/fastshop/',
    'https://www.promobit.com.br/promocoes/loja/americanas/',
    'https://www.promobit.com.br/promocoes/informatica/',
    'https://www.promobit.com.br/promocoes/eletronicos-audio-e-video/',
    'https://www.promobit.com.br/promocoes/smartphones-tablets-e-telefones/',
    'https://www.promobit.com.br/promocoes/games/',
    'https://www.promobit.com.br/promocoes/loja/ponto-frio/',
    'https://www.promobit.com.br/promocoes/perfumes-e-beleza/',
    'https://www.promobit.com.br/promocoes/cama-mesa-e-banho/',
    'https://www.promobit.com.br/promocoes/saude-e-higiene/',
    'https://www.promobit.com.br/promocoes/supermercado-e-delivery/',
    'https://www.promobit.com.br/promocoes/eletrodomesticos/'
]


# Arquivo para armazenar as URLs das promoções enviadas
sent_promos_file = 'sent_promos.txt'

async def extract_deals():
    try:
        while True:
            for url in urls:
                # Limpa o cache atual
                await asyncio.sleep(2)

                # Refresh da página
                print(f"{datetime.now()} - Atualizando página: {url}")
                soup = refresh_page(url)

                # Verifica se houve mudanças no conteúdo da página
                if has_changes(soup, url):
                    print(f"{datetime.now()} - Detectadas mudanças na página: {url}")
                    # Extrai as promoções da página
                    deal_elements = soup.find_all(class_=re.compile('^font-sans text-neutral-low-100 whitespace-pre-wrap text-base'))[:10]

                    for deal in deal_elements:
                        title = deal.text.strip()
                        price_element = deal.find_previous('span', class_='font-sans text-base font-bold lg:text-xl whitespace-nowrap text-primary-500 dark:text-primary-100')
                        price = price_element.text.strip() if price_element else 'Preço não encontrado'
                        previous_price_element = price_element.find_previous('span', class_='font-sans text-sm whitespace-nowrap text-neutral-low-100 dark:text-neutral-high-100 line-through')
                        previous_price = previous_price_element.text.strip() if previous_price_element else '?'
                        url_element = deal.find_previous('a', href=True)
                        product_url = f'https://www.promobit.com.br{url_element["href"]}' if url_element else 'URL não encontrada'

                        # Verifica se o URL do produto já foi enviado anteriormente
                        if not is_url_sent(product_url):
                            # Adiciona a URL ao arquivo de URLs enviadas
                            mark_url_as_sent(product_url)

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

                            # Verifica se há cupom disponível
                            coupon = None
                            coupon_match = re.search(r'"offerCoupon":"([^"]+)"', product_page_response.text)
                            if coupon_match:
                                coupon = coupon_match.group(1)

                            await send_message(title, price, previous_price, product_url, image_url, coupon)
                            
                            # Aguarda 2 segundos entre cada mensagem enviada
                            await asyncio.sleep(2)

            # Aguarda 1 segundo antes de verificar novamente
            await asyncio.sleep(1)

            # Aguarda 5 segundos antes de executar novamente
            await asyncio.sleep(5)

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
    # Carrega o conteúdo da última verificação, se disponível
    last_content = load_last_content(url)
    
    # Se não houver conteúdo anterior, assume que houve mudança
    if not last_content:
        return True

    # Verifica se o conteúdo atual é diferente do conteúdo anterior
    return str(new_soup) != str(last_content)


def load_last_content(url):
    """
    Carrega o conteúdo da última verificação da URL especificada.
    Retorna None se não houver conteúdo anterior.
    """
    file_path = f"{url.replace('/', '_').replace(':', '_')}.html"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return BeautifulSoup(file.read(), "html.parser")
    return None

def save_current_content(new_soup, url):
    """
    Salva o conteúdo atual da página para uso futuro.
    """
    file_path = f"{url.replace('/', '_').replace(':', '_')}.html"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(str(new_soup))

async def send_message_with_photo(message, image_url):
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
                await bot.send_photo(chat_id=chat_id, photo=image_file, caption=message, parse_mode='HTML')
        else:
            print("Erro ao baixar a imagem. Status code:", image_response.status_code)
    except Exception as e:
        print("Erro ao enviar a mensagem com a imagem:", e)

async def send_message(title, price, previous_price, url, image_url, coupon=None):
    # Verifica se a URL do produto é válida
    if 'promobit.com.br/oferta/' in url:
        try:
            # Extrai o ID do URL original
            product_id = url.split('-')[-1]
            product_id = product_id[:-1] if product_id.endswith('/') else product_id
            # Cria o novo URL com o formato desejado
            link_direto = findLink(product_id)
            await asyncio.sleep(5)


            # Monta a mensagem com base nos dados
            message = f'<b>{title}</b>\n\n'
            if coupon:
                message += f'🎟️ <b>CUPOM:</b> {coupon}\n'
            message += f'💵 De: {previous_price} por {price}\n\n🛒 Ver Produto: {link_direto}'

            # Verifica se a imagem está disponível
            if image_url:
                # Envia a mensagem com a foto
                await send_message_with_photo(message, image_url)
            else:
                # Envia a mensagem sem foto
                await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
        except Exception as e:
            print("Erro ao processar o URL do produto:", e)
    else:
        print("URL do produto inválido:", url)

def is_url_sent(url):
    with open('sent_promos.txt', 'r') as file:
        for line in file:
            if url.strip() == line.strip():
                return True
    return False


def mark_url_as_sent(url):
    with open('sent_promos.txt', 'a') as file:
        file.write(url + '\n')

async def main():
    await extract_deals()

if __name__ == "__main__":
    asyncio.run(main())