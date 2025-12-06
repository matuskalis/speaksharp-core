# Stripe Payment Integration Setup Guide

This guide will help you set up Stripe payments for Vorex (English learning app).

## Overview

The integration supports:
- Monthly subscription ($9.99/month)
- Yearly subscription ($79.99/year)
- Stripe Checkout for payment processing
- Webhook handling for subscription lifecycle events
- Customer portal for subscription management
- Automatic database updates on payment events

## Prerequisites

1. A Stripe account (use test mode for development)
2. PostgreSQL database with `user_subscriptions` table
3. Backend API running
4. Frontend app running

## Backend Setup

### 1. Install Dependencies

```bash
cd vorex-backend
pip install -r requirements.txt
```

The `stripe==11.2.0` package is already included in requirements.txt.

### 2. Create Stripe Products and Prices

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/test/products)
2. Click "Add product"
3. Create two products:

**Monthly Subscription:**
- Name: "Vorex Premium - Monthly"
- Description: "Monthly subscription to Vorex Premium"
- Pricing: Recurring, $9.99 USD, Monthly
- Copy the Price ID (starts with `price_`)

**Yearly Subscription:**
- Name: "Vorex Premium - Yearly"
- Description: "Yearly subscription to Vorex Premium"
- Pricing: Recurring, $79.99 USD, Yearly
- Copy the Price ID (starts with `price_`)

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your Stripe credentials:

```bash
# Stripe Configuration (TEST MODE)
STRIPE_SECRET_KEY=sk_test_51xxxxx  # From https://dashboard.stripe.com/test/apikeys
STRIPE_WEBHOOK_SECRET=whsec_xxxxx  # Get this after setting up webhook (step 4)
STRIPE_PRICE_ID_MONTHLY=price_xxxxx  # From step 2
STRIPE_PRICE_ID_YEARLY=price_xxxxx   # From step 2
```

### 4. Set Up Stripe Webhook

For local development, use Stripe CLI:

```bash
# Install Stripe CLI
# macOS
brew install stripe/stripe-cli/stripe

# Login to Stripe
stripe login

# Forward webhooks to local backend
stripe listen --forward-to localhost:8000/api/payments/webhook
```

This will output a webhook signing secret (starts with `whsec_`). Add it to your `.env` file.

**For production:**
1. Go to [Stripe Webhooks](https://dashboard.stripe.com/webhooks)
2. Click "Add endpoint"
3. URL: `https://your-api-domain.com/api/payments/webhook`
4. Select events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
5. Copy the signing secret to your production `.env`

### 5. Verify Database Schema

Ensure the `user_subscriptions` table exists (should already be in your migration):

```sql
CREATE TABLE IF NOT EXISTS user_subscriptions (
  subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id),
  tier VARCHAR(50) NOT NULL,
  status VARCHAR(50) NOT NULL,
  billing_cycle VARCHAR(50),
  price_paid_cents INTEGER,
  currency VARCHAR(10) DEFAULT 'USD',
  stripe_customer_id VARCHAR(255),
  stripe_subscription_id VARCHAR(255),
  payment_method_last4 VARCHAR(4),
  payment_method_type VARCHAR(50),
  started_at TIMESTAMP DEFAULT NOW(),
  current_period_start TIMESTAMP,
  current_period_end TIMESTAMP,
  cancelled_at TIMESTAMP,
  trial_start TIMESTAMP,
  trial_end TIMESTAMP,
  cancellation_reason TEXT,
  will_renew BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### 6. Start the Backend

```bash
cd vorex-backend
python -m uvicorn app.api:app --reload
```

## Frontend Setup

### 1. Configure Environment Variables

Copy `.env.local.example` to `.env.local` and add your Stripe price IDs:

```bash
# Stripe Configuration (TEST MODE)
NEXT_PUBLIC_STRIPE_PRICE_ID_MONTHLY=price_xxxxx  # Same as backend
NEXT_PUBLIC_STRIPE_PRICE_ID_YEARLY=price_xxxxx   # Same as backend
```

### 2. Start the Frontend

```bash
cd vorex-frontend
npm run dev
```

## Testing the Integration

### Test Credit Cards

Use Stripe test cards for testing:
- **Success:** 4242 4242 4242 4242
- **Decline:** 4000 0000 0000 0002
- **Requires 3D Secure:** 4000 0025 0000 3155

Any future expiry date and any 3-digit CVC will work.

### Test Flow

1. Navigate to `/subscribe` page
2. Click "Get Started" on Monthly or Yearly plan
3. You'll be redirected to Stripe Checkout
4. Enter test card details
5. Complete checkout
6. You'll be redirected to `/subscribe/success`
7. Check backend logs for webhook processing
8. Verify subscription in database:
   ```sql
   SELECT * FROM user_subscriptions WHERE user_id = 'your-user-id';
   ```

### Test Subscription Management

1. Navigate to settings/profile page (wherever you add the SubscriptionManager component)
2. Click "Manage Subscription" - opens Stripe Customer Portal
3. Test cancellation by clicking "Cancel Subscription"
4. Verify in database that `will_renew` is set to `false` and `cancelled_at` is set

## API Endpoints

### Create Checkout Session
```http
POST /api/payments/create-checkout-session
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
  "price_id": "price_xxxxx",
  "success_url": "https://yourapp.com/subscribe/success",
  "cancel_url": "https://yourapp.com/subscribe"
}

Response:
{
  "session_id": "cs_xxxxx",
  "checkout_url": "https://checkout.stripe.com/xxxxx"
}
```

### Get Subscription Status
```http
GET /api/payments/subscription
Authorization: Bearer <jwt-token>

Response:
{
  "status": "active",
  "tier": "premium",
  "billing_cycle": "monthly",
  "price_cents": 999,
  "currency": "USD",
  "current_period_end": "2024-01-15T00:00:00Z",
  "will_renew": true
}
```

### Cancel Subscription
```http
POST /api/payments/cancel
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
  "reason": "Too expensive"
}

Response:
{
  "status": "success",
  "message": "Subscription will be cancelled at the end of the billing period",
  "cancel_at_period_end": true
}
```

### Create Portal Session
```http
POST /api/payments/create-portal-session
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
  "return_url": "https://yourapp.com/settings"
}

Response:
{
  "portal_url": "https://billing.stripe.com/session/xxxxx"
}
```

### Webhook Endpoint
```http
POST /api/payments/webhook
Stripe-Signature: <signature-header>

(Stripe sends this automatically)
```

## Subscription Tiers

### Free Tier
- Limited exercises
- Basic text tutor
- No voice features

### Premium Tier ($9.99/mo or $79.99/yr)
- Unlimited exercises and lessons
- Full voice tutor with pronunciation analysis
- All conversation scenarios
- Advanced progress tracking
- Priority support

## Going to Production

1. Switch to live mode in Stripe Dashboard
2. Create production products and prices
3. Update environment variables with live keys:
   - `STRIPE_SECRET_KEY=sk_live_xxxxx`
   - Update `STRIPE_PRICE_ID_MONTHLY` and `STRIPE_PRICE_ID_YEARLY`
4. Set up production webhook endpoint
5. Update `STRIPE_WEBHOOK_SECRET` with production signing secret
6. Test thoroughly before launch

## Troubleshooting

### Webhook not receiving events
- Check Stripe CLI is running: `stripe listen --forward-to localhost:8000/api/payments/webhook`
- Verify webhook secret in `.env` matches the one from Stripe CLI
- Check backend logs for webhook processing

### Checkout session fails
- Verify price IDs are correct in both backend and frontend
- Check Stripe Dashboard for error messages
- Ensure user is authenticated (JWT token is valid)

### Database not updating
- Check webhook events in Stripe Dashboard → Developers → Webhooks
- Verify webhook signature is correct
- Check backend logs for errors
- Ensure `user_subscriptions` table exists

### Customer portal not working
- Verify Stripe customer exists (created during first checkout)
- Check that customer portal is enabled in Stripe Dashboard → Settings → Customer portal

## Support

For issues:
1. Check Stripe Dashboard → Developers → Logs
2. Check backend server logs
3. Verify environment variables are set correctly
4. Test with Stripe CLI webhook forwarding

## Security Notes

- Never commit real Stripe keys to version control
- Always use test mode for development
- Validate webhook signatures (already implemented)
- Don't store sensitive card details (handled by Stripe)
- Use HTTPS in production
