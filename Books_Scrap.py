#Fonctions à coder :
    Faire une fonction pour avoir l'URL de l'ensemble des livre de la page
    Faire une fonction popur aller à la page suivante
    Faire une fonction pour avoir l'ensemble des URLS de la bibliothèque
    Faire une fonction qui récupère le prix
    Faire une fonction qui récupère la quantité
    Faire une fonction pour calculer la valeur d'un livre'
"""
from selectolax.parser import HTMLParser
from loguru import logger
import sys
import requests
import re
from urllib.parse import urljoin

logger.remove()
logger.add(f'books.log',
           level="WARNING",
           rotation="500kb")
logger.add(sys.stderr,level="INFO")

BASE_URL='https://books.toscrape.com/catalogue/category/books_1/index.html'

def get_all_books_urls(url:str)-> list[str]:
    """
    Récupère l'url de tous les livres sur toutes les pages à partir d'une URL

    :param url: URL de départ
    :Return: Listede toutes les urls de la librairie

    """
    
    urls=[]
    with requests.Session() as session:
        while True: 
            logger.info(f'Scrapping page at {url}')
            try:
                response=session.get(url)
                response.raise_for_status()
            except session.exceptions.RequestException as e:
                logger.error(f"Erreur lors de la requête HTTP sur la page {url} : {e}")
                continue
            tree=HTMLParser(response.text)
            books_urls=get_all_books_on_page(url=url,tree=tree)
            urls.extend(books_urls)#liste flat avec toutes les URLS, different de append qui fait des listes de listes
            
            url=get_next_page_url(url,tree)
            if not url:
                break
            
    return urls

def get_next_page_url(url:str,tree: HTMLParser)-> str | None:
    """
    Va récupérer l'URL de la page suivante à l'aide du HTML
    Si elle existe
    Parameters
    ----------
    tree : HTMLParser
        DESCRIPTION.

    Returns
    -------
    str
        DESCRIPTION.

    """
    next_page_node= tree.css_first("li.next > a")
    if next_page_node and "href" in next_page_node.attributes:
        return urljoin(url,next_page_node.attributes["href"])
    else:
        logger.info("Aucun boutton next trouvé sur la page.")
        return None

def get_all_books_on_page(url:str,tree:HTMLParser)-> str | None:

    try : 
        books_links_nodes=tree.css("h3 > a")
        return [urljoin(url,link.attributes["href"]) for link in books_links_nodes if "href" in link.attributes]
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des URLS des livres: {e}")
    return []

def get_book_price(url, session: requests.Session=None)->float:
    """
    On recupère le prix d'un livre à partir de son url'
    Parameters
    ----------
    url : TYPE
        L'url du livre
    Returns
    -------
    float
        Prix du livre multiplié par sa quantité
    """
    try:
        if session:
            response=session.get(url)
        else:
            response=requests.get(url)
        response.raise_for_status()
        
        tree=HTMLParser(response.text)
        
        price=extract_price_from_page(tree=tree)
        quantity=extract_stock_quantity_from_page(tree=tree)
        value=price*quantity
        logger.info(f"Get book price at {url}: {value}")

    except requests.exceptions.RequestException as e:
        logger.error(f'Erreur lors de la requête HTTP:{e}')
        return 0.0
    else:
        return value

def extract_price_from_page(tree:HTMLParser)->float:
    """
    Extrait le prix du livre depuis le html de la page

    Parameters
    ----------

    Returns
    -------
    float
        Prix du livre.

    """
    price_node=tree.css_first("p.price_color")
    if price_node:
        price_string=price_node.text()
    else:
        logger.error("Aucun noeud contenant le prix n'a été trouvé")
        return 0.0
    try:
        #r"[0-9.]+" je cherche un nombre entre 0 et 9 apparaissant une fois ou plus
        price=re.findall(r"[0-9.]+",price_string)[0]
    except IndexError as e:
        logger.error(f"Aucun nombre n'a été trouvé: {e}")
        return 0.0
    else:
        return float(price)
    
def extract_stock_quantity_from_page(tree:HTMLParser)->int:
    """
    Extrait la quantité des livres depuis le html de la page

    Parameters
    ----------
    url : str
        URL du livre.

    Returns
    -------
    int
        quantité de livre.

    """
    try:
        stock_node=tree.css_first("p.instock.availability")
        stock=re.findall(f"\d+",stock_node.text())[0]
    except AttributeError as e:
        print(f"Aucun noeud p.instock.availability n'a été trrouvé ici {e}")
        return 0
    except IndexError as e:
        print(f"Aucun nombre n'a été trouvé dans le noeud {e}")
        return 0
    else:
        return int(stock)
    



def main():
    all_books_url=get_all_books_urls(url=BASE_URL)
    total_price=[]
    with requests.Session() as session:
        for book_url in all_books_url:
            price=get_book_price(url=book_url,session=session)
            total_price.append(price)
        print(sum(total_price))
    return sum(total_price)

if __name__ == '__main__':
    main()
