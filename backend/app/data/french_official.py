"""Official French sequences 1AM–4AM from the Ministry's annual plans (Plans annuels, septembre 2022).
Run:  python -m app.data.french_official
"""
import json
from pathlib import Path

SRC = "Plan annuel des apprentissages — Français {n}AM, Ministère de l'Éducation Nationale (septembre 2022)"

CT = {
    1: {1: "Comprendre et produire à l'oral et à l'écrit des textes explicatifs en tenant compte des contraintes de la situation de communication.",
        2: "Comprendre et produire à l'oral et à l'écrit des textes prescriptifs en tenant compte des contraintes de la situation de communication."},
    2: {1: "Comprendre et produire, oralement et par écrit, des récits de fiction (conte, fable, bande dessinée, légende) en tenant compte de la situation de communication."},
    3: {1: "Comprendre et produire, oralement et par écrit, des récits de faits réels (article de presse, fait divers, récit de vie, biographie) en tenant compte de la situation de communication."},
    4: {1: "À la fin de la 4ème AM, dans le respect des valeurs et en s'appuyant sur les compétences transversales, l'élève est capable de comprendre et de produire, oralement et par écrit, et ce, en adéquation avec la situation de communication, des textes argumentatifs."},
}
GLOBAL = {
    1: "Au terme de la 1ère AM, dans une démarche de résolution de situations problèmes, à partir de supports sonores et visuels, dans le respect des valeurs et en s'appuyant sur les compétences transversales, l'élève est capable de comprendre et de produire oralement et par écrit, en adéquation avec la situation de communication, des textes explicatifs et des textes prescriptifs.",
    2: "Au terme du 2e palier, dans une démarche de résolution de situations problèmes, dans le respect des valeurs, en s'appuyant sur les compétences transversales, l'élève est capable de comprendre et de produire oralement et par écrit, en adéquation avec la situation de communication, des textes narratifs.",
    3: "Au terme du 2e palier, dans une démarche de résolution de situations problèmes, dans le respect des valeurs, en s'appuyant sur les compétences transversales, l'élève est capable de comprendre et de produire oralement et par écrit, en adéquation avec la situation de communication, des textes narratifs.",
    4: "Au terme de la 4ème AM, dans une démarche de résolution de situations problèmes à partir de supports sonores et visuels, dans le respect des valeurs et en s'appuyant sur les compétences transversales, l'élève est capable de comprendre et de produire oralement et par écrit des textes argumentatifs.",
}

# (title, CT index, oral (réception, production), écrit (réception, production), [ressources], [indicateurs])
S = {
    1: [
        ("Comprendre et produire une explication : la définition", 1,
         ("Écouter et comprendre un document (audio/audiovisuel) contenant un message explicatif", "Produire/reformuler un message explicatif"),
         ("Lire et comprendre des textes explicatifs", "Formuler/reformuler une explication"),
         ["Manipuler les procédés explicatifs : la définition, la synonymie", "Utiliser un document/outil de recherche (dictionnaire, encyclopédie, moteur de recherche)",
          "Employer la relative par « qui » au service de l'explication", "Manipuler le présent atemporel"],
         ["Identifier une explication et l'objet de l'explication", "Élaborer une définition simple et chercher un synonyme dans un ouvrage de référence",
          "Utiliser les ressources lexicales et grammaticales adéquates : les procédés, les structures syntaxiques et le temps approprié"]),
        ("Comprendre et produire une explication : l'illustration", 1,
         ("Écouter et comprendre un document (audio/audiovisuel) contenant un message explicatif", "Donner/reformuler une explication basée sur un support d'aide iconique"),
         ("Lire et comprendre un texte explicatif accompagné d'un support d'illustration : dessin, affiche, plan, schéma", "Produire un petit énoncé explicatif avec un support d'aide illustratif"),
         ["Manipuler les procédés explicatifs : l'illustration", "Maîtriser l'équivalence sémantique et syntaxique entre le complément du nom et l'adjectif qualificatif",
          "Accorder l'adjectif qualificatif", "Employer le présent de l'indicatif au service de l'explication"],
         ["Identifier une explication et l'objet de cette explication", "Formuler une explication simple à partir d'un support d'aide",
          "Mobiliser les ressources lexicales et syntaxiques pertinentes : complément du nom et adjectif"]),
        ("Comprendre et produire une explication : l'énumération", 1,
         ("Écouter et comprendre un document (audio/audiovisuel) contenant un message explicatif", "Donner/formuler une explication énumérative avec ou sans support d'aide"),
         ("Lire et comprendre un texte explicatif présentant une structure énumérative", "Produire une explication comportant une structure énumérative simple"),
         ["Manipuler les procédés explicatifs : l'énumération", "Utiliser les signes de ponctuation : les tirets et les parenthèses",
          "Utiliser la phrase déclarative et la phrase interrogative", "Accorder au présent le sujet avec le verbe (renforcer au besoin les verbes du 2e groupe)"],
         ["Identifier une explication et l'objet de cette explication", "Retrouver l'ordre dans lequel sont données des informations dans un texte explicatif",
          "Formuler une explication énumérative simple", "Mobiliser les ressources adéquates : ponctuation, types de phrase, accords"]),
        ("Comprendre et produire une explication : reformuler", 1,
         ("Écouter et comprendre un document contenant une explication avec des passages reformulés", "Reformuler des énoncés explicatifs avec ou sans marqueur de relation"),
         ("Lire et comprendre un texte explicatif contenant des reformulations avec et sans marqueur de relation", "Produire une explication simple comportant un passage reformulé à l'aide d'un marqueur de relation"),
         ["Manipuler les procédés explicatifs : la reformulation, avec les marqueurs de relation (« c'est-à-dire », « autrement dit »)", "Utiliser la substitution lexicale",
          "Manipuler le rapport logique de cause-conséquence au service de l'explication", "Manipuler le présent de vérité générale"],
         ["Identifier une explication et l'objet de cette explication", "Retrouver le rapport logique cause-conséquence d'un problème",
          "Donner une explication en utilisant un marqueur de reformulation", "Mobiliser les marqueurs de relation, le rapport logique, le présent de l'indicatif"]),
        ("Comprendre et produire une explication : insérer un/des exemples", 1,
         ("Écouter et comprendre un document contenant une explication renforcée par des exemples", "Produire des exemples pour étayer une explication, avec ou sans support d'aide"),
         ("Lire et comprendre un texte contenant une explication appuyée par des exemples", "Produire un texte explicatif et y insérer des exemples/des illustrations"),
         ["Manipuler les procédés explicatifs : l'exemple", "Utiliser les structures « en effet », « par exemple », « pour » afin d'introduire l'exemple ou le but",
          "Employer le présent de l'indicatif (renforcer au besoin les verbes du 3e groupe)"],
         ["Reconnaître une explication et l'objet de cette explication", "Identifier les détails qui appuient une explication",
          "Formuler une explication enrichie par des exemples", "Mobiliser vocabulaire, structures et temps adéquats"]),
        ("Comprendre et produire des textes prescriptifs : les conseils et/ou les recommandations", 2,
         ("Écouter et comprendre des documents contenant des recommandations et/ou des conseils", "Faire des recommandations et/ou donner des conseils en tenant compte des contraintes de la situation"),
         ("Lire et comprendre des textes contenant des recommandations et/ou des conseils", "Formuler une liste de conseils et/ou de recommandations en rapport avec une situation donnée"),
         ["Classer dans un ordre cohérent les éléments d'une liste de conseils/recommandations", "Manipuler la phrase impérative (injonctive) affirmative/négative",
          "Manipuler les verbes aux modes infinitif/impératif pour recommander ou conseiller"],
         ["Reconnaître une liste de recommandations et de conseils liés à une situation", "Formuler des recommandations et des conseils exigés par une situation",
          "Intégrer les ressources étudiées : ordre et pertinence, modes infinitif/impératif, ponctuation"]),
        ("Comprendre et produire des textes prescriptifs : l'ordre, l'interdiction", 2,
         ("Écouter et comprendre des documents contenant des ordres et/ou des interdictions", "Donner/formuler une série de consignes en tenant compte des contraintes de la situation"),
         ("Lire et comprendre des textes prescriptifs contenant des ordres et/ou des interdictions", "Produire des énoncés prescriptifs liés à une situation spécifique"),
         ["Utiliser les verbes de modalité « falloir + infinitif », « devoir » au présent de l'indicatif pour exprimer l'ordre et/ou l'obligation",
          "Manipuler le mode impératif en situation"],
         ["Reconnaître le texte prescriptif", "Formuler des consignes cohérentes en fonction d'une situation",
          "Mobiliser les tournures impersonnelles, la modalité injonctive, la ponctuation, la typographie"]),
    ],
    2: [
        ("Comprendre et produire les moments d'un conte : la situation initiale", 1,
         ("Écouter et comprendre un conte : la situation initiale", "Dire des débuts de contes"),
         ("Lire et comprendre un conte : la situation initiale", "Écrire des débuts de contes"),
         ["Employer les formules d'ouverture du conte", "Manipuler les compléments circonstanciels (temps, lieu et manière)", "Utiliser l'imparfait de l'indicatif"],
         ["Repérer la structure d'un conte et identifier le cadre spatio-temporel d'une situation initiale", "Dire/écrire le début d'un conte de manière attrayante",
          "Utiliser les formules d'ouverture, les indicateurs spatio-temporels et l'imparfait"]),
        ("Comprendre et produire les moments d'un conte : les péripéties", 1,
         ("Écouter et comprendre un conte : suivre la trame des événements", "Dire une succession d'événements d'un conte"),
         ("Lire et comprendre un conte : les péripéties", "Écrire une suite d'actions en cohérence avec la situation initiale d'un conte"),
         ["Connaître le vocabulaire du merveilleux", "Utiliser les expansions du groupe nominal (adjectif, complément du nom…)", "Utiliser les articulateurs chronologiques",
          "Trouver des qualités au personnage principal d'un conte", "Utiliser le passé simple en situation"],
         ["Repérer la structure d'un conte et identifier les péripéties", "Développer un enchaînement d'actions en cohérence avec le début d'un conte",
          "Utiliser le vocabulaire approprié, une suite chronologique, des qualifiants, le passé simple"]),
        ("Comprendre et produire les moments d'un conte : la situation finale", 1,
         ("Écouter et comprendre un conte : la situation finale", "Dire la fin d'un conte"),
         ("Lire et comprendre un conte : le dénouement", "Écrire une fin heureuse en cohérence avec les moments précédents du conte"),
         ["Utiliser les formules de clôture du conte", "Éviter la répétition en employant des substituts lexicaux et grammaticaux"],
         ["Repérer la structure d'un conte en identifiant les différents moments", "Reconstituer un conte présenté dans le désordre",
          "Dire un conte à partir d'un support d'aide", "Utiliser les ressources grammaticales étudiées dans les 3 séquences"]),
        ("Comprendre et produire une fable", 1,
         ("Écouter et comprendre une fable : identifier le narrateur, les interlocuteurs, les propos, la morale", "Jouer une fable étudiée"),
         ("Lire et comprendre une fable : les caractéristiques typographiques et discursives du dialogue", "Transposer une fable sous une autre forme narrative"),
         ["Utiliser les verbes introducteurs de paroles", "Employer le présent de l'indicatif", "Manipuler les adverbes de manière"],
         ["Comprendre une fable : narrateur, interlocuteurs, propos, morale", "Insérer un petit échange entre interlocuteurs d'une fable",
          "Utiliser verbes introducteurs, marques du discours direct, présent de l'indicatif"]),
        ("Comprendre et produire une bande dessinée", 1,
         ("Écouter et comprendre un récit présenté sous forme de dessin animé : personnages, circonstances, événements", "Discuter le contenu d'un dessin animé fabuliste (le récit et la morale)"),
         ("Lire et comprendre le langage de la bande dessinée : planches, vignettes, bulles", "Produire des bulles narrateur et/ou personnages de bande dessinée"),
         ["Connaître le vocabulaire de la B.D.", "Employer les différents types de phrases", "Utiliser le futur simple"],
         ["Retrouver les caractéristiques de la fable transposée en dessin", "Comprendre le langage de la bande dessinée", "Produire des bulles de B.D.",
          "Employer le vocabulaire, les structures et les temps étudiés"]),
        ("Comprendre et produire le récit d'un personnage légendaire", 1,
         ("Écouter et comprendre le récit d'un personnage légendaire : ses qualités physiques et morales", "Discuter autour de récits de légende : faits et personnages extraordinaires"),
         ("Lire et comprendre des récits de personnages légendaires : portrait, caractère, pouvoir, qualités", "Décrire un personnage de légende de son choix en mettant en valeur ses qualités extraordinaires"),
         ["Utiliser le procédé de dérivation lexicale : suffixes -ation / -age / -ment", "Employer la proposition subordonnée relative avec « qui » pour caractériser un personnage",
          "Manipuler la distanciation/actualisation à travers l'emploi alternatif du passé composé/passé simple"],
         ["Reconnaître le récit de légende", "Identifier les caractéristiques physiques et morales d'un personnage légendaire",
          "Décrire un personnage légendaire", "Mobiliser les ressources lexicales et grammaticales pertinentes"]),
        ("Comprendre et produire le récit d'un lieu de légende", 1,
         ("Écouter et comprendre le récit d'un lieu de légende : les faits légendaires et leur impact sur le lieu", "Discuter autour de récits de lieux de légende"),
         ("Lire et comprendre le récit d'un lieu et/ou de faits légendaires", "Décrire un lieu de légende de son choix en mettant en valeur les faits extraordinaires qui y sont liés"),
         ["Manipuler le vocabulaire de la description d'un lieu", "Utiliser les indicateurs de lieu", "Employer la proposition subordonnée relative avec « qui », « où »"],
         ["Reconnaître le récit de légende se rapportant à un personnage ou un lieu", "Décrire un lieu de légende avec ou sans support d'aide",
          "Utiliser vocabulaire approprié, propositions relatives et formes verbales"]),
    ],
    3: [
        ("Produire un article de presse sous forme d'une brève", 1,
         ("Écouter et comprendre un récit de faits réels sous la forme d'une brève", "Produire une brève à partir d'éléments de situation donnés"),
         ("Lire et comprendre un texte de faits réels sous la forme d'une brève", "Produire un récit de presse cohérent sous la forme d'une brève et réviser sa production"),
         ["Utiliser le vocabulaire lié au thème, le champ lexical de la brève", "Employer les indicateurs de temps et de lieu", "Manipuler le passé composé en situation"],
         ["Reconnaître les éléments constitutifs d'une brève", "Produire un récit de faits cohérent et structuré sous forme d'une brève", "Employer le passé composé"]),
        ("Produire un article de presse contenant un titre et un chapeau", 1,
         ("Écouter et comprendre un fait divers en tenant compte de la situation de communication", "Produire un fait divers avec ou sans support d'aide"),
         ("Lire et comprendre des articles de presse / faits divers", "Produire un titre et un chapeau en tenant compte de la situation de communication"),
         ["Formuler des titres par le procédé de la nominalisation des verbes", "Produire des chapeaux d'articles", "Utiliser le présent de l'indicatif en situation"],
         ["Produire des titres d'articles", "Introduire un fait divers sous une forme synthétisée", "Mobiliser les bonnes ressources linguistiques"]),
        ("Insérer un témoignage dans un article de presse", 1,
         ("Écouter et comprendre un témoignage dans un fait divers", "Insérer un témoignage dans un récit de faits réels"),
         ("Lire et comprendre des récits comportant des paroles de témoin", "Introduire des paroles de témoin dans un récit de presse en respectant les codes en usage"),
         ["Employer les verbes de perception", "Manipuler le discours direct et le discours indirect dans des situations de témoignage (au présent)",
          "Exprimer l'antériorité des actions en employant le plus-que-parfait"],
         ["Localiser et extraire des paroles de témoin dans un article", "Insérer des témoignages dans un article",
          "Employer verbes de perception, style direct/indirect, antériorité"]),
        ("Raconter des faits / événements réels", 1,
         ("Écouter et comprendre un récit de faits réels", "Élaborer un récit de faits/d'événements cohérent"),
         ("Lire et comprendre un texte relatant un enchaînement d'événements vécus", "Produire/transposer un récit d'événements en s'appuyant sur une trame narrative ou un support d'aide"),
         ["Utiliser le vocabulaire lié au thème ; les mots de la même famille", "Employer les connecteurs chronologiques", "Articuler les temps du récit : imparfait / passé simple"],
         ["Reconnaître un récit basé sur une succession d'événements liés", "Construire un récit de faits cohérent",
          "Utiliser les connecteurs et les temps du récit"]),
        ("Insérer la description d'un objet dans une séquence narrative", 1,
         ("Écouter et comprendre une séquence descriptive relative à un objet de valeur, un lieu historique…", "Produire une séquence descriptive relative à un objet de valeur, un lieu"),
         ("Lire et comprendre un texte descriptif qui valorise un objet / un lieu", "Produire un passage descriptif qui valorise un objet / un lieu"),
         ["Utiliser les verbes de perception et de localisation", "Utiliser le vocabulaire du beau (vocabulaire mélioratif)", "Enrichir les phrases par des expansions du nom",
          "Employer le présent de l'indicatif dans des passages descriptifs", "Accorder l'adjectif qualificatif avec le nom"],
         ["Reconnaître un passage descriptif dans une narration", "Produire un passage descriptif pour l'insérer dans une séquence narrative",
          "Employer verbes de perception et de localisation, présent, adjectifs qualificatifs"]),
        ("Raconter un souvenir d'enfance ou une expérience vécue", 1,
         ("Écouter et comprendre un récit autobiographique / un souvenir d'enfance", "Raconter des souvenirs d'enfance"),
         ("Lire et comprendre un texte autobiographique / un souvenir d'enfance", "Produire un texte évoquant un souvenir d'enfance"),
         ["Utiliser le lexique du portrait", "Employer les déterminants", "Manipuler le présent d'énonciation"],
         ["Reconnaître un récit autobiographique", "Raconter une expérience personnelle ou des événements vécus",
          "Utiliser le « je », le présent, l'expression des perceptions/sentiments personnels"]),
        ("Rédiger une notice biographique", 1,
         ("Écouter et comprendre un document présentant une personne", "Présenter brièvement une personnalité de son choix"),
         ("Lire et comprendre un texte présentant une personne importante", "Produire une notice biographique d'une personnalité de son choix"),
         ["Caractériser une personne physiquement et moralement", "Employer les substituts lexicaux et grammaticaux",
          "Utiliser le présent à valeur d'actualisation", "Transcrire les noms propres"],
         ["Présenter un personnage de son choix et indiquer son parcours", "Suivre et respecter un plan de présentation",
          "Utiliser les éléments de progression et le présent de l'indicatif"]),
    ],
    4: [
        ("Comprendre et produire un message argumentatif : exprimer un point de vue / une opinion", 1,
         ("Écouter et comprendre un document (audio/audiovisuel) à structure argumentative", "Formuler un point de vue / une opinion en adéquation avec la situation de communication"),
         ("Lire et comprendre un texte argumentatif structuré", "Formuler un point de vue / une opinion par rapport à un thème spécifique de son choix"),
         ["Utiliser les verbes d'opinion pour formuler un point de vue personnel", "Utiliser le vocabulaire de la description (adj. qualificatifs, adj. de couleur…) et de la localisation",
          "Employer la proposition subordonnée complétive", "Verbes au présent de l'indicatif"],
         ["Reconnaître un message de type argumentatif", "Localiser et extraire le point de vue de l'énonciateur",
          "Formuler une opinion/un point de vue personnel par rapport à une question spécifique", "Mobiliser les ressources lexicales et syntaxiques étudiées"]),
        ("Comprendre et produire un message argumentatif : argumenter", 1,
         ("Écouter et comprendre un document contenant un argumentaire à l'appui d'une opinion", "Formuler des arguments pour appuyer un point de vue / une opinion"),
         ("Lire et comprendre un texte contenant un argumentaire à l'appui d'un point de vue", "Développer quelques arguments simples qui appuient un point de vue sur une thématique de son choix"),
         ["Utiliser les connecteurs d'énumération", "Employer la proposition subordonnée relative avec « que » / « qui »", "Manipuler le présent de narration / atemporel"],
         ["Reconnaître un message de type argumentatif", "Identifier le point de vue de l'énonciateur", "Localiser et extraire les arguments qui appuient l'opinion",
          "Formuler un point de vue étayé par quelques arguments"]),
        ("Comprendre et produire un message argumentatif : conclure", 1,
         ("Écouter et comprendre un document contenant un argumentaire enrichi par des exemples", "Formuler une conclusion en cohérence avec un argumentaire"),
         ("Lire et comprendre un texte argumentatif structuré enrichi par des exemples", "Clore une argumentation"),
         ["L'expression du jugement (vocabulaire mélioratif / dépréciatif) dans un texte argumentatif", "Utiliser les formules pour clore un argumentaire",
          "Articuler le rapport logique cause-conséquence"],
         ["Identifier la structure argumentative", "Localiser et extraire les arguments et les exemples qui les appuient", "Formuler une conclusion pour clore l'argumentaire"]),
        ("Comprendre et produire un dialogue argumentatif", 1,
         ("Écouter et comprendre un document contenant des échanges d'arguments sous forme dialoguée", "Interagir dans un échange d'arguments en adéquation avec une situation de communication"),
         ("Lire et comprendre un dialogue argumentatif structuré", "Produire des arguments dans une situation d'échange"),
         ["Employer le vocabulaire lié au thème", "Utiliser les signes typographiques dans un dialogue", "Manipuler la proposition circonstancielle de but",
          "Manipuler le présent du subjonctif en situation"],
         ["Identifier les interlocuteurs et les points de vue développés", "Identifier des arguments et les associer aux différents intervenants",
          "Produire un échange d'arguments cohérent qui s'appuie sur des points de vue différents"]),
        ("Comprendre et produire un message argumentatif : rapporter un point de vue / une opinion", 1,
         ("Écouter et comprendre un document contenant un argumentaire structuré", "Rapporter un point de vue argumenté en adéquation avec la situation de communication"),
         ("Lire et comprendre un texte / un dialogue structuré autour d'un point de vue argumenté", "Rapporter un point de vue étayé par des arguments"),
         ["Repérer le champ lexical", "Utiliser les verbes de parole (au présent de l'indicatif)", "Maîtriser les transformations induites par le passage du style direct au style indirect"],
         ["Reconnaître des arguments dans toutes les situations", "Identifier les interlocuteurs et les points de vue développés",
          "Rapporter un point de vue développé par un argumentaire et une conclusion, sous forme de résumé succinct"]),
        ("Comprendre et produire un message argumentatif : sensibiliser sur une cause", 1,
         ("Écouter et comprendre un message argumentatif de sensibilisation sur une cause d'intérêt public", "Formuler un argumentaire destiné à sensibiliser sur une cause de son choix"),
         ("Lire et comprendre un texte argumentatif de sensibilisation sur une cause humaine ou d'intérêt général", "Produire un message de sensibilisation contenant des arguments"),
         ["Explorer le champ thématique lié à la problématique", "Impliquer l'interlocuteur", "Employer la proposition circonstancielle de condition",
          "Articuler les modes de verbes appropriés : indicatif – subjonctif ou conditionnel"],
         ["Reconnaître un message de sensibilisation argumenté", "Identifier les interlocuteurs et la cause concernée", "Produire un message de sensibilisation argumenté"]),
        ("Comprendre et produire un message argumentatif : inciter à agir", 1,
         ("Écouter et comprendre un message qui incite à agir", "Formuler des arguments destinés à faire agir en faveur d'une cause de son choix"),
         ("Lire et comprendre un texte argumentatif qui incite à agir en faveur d'une cause", "Produire un argumentaire pour faire agir"),
         ["Explorer le champ thématique lié à la problématique", "Employer la proposition circonstancielle d'opposition", "Articuler les modes de verbe : indicatif / subjonctif"],
         ["Reconnaître un message qui incite à agir", "Produire un message argumentatif qui cherche à faire agir le destinataire",
          "Mobiliser les ressources lexicales, syntaxiques et typographiques étudiées"]),
    ],
}

GUIDE = ("Chaque séquence : 12 h + 2 h (évaluation/remédiation). Savoir-faire langagiers 9 h, ressources linguistiques 3 h. "
         "Déroulement type : Oral 2 h (réception puis production) ; Compréhension de l'écrit 1 (1 h) ; ressources linguistiques (3 h) ; "
         "Compréhension de l'écrit 2 (1 h, apprentissage moins guidé) ; Apprentissage de la mobilisation et de l'intégration des ressources / production écrite (4 h : "
         "analyse de la consigne, co-élaboration de la grille d'évaluation, planification, rédaction, autocorrection, réécriture) ; "
         "travaux dirigés de mise en forme finale et présentation orale (1 h) ; lecture plaisir (1 h). "
         "Grille d'évaluation : pertinence, correction de la langue, cohérence sémantique, perfectionnement. "
         "La production n'est pas une fin en soi : accompagner l'apprenant dans l'autocorrection.")

D_ORAL, D_ECRIT, D_RES, D_PROD = "Compréhension de l'oral", "Compréhension de l'écrit", "Points de langue", "Production de l'écrit"


def lessons(t):
    title, _, oral, ecrit, res, _ = t
    out = [
        {"title": f"Situation-problème de départ + Oral (réception) : {oral[0]}", "domain": D_ORAL,
         "hint": "Présentation de la situation-problème de la séquence, puis écoute du document."},
        {"title": f"Oral (production) : {oral[1]}", "domain": "Production de l'oral"},
        {"title": f"Compréhension de l'écrit 1 : {ecrit[0]}", "domain": D_ECRIT, "needs_text": True,
         "hint": "Indiquez le titre du texte support (manuel) dans « Support / titre du texte »."},
    ]
    out += [{"title": f"Ressources linguistiques : {r}", "domain": D_RES} for r in res]
    out += [
        {"title": f"Compréhension de l'écrit 2 : {ecrit[0]}", "domain": D_ECRIT, "needs_text": True,
         "hint": "Apprentissage moins guidé que dans la première lecture."},
        {"title": f"Production écrite (1) : préparation — {ecrit[1]}", "domain": D_PROD,
         "hint": "Analyse de la consigne, co-élaboration de la grille d'évaluation, planification du texte à produire."},
        {"title": f"Production écrite (2) : rédaction — {ecrit[1]}", "domain": D_PROD,
         "hint": "Rédaction, mise au propre et relecture de la production."},
        {"title": "Production écrite (3) : compte rendu, autocorrection et réécriture", "domain": D_PROD,
         "hint": "Partage, autocorrection (recours aux usuels), amélioration et réécriture."},
        {"title": "Travaux dirigés : mise en forme finale et présentation orale", "domain": "Production de l'oral"},
        {"title": "Lecture plaisir / détente", "domain": D_ECRIT},
        {"title": "Évaluation et remédiation de la séquence", "domain": D_PROD},
    ]
    return out


def build_level(n):
    out = []
    for i, t in enumerate(S[n], start=1):
        title, ct, oral, ecrit, res, ind = t
        out.append({
            "title": f"Séquence {i} : {title}",
            "hours": "12 h + 2 h",
            "official": {
                "source": SRC.format(n=n),
                "levels": {"Compétence terminale": CT[n][ct], "Compétence globale": GLOBAL[n]},
                "resources": {
                    "Oral": f"Réception : {oral[0]}. Production : {oral[1]}.",
                    "Écrit": f"Réception : {ecrit[0]}. Production : {ecrit[1]}.",
                    "Ressources linguistiques (3 h)": " ; ".join(res),
                },
                "situation": "Situation-problème de départ en lien avec le thème de la séquence, tirée du vécu de l'apprenant, débouchant sur une tâche de production.",
                "tasks": [oral[1], ecrit[1]],
                "criteria": ind,
            },
            "lessons": lessons(t),
        })
    return out


if __name__ == "__main__":
    path = Path(__file__).parent / "curriculum.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    fr = next(x for x in data["subjects"] if x["id"] == "french")
    fr["domains"] = [D_ORAL, "Production de l'oral", D_ECRIT, D_RES, D_PROD]
    for n in (1, 2, 3, 4):
        fr["levels"][str(n)] = build_level(n)
        fr.setdefault("guidelines", {})[str(n)] = GUIDE
        fr.setdefault("verified", {})[str(n)] = SRC.format(n=n)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print({n: len(S[n]) for n in S})
