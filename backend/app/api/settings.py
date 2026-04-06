from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.setting import Setting
from app.schemas.setting import SettingResponse, SettingUpdate

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
