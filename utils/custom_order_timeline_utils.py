from datetime import datetime

from database import db

from custom_orders_database import (

    CustomOrderTimeline

)



# =========================================
# CREATE TIMELINE EVENT
# =========================================

def create_timeline_event(

    custom_order_id,

    event_type,

    title,

    description,

    triggered_by="system"

):



    try:



        timeline_event = CustomOrderTimeline(

            custom_order_id=custom_order_id,

            event_type=event_type,

            title=title,

            description=description,

            triggered_by=triggered_by,

            created_at=datetime.utcnow()

        )



        db.session.add(

            timeline_event

        )



        db.session.commit()



        return True



    except Exception as error:



        db.session.rollback()



        print(

            "TIMELINE EVENT ERROR:",

            error

        )



        return False
