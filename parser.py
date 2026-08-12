import re
import html
from typing import Tuple, Optional
import httpx
from config import CATEGORIES

# Dicionário de palavras-chave para categorização automática (Smart Matching)
KEYWORD_CATEGORY_MAP = {
    "Eletrônicos": [
        "fone", "celular", "smartphone", "notebook", "pc", "monitor", "tv", "bluetooth",
        "headset", "teclado", "mouse", "ipad", "tablet", "placa", "processador", "ram",
        "ssd", "hd", "cabo", "carregador", "iphone", "xiaomi", "samsung", "apple", "fonte",
        "gopro", "câmera", "camera", "kindle"
    ],
    "Vestuário": [
        "camiseta", "camisa", "calça", "calca", "tênis", "tenis", "sapato", "jaqueta",
        "casaco", "vestido", "saia", "meia", "cueca", "sutiã", "bermuda", "shorts",
        "moletom", "relogio", "relógio", "óculos", "oculos", "boné", "bone", "bolsa",
        "mochila", "cinto"
    ],
    "Games & Software": [
        "jogo", "game", "ps5", "ps4", "xbox", "nintendo", "switch", "steam", "playstation",
        "gta", "fifa", "zelda", "mario", "licença", "licenca", "software", "controle",
        "joystick", "pass", "plus", "card"
    ],
    "Casa & Cozinha": [
        "panela", "airfryer", "fritadeira", "cadeira", "mesa", "sofa", "sofá", "cama",
        "colchão", "colchao", "geladeira", "fogão", "fogao", "microondas", "micro-ondas",
        "aspirador", "lampada", "lâmpada", "organizador", "copo", "caneca", "prato",
        "almofada", "ventilador", "ar condicionado"
    ],
    "Cosméticos & Beleza": [
        "perfume", "creme", "maquiagem", "batom", "shampoo", "condicionador", "sabonete",
        "protetor", "base", "serum", "sérum", "skincare", "hidratante", "esmalte", "perfumaria"
    ]
}


def extract_price(text: str) -> Tuple[Optional[float], str]:
    """
    Extrai o valor numérico do produto do texto e retorna (preço, texto_limpo).
    Suporta formatos: R$ 250,00, R$ 250.00, 250,00, 250.00, 1.250,50, 1250
    """
    # Regex para capturar padrões de preço com ou sem R$
    price_pattern = r'(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*|\d+)(?:[\,\.](\d{2}))?'
    
    # Procura por R$ explicitamente primeiro
    r_match = re.search(r'R\$\s*(\d{1,3}(?:\.\d{3})*|\d+)(?:[\,\.](\d{2}))?', text, re.IGNORECASE)
    if r_match:
        price_str = r_match.group(0)
        clean_number = r_match.group(1).replace('.', '')
        cents = r_match.group(2) if r_match.group(2) else "00"
        price_val = float(f"{clean_number}.{cents}")
        remaining_text = text.replace(price_str, '').strip()
        return price_val, remaining_text

    # Caso não tenha R$, busca números isolados no texto
    matches = list(re.finditer(r'\b(\d{1,3}(?:\.\d{3})*|\d+)(?:[\,\.](\d{2}))?\b', text))
    if matches:
        # Pega o último número encontrado
        match = matches[-1]
        price_str = match.group(0)
        clean_number = match.group(1).replace('.', '')
        cents = match.group(2) if match.group(2) else "00"
        price_val = float(f"{clean_number}.{cents}")
        
        # Garante que o valor não é zero
        if price_val > 0:
            remaining_text = (text[:match.start()] + text[match.end():]).strip()
            return price_val, remaining_text

    return None, text


def extract_url(text: str) -> Tuple[Optional[str], str]:
    """Extrai uma URL do texto se presente e retorna (url, texto_sem_url)."""
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, text)
    if match:
        url = match.group(0)
        clean_text = text.replace(url, '').strip()
        return url, clean_text
    return None, text


def parse_price_str(val_str: str) -> Optional[float]:
    """Auxiliar para converter strings contendo valores para float."""
    val_str = str(val_str).replace('\xa0', ' ').strip()
    match = re.search(r'(\d{1,3}(?:\.\d{3})*|\d+)(?:[\,\.](\d{2}))?', val_str)
    if not match:
        return None
    main_num = match.group(1).replace('.', '')
    cents = match.group(2) if match.group(2) else "00"
    try:
        val = float(f"{main_num}.{cents}")
        return val if val > 0 else None
    except ValueError:
        return None


async def fetch_url_data(url: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Tenta obter o título e o preço do produto a partir de uma URL de e-commerce.
    Utiliza metatags (OpenGraph/Schema), classes CSS conhecidas (Amazon, Mercado Livre) e Regex.
    """
    title = None
    price = None

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            if response.status_code == 200:
                html_content = response.text

                # 1. Extração do Título
                title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
                if title_match:
                    raw_title = html.unescape(title_match.group(1)).strip()
                    # Limpa marca da loja no final do título
                    raw_title = re.sub(r'\s*[:\|–-]\s*(Amazon\.com\.br|Mercado Livre|Shopee|Magalu|Magazineluiza|AliExpress).*$', '', raw_title, flags=re.IGNORECASE)
                    title = re.sub(r'\s+', ' ', raw_title).strip()[:120]

                # 2. Extração do Preço - Estratégia A: Metatags OpenGraph / Schema
                meta_patterns = [
                    r'<meta[^>]+(?:property|name)=[\"\'](?:og:price:amount|product:price:amount|twitter:data1)[\"\'][^>]+content=[\"\']([^\"\']+)[\"\']',
                    r'<meta[^>]+content=[\"\']([^\"\']+)[\"\'][^>]+(?:property|name)=[\"\'](?:og:price:amount|product:price:amount|twitter:data1)[\"\']',
                    r'itemprop=[\"\']price[\"\'][^>]+content=[\"\']([^\"\']+)[\"\']',
                    r'<meta[^>]+content=[\"\']([^\"\']+)[\"\'][^>]+itemprop=[\"\']price[\"\']'
                ]
                for pattern in meta_patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        p = parse_price_str(match.group(1))
                        if p:
                            price = p
                            break

                # Estratégia B: Classes CSS conhecidas (Amazon a-offscreen, Mercado Livre, etc.)
                if not price:
                    offs = re.findall(r'class=[\"\'][^\"\']*(?:a-offscreen|price|andes-money-amount|product-price)[^\"\']*[\"\']>([^<]+)', html_content, re.IGNORECASE)
                    for o in offs:
                        p = parse_price_str(o)
                        if p:
                            price = p
                            break

                # Estratégia C: JSON-LD price
                if not price:
                    json_prices = re.findall(r'\"(?:price|priceAmount)\"\s*:\s*\"?([\d\.\,]+)\"?', html_content, re.IGNORECASE)
                    for jp in json_prices:
                        p = parse_price_str(jp)
                        if p:
                            price = p
                            break

                # Estratégia D: Padrão R$ no HTML
                if not price:
                    r_matches = re.findall(r'R\$\s*(\d{1,3}(?:\.\d{3})*[\,\.]\d{2}|\d+[\,\.]\d{2})', html_content)
                    for rm in r_matches:
                        p = parse_price_str(rm)
                        if p:
                            price = p
                            break
    except Exception:
        pass

    return title, price


def categorize_text(text: str) -> str:
    """Categorização automática por palavras-chave (Smart Matching)."""
    text_lower = text.lower()
    
    for category, keywords in KEYWORD_CATEGORY_MAP.items():
        for keyword in keywords:
            # Procura por palavra inteira ou radical no texto
            if re.search(rf'\b{re.escape(keyword)}', text_lower):
                return category
                
    return "Geral"


async def parse_product_message(raw_text: str) -> dict:
    """
    Analisa a mensagem recebida e retorna um dicionário estruturado:
    {
        'title': str,
        'price': float,
        'url': str | None,
        'category': str
    }
    """
    # 1. Extrair URL
    url, text_no_url = extract_url(raw_text)

    # 2. Extrair Preço do texto fornecido pelo usuário
    text_price, text_clean = extract_price(text_no_url)

    web_title = None
    web_price = None

    # 3. Se houver URL, tenta buscar título e preço diretamente da página web
    if url:
        web_title, web_price = await fetch_url_data(url)

    # Prioriza o preço explicitado pelo usuário no texto, depois o preço extraído da página
    if text_price and text_price > 0:
        final_price = text_price
    elif web_price and web_price > 0:
        final_price = web_price
    else:
        final_price = 0.0

    # Prioriza o título do texto do usuário se for suficiente, caso contrário usa o título da página web
    title = text_clean.strip()
    if not title or len(title) < 2:
        if web_title:
            title = web_title
        elif url:
            domain = url.split('/')[2].replace('www.', '')
            title = f"Produto em {domain}"
        else:
            title = "Item sem nome"

    # 4. Categorizar automaticamente
    category = categorize_text(f"{title} {raw_text}")

    return {
        "title": title,
        "price": final_price,
        "url": url,
        "category": category
    }

