import stripe
import os
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

def create_checkout_session(user_id: str, product_id: str, success_url: str, cancel_url: str):
    try:
        # In a real application, you would fetch product details (price, currency) from your database
        # based on the product_id. For this example, we'll use a dummy price.
        price_id = "price_12345" # Replace with your actual Stripe Price ID

        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=user_id, # Link to your user in Stripe
        )
        return {"session_id": checkout_session.id, "url": checkout_session.url}
    except Exception as e:
        return {"error": str(e)}

def handle_webhook(payload: bytes, sig_header: str):
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        return {"error": str(e), "status_code": 400}
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return {"error": str(e), "status_code": 400}

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('client_reference_id')
        # Fulfill the purchase, e.g., grant access to paid features
        print(f"Checkout session completed for user {user_id}. Session ID: {session.id}")
        # You would update your database here to mark the user as paid
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        # Handle subscription updates (e.g., renewal, cancellation)
        print(f"Subscription updated: {subscription.id}")
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        # Handle subscription cancellation
        print(f"Subscription deleted: {subscription.id}")
    else:
        print(f"Unhandled event type {event['type']}")

    return {"status": "success", "status_code": 200}