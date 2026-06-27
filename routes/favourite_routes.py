from flask import Blueprint
from flask import jsonify

from flask_login import login_required
from flask_login import current_user

from database import db
from database import Favourite



favourite_bp = Blueprint(

    "favourite",
    __name__

)



# =========================================
# TOGGLE FAVOURITE
# =========================================

@favourite_bp.route(

    "/toggle_favourite/<int:product_id>",

    methods=["POST"]

)
@login_required
def toggle_favourite(product_id):

    existing_favourite = (

        Favourite.query.filter_by(

            user_id=current_user.user_id,

            product_id=product_id

        ).first()

    )



    # =========================
    # REMOVE FAVOURITE
    # =========================

    if existing_favourite:

        db.session.delete(

            existing_favourite

        )

        db.session.commit()



        return jsonify({

            "success": True,

            "action": "removed",

            "message":
                "Removed from favourites 💔"

        })



    # =========================
    # ADD FAVOURITE
    # =========================

    new_favourite = Favourite(

        user_id=current_user.user_id,

        product_id=product_id

    )



    db.session.add(

        new_favourite

    )



    db.session.commit()



    return jsonify({

        "success": True,

        "action": "added",

        "message":
            "Added to favourites ❤️"

    })
