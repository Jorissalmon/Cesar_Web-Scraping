import subprocess

def install_packages(): #on install tous les package à avoir
    packages_to_install = [
        "selenium", "selectolax", "pandas", "openpyxl", 
        "numpy", "spacy", "openai"
    ]
    try:
        subprocess.check_call(["pip", "install", "--upgrade"] + packages_to_install)
        print("Packages installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
    
    # Ligne distincte pour le téléchargement du modèle de langue anglaise pour spacy
    try:
        subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])
        print("English language model for spacy installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading English language model for spacy: {e}")


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selectolax.parser import HTMLParser
import time
import logging
import random
import pandas as pd
import openpyxl
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from openpyxl import Workbook

def extract_product_name(url):
    # Exemple d'extraction basé sur l'URL donnée, cela peut nécessiter des ajustements
    match = re.search(r"/([a-zA-Z0-9-]+/product-reviews/)", url)
    if match:
        # Remplace les tirets par des espaces et prend les premiers mots pour simplifier
        return " ".join(match.group(1).replace("-", " ").replace("/product-reviews/", "").title().split(" ")[:5])
    return "Unknown Product"

def scrape_amazon_reviews(product_url):
    reviews_by_product = {}  # Dictionnaire pour stocker les avis par produit
    reviews = [] # Dictionnaire pour stocker les avis du produit
    options = Options()
    options.headless = True  # Pour exécuter Chrome en mode headless (sans interface graphique)

    driver = webdriver.Chrome(options=options)

    try:
        # Charger le cookie de session
        driver.get("https://www.amazon.com")
        input("Remplies le Capchta, laisse l'onglet Google ouvert, puis appuies sur Entrée pour continuer...")
        p=0
        for product_url in product_urls :
            # Charger la page des avis
            p=p+1
            print(f"Récupération des avis du produit n°{p}")
            try : 
                driver.get(product_url)
            except Exception as e:
                logger.error(f"Couldn't fetch content from {product_url}: {e}")
                continue
            time.sleep(4)  
            i=0
            while True:
                i=i+1
                html = driver.page_source
                tree = HTMLParser(html)
    
                review_wrappers = tree.css("div[data-hook='review']")
                print("page "+str(i))
                for review_wrapper in review_wrappers:
                    review = {}
                    review["title"] = review_wrapper.css_first("a[data-hook='review-title']").text(strip=True)
                    review["body"] = review_wrapper.css_first("span[data-hook='review-body']").text(strip=True)
                    review["rating"] = float(review_wrapper.css_first("i[data-hook='review-star-rating']").text(strip=True).split(" ")[0])
                    review["date"] = review_wrapper.css_first("span[data-hook='review-date']").text(strip=True)
                    reviews.append(review)
    
                # Vérifier si le bouton "Next" est présent
                next_button = driver.find_elements(By.CSS_SELECTOR, ".a-last a")
                if next_button:
                    next_button[0].click()
                    random_delay = random.uniform(1, 5)
                    time.sleep(random_delay)
                else:
                    logger.info("Tous les avis ont été scrappé !")
                    break  # Sortir de la boucle si le bouton "Next" n'est pas trouvé
            reviews_by_product[product_url] = reviews  # Ajouter les avis de ce produit au dictionnaire
    except Exception as e:
        print(f"Erreur dans la récupération des reviews : {e}")
    return reviews_by_product

if __name__ == "__main__":
    install_packages()
    product_urls = [
      #Insérez ici vos urls de page d'avis des produits
        "https://www.amazon.com/elitespace-Mattress-Mattresses-Breathable-Comfortable/product-reviews/B0CTM5GXSP/ref=cm_cr_arp_d_paging_btm_prev_1?ie=UTF8&reviewerType=all_reviews&pageNumber=1"
    ,"https://www.amazon.com/Dourxi-Mattress-Springs-Cooling-Pressure/product-reviews/B0C1FXL8BQ/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"] #Ajouter l'ensemble des urls avis des produits Amazon
    reviews_by_product = scrape_amazon_reviews(product_urls)
    #reviews_by_product = {extract_product_name(url): url for url in product_urls}
    Nom = "Avis_Amazon.xlsx"

    with pd.ExcelWriter(Nom, engine='openpyxl') as writer:
        for product_url, reviews in reviews_by_product.items():
            if reviews:  # Vérifier si la liste des avis n'est pas vide
                df = pd.DataFrame(reviews)
                # Utiliser une partie de l'URL ou une transformation de celle-ci comme nom de la feuille
                invalid_chars = ['\\', '/', '?', '*', '[', ']', ':', '.']
                # Extract a simplified product name from the URL
                product_name = extract_product_name(product_url)
                # Ensure the product name is a valid Excel sheet name
                sheet_name = ''.join(c for c in product_name if c not in invalid_chars)[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"Le fichier a été enregistré sous le nom {Nom}")

    #Analyse des avis
    import pandas as pd
    import numpy as np
    import spacy
    from collections import Counter
    from openai import OpenAI
    import os

    client = OpenAI()
    # Ouvrir le fichier Excel une seule fois
    xls = pd.ExcelFile("Avis_Amazon.xlsx")

    # Obtenir la liste de tous les noms de feuilles
    sheet_names = xls.sheet_names

    # Compter le nombre de feuilles
    nombre_de_feuilles = len(sheet_names)
    print(f"Nombre de feuilles: {nombre_de_feuilles}")

    # Lire chaque feuille en utilisant une boucle
    for sheet_name in sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        # Charger la clé API depuis une variable d'environnement
        OpenAI.api_key = os.getenv('OPENAI_API_KEY')


        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        model=SentimentIntensityAnalyzer()
        def get_sentiment(text:str):
            scores=model.polarity_scores(text)
            return scores["compound"]

        df["sentiment"]=df["body"].apply(get_sentiment)
        df['is_positive']=df['sentiment'].apply(lambda x: x>0)

        nlp = spacy.load("en_core_web_sm")

        def get_entities(text:str):
            doc=nlp(text)
            list=[]
            for ent in doc.ents:
                if ent.label_.lower() not in ["time","money","date"]:
                    temp_=re.sub('[^a-zA-Z0-9]','_',ent.text.lower())
                    list.append('__'.join([temp_,ent.label_.upper()]))
            return ' '.join(list)


        df["entities"]=np.vectorize(get_entities)(df["body"])

        df['X']=df['entities']
        df['Y']=df['is_positive']

        from sklearn.feature_extraction.text import CountVectorizer

        def extract_adjectives(text):
            """
            Cette fonction extrait les adjectifs d'un texte donné en utilisant spaCy.
            """
            adjectives = []
            doc = nlp(text)
            for token in doc:
                if token.pos_ == "ADJ":  # Vérifie si le token est un adjectif
                    adjectives.append(token.lemma_.lower())  # Utilise la forme de base (lemme) de l'adjectif
            return adjectives

        def summarize_reviews(reviews):
            """
            Cette fonction prend une liste d'avis et retourne un résumé basé sur les adjectifs les plus fréquents.
            """
            all_adjectives = []
            for review in reviews:
                all_adjectives.extend(extract_adjectives(review))
            
            # Compte la fréquence de chaque adjectif
            adjective_freq = Counter(all_adjectives)
            
            # Trie les adjectifs par leur fréquence en ordre décroissant
            most_common_adjectives = adjective_freq.most_common(10)  # Vous pouvez ajuster le nombre selon vos besoins
            
            # Crée un rapport basé sur les adjectifs les plus fréquents
            report = "Résumé des avis basé sur les adjectifs les plus fréquents:\n"
            for adj, freq in most_common_adjectives:
                report += f"{adj}: {freq} fois\n"
            
            return report

        def generate_summary(report):
            """
            Génère un résumé des avis en utilisant l'API OpenAI GPT-3.
            """
            # Consigne pour l'API OpenAI
            prompt_consigne = "Résumez les points clés de ces avis clients en mettant d'un coté en avant les aspects positifs et d'un autre, les aspects négatifs en essayant d'être clair, précis et conçit: "
            
            # Joindre les avis en une seule chaîne de caractères, séparés par des espaces
            reviews_text = " ".join(report[:40])
            # Concaténation de la consigne avec les avis
            full_prompt = prompt_consigne + reviews_text
            
            response = client.chat.completions.create(
                model = 'gpt-3.5-turbo',
                messages = [
                    {'role': 'user', 'content': full_prompt}
                ],
                temperature = 0  
                ) 
            answer = response.choices[0].message.content.strip()
            return answer

        reviews = df["body"].tolist()
        report=summarize_reviews(reviews)
        summary = generate_summary(report)
        print(f"Résumé des avis pour le produit {sheet_name} :\n", summary)
