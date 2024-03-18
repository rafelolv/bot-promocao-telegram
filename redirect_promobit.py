import requests
from bs4 import BeautifulSoup
import re


def findLink (promo_code):
    url = 'https://www.promobit.com.br/Redirect/to/'+str(promo_code)+'/'

    response = requests.get(url)

    content = response.text

    # Usando expressão regular para buscar a URL
    link_match = re.search(r'href="(https?://.*?)"', content)

    link_url = link_match.group(1)
    #print("Link encontrado:", link_url)

    
    if "mercadolivre" in link_url:
        return (mercado_livre(link_url))

    elif "url=" in link_url or "ued=" in link_url or "destination:" in link_url:
        return (lojas_deep(link_url))
    
    elif "ulp=" in link_url:
        return (banggood_store(link_url))
    
    elif "afilio.com.br" in link_url:
        return (vivo_store (link_url))

    elif "shope.ee" in link_url:
        return (shopee_store (link_url))
 
    else:
        return(lojas_normais(link_url))

def mercado_livre (url):

    ml_links = []
    response = requests.get(url)

    content = response.text

    link_match = re.finditer(r'href="(https?://.*?)"', content)

    for match in link_match:
        link_url = match.group(1)
        ml_links.append(link_url)

    indice = ml_links.index("https://www.mercadolivre.com.br/gz/cart/v2")

    link_direto = ml_links[indice+1].split('#')[0]

    return (link_direto)

def lojas_normais (url):
    link_direto = url.split('?')[0]
    #print (link_direto)
    return (link_direto)

def lojas_deep (url):

    if 'ued=' in url:
        partes = url.split('ued=')
    elif 'url=' in url:
        partes = url.split('url=')
    elif 'destination:'in url:
        partes = url.split('destination:')

    url_parte = partes[1]

    partes_url = url_parte.split('%3F')

    url_done = partes_url[0]

    link_direto = url_done.replace('%3A', ':').replace('%2F', '/').replace('%3F', '')

    #print (link_direto)
    return (link_direto)

def banggood_store (url):
   
    partes = url.split('ulp=')

    url_parte = partes[1]

    partes_url = url_parte.split('&')

    url_done = partes_url[0]

    link_direto = url_done.replace('%3A', ':').replace('%2F', '/').replace('%3F', '')

    #print (link_direto)
    return (link_direto)

def vivo_store (url):

    response = requests.get(url)
    
    content = response.text
    #print (content)

    padrao = r'cZone: "([^"]+)",.*?cUPMDTk: "([^"]+)'

    match = re.search(padrao, content)

    if match:

        cZone = match.group(1)

        cUPMDTk = match.group(2)

        url_completa = f"https://{cZone}{cUPMDTk}"
        
        partes = url_completa.split('?')[0]

        link_direto = partes.replace('/', '/')

        #print(link_direto)
    return (link_direto)

def shopee_store (url):
    
    response = requests.head(url, allow_redirects=True)

    link_direto = response.url.split('?')[0]+'?'
    #print (link_direto)
    return (link_direto)