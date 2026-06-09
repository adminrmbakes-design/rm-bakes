from database import db
from app import app

with app.app_context():

    with db.engine.connect() as conn:

        conn.execute(
            db.text(
                """
                ALTER TABLE coupons
                ADD COLUMN popularity_text VARCHAR(255)
                """
            )
        )

        conn.commit()

print(
    "Popularity text column added!"
)
