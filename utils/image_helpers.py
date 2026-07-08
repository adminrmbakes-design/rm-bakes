from flask import url_for


def get_product_image(image_path):

    if not image_path:

        return ""

    if image_path.startswith(

        "http"

    ):

        return image_path

    return url_for(

        "static",

        filename=f"uploads/{image_path}"

    )
