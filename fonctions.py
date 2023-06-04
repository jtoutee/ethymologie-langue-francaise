# coding: utf8
import re
import urllib.request
import urllib.parse
import pickle
import time
DEBUG = False

def url_mots(dico_mots, page, lettre):
    """ cette fonction parse la page passée en paramètre (sous form de chaine), trouve les URL de chaque mot en recherchant
    toutes les occurrences de Etymologie de <lettre en cours en minusule> et les ajoute dans le dico
    passé en paramètre sous la forme clé = <le mot>, valeur =  <URL de la page qui décrit le mot>
    Puis elle renvoi le dico """
    
    liste = re.findall(r'Etymologie de [a-zàéèôêëïç -]*\"', page)
    # Chaque élément de la liste est de la forme 'Etymologie de zygophylle"'
    # il faut donc ne garder que "zygophylle": on supprime 'Etymologie de ' et ensuite on supprime le guillement '"'
    for i, elt in enumerate(liste):
        liste[i] = elt.replace('Etymologie de ', '').replace('"', '')
        
    # Pour chaque mot on construit l'URL sous la forme http://www.cnrtl.fr/etymologie/<mot>, et on remplis le dico
    for mot in liste:
        dico_mots[mot] = 'http://www.cnrtl.fr/etymologie/' + mot
        ##if DEBUG: print("DEBUG: mot = {}, dico_mot[mot] = {}".format(mot, dico_mots[mot]))

    return dico_mots

def mots_empruntes(dico_mots, mode="leech"):
    """ cette fonction va chercher leur définition et on ne garde que les mots qui sont empruntés d'une autre
    langue.
    Le critère étant la présence de 'Empr.'dans la définition.
    Si le mot 'Empr. ' n.est pas présent on efface le mot du dico.
    Si le mot 'Empr. . est présent, on remplace dans le dico l'URL par le texte de la définition
    Si le paramètre mode est défini à "leech" (défaut), la définition va être récupérée sur le web (22h)
    Si le paramètre mode est défini à "dico", la définition est prise dans la value du dico[mot]. (cas
    où on a déjà leeché un dico complet avec les définitions complètes (à partir du mot "Empr." jusqu'au
    </div>))
    La fonction renvoie le dico nettoyé et avec les définitions à la place des URL des mots"""

    if DEBUG: print("Mode = ", mode)
    # Pour faciliter le débug et permettre d'afficher une progression par ordre alphabétique on va "trier"
    # le dico en fonction des clés:
    liste = sorted(dico_mots.items(), key=lambda t: t[0])
    ##liste = liste[1]    # DEBUG ONLY pour ne travailler que sur le mot "aba"
    if DEBUG: print("DEBUG: liste =", liste)
    for elt in liste:
        # Ralentir un peu la boucle, sinon le serveur web risque de voir cela comme un DOS
        if (mode == "leech"):
            time.sleep(1)
        # On va chercher la définition:
        if DEBUG: print("DEBUG: mot =", elt[0])
        ##if DEBUG: print("DEBUG: url =", elt[1])
        mot = elt[0]
        print("Mot =", mot)
        if (mode == "leech"):
            url = elt[1]
        elif(mode == "dico"):
            ##definition = elt[1]
            definition = nettoyage(elt[1])  # On fait le nettoyage avant de chercher la fin de phrase
            definition = substitution(definition)   # Puis les substitutions des abréviations
        else:
            print("Erreur: paramètre mode = {} non valide".format(mode))
            exit() 

        # Comme l'URL peut contenir des caractères accentués qui vont générer cette horrible erreur:
        # UnicodeEncodeError: 'ascii' codec can't encode character '\xe8' in position 23: ordinal not in range(128), 
        # il faut encoder le dernier mot de l'URL avec la fonction quote du module urllib.parse
        # exemple : 'http://www.cnrtl.fr/etymologie/zée' c'est le zée à la fin qui fout la grouille, un simple
        # quote('zée') le tranforme en 'z%C3%A9e'. l'URL sera finalement 'http://www.cnrtl.fr/etymologie/z%C3%A9e', ce qui ne
        # provoque plus d'erreur lors de urlopen
        if (mode == "leech"):
            unquoted = url.split('/')[-1]   # le dernier mot de l'URL 
            quoted = urllib.parse.quote(unquoted)
            url = url.replace(unquoted, quoted)
            ##if DEBUG: print("DEBUG: url avec quote des caractères accentués =", url)
            
            LECTURE_URL_NOK = True
            while LECTURE_URL_NOK:
                try:
                    definition = urllib.request.urlopen(url, timeout=20).read()
                    LECTURE_URL_NOK = False     # Ça a marché
                except:
                    print('Erreur lecture url =', url)
                    print("Temporisation de 10s")
                    time.sleep(10)       # Wait 10s
            definition = definition.decode("UTF-8")     # Pour passer de type bytes à type str
            if "BLOCAGE TEMPORAIRE" in definition:
                print("BLOCAGE TEMPORAIRE : attente de 60mn, soyez patient")
                time.sleep(3600)
            definition = nettoyage(definition)          # On fait le nettoyage avant de chercher la fin de phrase
            definition = substitution(definition)       # Puis les substitutions des abréviations
        if "Empr. " not in definition:   # La définition ne contient pas Empr. (emprunté), il faut éliminer ce mot
            del dico_mots[mot]
            ##if DEBUG: print("DEBUG: le mot {} n'est pas emprunté ==> éliminé".format(mot))
        else:
            if DEBUG: print("DEBUG: le mot {} est emprunté ==> conservé".format(mot))
            ##if DEBUG: print("DEBUG: definition =", definition)
            # On ne garde que de 'Empr. " à la fin d'une phrase, caractérisée par la première occurrence de parenthèses ou minuscule,
            # suivi de . suivit de espace, suivi de majuscule - ou jusqu'à la balise balise </div>
            # Attention1: bien utiliser le non-greedy ? après .* sinon on attrape plusieurs phrases et pas juste la première.
            # Attention2: dans certains cas où la définition est courte (comme Yachmak), on ne trouve pas de "<minusocule>. <majustcule>
            #             avant la fin (le </div>. On doit don tester si on match ou pas. Si on ne match pas on prend tout jsuqu'à la fin
            # Attention3: ne pas utiliser .* comme wildacrd, mais plutôt [\s\S]* pour aussi attraper les \n
            ##match_fin_de_phrase = re.search(r'(Empr\. [\s\S]*?)[()a-z]\. [A-Z].*< \/div>', definition)
            ## A FAIRE : enlever les balises <b> car elles font rater la découverte de .<espace><majuscule>
            ## A AFIRE : pb de abaque 
            if DEBUG: print("DEBUG: definition = ", definition)
            if mode == "leech":
                match_fin_de_phrase = re.search(r'(Empr\. [\s\S]*?[»a-z])\. [A-Z].*<\/div>', definition)
            else:   # Si mode dico, la définition ne contient déjà plus le </div>, et en plus elle commnce avant
                    # le "Empr." car pour populer le dico on a aussi gardé le type de mot (subst. par exemple)
                if DEBUG: print("DEBUG: more = ", mode)
                match_fin_de_phrase = re.search(r'(Empr\. [\s\S]*?[»a-z]\.)\s+[A-Z]', definition)
                ##if DEBUG: print("DEBUG: match_fin_de_phrase.group(0) = ", match_fin_de_phrase.group(0))

            if match_fin_de_phrase == None:     # Si le critère de fin de phrase pas ok, on prend juaqu'au </div> (si leech)
                if mode == "leech":
                    definition_courte = re.search(r'(Empr\. [\s\S]*?)<\/div>', definition).group(1)
                else:   # Mode dico, si on n'a pas été capable de détecter la fin d'une phrase on prend toute
                        # la définition _à_partir_ de Empr jusqu'à </div  (sans le > à la fin, pour une raison
                        # étrange les définitions stockées après un leech dans le dico n'ont pas le </div> complet
                    definition_courte = re.search(r'(Empr\. [\s\S]*?)<\/div', definition).group(1)
            else:   # On a réussion à détecter une fin de phrase
                definition_courte = match_fin_de_phrase.group(1) 
            ##print("DEBUG: definition avant rempalcementr de Empr", definition_courte)
            # Enfin, avant de stocker la définition, on remet Emprunté à la place de Empr.: 
            definition_courte = definition_courte.replace('Empr.', 'Emprunté')
            ##print("DEBUG: definition après rempalcementr de Empr", definition_courte)
            # Puis on nettoie:
            dico_mots[mot] = nettoyage(definition_courte)
            
    print("")
    return dico_mots

def mots_avec_definition(dico_mots):
    """ cette fonction va chercher leur définition, sans filtrage, et renvoie le dico avec les définitions à la place 
    des URL des mots."""
    
    # Pour faciliter le débug et permettre d'afficher une progression par ordre alphabétique on va "trier" le dico en
    # fonction des clés:
    liste = sorted(dico_mots.items(), key=lambda t: t[0])
    ##if DEBUG: print("DEBUG: liste =", liste)
    i = 0
    for elt in liste:
        # Ralentir un peu la boucle, sinon le serveur web risque de voir cela comme un DOS
        time.sleep(1)
        # On va chercher la définition:
        if DEBUG: print("DEBUG: mot =", elt[0])
        ##if DEBUG: print("DEBUG: url =", elt[1])
        mot = elt[0]
        print("Mot =", mot)
        url = elt[1]
        # Comme l'URL peut contenir des caractères accentués qui vont générer cette horrible erreur:
        # UnicodeEncodeError: 'ascii' codec can't encode character '\xe8' in position 23: ordinal not in range(128), 
        # il faut encoder le dernier mot de l'URL avec la fonction quote du module urllib.parse
        # exemple : 'http://www.cnrtl.fr/etymologie/zée' c'est le zée à la fin qui fout la grouille, un simple
        # quote('zée') le tranforme en 'z%C3%A9e'. l'URL sera finalement 'http://www.cnrtl.fr/etymologie/z%C3%A9e', ce qui ne
        # provoque plus d'erreur lors de urlopen
        unquoted = url.split('/')[-1]   # le dernier mot de l'URL 
        quoted = urllib.parse.quote(unquoted)
        url = url.replace(unquoted, quoted)
        ##if DEBUG: print("DEBUG: url avec quote des caractères accentués =", url)
    
        LECTURE_URL_NOK = True
        while LECTURE_URL_NOK:
            try:
                definition = urllib.request.urlopen(url, timeout=20).read()
                LECTURE_URL_NOK = False     # Ça a marché
            except:
                print('Erreur lecture url =', url)
                print("Temporisation de 10s")
                time.sleep(10)       # Wait 10s
        definition = definition.decode("UTF-8")     # Pour passer de type bytes à type str
        if "BLOCAGE TEMPORAIRE" in definition:
            print("BLOCAGE TEMPORAIRE : attente de 60mn, soyez patient")
            time.sleep(3600)
        if DEBUG: print("DEBUG: définition avant détection de Empr. =", definition)

        if "Empr. " not in definition:   # La définition ne contient pas Empr. (emprunté), il faut éliminer ce mot
            del dico_mots[mot]
            print("le mot {} n'est pas emprunté ==> éliminé".format(mot))
        else:
            ##if DEBUG: print("DEBUG: definition =", definition)
            # On ne garde que de 'Empr. " à la fin d'une phrase, caractérisée par la première occurrence de parenthèses ou minuscule,
            # suivi de . suivit de espace, suivi de majuscule - ou jusqu'à la balise balise </div>
            # Attention1: bien utiliser le non-greedy ? après .* sinon on attrape plusieurs phrases et pas juste la première.
            # Attention2: dans certains cas où la définition est courte (comme Yachmak), on ne trouve pas de "<minusocule>. <majustcule>
            #             avant la fin (le </div>. On doit don tester si on match ou pas. Si on ne match pas on prend tout jsuqu'à la fin
            # Attention3: ne pas utiliser .* comme wildcard, mais plutôt [\s\S]* pour aussi attraper les \n
            ##match_fin_de_phrase = re.search(r'(Empr\. [\s\S]*?)[()a-z]\. [A-Z].*</div>', definition)
            ## A AFIRE : pb de abaque
            ### ^[\s\S]*(Empr\. [\s\S]*?)<\/div>
            ##definition_courte = re.search(r'(Empr\. [\s\S]*?)</div>', definition).group(1)
            ### tlf_ccode[\s\S]*?<\/div>[\s\S]*?<\/div> semble attraper la définition en entier mais trop de truc emn plus
            try:
                definition_courte = re.search(r'tlf_ccode[\s\S]*?<\/div>[\s\S]*?<\/div>', definition).group(0)
            except AttributeError:
                print("ERROR: mot = {}, regex tlf_ccode ne renvoie rien".format(mot))
            print("DEBUG: definition courte =", definition_courte)
            dico_mots[mot] = nettoyage(definition_courte)
        i += 1
        if (i % 500) == 0:  # On sauve tous les 500 mots
                # On sauve le dico en cours
                progres = str(i)
                nom_dico = "dico_mots_" + progres
                print("DICO {} sauvé. Mot en cours = {}".format(nom_dico, mot))
                sauver_dico(dico_mots, nom_dico)
            
    print("")
    return dico_mots


def nettoyage(definition):
    """ nettoie les définitions des choses indésirables comme
    <i>jacht</i>
    <b> et </b>
    <span class="tlf_smallcaps">De</span> <span class="tlf_smallcaps">Vries </span>
    <span class="tlf_smallcaps">Kemna</span>
    ou encore des séquences d'espaces consécutifs
    ou encore tout ce qui est entre parenthèses
    et renvoie la chaine definition nettoyée """
    definition = definition.replace('<sup', '')
    definition = definition.replace('</sup', '')
    definition = definition.replace('<i>', '')
    definition = definition.replace('</i>', '')
    definition = definition.replace('<b>', '')
    definition = definition.replace('</b>', '')
    definition = definition.replace('<b', '')      # For some reason I have some partial <b> lile <b
    definition = definition.replace('</b', '')     # For some reason I have some partial </b> lile </b
    definition = re.sub('\([^\)]*\)', '', definition)   # On enlève ce qui est entre parenthèses
    definition = re.sub('<span .*?>', ' ', definition)
    definition = definition.replace('</span>', '')
    definition = definition.replace('\n', '')
    definition = re.sub('\(.*?\)', '', definition)
    definition = re.sub('[\s]{2,} ', ' ', definition)   # On remplace toute suite de 2 espaces ou plus par un seul espace
    definition = re.sub(' *?>', ' ', definition)
    ##print("DEBUG: definition avant rempalcementr de Empr", definition)
    ##definition = definition.replace('Empr.', 'Emprunté')
    ##print("DEBUG: definition après rempalcementr de Empr", definition)
    if DEBUG: print("DEBUG: definition courte nettoyee=", definition)
    return definition

def substitution(definition):
    """ remplace les abréviaitons par leur nom long. Ex. Ital. ==>   Italien""" 
    definition = definition.replace(" sup. ", " supérieur ")
    definition = definition.replace(" s. ", " siècle ")
    definition = definition.replace(" m. ", " moyen ")
    definition = definition.replace(" n. ", " nom ")
    definition = definition.replace(" pol. ", " polonais ")
    definition = definition.replace(" rad. ", " radical ")
    definition = definition.replace(" suff. ", " suffixe ")
    definition = definition.replace(" part. prés. ", " participe présent ")
    definition = definition.replace(" part. passé ", " participe passé ")
    definition = definition.replace(" l'acc. ", " l'accusatif ")
    definition = definition.replace(" l'alsac ", " l'alsacien ")
    definition = definition.replace(" frq. ", " francique ")
    definition = definition.replace(" gasc. ", " gascon. ")
    definition = definition.replace(" l'a.b.frq. ", " l'ancien bas francique ")
    definition = definition.replace(" l'a.prov. ", " l'ancien provençal ")
    definition = definition.replace(" l'adj. ", " l'adjectif ")
    definition = definition.replace(" Empr. par l'intermédiaire ", ' Empr. ')
    definition = definition.replace(' Empr. directement ', ' Empr. ')
    definition = definition.replace(' Empr. deux fois ', ' Empr. ')
    definition = definition.replace(' Empr. prob. ', ' Empr. ')
    definition = definition.replace(' Empr. 1 ', ' Empr. ')
    definition = definition.replace(' adj. latin ', ' latin ')
    definition = definition.replace(" l'anglo-américain ", ' anglais ')  
    definition = definition.replace(" l'anglo-amér. ", ' anglais ')
    definition = definition.replace(" l'a. ", " l'ancien ")              ### tbc Louise
    definition = definition.replace(" h. ", " haut ")                 ### tbc Louise
    definition = definition.replace(" b. ", " bas ")                 ### tbc Louise
    definition = definition.replace(' ital.', ' italien')
    definition = definition.replace(" l'ital.", " l'italien")
    definition = definition.replace(' ar.', ' arabe')
    definition = definition.replace(" l'ar.", " l'arabe")
    definition = definition.replace(' plur.', ' pluriel')
    definition = definition.replace(' lat.', ' latin')
    definition = definition.replace(' obj.', ' objet')
    definition = definition.replace(' dep.', ' depuis')
    definition = definition.replace(' orig.', ' origine')
    definition = definition.replace(' attest.', ' attestation')
    definition = definition.replace(' ant.', ' antérieure')
    definition = definition.replace(' expr.', ' expression')
    definition = definition.replace(' lang.', ' langue')
    definition = definition.replace(' équit.', ' équitation')
    definition = definition.replace(' fig.', ' figuré')
    definition = definition.replace(' dict.', ' dicton')
    definition = definition.replace(' partic.', ' particulière')
    definition = definition.replace(' étymol.', ' étymologie')
    definition = definition.replace(' dér.', ' dérivé')
    definition = definition.replace(' techn.', ' technique')
    definition = definition.replace(' sém.', ' sémantique')
    definition = definition.replace(' arg.', ' argot')
    definition = definition.replace(" l'arg. ", " l'argot ")
    definition = definition.replace(' onomat.', ' onomatopé')
    definition = definition.replace(' angl.', ' anglais')
    definition = definition.replace(" l'angl.", " l'anglais")
    definition = definition.replace(' prob.', ' probablement')
    definition = definition.replace(" l'angl.", " l'anglais")
    definition = definition.replace(' néerl.', ' néerlandais')
    definition = definition.replace(' isl.', ' islandais')
    definition = definition.replace(' apr.', ' après')
    definition = definition.replace(' esp.', ' espagnol')
    definition = definition.replace(" l'esp.", " l'espagnol")
    definition = definition.replace(' s.v.', ' ')
    definition = definition.replace(' sag.', ' sagesse')
    definition = definition.replace(' all.', ' allemand ')
    definition = definition.replace(" l'all.", " l'allemand ")
    definition = definition.replace(' sax.', ' saxon')
    definition = definition.replace(' scand.', ' scandinave')
    definition = definition.replace(' sav.', ' savant')
    definition = definition.replace(' scol.', ' scolaire')
    definition = definition.replace(' second.', ' secondaire')
    definition = definition.replace(' septentr.', ' septentrional')
    definition = definition.replace(' signif.', ' signification')
    definition = definition.replace(' sing.', ' singulier')
    definition = definition.replace(' skr.', ' sanskrit')
    definition = definition.replace(' sl.', ' slave')
    definition = definition.replace(' soc.', ' social')
    definition = definition.replace(' sté.', ' société')
    definition = definition.replace(' suéd.', ' suédois')
    definition = definition.replace(' suiv.', ' suivant')
    definition = definition.replace(' subj.', ' subjonctif')
    definition = definition.replace(' suj.', ' sujet')
    definition = definition.replace(' acquis.', ' acquisition')
    definition = definition.replace(' aff.', ' affixe')
    definition = definition.replace(' agn.', ' anglo-normand')
    definition = definition.replace(" l'agn.", " l'anglo-normand")
    definition = definition.replace(' alsac.', ' alscacien')
    definition = definition.replace(' anc.', ' ancien')
    definition = definition.replace(' att.', ' attesté')
    definition = definition.replace(' auxil.', ' auxilaire')
    definition = definition.replace(" l'auxil.", " l'auxilaire")
    definition = definition.replace(' av.', ' avant')
    definition = definition.replace(' byz.', ' byzantin')
    definition = definition.replace(' bulg.', ' bulgare')
    definition = definition.replace(' bret.', ' breton')
    definition = definition.replace(' carol.', ' carolingien')
    definition = definition.replace(' cast.', ' castillan')
    definition = definition.replace(' cat.', ' catalan')
    definition = definition.replace(' cf.', ' ')
    definition = definition.replace(' chrét.', ' chrétien')
    definition = definition.replace(' civilis.', ' civilisation')
    definition = definition.replace(' class.', ' classique')
    definition = definition.replace(' cr.', ' croate')
    definition = definition.replace(' cult.', ' culture')
    definition = definition.replace(' dan.', ' danois')
    definition = definition.replace(" d'apr.", " d'après")
    definition = definition.replace(' dial.', ' dialecte')
    definition = definition.replace(' ds.', ' dans')
    definition = definition.replace(' env.', ' environ')
    definition = definition.replace(' étr.', ' étranger')
    definition = definition.replace(' fac.', ' faculté')
    definition = definition.replace(' fam.', ' familier')
    definition = definition.replace(' fém.', ' féminin')
    definition = definition.replace(' fig.', ' figuré')
    definition = definition.replace(' finn.', ' finnois')
    definition = definition.replace(' flam.', ' flamand')
    definition = definition.replace(' gall.', ' gallois')
    definition = definition.replace(' gaul.', ' gaulois')
    definition = definition.replace(' germ.', ' germanique')
    definition = definition.replace(' gloss.', ' glossaire')
    definition = definition.replace(' gr.', ' grec')
    definition = definition.replace(' germ.', ' germanique')
    definition = definition.replace(' hébr.', ' hébreu')
    definition = definition.replace(" l'hébr.", " l'hébreu")
    definition = definition.replace(' hind.', ' hindouisme')
    definition = definition.replace(' hisp.', ' hispanique')
    definition = definition.replace(' holl.', ' hollandais')
    definition = definition.replace(' hongr.', ' hongrois')
    definition = definition.replace(' inf.', ' infinitif')
    definition = definition.replace(" l'inf.", " l'infinitif")
    definition = definition.replace(' inv.', ' invariable')
    definition = definition.replace(' indir.', ' indirect')
    definition = definition.replace(' ling.', ' linguistique')
    definition = definition.replace(' lit.', ' littérature')
    definition = definition.replace(' litt.', ' littéraire')
    definition = definition.replace(' loc.', ' locution')
    definition = definition.replace(' masc.', ' masculin')
    definition = definition.replace(' médiév.', ' médiéval')
    definition = definition.replace(' mérid.', ' méridional')
    definition = definition.replace(' mod.', ' moderne')
    definition = definition.replace(' moy.', ' moyen')
    definition = definition.replace(' néol.', ' néologisme')
    definition = definition.replace(' nom.', ' nominal')
    definition = definition.replace(' nord.', ' nordique')
    definition = definition.replace(' norm.', ' normand')
    definition = definition.replace(' norv.', ' norvégien')
    definition = definition.replace(' occ.', ' occidental')
    definition = definition.replace(" l'occ.", " l'occidental")
    definition = definition.replace(' occit.', ' occitan')
    definition = definition.replace(" l'occit.", " l'occitan")
    definition = definition.replace(' pat.', ' patois')
    definition = definition.replace(' phonét.', ' phonétique')
    definition = definition.replace(' polon.', ' polonais')
    definition = definition.replace(' port.', ' portugais')
    definition = definition.replace(' poss.', ' possessif')
    definition = definition.replace(' prim.', ' primaire')
    definition = definition.replace(' prop.', ' proposition')
    definition = definition.replace(' prov.', ' provençal')
    definition = definition.replace(' réf.', ' référence')
    definition = definition.replace(' rég.', ' régulier')
    definition = definition.replace(' rom.', ' roman')
    definition = definition.replace(' roum.', ' roumain')
    definition = definition.replace(' tch.', ' tchèque')
    definition = definition.replace(' temp.', ' temporel')
    definition = definition.replace(' théor.', ' théorique')
    definition = definition.replace(' topol.', ' topologie')
    definition = definition.replace(' trans.', ' transitif')
    definition = definition.replace(' us.', ' usage')
    definition = definition.replace(" l'us.", " l'usage")
    definition = definition.replace(' vx.', ' vieux')
    definition = definition.replace(' vulg.', ' vulgaire')
    definition = definition.replace(' vocab.', ' vocabulaire')
    return definition


def sauver_dico(dico, nom_du_fichier):
    """ sauve sur disque le dico passé en argument"""
    try:
        with open(nom_du_fichier, 'wb') as fichier:
            mon_pickler = pickle.Pickler(fichier)
            mon_pickler.dump(dico)
            fichier.close()
    except IOError:
        print('Erreur d\'écriture dans le fichier ', nom_du_fichier)

def lire_dico(nom_du_fichier):
    """lit le fichier-dico et renvoie un dictionnaire"""
    try:
        with open(nom_du_fichier, 'rb') as fichier:
            mon_depickler = pickle.Unpickler(fichier)
            dico = mon_depickler.load()
    except IOError:    # Si le fichier n'existe pas, on renvoie un dictionnaire vide
        dico = {}
    return dico


def dico_to_excel(dico, fichier_excel):
    """# Lire le dico passé en paramètre et l'exporter sous forme de csv avec "|" comme délimiteur"""
    with open(fichier_excel, "w", encoding='utf8') as fichier:
        for mot in dico:
            chaine = mot + "|" + dico[mot] + "\n"
            try:
                fichier.write(chaine)
            except:
                print("Problème avec mot :", mot)
                print("Problème avec définition :", grand_dico[mot])

def dico_to_excel2(dico_def, dico_type_de_mot, fichier_excel):
    """Lire les dicos passés en paramètre et exporter sous forme de csv avec "|" comme délimiteur
    Le 3 chamsp produits sont : 1) le mot, 2) le type de mot, 3) le définition courte et nettoyée"""
    with open(fichier_excel, "w", encoding='utf8') as fichier:
        for mot in dico_def:
            chaine = mot + "|" + dico_type_de_mot[mot] + "|" + dico_def[mot] + "\n"
            print("DEBUG: chaine = ", chaine)
            try:
                fichier.write(chaine)
            except:
                print("Problème avec mot :", mot)
                print("Problème avec définition :", grand_dico[mot])

def dico_to_excel3(dico_def, dico_type_de_mot, dico_langue_du_mot, fichier_excel):
    """Lire les dicos passés en paramètre et exporter sous forme de csv avec "|" comme délimiteur
    Le 4 chamsp produits sont : 1) le mot, 2) le type de mot, 3) la langue empruntée 
    4) le définition courte et nettoyée"""
    with open(fichier_excel, "w", encoding='utf8') as fichier:
        for mot in dico_def:
            chaine = mot + "|" + dico_type_de_mot[mot] + "|" + dico_langue_du_mot[mot] + "|" + dico_def[mot] + "\n"
            print("DEBUG: chaine = ", chaine)
            try:
                fichier.write(chaine)
            except:
                print("Problème avec mot :", mot)
                print("Problème avec définition :", grand_dico[mot])

def type_de_mot(definition):
    """Détermine si le mot est un adverbe, un verbe, un substantif, etc. en cherchant entre:
    <span class="tlf_ccode">
    adj.
    </span></div><b>
    La regexp suivant semble fonctionner:  <span class="tlf_ccode">(.*?)<\/span>
    La fonction renvoie le type de mot: verbe ou non-verbe """
    try:
        ##type = re.search(r'tlf_ccode"(.*) <\/div', definition).group(1)
        type = re.search(r'tlf_ccode"([\s\S]*?)<\/div', definition).group(1)
        if "verbe" in type:
            return("verbe")
        else:
            return("non-verbe")
    except AttributeError:
        print("regexp n'a pas marché")
        print("definition = ", definition)

def ajoute_type_de_mot(dico1):
    """lit la definition du mot dans dico1[mot], détermine le type de mot (verbe ou non-verne) et renvoi un autre
    dico avec key = mot et value = type-de-mot. Au moment de créer le fichier CSV on utilisera les 2 dicos"""
    dico2 = {}
    for mot, definition in dico1.items():
        ##print("DEBUG: mot = {}, type_de_mot(definition) = {}".format(mot, type_de_mot(definition)))
        dico2[mot] = type_de_mot(definition)
        ##print("definition avant appel de la fonction type_de_mot = ", definition)
    return dico2

def langue_du_mot(definition):
    """Trouve la langue d'emprunt, en utilisant la regex suivante: r'Emprunté ((à l')|au )([\wç]*)' 
    Empr\. ((à l')|au |du |de l')([\wç]*)
    Emprunté ((à l')|au |de |du )([\wç]*)
    Emprunté +((à l')|au |de |du |à +|ou )([\wç]*)
    Emprunté +(à l'adjectif |à l'ancien bas |à l'ancien |à bas |à l'|au bas |au |de |du |à +|ou )([\wç]*)
Emprunté +(à l'ancien haut |à l'adjectif |à l'ancien bas |à l'ancien |de l'ancien |à bas |à l'|au bas |au |de l.|de |du |à +|ou )([\wç]*)
Emprunté +(au moyen |à l'ancien haut |à l'adjectif |à l'ancien bas |à l'ancien |de l'ancien |à bas |à l'|au bas |au |de l.|de |du |à +|ou )([\wç]*)"""
    try:
        type = re.search(r"Emprunté +(au moyen |à l'ancien haut |à l'adjectif |à l'ancien bas |à l'ancien |de l'ancien |à bas |à l'|au bas |au |de l.|de |du |à +|ou )([\wç]*)", definition).group(2)
        return(type)
    except AttributeError:
        print("ERREUR: regexp n'a pas marché")
        print("ERREUR: definition = ", definition)
        return("langue_inconnue")

def ajoute_langue_du_mot(dico1):
    """lit la definition du mot dans dico1[mot], détermine la langue à qui le mot est emprunté et renvoi un autre
    dico avec key = mot et value = langue-du-mot. Au moment de créer le fichier CSV on utilisera les 2 dicos"""
    dico2 = {}
    for mot, definition in dico1.items():
        print("DEBUG: mot = {}, lange_du_mot(definition) = {}".format(mot, langue_du_mot(definition)))
        dico2[mot] = langue_du_mot(definition)
        print("definition avant appel de la fonction langue_du_mot = ", definition)
    return dico2