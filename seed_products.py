import json

from app import app

from database import db
from database import Product



with app.app_context():

    with open(

        "rm_products.json",

        "r",

        encoding="utf-8"

    ) as file:

        product_data = json.load(file)



    for item in product_data:

        existing_product = Product.query.filter_by(

            product_name=item["product_name"]

        ).first()



        if existing_product:

            continue



        new_product = Product(

            product_name=item["product_name"],

            product_price=item["product_price"],

            product_unit=item["product_unit"],

            product_tags=item["product_tags"],

            product_category=item["product_category"],

            product_description=item["product_description"],

            product_image=item["product_image"]

        )



        db.session.add(new_product)



    db.session.commit()



    print(

        "Products seeded successfully 🍰"

    )