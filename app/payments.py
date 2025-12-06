"""
Stripe payment integration for Vorex.

Handles:
- Creating checkout sessions
- Processing webhooks
- Managing subscriptions
- Customer portal sessions
"""

import os
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import stripe
from fastapi import HTTPException

from app.db import Database


# Initialize Stripe with secret key from environment
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Price IDs from environment
STRIPE_PRICE_ID_MONTHLY = os.getenv("STRIPE_PRICE_ID_MONTHLY")
STRIPE_PRICE_ID_YEARLY = os.getenv("STRIPE_PRICE_ID_YEARLY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


class StripePaymentService:
    """Service for handling Stripe payment operations."""

    def __init__(self, db: Database):
        self.db = db

    async def create_checkout_session(
        self,
        user_id: uuid.UUID,
        price_id: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for subscription.

        Args:
            user_id: The user's UUID
            price_id: Stripe price ID (monthly or yearly)
            success_url: URL to redirect on successful payment
            cancel_url: URL to redirect on cancelled payment

        Returns:
            Dict with session_id and checkout_url
        """
        try:
            # Get or create Stripe customer
            customer_id = await self._get_or_create_customer(user_id)

            # Validate price ID
            if price_id not in [STRIPE_PRICE_ID_MONTHLY, STRIPE_PRICE_ID_YEARLY]:
                raise HTTPException(status_code=400, detail="Invalid price ID")

            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": str(user_id),
                },
                subscription_data={
                    "metadata": {
                        "user_id": str(user_id),
                    }
                },
                allow_promotion_codes=True,
            )

            return {
                "session_id": session.id,
                "checkout_url": session.url,
            }

        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating checkout session: {str(e)}")

    async def create_portal_session(
        self,
        user_id: uuid.UUID,
        return_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe customer portal session for managing subscription.

        Args:
            user_id: The user's UUID
            return_url: URL to redirect after portal session

        Returns:
            Dict with portal_url
        """
        try:
            # Get Stripe customer ID
            customer_id = await self._get_or_create_customer(user_id)

            # Create portal session
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )

            return {
                "portal_url": session.url,
            }

        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating portal session: {str(e)}")

    async def get_subscription_status(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get current subscription status for a user.

        Args:
            user_id: The user's UUID

        Returns:
            Dict with subscription details
        """
        query = """
            SELECT
                subscription_id,
                tier,
                status,
                billing_cycle,
                price_paid_cents,
                currency,
                stripe_subscription_id,
                current_period_start,
                current_period_end,
                cancelled_at,
                trial_start,
                trial_end,
                will_renew
            FROM user_subscriptions
            WHERE user_id = $1
            ORDER BY started_at DESC
            LIMIT 1
        """

        result = await self.db.fetch_one(query, user_id)

        if not result:
            return {
                "status": "none",
                "tier": "free",
                "message": "No active subscription"
            }

        return {
            "subscription_id": str(result["subscription_id"]),
            "tier": result["tier"],
            "status": result["status"],
            "billing_cycle": result["billing_cycle"],
            "price_cents": result["price_paid_cents"],
            "currency": result["currency"],
            "current_period_start": result["current_period_start"].isoformat() if result["current_period_start"] else None,
            "current_period_end": result["current_period_end"].isoformat() if result["current_period_end"] else None,
            "cancelled_at": result["cancelled_at"].isoformat() if result["cancelled_at"] else None,
            "trial_start": result["trial_start"].isoformat() if result["trial_start"] else None,
            "trial_end": result["trial_end"].isoformat() if result["trial_end"] else None,
            "will_renew": result["will_renew"],
        }

    async def cancel_subscription(self, user_id: uuid.UUID, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel a user's subscription (at end of billing period).

        Args:
            user_id: The user's UUID
            reason: Optional cancellation reason

        Returns:
            Dict with cancellation confirmation
        """
        try:
            # Get current subscription
            subscription_data = await self.get_subscription_status(user_id)

            if subscription_data["status"] == "none":
                raise HTTPException(status_code=404, detail="No active subscription found")

            # Get Stripe subscription ID
            query = """
                SELECT stripe_subscription_id
                FROM user_subscriptions
                WHERE user_id = $1 AND status IN ('active', 'trialing')
                ORDER BY started_at DESC
                LIMIT 1
            """
            result = await self.db.fetch_one(query, user_id)

            if not result or not result["stripe_subscription_id"]:
                raise HTTPException(status_code=404, detail="Stripe subscription not found")

            stripe_sub_id = result["stripe_subscription_id"]

            # Cancel subscription in Stripe (at period end)
            stripe.Subscription.modify(
                stripe_sub_id,
                cancel_at_period_end=True,
            )

            # Update database
            update_query = """
                UPDATE user_subscriptions
                SET
                    cancelled_at = NOW(),
                    cancellation_reason = $2,
                    will_renew = FALSE,
                    updated_at = NOW()
                WHERE user_id = $1 AND stripe_subscription_id = $3
            """
            await self.db.execute(update_query, user_id, reason, stripe_sub_id)

            return {
                "status": "success",
                "message": "Subscription will be cancelled at the end of the billing period",
                "cancel_at_period_end": True,
            }

        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error cancelling subscription: {str(e)}")

    async def handle_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.

        Args:
            event: Stripe webhook event

        Returns:
            Dict with processing status
        """
        event_type = event["type"]

        if event_type == "checkout.session.completed":
            return await self._handle_checkout_completed(event)
        elif event_type == "customer.subscription.created":
            return await self._handle_subscription_created(event)
        elif event_type == "customer.subscription.updated":
            return await self._handle_subscription_updated(event)
        elif event_type == "customer.subscription.deleted":
            return await self._handle_subscription_deleted(event)
        elif event_type == "invoice.payment_failed":
            return await self._handle_payment_failed(event)
        else:
            return {"status": "ignored", "event_type": event_type}

    async def _get_or_create_customer(self, user_id: uuid.UUID) -> str:
        """Get or create a Stripe customer for the user."""
        # Check if customer already exists in database
        query = """
            SELECT stripe_customer_id
            FROM user_subscriptions
            WHERE user_id = $1 AND stripe_customer_id IS NOT NULL
            ORDER BY started_at DESC
            LIMIT 1
        """
        result = await self.db.fetch_one(query, user_id)

        if result and result["stripe_customer_id"]:
            return result["stripe_customer_id"]

        # Get user profile for email
        user_query = """
            SELECT user_id
            FROM user_profiles
            WHERE user_id = $1
        """
        user = await self.db.fetch_one(user_query, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Create new Stripe customer
        customer = stripe.Customer.create(
            metadata={"user_id": str(user_id)},
        )

        return customer.id

    async def _handle_checkout_completed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful checkout session."""
        session = event["data"]["object"]
        user_id = uuid.UUID(session["metadata"]["user_id"])
        customer_id = session["customer"]
        subscription_id = session["subscription"]

        # Subscription will be created in subscription.created event
        return {"status": "processed", "user_id": str(user_id)}

    async def _handle_subscription_created(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription creation."""
        subscription = event["data"]["object"]
        user_id = uuid.UUID(subscription["metadata"]["user_id"])

        # Determine tier and billing cycle from price ID
        price_id = subscription["items"]["data"][0]["price"]["id"]
        tier = "premium"
        billing_cycle = "monthly" if price_id == STRIPE_PRICE_ID_MONTHLY else "yearly"
        price_cents = subscription["items"]["data"][0]["price"]["unit_amount"]

        # Check if subscription already exists for this user
        check_query = """
            SELECT subscription_id FROM user_subscriptions
            WHERE user_id = $1 OR stripe_subscription_id = $2
            LIMIT 1
        """
        existing = await self.db.fetch_one(check_query, user_id, subscription["id"])

        if existing:
            # Update existing subscription
            query = """
                UPDATE user_subscriptions
                SET
                    tier = $2,
                    status = $3,
                    billing_cycle = $4,
                    price_paid_cents = $5,
                    currency = $6,
                    stripe_customer_id = $7,
                    stripe_subscription_id = $8,
                    current_period_start = $9,
                    current_period_end = $10,
                    will_renew = $11,
                    updated_at = NOW()
                WHERE subscription_id = $1
            """
            await self.db.execute(
                query,
                existing["subscription_id"],
                tier,
                subscription["status"],
                billing_cycle,
                price_cents,
                subscription["currency"].upper(),
                subscription["customer"],
                subscription["id"],
                datetime.fromtimestamp(subscription["current_period_start"]),
                datetime.fromtimestamp(subscription["current_period_end"]),
                True,
            )
        else:
            # Insert new subscription
            query = """
                INSERT INTO user_subscriptions (
                    user_id,
                    tier,
                    status,
                    billing_cycle,
                    price_paid_cents,
                    currency,
                    stripe_customer_id,
                    stripe_subscription_id,
                    started_at,
                    current_period_start,
                    current_period_end,
                    will_renew
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """
            await self.db.execute(
                query,
                user_id,
                tier,
                subscription["status"],
                billing_cycle,
                price_cents,
                subscription["currency"].upper(),
                subscription["customer"],
                subscription["id"],
                datetime.fromtimestamp(subscription["created"]),
                datetime.fromtimestamp(subscription["current_period_start"]),
                datetime.fromtimestamp(subscription["current_period_end"]),
                True,
            )

        return {"status": "processed", "user_id": str(user_id), "tier": tier}

    async def _handle_subscription_updated(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updates."""
        subscription = event["data"]["object"]

        # Get user_id from subscription metadata
        user_id = uuid.UUID(subscription["metadata"]["user_id"])

        # Update subscription status
        query = """
            UPDATE user_subscriptions
            SET
                status = $2,
                current_period_start = $3,
                current_period_end = $4,
                will_renew = $5,
                updated_at = NOW()
            WHERE stripe_subscription_id = $1
        """

        cancel_at_period_end = subscription.get("cancel_at_period_end", False)

        await self.db.execute(
            query,
            subscription["id"],
            subscription["status"],
            datetime.fromtimestamp(subscription["current_period_start"]),
            datetime.fromtimestamp(subscription["current_period_end"]),
            not cancel_at_period_end,
        )

        return {"status": "processed", "subscription_status": subscription["status"]}

    async def _handle_subscription_deleted(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription deletion/cancellation."""
        subscription = event["data"]["object"]

        # Update subscription to cancelled
        query = """
            UPDATE user_subscriptions
            SET
                status = 'cancelled',
                cancelled_at = NOW(),
                will_renew = FALSE,
                updated_at = NOW()
            WHERE stripe_subscription_id = $1
        """

        await self.db.execute(query, subscription["id"])

        return {"status": "processed", "action": "cancelled"}

    async def _handle_payment_failed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment."""
        invoice = event["data"]["object"]
        subscription_id = invoice.get("subscription")

        if subscription_id:
            # Update subscription status to past_due
            query = """
                UPDATE user_subscriptions
                SET
                    status = 'past_due',
                    updated_at = NOW()
                WHERE stripe_subscription_id = $1
            """
            await self.db.execute(query, subscription_id)

        return {"status": "processed", "action": "marked_past_due"}
