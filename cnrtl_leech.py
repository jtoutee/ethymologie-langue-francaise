# coding: utf8
import fonctions
import os
import urllib.request
import re
import time
DEBUG = False

dico_mots = {}
dico_mots_avec_definition = {}
topurl = "http://www.cnrtl.fr/portailindex/ETYM//"     # À compléter par A pour la lettre A

alphabet = []
for ascii in range(65, 65+1):      ### On commence au B on fera le A plus tard
    alphabet.append(chr(ascii))
if DEBUG: print("DEBUG: alphabet =", alphabet)

# Boucle principale, de A à Z
for lettre in alphabet:

    print("Lettre {} en traitement...".format(lettre))
    derniere_page = False
    url_lettre = topurl + lettre
    url = url_lettre
    
    while not derniere_page:
        # Ralentir un peu la boucle, sinon le serveur web risque de voir cela comme un DOS
        time.sleep(1)
        
        if DEBUG: print("DEBUG: url =", url) 
        # Lire la page
        page = urllib.request.urlopen(url).read()

        # Tranforme la page de type bytes en type string en la décodant:
        page = page.decode("UTF-8")

        # Appelle la fonction url_mots pour ajouter au dico des mots les URL de chaque mot présent sur la page:
        dico_mots = fonctions.url_mots(dico_mots, page, lettre.lower())
        
        # Déterminer si c'est la dernière page de la lettre en chechant la présense de dright.gif (flèche droite grisée)
        derniere_page = 'dright.gif' in page
        if DEBUG: print("DEBUG: derniere_page =", derniere_page)
        if derniere_page:
            exit        # Sortir de la boucle des pages de la lettre
        else:
            # Pas la dernière, aller chercher URL de la suivante. On Cherche (exemple avec lettre B)
            # href="/portailindex/ETYM//A/80  qui correspond à http://www.cnrtl.fr/portailindex/ETYM//B/160
            # Ce qui donne cette regexp: r'/portailindex/ETYM//[A-Z]/[1-9][0-9]+'
            # (re.search renvoie un objet, il faut utiliser la méthode group de cet objet pour récupérer ce qui a matché)
            # ATTENTION : dans une page intermédiaire (ni première ni dernière pour une lettre), cette regexp match 2 fois, 
            # par exemple: /portailindex/ETYM//Z/80 ET /portailindex/ETYM//Z/240
            # Il faut donc utiliser findall et ne garder que le dernier match (attention pour la première page il n'y a qu'un seul
            # match donc le dernier match n'est pas le 2e match, mais le premier et unique)
            liste = re.findall(r'/portailindex/ETYM//[A-Z]/[1-9][0-9]+', page)
            url = 'http://www.cnrtl.fr' + liste[-1]     # liste[-1] c'est le dernier élément de la liste
            if DEBUG: print("DEBUG: url page suivante =", url)
    
# Le dico_mots est constitué, quelques statistiques:
print("Le dico_mots contient {} mots.".format(len(dico_mots)))

# On parcours les mots du dico_mots, on va chercher leur définition (leech) et on la garde en entier et uniquement
# s'ils sont "empruntés" (pour traitement ultérieur)
dico_mots_avec_definition = fonctions.mots_avec_definition(dico_mots)

# On sauve le gros dico avec les définitions complètes sur disque:
fonctions.sauver_dico(dico_mots_avec_definition, "dico_mots_empr_definition_complete")

# On fabrique le fichier excel en partant du dico (oula ça va être énoorme !)
fonctions.dico_to_excel(dico_mots_avec_definition, "dico_mots_empr_definition_complete.txt")

exit()

# On parcours les mots du dico_mots, on va chercher leur définition et on ne garde que les mots qui sont empruntés
# d'une autre langue
dico_mots_empr = fonctions.mots_empruntes(dico_mots, mode="dico")
print("Le dico_mots nettoyé contient {} mots.".format(len(dico_mots_empr)))

# On sauve le dico sur disque:
fonctions.sauver_dico(dico_mots_empr, "dico_mots_empr")
##print(dico_mots_empr)
##print(dico_mots_empr["zeugma"])
