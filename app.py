import markdown
from flask import Flask, render_template, redirect, url_for, request, g, \
    session
from database import Database
import os
import re

app = Flask(__name__, static_url_path='', static_folder='static')
app.secret_key = os.urandom(24)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        g._database = Database()
    return g._database


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.disconnect()


def valider_courriel_existe(courriel):
    return get_db().courriel_existe(courriel)


def valider_courriel(courriel, validation_courriel):
    return courriel == validation_courriel


def valider_mdp(mdp):
    regex = r"^[A-Za-z0-9#$%&'*+/=?@]{8,}$"
    mdp_format_test = re.compile(regex).fullmatch
    return mdp_format_test(mdp) is not None


def password_validation(courriel, mpd):
    return get_db().validate_password(courriel, mpd)


@app.route('/')
def index():
    print("Session data:", session)
    title = "ROCKET CMS"
    if 'user_id' in session:
        return redirect(url_for('dashboard')), 302
    # print("Articles fetched from database:", articles)
    return render_template('index.html',
                           title=title,
                           articles=get_db().get_all_articles(5)), 200


@app.route('/admin', methods=['GET', 'POST'])
def signin():
    title = "Mon compte - veuillez vous connecter"

    if request.method == "GET":
        return render_template('sign-in.html', title=title), 200

    # Manage POST queries
    if request.method == "POST":
        form_data = {
            'courriel': request.form.get('courriel', "").strip(),
            'mdp': request.form.get('mdp', "").strip()
        }

        if not all(form_data.values()):
            return render_template('sign-in.html', title=title,
                                   message_erreur="Tous les champs doivent "
                                                  "être remplis"), 400

        if not password_validation(form_data['courriel'], form_data['mdp']):
            return render_template('sign-in.html', title=title,
                                   mdp_erreur="Le courriel ou le mot de passe "
                                              "est incorrect. "
                                              "Veuillez réessayer."), 400

        user = get_db().fetch_user_info(form_data['courriel'])
        session.clear()
        session['user_id'] = user[0]
        session['nom'] = user[1]
        session['prenom'] = user[2]
        session['courriel'] = user[3]

        # logged in -> go to dasbord
        return redirect(url_for('dashboard')), 302


@app.route('/createaccount', methods=['GET', 'POST'])
def create_account():
    title = "Créer un compte"

    if request.method == "GET":
        return render_template('new-account.html', title=title), 200

    # Manage POST queries
    form_data = {
        'nom': request.form.get('nom', "").strip(),
        'prenom': request.form.get('prenom', "").strip(),
        'courriel': request.form.get('courriel', "").strip(),
        'validation-courriel':
            request.form.get('validation-courriel', "").strip(),
        'mdp': request.form.get('mdp', "").strip()
    }

    erreurs = {}

    if not all(form_data.values()):
        erreurs["message_erreur"] = "Tous les champs doivent être remplis"

    if form_data['courriel'] != form_data['validation-courriel']:
        erreurs['courriel_erreur'] = "Les courriels ne correspondent pas."

    if valider_courriel_existe(form_data['courriel']):
        erreurs["courriel_erreur"] = "Ce courriel existe déjà"

    if not valider_mdp(form_data['mdp']):
        erreurs["mdp_erreur"] = ("Votre mot de passe ne respecte pas "
                                 "les critères")

    if erreurs:
        return render_template('new-account.html', title=title,
                               **erreurs, **form_data), 400

    # Attempt to create a user
    try:
        get_db().create_user(
            form_data['nom'],
            form_data['prenom'],
            form_data['courriel'],
            form_data['mdp']
        )
    except Exception as e:
        erreurs["db_erreur"] = ("Une erreur est survenue lors de "
                                "l'inscription. Veuillez réessayer.")
        return render_template('new-account.html', title=title,
                               **erreurs, **form_data), 500

    # account created & logged in -> go to dashboard
    return redirect(url_for('dashboard')), 302


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    title = 'ADMIN PAGE'

    print("Session data:", session)  # Debugging
    # Redirect if user not session
    if 'user_id' not in session:
        return redirect(url_for('signin')), 302

    return render_template('dashboard.html',
                           title=title,
                           user=session,
                           articles=get_db().get_all_articles(limit=None),
                           is_admin=True), 200


@app.route('/logout', methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for('index')), 302


@app.errorhandler(404)
def page_not_found(e):
    title = "ERROR PAGE"
    return render_template('404.html', title=title), 404


@app.route('/search', methods=['GET'])
def search():
    title = "Article Search"
    query = request.args.get('query', '').strip()

    print("Session data:", session)  # Debugging

    if not query:
        return redirect(url_for('index')), 302  # Go home if request is empty

    article_data = get_db().search_articles(query)

    # Conversion
    articles = [
        {
            'id': article[0],
            'titre': article[1],
            'identifiant': article[2],
            'date_publication': article[3]
        }
        for article in article_data
    ]
    # Check if user connected to apply dynamically different links
    is_admin = 'user_id' in session

    return render_template('search_results.html',
                           query=query,
                           articles=articles,
                           is_admin=is_admin, title=title), 200


@app.route('/article/<identifiant>')
def view_article(identifiant):
    title = 'Article'

    # Ret a tuple -> turn into dictionary
    article_data = get_db().fetch_article_by_identifiant(identifiant)

    if not article_data:
        return render_template('404.html'), 404  # 404 and profile pic of user

    # Conversion into dictionary
    article = {
        'id': article_data[0],
        'titre': article_data[1],
        'identifiant': article_data[2],
        'date_publication': article_data[3],
        'contenu': markdown.markdown(article_data[4]),
        'auteur': article_data[5],
        'user_avatar': article_data[6]
    }

    return render_template('article.html', article=article, title=title), 200


@app.route('/edit/<identifiant>', methods=["GET", "POST"])
def edit_article(identifiant):
    title = "Editing an article"
    print("Session data:", session)  # Debugging
    if 'user_id' not in session:
        return redirect(url_for('signin')), 302

    article_data = get_db().fetch_article_by_identifiant(identifiant)

    if not article_data:
        return render_template('404.html', title="ERROR PAGE"), 404

    if request.method == "POST":
        new_title = request.form['titre']
        new_contenu = request.form['contenu']

        get_db().update_article(identifiant, new_title, new_contenu)
        return redirect(url_for('dashboard')), 302

    # Conversion
    article = {
        'id': article_data[0],
        'titre': article_data[1],
        'identifiant': article_data[2],
        'date_publication': article_data[3],
        'contenu': article_data[4]
    }

    return render_template('edit_article.html',
                           article=article, title=title), 200


@app.route('/admin-nouveau', methods=["GET", "POST"])
def create_article():
    title = "Creating a new article "
    # Debugging : print("Session data:", session)
    if 'user_id' not in session:
        return redirect(url_for('signin')), 302

    # Manage POST requests in different way this will be store
    if request.method == "POST":
        form_data = {
            'titre': request.form.get('titre', "").strip(),
            'contenu': request.form.get('contenu', "").strip(),
            'date_publication': request.form.get('date_publication', "")
        }

        is_admin = 'user_id' in session
        if not all(form_data.values()):
            return render_template('create_article.html',
                                   message_erreur="Tous les champs doivent "
                                                  "être remplis",
                                   **form_data,
                                   is_admin=is_admin), 400

        get_db().insert_article(form_data['titre'],
                                session['user_id'],
                                form_data['date_publication'],
                                form_data['contenu'])
        return redirect(url_for('dashboard')), 302

    return render_template('create_article.html', title=title), 200


@app.route('/utilisateurs', methods=["GET", "POST"])
def manage_users():
    title = "User Management"
    if 'user_id' not in session:
        return redirect(url_for('signin')), 302

    db = get_db()
    users = db.get_all_users()
    return render_template('manage_users.html',
                           users=users, title=title), 200


@app.route('/utilisateurs/nouveau', methods=["GET", "POST"])
def create_user():
    title = "Adding a new user"
    if 'user_id' not in session:
        return redirect(url_for('signin')), 302

    if request.method == "POST":
        form_data = {
            'nom': request.form.get('nom', "").strip(),
            'prenom': request.form.get('prenom', "").strip(),
            'courriel': request.form.get('courriel', "").strip(),
            'password': request.form.get('password', "").strip()
        }

        is_admin = 'user_id' in session
        if not all(form_data.values()):
            return render_template('create_user.html',
                                   message_erreur="Tous les champs doivent "
                                                  "être remplis",
                                   **form_data,
                                   is_admin=is_admin), 400

        get_db().create_user(form_data['nom'],
                             form_data['prenom'],
                             form_data['courriel'],
                             form_data['password'])
        return redirect(url_for('manage_users')), 302

    return render_template('create_user.html', title=title), 200


@app.route('/utilisateurs/modifier/<int:user_id>', methods=["GET", "POST"])
def modify_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('signin')), 302

    if request.method == "POST":
        form_data = {
            'nom': request.form.get('nom', "").strip(),
            'prenom': request.form.get('prenom', "").strip(),
            'courriel': request.form.get('courriel', "").strip(),
        }

        is_admin = 'user_id' in session
        if not all(form_data.values()):
            return render_template('modify_user.html',
                                   message_erreur="Tous les champs doivent "
                                                  "être remplis",
                                   **form_data,
                                   is_admin=is_admin), 400
        get_db().update_user(user_id,
                             form_data['nom'],
                             form_data['prenom'],
                             form_data['courriel']
                             )
        return redirect(url_for('manage_users')), 302

    user = get_db().fetch_user(user_id)
    return render_template('modify_user.html', user=user), 200


@app.route('/utilisateurs/supprimer/<int:user_id>', methods=["POST"])
def delete_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('signin')), 302

    get_db().deactivate_user(user_id)
    return redirect(url_for('manage_users')), 302


if __name__ == '__main__':
    app.run()
