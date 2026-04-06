from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.setting import Setting
from app.models.usage_log import UsageLog
from app.schemas.setting import SettingResponse, SettingUpdate, UsageSummary

router = APIRouter(prefix="/settings", tags=["settings"])

DEFAULT_SETTINGS = {
    "scrape_frequency": {"interval": "daily"},
    "scrape_portals": {"enabled": ["linkedin", "indeed", "glassdoor", "wellfound", "seek"]},
    "match_threshold": {"threshold": 50},
    "usage_cap_type": {"type": None},
    "usage_cap_value": {"value": None},
    "telegram_chat_id": {"chat_id": ""},
    "search_keywords": {"keywords": []},
    "preferred_locations": {"locations": []},
    "default_visa_filter": {"values": ["authorized", "will_sponsor"]},
}


@router.get("", response_model=list[SettingResponse])
async def list_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Setting))
    settings = result.scalars().all()
    return [SettingResponse.model_validate(s) for s in settings]


@router.get("/usage", response_model=UsageSummary)
async def get_usage(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            func.coalesce(func.sum(UsageLog.tokens_input), 0),
            func.coalesce(func.sum(UsageLog.tokens_output), 0),
            func.coalesce(func.sum(UsageLog.cost_usd), 0),
        )
    )
    tokens_input, tokens_output, cost_usd = result.one()

    cap_type_result = await db.execute(
        select(Setting).where(Setting.key == "usage_cap_type")
    )
    cap_type_setting = cap_type_result.scalar_one_or_none()
    cap_type = cap_type_setting.value.get("type") if cap_type_setting else None

    cap_value_result = await db.execute(
        select(Setting).where(Setting.key == "usage_cap_value")
    )
    cap_value_setting = cap_value_result.scalar_one_or_none()
    cap_value = cap_value_setting.value.get("value") if cap_value_setting else None

    usage_percentage = None
    if cap_type and cap_value:
        usage_percentage = (float(cost_usd) / float(cap_value)) * 100

    return UsageSummary(
        total_tokens_input=int(tokens_input),
        total_tokens_output=int(tokens_output),
        total_cost_usd=float(cost_usd),
        cap_type=cap_type,
        cap_value=float(cap_value) if cap_value else None,
        usage_percentage=usage_percentage,
        period_start=None,
    )


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        if key in DEFAULT_SETTINGS:
            setting = Setting(key=key, value=DEFAULT_SETTINGS[key])
            db.add(setting)
            await db.commit()
            await db.refresh(setting)
            return SettingResponse.model_validate(setting)
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return SettingResponse.model_validate(setting)


@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str, body: SettingUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = body.value
    else:
        setting = Setting(key=key, value=body.value)
        db.add(setting)
    await db.commit()
    await db.refresh(setting)
    return SettingResponse.model_validate(setting)
