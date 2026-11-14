CREATE TABLE utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    courriel TEXT UNIQUE NOT NULL,
    avatar_id VARCHAR(32),
    mot_de_passe_hash TEXT NOT NULL,
    mot_de_passe_salt TEXT NOT NULL

);

CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    identifiant TEXT UNIQUE NOT NULL, --Slug for requested unique article id
    id_auteur INTEGER NOT NULL,
    date_publication DATE NOT NULL,
    contenu TEXT NOT NULL,
    FOREIGN KEY (id_auteur) REFERENCES utilisateurs (id)
);

CREATE TABLE avatar (
    id VARCHAR(32),
    data blob
);

