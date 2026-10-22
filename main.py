# Python (PyScript) handles the inquiry form validation.
# The product filter tabs, "Customize Now" buttons, Design Lab and chat live in index.html (JavaScript),
# so they work right away without waiting for Python to load.
from pyscript import when
from js import document
import re

FIELD_IDS = ["name", "email", "product", "message"]


def set_feedback(message, kind):
    feedback = document.querySelector("#form-feedback")
    feedback.innerText = message
    feedback.className = f"form-feedback {kind}"


def mark_invalid(invalid_ids):
    """Flag problem fields for screen readers and put the cursor in the first one."""
    for field_id in FIELD_IDS:
        field = document.querySelector("#" + field_id)
        if field_id in invalid_ids:
            field.setAttribute("aria-invalid", "true")
        else:
            field.removeAttribute("aria-invalid")
    if invalid_ids:
        document.querySelector("#" + invalid_ids[0]).focus()


@when("submit", "#inquiry-form")
def validate_inquiry(event):
    event.preventDefault()

    name = document.querySelector("#name").value.strip()
    email = document.querySelector("#email").value.strip()
    product = document.querySelector("#product").value.strip()
    message = document.querySelector("#message").value.strip()

    missing = []
    missing_ids = []

    if not name:
        missing.append("your name")
        missing_ids.append("name")
    if not email:
        missing.append("your email")
        missing_ids.append("email")
    if not product:
        missing.append("a product")
        missing_ids.append("product")
    if not message:
        missing.append("a few details")
        missing_ids.append("message")

    if missing:
        mark_invalid(missing_ids)
        set_feedback("Please add " + ", ".join(missing) + ".", "error")
        return

    # Check the email format
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        mark_invalid(["email"])
        set_feedback("That email looks a little off — please check it and try again.", "error")
        return

    mark_invalid([])
    set_feedback(
        f"Thanks, {name}! Your {product.lower()} inquiry is noted. "
        "We will get back to you shortly.",
        "success"
    )

    document.querySelector("#inquiry-form").reset()