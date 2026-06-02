from app import app

from database import (

    db,
    User

)

from werkzeug.security import (

    generate_password_hash

)



with app.app_context():



    # =====================================
    # ADMIN 1
    # =====================================

    admin1 = User.query.filter_by(

        username="rmbakes.admin_joel"

    ).first()



    if not admin1:

        admin1 = User(

            username="rmbakes.admin_joel",

            email="adminjoel@rmbakes.com",

            password=generate_password_hash(
                "joe_the_rizz.admin@123"
            ),

            is_admin=True,

            admin_role="Owner"

        )



        db.session.add(admin1)



    # =====================================
    # ADMIN 2
    # =====================================

    admin2 = User.query.filter_by(

        username="rmbakes.admin_akami"

    ).first()



    if not admin2:

        admin2 = User(

            username="rmbakes.admin_akami",

            email="adminakami@rmbakes.com",

            password=generate_password_hash(
                "akami_desuu.admin@123"
            ),

            is_admin=True,

            admin_role="Assistant Admin"

        )



        db.session.add(admin2)



    # =====================================
    # COMMIT
    # =====================================

    db.session.commit()



    print(
        "Admins created successfully 🔥"
    )