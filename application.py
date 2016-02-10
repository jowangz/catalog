# Catalog web app
# Zheng Wang 02/09/2016
# Udacity Catalog Project


import os
from flask import Flask, render_template, request, redirect, g
from werkzeug import secure_filename
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from functools import wraps
from dict2xml import dict2xml as xmlify

from flask import session as login_session
import random
import string
import uuid

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import httplib2
import json
from flask import make_response, jsonify, url_for, flash, send_from_directory
import requests

UPLOAD_FOLDER = 'statics/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpeg', 'jpg', 'gif'])

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Connect to Database and create database session
engine = create_engine('sqlite:///categoryitemwithuserandpicture.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect(url_for('showLogin'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login')
def showLogin():
    """Show login page."""
    # create state
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    # append state to login session
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Connect user to server."""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
                                json.dumps(
                                    'Current user is already connected.'),
                                200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.to_json()
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    # append name, picture and email to login_session
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['access_token'] = credentials.access_token

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius:'
    output += ' 150px;-webkit-border-radius: 150px;'
    output += ' -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """Disconnect user from server."""
    credentials = login_session.get('credentials')
    # check if user is already disconnected
    if credentials is None:
        response = make_response(json.dumps(
                                'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['access_token']

        response = make_response(json.dumps('Successfully Disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash('Successfully Disconnected.')
        return redirect(url_for('showLogin'))
    else:
        response = make_response(json.dumps(
                                'Fail to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showLogin'))


@app.route('/')
@app.route('/catalog/')
def catalog():
    """Show all categories."""
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(Item).order_by(desc(Item.id))
    return render_template('catalog.html', categories=categories, items=items)


@app.route('/catalog/<category_name>/')
def showCategory(category_name):
    """Show items within a category."""
    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(name=category_name).first()
    items = session.query(Item).filter_by(category_id=category.id).order_by(
                                                                asc(Item.name))
    return render_template(
                            'showCategory.html',
                            categories=categories,
                            items=items,
                            category=category)


@app.route('/new_category/', methods=['GET', 'POST'])
@login_required
def newCategory():
    """Create new category."""
    if request.method == 'POST':
        if request.form['name']:
            newCategory_name = request.form['name']
            # category name has to be unique.
            if session.query(Category).filter_by(
                                                name=newCategory_name).first():
                flash('Cannot Duplicate Category %s' % newCategory_name)
                return redirect(url_for('catalog'))
            newCategory = Category(
                            name=newCategory_name,
                            user_id=login_session['user_id'])
            session.add(newCategory)
            flash('New Category %s Successfully Created' % newCategory.name)
            session.commit()
            return redirect(url_for('catalog'))
        flash('You Need To Enter a Name for This Category.')
        return redirect(url_for('newCategory'))
    else:
        return render_template('newCategory.html')


@app.route('/catalog/<path:category_name>/edit/', methods=['GET', 'POST'])
@login_required
def editCategory(category_name):
    """Edit a category with given category name."""
    editedCategory = session.query(Category).filter_by(
                                    name=category_name).first()
    if login_session['user_id'] != editedCategory.user_id:
        flash(
            'Permission Is Required To Edit Category %s.'
            % editedCategory.name)
        return redirect('/catalog/%s/' % (category_name))
    if request.method == 'POST':
        if request.form['name']:
            # check if the category is duplicated.
            if session.query(Category).filter_by(
                                                name=request.form['name']
                                                ).first():
                flash('Cannot Duplicate Category %s' % request.form['name'])
                return redirect(url_for('catalog'))
            editedCategory.name = request.form['name']
            flash('Category Successfully Edited %s' % editedCategory.name)
            return redirect(url_for('catalog'))
    else:
        return render_template('editCategory.html', category=editedCategory)


@app.route('/catalog/<path:category_name>/delete/', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_name):
    """Delete a category with a given category name."""
    categoryToDelete = session.query(Category).filter_by(
                                                        name=category_name
                                                        ).first()
    if login_session['user_id'] != categoryToDelete.user_id:
        flash(
            'Permission Is Required To Edit Category %s.'
            % categoryToDelete.name)
        return redirect('/catalog/%s/' % (category_name))
    if request.method == 'POST':
        itemsToDelete = session.query(Item).filter_by(
                            category_id=categoryToDelete.id).all()
        for i in itemsToDelete:
            if i.picture:
                os.remove(os.path.join(
                                        app.config['UPLOAD_FOLDER'],
                                        i.picture))
            session.delete(i)
        session.delete(categoryToDelete)
        flash('%s Successfully Deleted' % categoryToDelete.name)
        session.commit()
        return redirect(url_for('catalog', category_name=category_name))
    else:
        return render_template(
                                'deleteCategory.html',
                                category=categoryToDelete)


@app.route('/catalog/<path:category_name>/<path:item_name>/')
def showCategoryItems(category_name, item_name):
    """Show the detail informations for a item
        with given category and item name.
    """
    categoryID = session.query(Category).filter_by(
                                                name=category_name).first().id
    item = session.query(Item).filter_by(
                                        name=item_name,
                                        category_id=categoryID).first()
    return render_template("item.html", item=item, category=item.category)


@app.route('/new_category_item/', methods=['GET', 'POST'])
@login_required
def newCategoryItem():
    """Create a new category item."""
    if request.method == 'POST':
        if not request.form['category']:
            flash('Need To Select a Category for This Item')
            return redirect(url_for('newCategoryItem'))
        if request.form['name']:
            newCategoryItem_name = request.form['name']
            if session.query(Item).filter_by(
                                            name=newCategoryItem_name
                                            ).first():
                flash(
                    'Cannot Duplicate Item %s In This Category'
                    % newCategoryItem_name)
                return redirect(url_for('catalog'))
            category_id = session.query(Category).filter_by(
                                                name=request.form['category']
                                                ).first().id

            file = request.files['file']
            unique_file_name = ''
            if file and allowed_file(file.filename):
                file_extension = os.path.splitext(file.filename)[-1].lower()
                filename = secure_filename(file.filename)
                # create unique file name for the image.
                unique_file_name = str(uuid.uuid4()) + file_extension
                file.save(os.path.join(
                                        app.config['UPLOAD_FOLDER'],
                                        unique_file_name))
            newCategoryItem = Item(
                name=newCategoryItem_name,
                description=request.form['description'],
                category_id=category_id,
                user_id=login_session['user_id'],
                picture=unique_file_name)

            session.add(newCategoryItem)
            flash('New Item %s Sucessfully Created' % newCategoryItem_name)
            session.commit()
            return redirect(url_for('catalog'))
        flash('You Need To Enter a Name for This Category Item.')
        return redirect(url_for('newCategoryItem'))

    else:
        categories = session.query(Category).order_by(
                                                asc(Category.name))
        return render_template('newCategoryItem.html', categories=categories)


@app.route(
    '/catalog/<path:category_name>/<path:item_name>/edit/',
    methods=['GET', 'POST'])
@login_required
def editCategoryItem(category_name, item_name):
    """Edit a item with given category and item name."""
    editedItemCategoryID = session.query(Category).filter_by(
                                            name=category_name).first().id
    editedItem = session.query(Item).filter_by(
                                            name=item_name,
                                            category_id=editedItemCategoryID
                                            ).first()
    if login_session['user_id'] != editedItem.user_id:
        flash('Permission Is Required To Edit Item %s.' % editedItem.name)
        return redirect('/catalog/%s/%s/' % (category_name, item_name))
    if request.method == 'POST':
        if request.form['name'] and request.form['description']:
            editedItem.name = request.form['name']
            editedItem.description = request.form['description']
            file = request.files['file']
            unique_file_name = ''
            if file and allowed_file(file.filename):
                file_extension = os.path.splitext(file.filename)[-1].lower()
                filename = secure_filename(file.filename)
                unique_file_name = str(uuid.uuid4()) + file_extension
                file.save(os.path.join(
                                        app.config['UPLOAD_FOLDER'],
                                        unique_file_name))
                if editedItem.picture:
                    os.remove(os.path.join(
                                            app.config['UPLOAD_FOLDER'],
                                            editedItem.picture))
                editedItem.picture = unique_file_name
            flash('Item Successfully Edited %s' % editedItem.name)
        return redirect(url_for(
                                'showCategoryItems',
                                category_name=category_name,
                                item_name=editedItem.name))
    else:
        return render_template('editCategoryItem.html', item=editedItem)


@app.route(
            '/catalog/<path:category_name>/<path:item_name>/delete/',
            methods=['GET', 'POST'])
@login_required
def deleteCategoryItem(category_name, item_name):
    """Delete a item with given category and item name."""
    itemToDeleteCategoryID = session.query(Category).filter_by(
                                                    name=category_name
                                                    ).first().id
    itemToDelete = session.query(Item).filter_by(
                                        name=item_name,
                                        category_id=itemToDeleteCategoryID
                                        ).first()
    if login_session['user_id'] != itemToDelete.user_id:
        flash('Permission Is Required To Edit Item %s.' % itemToDelete.name)
        return redirect('/catalog/%s/%s/' % (category_name, item_name))
    if request.method == 'POST':
        session.delete(itemToDelete)
        if itemToDelete.picture:
            os.remove(os.path.join(
                                    app.config['UPLOAD_FOLDER'],
                                    itemToDelete.picture))
        flash('%s Successfully Deleted' % itemToDelete.name)
        session.commit()
        return redirect(url_for('showCategory', category_name=category_name))
    else:
        return render_template(
                                'deleteCategoryItem.html',
                                item=itemToDelete,
                                category=itemToDelete.category)


@app.route('/JSON/<path:category_name>/')
@login_required
def categoryJSON(category_name):
    """return JSON objects for the category."""
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    return jsonify(CategoryItems=[i.serialize for i in items])


@app.route('/XML/<path:category_name>/')
@login_required
def categoryXML(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    data = [i.serialize for i in items]
    return "<xmp>%s</xmp>" % xmlify(data, wrap="all", indent="  ")


def getUserID(email):
    """Get user id."""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    """Get user informations."""
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    """Create an user."""
    newUser = User(
                    name=login_session['username'],
                    email=login_session['email'],
                    picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def allowed_file(filename):
    """list of allowed file extensions."""
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


def make_external(url):
    return urljoin(request.url_root, url)


if __name__ == '__main__':
    app.secret_key = 'wnod21id90192djR222E2111ccqqqwjncnwi12111'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
