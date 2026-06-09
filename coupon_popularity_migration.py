from app import app
from database import db

with app.app_context():

    db.session.execute(

        db.text(

            """
            ALTER TABLE coupons
            ADD COLUMN popularity_text VARCHAR(255)
            """

        )

    )

    db.session.commit()

print(
    "Popularity column added!"
)
