from database import db, Product
from app import app


with app.app_context():

    products = Product.query.all()

    print("\n========= RM BAKES PRODUCTS =========\n")

    for product in products:

        print("Name:", product.product_name)

        print("Category:", product.product_category)

        print("Price:", product.product_price)

        print("----------------------------")