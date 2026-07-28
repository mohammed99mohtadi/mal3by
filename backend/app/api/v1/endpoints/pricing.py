from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.court import Court
from app.models.user import User, UserRole
from app.schemas.pricing import (
    BookingPriceQuoteRequest,
    BookingPriceQuoteResponse,
    CourtDatePriceOverrideCreate,
    CourtDatePriceOverrideRead,
    CourtDatePriceOverrideUpdate,
    CourtPricingRuleCreate,
    CourtPricingRuleRead,
    CourtPricingRuleUpdate,
)
from app.services.pricing_service import (
    create_date_override,
    create_price_quote,
    create_pricing_rule,
    delete_date_override,
    delete_pricing_rule,
    get_date_override,
    get_pricing_rule,
    list_date_overrides,
    list_pricing_rules,
    update_date_override,
    update_pricing_rule,
)

router = APIRouter()


def check_court_owner_or_admin(db: Session, court_id: int, current_user: User) -> Court:
    court = db.query(Court).filter(Court.id == court_id).first()
    if not court:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Court with id {court_id} not found",
        )

    is_owner = (court.owner_id == current_user.id)
    is_admin = (current_user.role == UserRole.ADMIN or current_user.role == "admin" or current_user.is_admin)

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators or court owners can perform this action.",
        )
    return court


# --- Pricing Rules Endpoints ---
@router.get("/{court_id}/pricing/rules", response_model=list[CourtPricingRuleRead])
def get_court_pricing_rules_endpoint(
    court_id: int,
    db: Session = Depends(get_db),
) -> list[CourtPricingRuleRead]:
    court = db.query(Court).filter(Court.id == court_id).first()
    if not court:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Court with id {court_id} not found",
        )
    return list_pricing_rules(db, court_id)


@router.post("/{court_id}/pricing/rules", response_model=CourtPricingRuleRead, status_code=status.HTTP_201_CREATED)
def create_court_pricing_rule_endpoint(
    court_id: int,
    rule_in: CourtPricingRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CourtPricingRuleRead:
    check_court_owner_or_admin(db, court_id, current_user)
    return create_pricing_rule(db, court_id, rule_in, created_by_id=current_user.id)


@router.get("/{court_id}/pricing/rules/{rule_id}", response_model=CourtPricingRuleRead)
def get_pricing_rule_endpoint(
    court_id: int,
    rule_id: int,
    db: Session = Depends(get_db),
) -> CourtPricingRuleRead:
    rule = get_pricing_rule(db, rule_id)
    if not rule or rule.court_id != court_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule with id {rule_id} not found for court {court_id}",
        )
    return rule


@router.patch("/{court_id}/pricing/rules/{rule_id}", response_model=CourtPricingRuleRead)
def update_pricing_rule_endpoint(
    court_id: int,
    rule_id: int,
    rule_in: CourtPricingRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CourtPricingRuleRead:
    check_court_owner_or_admin(db, court_id, current_user)
    rule = get_pricing_rule(db, rule_id)
    if not rule or rule.court_id != court_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule with id {rule_id} not found for court {court_id}",
        )
    return update_pricing_rule(db, rule_id, rule_in)


@router.delete("/{court_id}/pricing/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pricing_rule_endpoint(
    court_id: int,
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    check_court_owner_or_admin(db, court_id, current_user)
    rule = get_pricing_rule(db, rule_id)
    if not rule or rule.court_id != court_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule with id {rule_id} not found for court {court_id}",
        )
    delete_pricing_rule(db, rule_id)


# --- Date Overrides Endpoints ---
@router.get("/{court_id}/pricing/date-overrides", response_model=list[CourtDatePriceOverrideRead])
def get_court_date_overrides_endpoint(
    court_id: int,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: Session = Depends(get_db),
) -> list[CourtDatePriceOverrideRead]:
    court = db.query(Court).filter(Court.id == court_id).first()
    if not court:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Court with id {court_id} not found",
        )
    return list_date_overrides(db, court_id, start_date=start_date, end_date=end_date)


@router.post("/{court_id}/pricing/date-overrides", response_model=CourtDatePriceOverrideRead, status_code=status.HTTP_201_CREATED)
def create_court_date_override_endpoint(
    court_id: int,
    override_in: CourtDatePriceOverrideCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CourtDatePriceOverrideRead:
    check_court_owner_or_admin(db, court_id, current_user)
    return create_date_override(db, court_id, override_in, created_by_id=current_user.id)


@router.get("/{court_id}/pricing/date-overrides/{override_id}", response_model=CourtDatePriceOverrideRead)
def get_date_override_endpoint(
    court_id: int,
    override_id: int,
    db: Session = Depends(get_db),
) -> CourtDatePriceOverrideRead:
    override = get_date_override(db, override_id)
    if not override or override.court_id != court_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Date price override with id {override_id} not found for court {court_id}",
        )
    return override


@router.patch("/{court_id}/pricing/date-overrides/{override_id}", response_model=CourtDatePriceOverrideRead)
def update_date_override_endpoint(
    court_id: int,
    override_id: int,
    override_in: CourtDatePriceOverrideUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CourtDatePriceOverrideRead:
    check_court_owner_or_admin(db, court_id, current_user)
    override = get_date_override(db, override_id)
    if not override or override.court_id != court_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Date price override with id {override_id} not found for court {court_id}",
        )
    return update_date_override(db, override_id, override_in)


@router.delete("/{court_id}/pricing/date-overrides/{override_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_date_override_endpoint(
    court_id: int,
    override_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    check_court_owner_or_admin(db, court_id, current_user)
    override = get_date_override(db, override_id)
    if not override or override.court_id != court_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Date price override with id {override_id} not found for court {court_id}",
        )
    delete_date_override(db, override_id)



# --- Public Price Quote Endpoint ---
@router.post("/{court_id}/price-quote", response_model=BookingPriceQuoteResponse)
def get_price_quote_endpoint(
    court_id: int,
    quote_in: BookingPriceQuoteRequest,
    db: Session = Depends(get_db),
) -> BookingPriceQuoteResponse:
    return create_price_quote(db, court_id, quote_in.start_time, quote_in.end_time)

