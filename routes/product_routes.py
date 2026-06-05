from flask import Blueprint
from flask import render_template
from flask import request

from flask_login import current_user

from database import Favourite

from database import Product


product_bp = Blueprint(
    "product",
    __name__
)



# ========================================
# PRODUCTS PAGE
# ========================================

@product_bp.route("/products")
def products():

    # SEARCH QUERY

    search_query = request.args.get(
        "search_query",
        ""
    ).strip()



    # CATEGORY

    selected_category = request.args.get(
        "category",
        "all"
    ).strip()



    # ========================================
    # BASE QUERY
    # ========================================

    if selected_category.lower() == "all":

        query = Product.query

    else:

        query = Product.query.filter_by(
            product_category=selected_category
        )



    # ========================================
    # SEARCH FILTER
    # ========================================

    if search_query:

        query = query.filter(

            Product.product_name.ilike(
                f"%{search_query}%"
            )

        )



    # ========================================
    # GET PRODUCTS
    # ========================================

    product_list = query.all()



    # ========================================
    # CATEGORY LIST (AUTO FROM DATABASE)
    # ========================================

    categories = ["all"]

    db_categories = {

        product.product_category.strip()

        for product in Product.query.all()

        if product.product_category

    }

    categories.extend(


        sorted(db_categories)

    )
    
    
    favourite_ids = []



    if current_user.is_authenticated:

        favourite_ids = [

             favourite.product_id

             for favourite in Favourite.query.filter_by(

                   user_id=current_user.user_id

                 ).all()

         ]



    # ========================================
    # RENDER TEMPLATE
    # ========================================

    return render_template(

        "products.html",

        product_list=product_list,

        categories=categories,

        selected_category=selected_category,

        search_query=search_query,
        
        favourite_ids=favourite_ids

    )



# =========================
# PRODUCT DETAILS PAGE
# =========================

@product_bp.route(
    "/product/<int:product_id>"
)
def product_details(product_id):

    product = Product.query.get_or_404(
        product_id
    )



    is_favourite = False



    if current_user.is_authenticated:

        is_favourite = (

            Favourite.query.filter_by(

                user_id=current_user.user_id,

                product_id=product_id

            ).first()

            is not None

        )



    return render_template(

        "product_details.html",

        product=product,

        is_favourite=is_favourite

    )
