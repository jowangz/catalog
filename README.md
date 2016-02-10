# Catalog-App
Catalog App

A catalog web app that shorts item into different categories.

## Quick Start:

1. Required installations:
    *   flask   ```pip install flask```
    *   sqlalchemy  ```pip install SQLAlchemy```
    *   oauth2client    ```pip install oauth2client```
    *   dict2xml    ```pip install dict2xml```
    *   requests    ```pip install requests```
2. Clone the repo: ```git clone https://github.com/jowangz/catalog```
3. Setup the database schema by using command ```python database_setup.py```
4. Start the server: ```python application.py```
5. ``` * Running on http://0.0.0.0:8000/``` will be shown if the code ran successfully.
6. App will be running on ```localhost:8000``` 

## What's included:

```
  statics/
  templates/
│   ├── catalog.html
│   ├── deleteCategory.html
│   ├── deleteCategoryItem.html
│   ├── editCategory.html
│   ├── editCategoryItem.html
│   ├── header.html
│   ├── item.html
│   ├── login.html
│   ├── main.html
│   ├── newCategory.html
│   ├── newCategoryItem.html
│   ├── showCategory.html
README.md
application.py
client_secrets.json
database_setup.py

```

## Features:
  
* This is a category web application.
* Users can create category list. 
* Users can create item within different categories.
* Users are able to modify items and categories which they created.
* Users are able to upload image for the item.
* Return JSON objects for the category by accessing ```localhost:8000/JSON/category_name/```
* Return XML objects for the category by accessing ```localhost:8000/XML/category_name/```  
* Three default categories: Baseball, Basketball and Soccer

## Creator:

**Zheng Wang**

* https://github.com/jowangz

**Udacity**

* https://udacity.com