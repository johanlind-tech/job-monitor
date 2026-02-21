import Stripe from "https://esm.sh/stripe@14?target=deno";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

Deno.serve(async (req) => {
  const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY")!, {
    apiVersion: "2024-06-20",
  });

  // 1. Verify webhook signature
  const body = await req.text();
  const signature = req.headers.get("stripe-signature");

  if (!signature) {
    return new Response("Missing stripe-signature header", { status: 400 });
  }

  let event: Stripe.Event;
  try {
    event = await stripe.webhooks.constructEventAsync(
      body,
      signature,
      Deno.env.get("STRIPE_WEBHOOK_SIGNING_SECRET")!
    );
  } catch (err) {
    console.error("Webhook signature verification failed:", err.message);
    return new Response(`Webhook Error: ${err.message}`, { status: 400 });
  }

  // 2. Use service role client (bypasses RLS)
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  console.log(`[Stripe Webhook] Received event: ${event.type}`);

  // 3. Handle event types
  switch (event.type) {
    case "checkout.session.completed": {
      const session = event.data.object as Stripe.Checkout.Session;

      if (session.subscription && session.customer) {
        // Retrieve subscription to get metadata
        const subscription = await stripe.subscriptions.retrieve(
          session.subscription as string
        );
        const userId = subscription.metadata?.supabase_user_id;
        const plan = subscription.metadata?.plan || "monthly";

        if (userId) {
          const { error } = await supabase
            .from("profiles")
            .update({
              subscription_status: "active",
              plan,
              stripe_customer_id: session.customer as string,
              stripe_subscription_id: subscription.id,
            })
            .eq("id", userId);

          if (error) {
            console.error("Failed to update profile on checkout:", error);
          } else {
            console.log(`[Stripe Webhook] User ${userId} activated with plan: ${plan}`);
          }
        }
      }
      break;
    }

    case "customer.subscription.updated": {
      const subscription = event.data.object as Stripe.Subscription;
      const userId = subscription.metadata?.supabase_user_id;

      if (userId) {
        // Map Stripe status to our enum (trialing, active, canceled)
        // Keep as "active" during past_due (Stripe retries payment)
        const stripeStatus = subscription.status;
        let mappedStatus: "active" | "canceled" = "active";
        if (stripeStatus === "canceled" || stripeStatus === "unpaid") {
          mappedStatus = "canceled";
        }

        const plan = subscription.metadata?.plan || "monthly";

        const { error } = await supabase
          .from("profiles")
          .update({
            subscription_status: mappedStatus,
            plan,
            stripe_subscription_id: subscription.id,
          })
          .eq("id", userId);

        if (error) {
          console.error("Failed to update profile on subscription update:", error);
        } else {
          console.log(`[Stripe Webhook] User ${userId} subscription updated: ${mappedStatus}`);
        }
      }
      break;
    }

    case "customer.subscription.deleted": {
      const subscription = event.data.object as Stripe.Subscription;
      const userId = subscription.metadata?.supabase_user_id;

      if (userId) {
        const { error } = await supabase
          .from("profiles")
          .update({ subscription_status: "canceled" })
          .eq("id", userId);

        if (error) {
          console.error("Failed to update profile on subscription delete:", error);
        } else {
          console.log(`[Stripe Webhook] User ${userId} subscription canceled`);
        }
      }
      break;
    }

    case "invoice.payment_failed": {
      const invoice = event.data.object as Stripe.Invoice;
      console.log(
        `[Stripe Webhook] Payment failed for customer ${invoice.customer}. Stripe will retry.`
      );
      // Stripe auto-retries failed payments. We keep status as "active"
      // until Stripe gives up and sends customer.subscription.deleted.
      break;
    }

    default:
      console.log(`[Stripe Webhook] Unhandled event type: ${event.type}`);
  }

  return new Response(JSON.stringify({ received: true }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
});
