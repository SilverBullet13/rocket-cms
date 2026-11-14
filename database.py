import hashlib
import random
import sqlite3
import uuid
from datetime import datetime

import markdown


def get_avatar_aleatoire():
    avatar = ['anime.png', 'batman.png', 'bear-russia.png',
              'coffee.png', 'jason.png', 'zombie.png']
    return random.choice(avatar)


class Database:

    def __init__(self):
        self.connection = None

    def get_connection(self):
        if self.connection is None:
            self.connection = sqlite3.connect('db/database.db')
        return self.connection

    def disconnect(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def get_all_articles(self, limit=None):
        cursor = self.get_connection().cursor()

        # Fetch all articles the no limit is specified aka logged in else,
        # fetch latest limit non-logged (5)
        query = """ SELECT articles.id, articles.titre, articles.identifiant,
                    utilisateurs.nom, utilisateurs.prenom,
                    articles.date_publication, articles.contenu
                    FROM articles
                    JOIN utilisateurs ON articles.id_auteur = utilisateurs.id
                    WHERE datetime(date_publication, 'localtime')
                        <= datetime('now', 'localtime')
                    ORDER BY date_publication DESC
                """

        if limit:
            limit = int(limit)
            query += " LIMIT ?"
            cursor.execute(query, (limit,))
        else:
            cursor.execute(query)

        articles = []

        for row in cursor.fetchall():
            (numero,
             titre,
             identifiant,
             nom, prenom,
             date_publication,
             contenu) = row

            contenu_html = markdown.markdown(contenu)
            articles.append({
                'id': numero,
                'titre': titre,
                "identifiant": identifiant,
                'auteur': f"{prenom} {nom}",
                'date_publication': date_publication,
                'contenu': contenu_html
            })
        return articles  # 5 articles or all

    def insert_article(self, titre, id_auteur, date_publication, contenu):
        connection = self.get_connection()
        identifiant = str(uuid.uuid4())[:8]

        connection.execute(
            "INSERT INTO articles (titre, identifiant, id_auteur, "
            "date_publication, contenu)"
            "VALUES (?, ?, ?, ?, ?)",
            (titre, identifiant, id_auteur, date_publication, contenu)
        )
        connection.commit()

    def create_user(self, nom, prenom, courriel, mdp):
        salt = uuid.uuid4().hex
        hashed_password = hashlib.sha3_512(str(mdp + salt)
                                           .encode("utf-8")).hexdigest()
        connection = self.get_connection()
        avatar_par_default = get_avatar_aleatoire()

        connection.execute(
            "INSERT INTO utilisateurs (nom, prenom, courriel, avatar_id,"
            "mot_de_passe_salt, mot_de_passe_hash)"
            "VALUES (?, ?, ?, ?, ?, ?)",
            (nom, prenom, courriel, avatar_par_default, salt, hashed_password)
        )
        connection.commit()

    def courriel_existe(self, courriel):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT 1 FROM utilisateurs WHERE courriel = ? ",
                           (courriel,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def validate_password(self, courriel, password):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT mot_de_passe_hash, mot_de_passe_salt "
                       "FROM utilisateurs "
                       "WHERE courriel = ?", (courriel,))
        user = cursor.fetchone()

        if not user:
            return False

        stored_hash = user[0]  # mot_de_passe_hash
        stored_salt = user[1]  # mot_de_passe_salt

        computed_hash = hashlib.sha3_512(str(password + stored_salt)
                                         .encode('utf-8')).hexdigest()

        return computed_hash == stored_hash

    def fetch_user_info(self, courriel):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT id, nom, prenom, courriel "
                       "FROM utilisateurs "
                       "WHERE courriel = ?", (courriel,))
        return cursor.fetchone()

    def fetch_article_by_identifiant(self, identifiant):
        cursor = self.get_connection().cursor()

        query = """SELECT articles.id, articles.titre, articles.identifiant,
                   articles.date_publication, articles.contenu,
                   utilisateurs.nom || ' ' || utilisateurs.prenom AS auteur,
                   utilisateurs.avatar_id FROM articles JOIN utilisateurs
                   ON articles.id_auteur = utilisateurs. id
                   WHERE identifiant = ?"""

        cursor.execute(query, (identifiant,))
        return cursor.fetchone()

    def search_articles(self, search_query):
        cursor = self.get_connection().cursor()

        query = """SELECT id, titre, identifiant, date_publication
                   FROM articles
                   WHERE (titre LIKE ? OR contenu LIKE ? )
                   AND date_publication <= datetime('now')
                   ORDER BY date_publication DESC"""

        like_query = f"%{search_query}%"
        cursor.execute(query, (like_query, like_query))

        return cursor.fetchall()

    def update_article(self, identifiant, new_title, new_contenu):
        connection = self.get_connection()
        cursor = connection.cursor()

        query = ("UPDATE articles SET titre = ?, contenu = ? "
                 "WHERE identifiant = ?")
        cursor.execute(query, (new_title, new_contenu, identifiant))

        connection.commit()

    def get_all_users(self):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT id, nom, prenom, courriel FROM utilisateurs")

        users = []
        for row in cursor.fetchall():
            id, nom, prenom, courriel = row
            users.append({
                'id': id,
                'nom': nom,
                'prenom': prenom,
                'courriel': courriel,
            })
        return users

    def update_user(self, user_id, new_nom, new_prenom, new_courriel):
        connection = self.get_connection()
        cursor = connection.cursor()
        query = ("UPDATE utilisateurs SET nom = ?, prenom = ?, courriel = ?"
                 "WHERE id = ?")
        cursor.execute(query, (new_nom, new_prenom,
                               new_courriel, user_id))
        connection.commit()

    def deactivate_user(self, user_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        query = "DELETE FROM utilisateurs WHERE id = ?"
        cursor.execute(query, (user_id,))
        connection.commit()

    def fetch_user(self, user_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT id, nom, prenom, courriel, avatar_id"
                       " FROM utilisateurs WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()

        # Return a dictionnary instead of a tuple like it did before
        return {
            'id': user_data[0],
            'nom': user_data[1],
            'prenom': user_data[2],
            'courriel': user_data[3],
            'avatar_id': user_data[4]
        }
