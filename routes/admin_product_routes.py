from flask import (

    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash

)

import os

from werkzeug.utils import secure_filename

from database import (

    db,
    Product

)

from utils.admin_guard import (

    admin_required

)


# =========================================
# BLUEPRINT
# =========================================

admin_product_bp = Blueprint(

    "admin_product",
    __name__

)


# =========================================
# UPLOAD CONFIG
# =========================================

UPLOAD_FOLDER = os.path.join(

    "static",
    "uploads"

)

os.makedirs(

    UPLOAD_FOLDER,

    exist_ok=True

)


# =========================================
# ADD PRODUCT
# =========================================

@admin_product_bp.route(

    "/admin/products/add",

    methods=["GET", "POST"]

)
@admin_required
def add_product():

    if request.method == "POST":

        product_name = request.form.get(
            "product_name"
        )

        product_description = request.form.get(
            "product_description"
        )

        product_price = request.form.get(
            "product_price"
        )

        product_unit = request.form.get(
            "product_unit"
        )

        product_tags = request.form.get(
            "product_tags"
        )

        product_category = request.form.get(
            "product_category"
        )

        new_category = request.form.get(
            "new_category"
        )

        product_image = request.files.get(
            "product_image"
        )

        # =====================================
        # USE NEW CATEGORY IF PROVIDED
        # =====================================

        if new_category and new_category.strip():

            product_category = (
                new_category
                .strip()
                .title()
            )

        # =====================================
        # VALIDATION
        # =====================================

        if (

            not product_name or
            not product_description or
            not product_price or
            not product_unit or
            not product_category

        ):

            flash(

                "Please fill all required fields",

                "danger"

            )

            return redirect(

                url_for(
                    "admin_product.add_product"
                )

            )

        # =====================================
        # IMAGE UPLOAD
        # =====================================

        image_filename = None

        if product_image and product_image.filename:

            image_filename = secure_filename(

                product_image.filename

            )

            image_path = os.path.join(

                UPLOAD_FOLDER,
                image_filename

            )

            product_image.save(

                image_path

            )

        # =====================================
        # CREATE PRODUCT
        # =====================================

        new_product = Product(

            product_name=product_name,

            product_description=product_description,

            product_price=float(
                product_price
            ),

            product_unit=product_unit,

            product_image=image_filename,

            product_tags=product_tags,

            product_category=product_category

        )

        db.session.add(

            new_product

        )

        db.session.commit()

        flash(

            f"{product_name} added successfully 🍰",

            "success"

        )

        return redirect(

            url_for(
                "admin_product.manage_products"
            )

        )

    # =====================================
    # LOAD EXISTING CATEGORIES
    # =====================================

    categories = [

        row[0]

        for row in db.session.query(
            Product.product_category
        ).distinct().all()

        if row[0]

    ]

    categories = sorted(categories)

    return render_template(

        "admin/admin_add_product.html",

        categories=categories

    )





# =========================================
# MANAGE PRODUCTS
# =========================================

@admin_product_bp.route(

    "/admin/products/manage"

)
@admin_required
def manage_products():

    search_query = request.args.get(

        "search",
        ""

    ).strip()



    if search_query:

        products = Product.query.filter(

            Product.product_name.ilike(

                f"%{search_query}%"

            )

        ).all()

    else:

        products = Product.query.order_by(

            Product.product_name.asc()

        ).all()



    return render_template(

        "admin/admin_manage_products.html",

        products=products,

        search_query=search_query

    )


# =========================================
# EDIT PRODUCT
# =========================================

@admin_product_bp.route(

    "/admin/products/edit/<int:product_id>",

    methods=["GET", "POST"]

)
@admin_required
def edit_product(product_id):

    product = Product.query.get_or_404(

        product_id

    )



    if request.method == "POST":

        product.product_name = request.form.get(

            "product_name"

        )



        product.product_description = request.form.get(

            "product_description"

        )



        product.product_price = float(

            request.form.get(
                "product_price"
            )

        )



        product.product_unit = request.form.get(

            "product_unit"

        )



        product.product_tags = request.form.get(

            "product_tags"

        )



        product.product_category = request.form.get(

            "product_category"

        )



        new_image = request.files.get(

            "product_image"

        )



        if (

            new_image and
            new_image.filename

        ):

            image_filename = secure_filename(

                new_image.filename

            )



            image_path = os.path.join(

                UPLOAD_FOLDER,
                image_filename

            )



            new_image.save(

                image_path

            )



            product.product_image = (

                image_filename

            )



        db.session.commit()



        flash(

            "Product updated successfully ✨",

            "success"

        )



        return redirect(

            url_for(
                "admin_product.manage_products"
            )

        )



    return render_template(

        "admin/admin_edit_product.html",

        product=product

    )


# =========================================
# DELETE PRODUCT
# =========================================

@admin_product_bp.route(

    "/admin/products/delete/<int:product_id>",

    methods=["POST"]

)
@admin_required
def delete_product(product_id):

    product = Product.query.get_or_404(

        product_id

    )



    product_name = product.product_name



    db.session.delete(

        product

    )



    db.session.commit()



    flash(

        f"{product_name} deleted successfully 🗑️",

        "success"

    )



    return redirect(

        url_for(
            "admin_product.manage_products"
        )

    )


# =========================================
# CATEGORIES
# =========================================

@admin_product_bp.route(

    "/admin/products/categories"

)
@admin_required
def categories():

    categories = db.session.query(

        Product.product_category

    ).distinct().all()



    category_list = [

        category[0]

        for category in categories

        if category[0]

    ]



    return render_template(

        "admin/admin_categories.html",

        categories=sorted(

            category_list

        )

    )
