# -*- coding: utf-8 -*-
"""
Created on February

@author: Joris
"""

import requests
from bs4 import BeautifulSoup
import re
import json

##################################EXTRACT#########################################


# Récupérer le contenu de la page
url = 'https://www.academie-cinema.org/en/awards/'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Initialiser une variable pour stocker le JSON extrait
extracted_json_data = None

# Définir l'expression régulière pour extraire le JSON
pattern = re.compile(r'var palmares_year_list = (\{.*?\});', re.DOTALL)

# Parcourir tous les éléments <script>
for script in soup.find_all('script'):
    if script.string:
        match = pattern.search(script.string)
        if match:
            # Extraire la chaîne JSON
            json_str = match.group(1)
            try:
                # Charger la chaîne JSON dans un objet Python
                extracted_json_data = json.loads(json_str)
                print("JSON trouvé et extrait avec succès.")
                # Procéder avec le traitement de `extracted_json_data` selon vos besoins
                break  # Sortir de la boucle une fois le JSON trouvé
            except json.JSONDecodeError as e:
                print(f"Erreur lors de la décodification du JSON: {e}")

# Afficher le JSON extrait pour vérification
if extracted_json_data:
    # Afficher de manière lisible
    print(json.dumps(extracted_json_data, indent=4))
else:
    print("Aucun JSON correspondant n'a été trouvé.")

#############################TRAITEMENT##################################
import pandas as pd

# Initialiser une liste pour stocker les informations extraites
info_lauréats = []

# Parcourir les données JSON par année
for annee, categories in extracted_json_data.items():
    for categorie in categories:
        nom_categorie = categorie['nomPrix']
        print(categorie)
        for nomination in categorie['palmares']:
                if nomination['recompense']==True :
                    recompense=True
                else:
                    recompense=False
                if 'personne' in nomination:  # Cas d'une seule personne
                    personnes = [nomination['personne']]  # Créer une liste avec un seul élément
                elif 'personnes' in nomination:  # Cas de plusieurs personnes
                    personnes = nomination['personnes']
                elif 'credits' in nomination:
                    if 'réalisé par' in nomination['credits'] and nomination['credits']['réalisé par']:
                        personnes = nomination['credits']['réalisé par']
                    else:
                        personnes = nomination['credits']['produit par']
                else:
                    continue  # Si ni 'personne' ni 'personnes' ne sont présents, passer à la nomination suivante
                nom = personnes[0]['nom']
                prenom = personnes[0]['prenom']
                nom =nom +" "+prenom
                if nomination['film'] is None :
                    titre_film ="Titre non disponible"
                else : 
                   titre_film = nomination['film']['titre'] 
                info_lauréat = {
                    'Année': annee,
                    'Catégorie': nom_categorie,
                    'Nom': nom,
                    'Titre du Film': titre_film,
                    'Récompense': recompense
                }
                info_lauréats.append(info_lauréat)

#############################################ANALYSE###################################
#Tout dépend de votre analyse
# Convertir la liste des informations extraites en DataFrame pandas
df_info_laureats = pd.DataFrame(info_lauréats)

df_info_laureats.columns

# Enregistrer le DataFrame dans un fichier Excel
chemin_fichier_excel = 'info_laureats_cesar.xlsx'
df_info_laureats.to_excel(chemin_fichier_excel, index=False)


import pandas as pd
import matplotlib.pyplot as plt

# 1. Nombre de nominations par année
nominations_par_annee = df_info_laureats.groupby('Année')['Année'].size()
chemin_fichier_excel = 'nomination_per_an.xlsx'
nominations_par_annee.to_excel(chemin_fichier_excel, index=True)

# 2. Nombre de personnes uniques nominées
personnes_uniques = df_info_laureats['Nom'].nunique()

# 3. Nombre de personnes nominées par catégorie en 2024
personnes_par_categorie_2024 = df_info_laureats[df_info_laureats['Année'] == '2024'].groupby('Catégorie')['Nom'].nunique()

# 4. Nombre de catégories par année
categories_par_annee = df_info_laureats.groupby('Année')['Catégorie'].nunique()
chemin_fichier_excel = 'categorie_per_annee.csv'
categories_par_annee.to_csv(chemin_fichier_excel, index=True)

# 5. Les 5 premières personnes les plus nominées
top_5_nominations = df_info_laureats.groupby('Nom').size().sort_values(ascending=False).head(5)
chemin_fichier_excel = 'Top5nom.xlsx'
top_5_nominations.to_excel(chemin_fichier_excel, index=True)

details_top_5 = df_info_laureats[df_info_laureats['Nom'].isin(top_5_nominations.index)].groupby(['Nom', 'Catégorie']).size()
# Compter le nombre d'occurrences de chaque catégorie
categories_occurrences = df_info_laureats.groupby('Catégorie')['Année'].nunique().sort_values(ascending=False)

# Compter le nombre d'occurrences de chaque titre de film
films_occurrences = df_info_laureats['Titre du Film'].value_counts()

# Filtrer pour ne conserver que les films nommés plus d'une fois
films_nommés_plusieurs_fois = films_occurrences[films_occurrences > 1]
films_nommés_plusieurs_fois.nunique()

# 1. Identifier les 5 personnes les plus nominées
top_5_nominés = df_info_laureats['Nom'].value_counts().head(5).index
# 2. Extraire les données de nominations pour ces personnes
top_5_data = df_info_laureats[df_info_laureats['Nom'].isin(top_5_nominés)]
# 3. Calculer les nominations cumulées par année pour chaque personne
nominations_cumulées = top_5_data.groupby(['Année', 'Nom']).size().unstack().fillna(0).cumsum()

chemin_fichier_excel = 'Top5nominé_cumul.xlsx'
nominations_cumulées.to_excel(chemin_fichier_excel, index=True)
chemin_fichier_excel = 'Top5nominé_cumul.csv'
nominations_cumulées.to_csv(chemin_fichier_excel, index=True)

df_info_laureats[df_info_laureats['Année']=='2024']['Récompense'].mean()*100

taux_de_recompenses=df_info_laureats.groupby('Année')['Récompense'].mean()*100
chemin_fichier_excel = 'taux_de_recompenses.csv'
taux_de_recompenses.to_csv(chemin_fichier_excel, index=True)
# Calculer le nombre total de nominations par catégorie
total_nominations_par_categorie = df_info_laureats.groupby('Catégorie').size()

# Calculer le nombre de récompenses (True) par catégorie
recompenses_par_categorie = df_info_laureats[df_info_laureats['Récompense']].groupby('Catégorie').size()

# Calculer le pourcentage de récompenses par catégorie
pourcentage_par_categorie = (recompenses_par_categorie / total_nominations_par_categorie * 100).sort_values(ascending=False)
# Compter le nombre d'années uniques de nomination par film
nominations_annees_par_film = df_info_laureats.groupby('Titre du Film')['Année'].nunique()

# Filtrer pour les récompenses attribuées et compter par film
recompenses_par_film = df_info_laureats[df_info_laureats['Récompense'] == True].groupby('Titre du Film').size()

# Créer un DataFrame résumant les informations
df_films_resume = pd.DataFrame({
    'Nombre de Nominations': nominations_par_film,
    'Nombre d\'Années Nominées': nominations_annees_par_film,
    'Nombre de Récompenses': recompenses_par_film
}).fillna(0).reset_index()

# Convertir le nombre de récompenses en entier (après remplissage des NaN par 0)
df_films_resume['Nombre de Récompenses'] = df_films_resume['Nombre de Récompenses'].astype(int)

# Trier les films par le nombre d'années durant lesquelles ils ont été nominés, en ordre décroissant
df_films_resume = df_films_resume.sort_values(by='Nombre d\'Années Nominées', ascending=False).reset_index().rename(columns={'index': 'Titre du Film'})
chemin_fichier_excel = 'films.xlsx'
df_films_resume.to_excel(chemin_fichier_excel, index=True)
print(df_films_resume)


print("Pourcentage de récompenses par catégorie :\n", pourcentage_par_categorie)# Affichages
print("Nombre de nominations par année :\n", nominations_par_annee)
print("\nNombre de personnes uniques nominées :", personnes_uniques)
print("\nNombre de personnes nominées par catégorie en 2024 :\n", personnes_par_categorie_2024)
print("\nNombre de catégories par année :\n", categories_par_annee)
print("\nLes 5 premières personnes les plus nominées :\n", top_5_nominations)
print("\nDétails des 5 premières personnes les plus nominées par catégorie :\n", details_top_5)
print("Nombre d'occurrences par catégorie :\n", categories_occurrences)
print("Films nommés plusieurs fois :\n", films_nommés_plusieurs_fois)

# 4. Créer un graphique montrant ces données
plt.figure(figsize=(10, 6))
for nom in nominations_cumulées.columns:
    plt.plot(nominations_cumulées.index, nominations_cumulées[nom], label=nom)

plt.title('Nominations Cumulées par Année pour les 5 Personnes les Plus Nominées')
plt.xlabel('Année')
plt.ylabel('Nominations Cumulées')
plt.xticks(rotation=45)
plt.legend()
plt.grid(True)
plt.show()


# Normaliser le titre du film : convertir en majuscules et supprimer les espaces de fin
df_info_laureats['Titre du Film'] = df_info_laureats['Titre du Film'].str.upper().str.strip()

# Filtrer les données pour "LES MISÉRABLES" après normalisation
les_miserables = df_info_laureats[df_info_laureats['Titre du Film'] == 'LES MISÉRABLES']

# Ensuite, vous pouvez compter les nominations et les récompenses comme précédemment
nominations_par_annee = les_miserables.groupby('Titre du Film')['Année'].nunique()
recompenses_par_annee = les_miserables[les_miserables['Récompense']].groupby('Année').size()

# Créer un DataFrame résumant les informations
df_les_miserables_resume = pd.DataFrame({
    'Nombre de Nominations': nominations_par_annee,
    'Nombre de Récompenses': recompenses_par_annee
}).fillna(0).astype(int)  # Assurer que les années sans récompenses montrent 0

print(df_les_miserables_resume)


