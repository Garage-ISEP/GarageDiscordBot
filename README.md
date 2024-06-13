# GarageDiscordBot

Un bot Discord pour le serveur Garage, créé par Simon Tuloup - promo 2027.

- Attribution automatique des rôles
- Génération d'OTP pour le local NDL
- Informations sur le propriétaire du serveur

## Commandes

`/add_member <pseudo> <lab>` : peut être exécuté par les présidents ou VP de lab pour ajouter des membres à leur lab.

`/remove_member <pseudo> <lab>` : peut être exécuté par les présidents ou VP de lab pour retirer des membres de leur lab.

Fonctionnement: Les membres possédant un rôle nommé "Prez - X" ou "VicePrez - X" peuvent ajouter ou retirer le rôle "X" à un autre membre en utilisant les commandes `/add_member` et `/remove_member`. Les admins aussi.


`/code_ndl` : nécessite le rôle `code`, permet de générer un code valable 1h pour le local NDL.

`/owner` : affiche les informations sur le propriétaire du serveur.

`/ping` : affiche le ping du bot.

`&&getlog` : nécessite le rôle `admin`, affiche les logs de `/code_ndl`.

`&&purge` : nécessite le rôle `admin`, force la purge des OTP périmés de `/code_ndl`. Renvoie un booléen indiquant si des codes ont été supprimés ou non.

## Fonctionnalités supplémentaires

- Fait tourner les fichiers de log pour éviter de dépasser 20MB, archive les anciens fichiers de log sous la forme `CodeLog-Archive-{date}.bak`.


## Installation

1. Téléchargez le fichier `docker-compose.yml` et le fichier `.env`.
2. Remplissez le fichier `.env` avec les informations nécessaires.
3. Exécutez la commande `docker compose up -d` pour lancer le bot.

Lien vers le dépôt GitHub : <https://github.com/Garage-ISEP/GarageDiscordBot>
