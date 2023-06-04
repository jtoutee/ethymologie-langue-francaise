# coding: utf8
import os
DEBUG = False

os.chdir("C:/Users/jerom/Documents/Louise")
langue = "Latin"
fichier_entree = "exemple_motsdulatin-1.txt"
fichier_sortie =  "test1.txt"        # +tard : créer un nom de sortie avec le nom de fichier + "csv" + txt 
with open(fichier_entree, "r") as fichier:
     contenu = fichier.read()
     fichier.close()
if DEBUG: print(contenu)
if DEBUG: print(len(contenu))
liste = contenu.split(sep='\n')
if DEBUG: print(liste[0].split(" ,")[0])
if DEBUG: print(liste[1])
if DEBUG: print("DEBUG: len(liste) =", len(liste))
i = 0
with open(fichier_sortie, "w") as fichier:
    while i < (len(liste) -1): 
        if DEBUG: print("DEBUG: i = ", i)
        mot = liste[i].split(" ,")[0]
        definition = liste[i+1]
        ligne = langue + "|" + mot + "|" + definition + "\n"
        fichier.write(ligne)
        if DEBUG: print(mot, "|", definition)
        i +=2
    fichier.close()
