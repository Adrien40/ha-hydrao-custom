[![English](https://img.shields.io/badge/Language-English-red)](README.md) [![Français](https://img.shields.io/badge/Langue-Fran%C3%A7ais-blue)](#)

# Hydrao Custom pour Home Assistant 🚿
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/Adrien40/ha-hydrao-custom)](https://github.com/Adrien40/ha-hydrao-custom/releases)

Une **intégration 100 % locale pour Home Assistant** qui dialogue directement en Bluetooth Low Energy (BLE) avec votre appareil de douche Hydrao, pour suivre votre consommation d'eau douche après douche, sans aucune dépendance au Cloud. 🛡️

> ℹ️ **À savoir** : Cette intégration interroge directement l'appareil Hydrao en Bluetooth pendant que l'eau coule — c'est nécessaire pour lire les données et envoyer les réglages en direct à l'appareil.

Si ce projet vous est utile, vous pouvez soutenir son développement 🙏

<a href="https://www.buymeacoffee.com/adrien40"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" width="160"></a>

---

## ⚡ En résumé
- 🔌 Fonctionnement 100 % local via Bluetooth (BLE)
- 🏠 Compatible Home Assistant (Sans cloud)
- 🚿 Suivi détaillé de chaque douche : Volume, durée, volume perdu en eau froide
- 🔄⭐ Synchro Mode Confort : Remise à zéro automatique du compteur de l'appareil dès que l'eau atteint la Température de confort minimum définie
- 🎨 Réglage des 4 seuils en litres et choix de leur couleur via un sélecteur direct intégré
- 🌡️ Température de confort minimum réglable dans Home Assistant (pas d'envoi à l'appareil Hydrao)
- 🔘 Bouton "Douche Terminée" pour clôturer une douche manuellement ou via une automatisation (Ex. : Hey Google, Douche Terminée "Prénom") — <sub>un `input_boolean` peut être nécessaire pour le relier à Google Assistant</sub>
- ⚙️ Installation via HACS en 2 minutes

---

## 📸 Exemples dans Home Assistant

### 📊 Visualisation

<p align="center">
  <img src="docs/screenshots/dashboard_overview.png" width="600">
</p>

<p align="center">
  <em>📊 Vue d'ensemble des données de douche dans Home Assistant</em>
</p>

### 🔍 Détails techniques

<p align="center">
  <img src="docs/screenshots/entities_overview.png" width="600">
</p>

<p align="center">
  <em>🔍 Entités exposées par l'intégration & ⚙️ Options de Configuration avancées</em>
</p>

---

### 💡 Pourquoi cette intégration ?
Cette intégration exploite directement le protocole BLE de votre Hydrao pour un suivi domotique complet, sans compromis :

* **🔒 100 % local :** Aucune connexion internet nécessaire, les données transitent uniquement de la douche à Home Assistant.
* **🚿 Suivi précis par douche :** Volume, durée, et surtout le volume d'eau froide perdu avant que l'eau ne soit à bonne température.
* **🔄 Synchro Mode Confort :** Redémarre le compteur sur l'appareil dès que la Température de confort minimum est atteinte, pour que les seuils de litres et couleurs ne reflètent que l'eau réellement confortable et donc utilisée.
* **🛡️ Pérennité :** Aucune dépendance à un serveur ou une application tierce.

---

### ✅ Compatibilité / Prérequis
* 🏷️ **Modèles supportés** : Appareils Hydrao diffusant en Bluetooth (BLE) sous un nom détecté automatiquement (`HYDRAO*`).
* 🏅 **Testé sur** : Validé sur le **Hydrao Aloé (HYDRA_SHOWER)**, version Hardware 9.
* 🛠️ **Matériel requis** : Adaptateur Bluetooth interne, clé USB Bluetooth, ou **Bluetooth Proxy ESPHome** (Recommandé pour la portée, [installation facile ici](https://esphome.github.io/bluetooth-proxies/)).
* 💧 **Réveil de l'appareil** : L'Hydrao ne communique en Bluetooth que lorsque l'eau coule, pensez à faire couler l'eau pour que l'intégration puisse lire ou écrire les réglages (seuils, couleurs, temps de savonnage).
* 📶 **Signal Bluetooth** : Un capteur RSSI dédié permet de surveiller la qualité du signal en direct.

---

### ✨ Points forts
* 🔄⭐ **Synchro Mode Confort** (Interrupteur) : Remise à zéro automatique du compteur de l'appareil dès que l'eau atteint la Température de confort minimum définie — la fonctionnalité phare de cette intégration.
* 🏠 **100 % Local (BLE)** : Aucune dépendance au Cloud.
* 💧 **Volumes détaillés** : Volume total cumulé, volume de la douche en cours, volume confort, volume perdu (eau froide) — en cumul de session et en cumul total.
* ⏱️ **Durées détaillées** : Durée de la douche en cours et durée en zone de confort.
* 🎨 **Seuils & Couleurs** : Réglage des 4 seuils en litres et choix de leur couleur via un sélecteur direct intégré, lus et modifiés en direct sur l'appareil.
* 🌡️ **Température de confort minimum** : Réglable dans Home Assistant via une entité Number, avec plage validée (0 - 50 °C) — ce réglage reste dans Home Assistant, il n'est jamais envoyé à l'appareil Hydrao.
* 🧴 **Durée maximale de savonnage** : Durée avant remise à zéro des compteurs, réglable (10 à 600 secondes).
* 🔘 **Bouton "Douche Terminée"** : Termine manuellement le comptage en cours sans attendre la coupure d'eau. <sub>Astuce : un `input_boolean` peut être nécessaire pour relier ce bouton à Google Assistant.</sub>
* 🔵 **État Bluetooth détaillé** : Eau Coupée, Connexion, Connecté, Erreur, Envoi de Configuration, Configuration Appliquée, Échec, ou Redémarrage de l'appareil.
* 📋 **Configuration en Attente** : Indique en un coup d'œil si des réglages (seuils, couleurs, temps de savonnage) n'ont pas encore pu être envoyés à l'appareil.
* 📶 **Signal Bluetooth en direct** via écoute passive, sans solliciter l'appareil ni sa batterie.
* 🔧 **Diagnostic** : Firmware, Hardware et Identifiant Unique de l'appareil exposés au niveau de la fiche appareil.
* ⚙️ **Configuration 100 % UI** : Découverte automatique Bluetooth ou ajout manuel par adresse MAC, tout se règle depuis l'interface Home Assistant.
* 🔄 **Réinitialisation aux valeurs d'usine** disponible directement depuis les options.

---

### 🚀 Installation

#### Via HACS (Recommandé)
Ce dépôt n'étant pas (encore) dans la liste officielle par défaut, vous devez l'ajouter en tant que dépôt personnalisé.

1. Ouvrez **HACS** dans votre Home Assistant.
2. Cliquez sur les 3 petits points en haut à droite et sélectionnez **Dépôts personnalisés**.
3. Dans **Dépôt**, collez l'URL : `https://github.com/Adrien40/ha-hydrao-custom`
4. Dans **Type**, choisissez **Intégration** puis cliquez sur **Ajouter**.
5. Une fois ajouté, une fenêtre apparaît : Cliquez sur **Télécharger** (Sélectionnez la dernière version).
6. **Redémarrez complètement Home Assistant**.
7. Allez dans **Paramètres** > **Appareils et Services** > **Ajouter une intégration** et cherchez "Hydrao Custom".

#### Manuelle
Copiez le dossier `custom_components/hydrao_custom` dans le dossier `custom_components` de votre configuration Home Assistant, puis redémarrez.

---

### 📊 Capteurs et Contrôles disponibles
| Entité | Unité / Type | Description |
| :--- | :--- | :--- |
| 🔘 **Douche Terminée** | Bouton | Termine manuellement le comptage de la douche en cours. |
| ⏱️ **Durée Douche** | min | Durée brute de la douche en cours. |
| ⏱️ **Durée Douche Confort** | min | Durée passée en zone de confort. |
| 🌡️ **Température** | °C | Température de l'eau mesurée en direct. |
| 🚿 **Volume Douche** | L | Volume brut de la douche en cours. |
| 💧 **Volume Douche Confort** | L | Volume utilisé une fois la température de confort atteinte, pour la douche en cours. |
| 💧 **Volume Douche Confort Cumulé** | L | Cumul historique du volume utilisé une fois la température de confort atteinte. |
| 💧 **Volume Douche Cumulé** | L | Volume total cumulé depuis l'installation. |
| ❄️ **Volume Perdu (Eau Froide)** | L | Volume perdu avant d'atteindre la température de confort, pour la douche en cours. |
| ❄️ **Volume Perdu Cumulé** | L | Cumul historique du volume perdu en eau froide. |
| 🔄 **Synchro Mode Confort** | Interrupteur | Active la remise à zéro automatique dès le confort atteint. |
| 🌡️ **Température de confort minimum** | Number (°C) | Seuil de confort réglable (0 - 50 °C). |
| 📋 **Configuration en attente** | Statut | Réglage(s) en attente d'envoi à l'appareil (Aucune, Savonnage, Seuils, Couleurs, ou combinaisons). |
| 💨 **Débit** | L/min | Débit d'eau instantané. |
| 🧴 **Durée maximale de savonnage** | s | Durée maximale de savonnage actuellement configurée, lue sur l'appareil. |
| 🔵 **État Bluetooth** | Statut | Eau Coupée / Connexion / Connecté / Erreur / Envoi Configuration / Configuration Appliquée / Échec / Redémarrage de l'appareil. |
| 🟢🔵🩷🔴 **Seuil 1 à 4** | L | Les 4 paliers de litres configurés sur l'appareil, avec leur couleur en attribut. |
| 📶 **Signal Bluetooth** | dBm | Force du signal Bluetooth reçu en temps réel. |

ℹ️ *Le Firmware, l'Hardware et l'Identifiant Unique de l'appareil sont exposés par Home Assistant au niveau de la fiche appareil*

---

## 🚀 Configuration
1. Allez dans **Paramètres** > **Appareils et services**.
2. **Si l'eau coule et que l'appareil Hydrao est à portée**, Home Assistant le détecte automatiquement : ouvrez la notification de découverte et suivez l'assistant. **Sinon**, cliquez sur **Ajouter une intégration**, recherchez **Hydrao Custom**, puis renseignez l'adresse MAC de l'appareil manuellement.
3. Dans les deux cas, vous pouvez régler la Température de confort minimum dès cette étape.

### ⚙️ Options
Une fois l'appareil ajouté, cliquez sur **Configurer** ⚙️ pour :
* Ajuster la Température de confort minimum, la Durée maximale de savonnage et la Synchro Mode Confort.
* Modifier les 4 seuils de litres et leurs couleurs (Uniquement une fois une première connexion établie — faites couler l'eau pour réveiller l'appareil).
* Réinitialiser aux valeurs d'usine en un clic.

> ⚠️ **L'eau doit couler** au moment de la validation du formulaire pour que les nouveaux seuils soient envoyés à l'appareil. Si ce n'est pas le cas, l'état affichera **"🚰 Eau Coupée"** et le réglage restera visible dans le capteur **Configuration en Attente** jusqu'à la prochaine douche — et si l'envoi échoue malgré tout une fois l'eau relancée, l'intégration réessaiera automatiquement à la douche suivante.

---

### 🐛 Dépannage

<details>
<summary>⚠️ Voir les problèmes fréquents</summary>

* **"Eau Coupée" en permanence** : Normal, l'Hydrao ne communique en Bluetooth que lorsque l'eau coule.
* **"Erreur de Connexion"** : Contrairement à "Eau Coupée", ce statut signifie que l'appareil a bien été détecté à portée, mais que la connexion ou la lecture a tout de même échoué (signal trop faible ou instable, coupure en plein milieu d'une douche). Rapprochez votre antenne ou [installez un Proxy Bluetooth ESPHome](https://esphome.github.io/bluetooth-proxies/) près de la douche.
* **"Échec de la Configuration"** : L'écriture des nouveaux réglages sur l'appareil a échoué après plusieurs tentatives. Aucune inquiétude : Le changement n'est pas perdu (visible dans **Configuration en Attente**), il sera automatiquement retenté à la prochaine douche.
* **Seuils/Couleurs grisés dans les options** : Ils ne sont lisibles/modifiables qu'après une première connexion réussie — faites couler l'eau une fois avant de les régler.

</details>

---

### 🤝 Contributions & Support
Pour tout bug ou demande d'amélioration, merci d'ouvrir une [Issue](https://github.com/Adrien40/ha-hydrao-custom/issues) sur ce dépôt.

### ⚖️ Licence & Avertissement
Projet sous licence **GPLv3**. Il s'agit d'un projet indépendant, sans aucun lien avec la société Hydrao. L'utilisation de ce logiciel se fait sous votre propre responsabilité.

---

**Développé avec ❤️ par @Adrien40**

<a href="https://www.buymeacoffee.com/adrien40"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" width="180"></a>

<!-- Keywords: Home Assistant custom integration, BLE sensor, water saving, shower monitoring, local control -->
