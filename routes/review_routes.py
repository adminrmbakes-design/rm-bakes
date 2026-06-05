from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import url_for
from flask import request
from flask import jsonify
from flask import flash

from flask_login import login_required
from flask_login import current_user

from database import db

from orders_database import (
    Order,
    OrderFeedback,
    ProductReview
)

import json


# =========================================
# BLUEPRINT
# =========================================

review_bp = Blueprint(
    "review",
    __name__
)


# =========================================
# REVIEW PAGE
# =========================================

@review_bp.route(
    "/leave-review/<int:order_id>"
)
@login_required
def leave_review(order_id):

    order = Order.query.filter_by(

        order_id=order_id,

        user_id=current_user.user_id

    ).first()

    if not order:

        return redirect(
            url_for("order.my_orders")
        )

    if order.order_status != "delivered":

        return redirect(
            url_for("order.order_details",
                order_id=order_id
            )
        )

    products = []

    if not order.is_custom_order:

        products = json.loads(
            order.products_json
        )

    return render_template(

        "review_order.html",

        order=order,

        products=products

    )


# =========================================
# SUBMIT REVIEW
# =========================================

@review_bp.route(
    "/submit-review/<int:order_id>",
    methods=["POST"]
)
@login_required
def submit_review(order_id):

    try:

        order = Order.query.filter_by(

            order_id=order_id,

            user_id=current_user.user_id

        ).first()

        if not order:

            return jsonify({

                "success": False,

                "message":
                "Order not found 😭"

            })

        # ================================
        # OVERALL EXPERIENCE
        # ================================

        overall_rating = int(

            request.form.get(
                "overall_rating",
                0
            )

        )

        existing_feedback = (

            OrderFeedback.query.filter_by(

                order_id=order.order_id,

                customer_id=
                    current_user.user_id

            ).first()

        )

        if not existing_feedback:

            feedback = OrderFeedback(

                order_id=
                    order.order_id,

                order_number=
                    order.order_number,

                is_custom_order=
                    order.is_custom_order,

                customer_id=
                    current_user.user_id,

                customer_name=
                    current_user.full_name,

                overall_rating=
                    overall_rating

            )

            db.session.add(
                feedback
            )

        # ================================
        # PRODUCT REVIEW (OPTIONAL)
        # ================================

        product_name = request.form.get(
            "product_name"
        )

        review_text = request.form.get(
            "review_text"
        )

        product_rating = request.form.get(
            "product_rating"
        )

        if product_name and product_rating:

            review = ProductReview(

                order_id=
                    order.order_id,

                order_number=
                    order.order_number,

                is_custom_order=
                    order.is_custom_order,

                product_name=
                    product_name,

                customer_id=
                    current_user.user_id,

                customer_name=
                    current_user.full_name,

                rating=
                    int(product_rating),

                review_text=
                    review_text

            )

            db.session.add(
                review
            )

        db.session.commit()

        return jsonify({

            "success": True,

            "message":
            "Thank you for sharing your sweet experience 💛"

        })

    except Exception as error:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message":
            str(error)

        })


# =========================================
# PRODUCT REVIEWS PAGE
# =========================================

@review_bp.route(
    "/product-reviews/<product_name>"
)
def product_reviews(product_name):

    reviews = (

        ProductReview.query.filter_by(

            product_name=product_name,

            is_visible=True

        )

        .order_by(

            ProductReview.created_at.desc()

        )

        .all()

    )

    average_rating = 0

    if reviews:

        average_rating = round(

            sum(

                review.rating

                for review in reviews

            )

            /

            len(reviews),

            1

        )

    return render_template(

        "product_reviews.html",

        product_name=product_name,

        reviews=reviews,

        average_rating=
            average_rating

    )



@review_bp.route(
    "/my-review/<int:order_id>"
)
@login_required
def my_review(order_id):

    review = ProductReview.query.filter_by(

        order_id=order_id,

        customer_id=current_user.user_id

    ).first()

    if not review:

        return redirect(
            url_for("order.my_orders")
        )

    return render_template(

        "my_review.html",

        review=review

    )



@review_bp.route(
    "/edit-review/<int:review_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_review(review_id):

    review = ProductReview.query.get_or_404(
        review_id
    )

    if review.customer_id != current_user.user_id:

        flash(
            "Unauthorized access.",
            "danger"
        )

        return redirect(
            url_for(
                "order.my_orders"
            )
        )

    if request.method == "POST":

        review.rating = int(
            request.form.get(
                "rating"
            )
        )

        review.review_text = (
            request.form.get(
                "review_text"
            )
        )

        db.session.commit()

        flash(
            "Review updated successfully 💖",
            "success"
        )

        return redirect(
            url_for(
                "review.my_review",
                order_id=review.order_id
            )
        )

    return render_template(

        "edit_review.html",

        review=review

    )


@review_bp.route(
    "/delete-review/<int:review_id>"
)
@login_required
def delete_review(review_id):

    review = ProductReview.query.get_or_404(
        review_id
    )

    if review.customer_id != current_user.user_id:

        flash(
            "Unauthorized access.",
            "danger"
        )

        return redirect(
            url_for(
                "order.my_orders"
            )
        )

    order_id = review.order_id

    db.session.delete(
        review
    )

    db.session.commit()

    flash(
        "Review deleted 💔",
        "success"
    )

    return redirect(
        url_for(
            "order.my_orders"
        )
    )
