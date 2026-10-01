from __future__ import annotations

from decimal import Decimal

import stripe
from sqlalchemy import text

from app.core.config import settings

PLAN_CATALOG = {
    "starter": {"monthly_price_usd": Decimal("299.00"), "monthly_executions": 1000, "monthly_voice_minutes": 500, "monthly_messages": 5000, "max_users": 5, "max_locations": 1},
    "growth": {"monthly_price_usd": Decimal("799.00"), "monthly_executions": 5000, "monthly_voice_minutes": 2500, "monthly_messages": 25000, "max_users": 15, "max_locations": 3},
    "professional": {"monthly_price_usd": Decimal("1499.00"), "monthly_executions": 15000, "monthly_voice_minutes": 7500, "monthly_messages": 75000, "max_users": 50, "max_locations": 10},
    "enterprise": {"monthly_price_usd": Decimal("3000.00"), "monthly_executions": 100000, "monthly_voice_minutes": 50000, "monthly_messages": 500000, "max_users": 500, "max_locations": 100},
}

_PRICE_ENV = {
    "starter": "stripe_price_starter",
    "growth": "stripe_price_growth",
    "professional": "stripe_price_professional",
    "enterprise": "stripe_price_enterprise",
}


def get_plan(plan_code: str) -> dict:
    try:
        return dict(PLAN_CATALOG[plan_code])
    except KeyError as exc:
        raise ValueError("unknown plan") from exc


async def _clinic_id(session, organization_id: str) -> str:
    clinic = await session.scalar(
        text("select id from clinics where clerk_org_id=:org"),
        {"org": organization_id},
    )
    if not clinic:
        raise ValueError("organization clinic is not provisioned")
    return str(clinic)


async def get_subscription(session, organization_id: str) -> dict:
    clinic = await _clinic_id(session, organization_id)
    row = (
        await session.execute(
            text(
                """
                select plan_code,status,provider,provider_customer_id,provider_subscription_id,
                       provider_price_id,billing_interval,current_period_start,current_period_end,
                       cancel_at_period_end,version,last_provider_event_at
                from subscriptions where clinic_id=:clinic
                """
            ),
            {"clinic": clinic},
        )
    ).mappings().first()
    if row:
        return dict(row)
    return {
        "plan_code": "starter",
        "status": "trialing",
        "provider": None,
        "provider_customer_id": None,
        "provider_subscription_id": None,
        "provider_price_id": None,
        "billing_interval": None,
        "current_period_start": None,
        "current_period_end": None,
        "cancel_at_period_end": False,
        "version": 1,
        "last_provider_event_at": None,
    }


async def change_plan(session, organization_id: str, plan_code: str, actor: str) -> dict:
    plan = get_plan(plan_code)
    clinic = await _clinic_id(session, organization_id)
    await session.execute(
        text(
            """
            insert into tenant_limits(clinic_id,plan_code,monthly_executions,monthly_voice_minutes,
              monthly_messages,max_users,max_locations)
            values(:clinic,:plan,:executions,:voice,:messages,:users,:locations)
            on conflict (clinic_id) do update set plan_code=excluded.plan_code,
              monthly_executions=excluded.monthly_executions,monthly_voice_minutes=excluded.monthly_voice_minutes,
              monthly_messages=excluded.monthly_messages,max_users=excluded.max_users,
              max_locations=excluded.max_locations,updated_at=now()
            """
        ),
        {"clinic": clinic, "plan": plan_code, "executions": plan["monthly_executions"], "voice": plan["monthly_voice_minutes"], "messages": plan["monthly_messages"], "users": plan["max_users"], "locations": plan["max_locations"]},
    )
    await session.execute(
        text(
            """
            insert into subscriptions(clinic_id,plan_code,status,provider)
            values(:clinic,:plan,'active','manual')
            on conflict (clinic_id) do update set plan_code=excluded.plan_code,status='active',
              version=subscriptions.version+1,updated_at=now()
            """
        ),
        {"clinic": clinic, "plan": plan_code},
    )
    await session.execute(
        text(
            """
            insert into platform_events(clinic_id,event_type,actor_id,payload)
            values(:clinic,'subscription.plan_changed',:actor,cast(:payload as jsonb))
            """
        ),
        {"clinic": clinic, "actor": actor, "payload": '{"plan":"' + plan_code + '"}'},
    )
    return await get_subscription(session, organization_id)


def _price_id(plan_code: str) -> str:
    env_name = _PRICE_ENV[plan_code]
    price_id = getattr(settings, env_name)
    if not price_id:
        raise ValueError(f"{env_name} is not configured")
    return price_id


async def create_checkout_session(
    session,
    organization_id: str,
    plan_code: str,
    idempotency_key: str,
) -> dict:
    get_plan(plan_code)
    clinic = await _clinic_id(session, organization_id)
    price_id = _price_id(plan_code)
    existing = (
        await session.execute(
            text(
                """
                select metadata->>'checkout_session_id' checkout_session_id
                from platform_events
                where clinic_id=:clinic and event_type='subscription.checkout_created'
                  and metadata->>'idempotency_key'=:key
                order by created_at desc limit 1
                """
            ),
            {"clinic": clinic, "key": idempotency_key},
        )
    ).scalar_one_or_none()
    if existing:
        return {"checkout_session_id": existing, "reused": True}

    if not settings.stripe_secret_key:
        raise ValueError("stripe payment provider is not configured")

    stripe.api_key = settings.stripe_secret_key
    checkout = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        client_reference_id=clinic,
        metadata={"clinic_id": clinic, "plan_code": plan_code},
        subscription_data={"metadata": {"clinic_id": clinic, "plan_code": plan_code}},
        success_url=settings.stripe_checkout_success_url,
        cancel_url=settings.stripe_checkout_cancel_url,
        idempotency_key=idempotency_key,
    )
    await session.execute(
        text(
            """
            insert into platform_events(clinic_id,event_type,actor_id,payload)
            values(:clinic,'subscription.checkout_created',NULL,cast(:payload as jsonb))
            """
        ),
        {"clinic": clinic, "payload": '{"checkout_session_id":"' + checkout.id + '","idempotency_key":"' + idempotency_key + '","plan_code":"' + plan_code + '"}'},
    )
    return {"checkout_session_id": checkout.id, "url": checkout.url, "reused": False}


async def apply_provider_event(session, event: dict) -> dict:
    provider_event_id = str(event.get("id") or "")
    event_type = str(event.get("type") or "")
    if not provider_event_id or not event_type:
        raise ValueError("provider event id and type are required")

    existing = await session.execute(
        text("select clinic_id,status from subscription_events where provider='stripe' and provider_event_id=:event_id"),
        {"event_id": provider_event_id},
    )
    prior = existing.mappings().first()
    if prior and prior["status"] == "processed":
        return {"processed": False, "duplicate": True, "clinic_id": prior["clinic_id"]}

    obj = (event.get("data") or {}).get("object") or {}
    metadata = obj.get("metadata") or {}
    clinic = metadata.get("clinic_id")

    if not clinic:
        provider_subscription_id = obj.get("id") if event_type.startswith("customer.subscription.") else obj.get("subscription")
        if provider_subscription_id:
            clinic = await session.scalar(
                text("select clinic_id from subscriptions where provider_subscription_id=:provider_id"),
                {"provider_id": provider_subscription_id},
            )

    if not clinic:
        await session.execute(
            text(
                """
                insert into subscription_events(clinic_id,provider,provider_event_id,event_type,status,payload_metadata,processed_at)
                values(NULL,'stripe',:event_id,:event_type,'ignored',cast(:metadata as jsonb),now())
                on conflict(provider,provider_event_id) do nothing
                """
            ),
            {"event_id": provider_event_id, "event_type": event_type, "metadata": '{"reason":"clinic_not_resolved"}'},
        )
        return {"processed": False, "ignored": True, "reason": "clinic_not_resolved"}

    inserted = await session.execute(
        text(
            """
            insert into subscription_events(clinic_id,provider,provider_event_id,event_type,status,payload_metadata)
            values(:clinic,'stripe',:event_id,:event_type,'received',cast(:metadata as jsonb))
            on conflict(provider,provider_event_id) do nothing
            returning id
            """
        ),
        {"clinic": clinic, "event_id": provider_event_id, "event_type": event_type, "metadata": '{"provider_object_id":"' + str(obj.get("id", "")) + '"}'},
    )
    if not inserted.scalar_one_or_none():
        return {"processed": False, "duplicate": True, "clinic_id": clinic}

    if event_type.startswith("customer.subscription."):
        status = str(obj.get("status") or "")
        mapped = {"trialing": "trialing", "active": "active", "past_due": "past_due", "paused": "paused", "canceled": "cancelled", "unpaid": "past_due"}.get(status, "paused")
        items = obj.get("items", {}).get("data", []) if isinstance(obj.get("items"), dict) else []
        price_id = items[0].get("price", {}).get("id") if items else None
        current_start = obj.get("current_period_start")
        current_end = obj.get("current_period_end")
        await session.execute(
            text(
                """
                update subscriptions
                set plan_code=coalesce(:plan,plan_code),status=:status,provider='stripe',
                    provider_customer_id=:customer,provider_subscription_id=:subscription,
                    provider_price_id=:price,billing_interval=:interval,
                    current_period_start=case when :start is null then current_period_start else to_timestamp(:start) end,
                    current_period_end=case when :end is null then current_period_end else to_timestamp(:end) end,
                    cancel_at_period_end=coalesce(:cancel_at_period_end,cancel_at_period_end),
                    version=version+1,last_provider_event_at=now(),updated_at=now()
                where clinic_id=:clinic
                """
            ),
            {
                "clinic": clinic,
                "plan": metadata.get("plan_code"),
                "status": mapped,
                "customer": obj.get("customer"),
                "subscription": obj.get("id"),
                "price": price_id,
                "interval": (items[0].get("price", {}).get("recurring") or {}).get("interval") if items else None,
                "start": current_start,
                "end": current_end,
                "cancel_at_period_end": obj.get("cancel_at_period_end"),
            },
        )
    elif event_type in {"invoice.paid", "invoice.payment_failed", "invoice.finalized", "invoice.voided"}:
        subscription_id = obj.get("subscription")
        if event_type == "invoice.paid":
            status, ledger_status = "active", "paid"
        elif event_type == "invoice.payment_failed":
            status, ledger_status = "past_due", "failed"
        elif event_type == "invoice.voided":
            status, ledger_status = "cancelled", "voided"
        else:
            status, ledger_status = "active", "pending"
        if subscription_id:
            await session.execute(
                text("update subscriptions set status=:status,version=version+1,last_provider_event_at=now(),updated_at=now() where clinic_id=:clinic and provider_subscription_id=:subscription"),
                {"status": status, "clinic": clinic, "subscription": subscription_id},
            )
        await session.execute(
            text(
                """
                insert into commercial_ledger(clinic_id,provider,provider_object_id,event_type,status,amount_minor,currency,idempotency_key,metadata)
                values(:clinic,'stripe',:object,:event_type,:status,:amount,:currency,:key,cast(:metadata as jsonb))
                on conflict(clinic_id,idempotency_key) do nothing
                """
            ),
            {"clinic": clinic, "object": obj.get("id"), "event_type": event_type, "status": ledger_status, "amount": obj.get("amount_paid") or obj.get("amount_due"), "currency": (obj.get("currency") or "").upper() or None, "key": provider_event_id, "metadata": '{"provider_event_id":"' + provider_event_id + '"}'},
        )

    await session.execute(
        text("update subscription_events set status='processed',processed_at=now() where provider='stripe' and provider_event_id=:event_id"),
        {"event_id": provider_event_id},
    )
    return {"processed": True, "clinic_id": clinic, "event_type": event_type}
