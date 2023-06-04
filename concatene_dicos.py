# coding: utf8
import re
import urllib.request
import urllib.parse
import pickle
import time
import os

# Cherche tous les dicos sauvés dans C:\Users\jerom\workspace\Louise Projet Intégrateur qui sont sous la forme dico_mots_empr_<LETTRE>
# puis les ouvre chacun dans un dico en mémoire, 
# puis les concatène tous en en seul gros dico (méthode update des dicso)
# puis sauve ce dico
  
grand_dico = {}
os.chdir("C:/Users/jerom/workspace/Louise Projet Intégrateur")
for nom_fichier in os.listdir():
    if re.match(r'dico_mots_empr_[A-Z]+', nom_fichier):
         with open(nom_fichier, 'rb') as fichier:
            mon_depickler = pickle.Unpickler(fichier)
            dico = mon_depickler.load()
            print("Taille du dico :", len(dico))
            grand_dico.update(dico)

print("Taille du grand_dico :", len(grand_dico))

# On écrit le grand dico:
with open('grand_dico_mots', 'wb') as fichier:
    mon_pickler = pickle.Pickler(fichier)
    mon_pickler.dump(grand_dico)
    fichier.close()
    
# Lire le grand dico et l'exporter sous forme de csv avec "|" comme délimiteur
with open("dico_des_mpts_emprunts.txt","w", encoding='utf8') as fichier:
    for mot in grand_dico:
        chaine = mot + "|" + grand_dico[mot] + "\n"
        try:
            fichier.write(chaine)
        except:
            print("Problème avec mot :", mot)
            print("Problème avec définition :", grand_dico[mot])