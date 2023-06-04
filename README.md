# ethymologie-langue-francaise
Programme de leech amical et à usage unique de certaines infos du site CNRTL (CNRS) pour un projet d'étudiant CEGEP.
Pour le projet linguistique de Louise Toutée, étudiante au CEGEP Maisonneuve en SLA, il était nécessaire d'obtenir des informations pour chaque mot du dictionnaire français sur l'origine du mot, dans le cas où il est emprunté à une autre langue que le français.
Le CNRTL (Centre National de Ressources Textuelles et Lexicales), partie du CNRS, offre un portail public de consultation Ortolang. par exemple pour la lettre C:
https://www.cnrtl.fr/portailindex/ETYM//C
Ce programme a pour objectif de lire les définitions de tous les mots qui sont empruntés à une autre langue que le français, et de produire un fichier tabulaire qui sera ensuite exploité par un autre programme pour le projet de Louise Toutée.
Le portail CNRTL n'offrant pas d'API publique en lecture (en tout cas à l'époque en 2018), il a fallu développer ce programme de 'leech', en prenant garde à ne pas dépasser des seuils de requète/seconde pour éviter de déclencher les blocages andti-DOS du serveur web. C'est donc un leeach lent et controllé.

Programme principal : cnrtl_leech.py

Fonctions : fonctions.py

Programme additonnel : concatene_dicos.py
