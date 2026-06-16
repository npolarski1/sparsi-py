import datetime
try:
    import zoneinfo
except ImportError:
    # For Python < 3.9
    try:
        from backports import zoneinfo
    except ImportError:
        # Fallback to a very simple manual offset if zoneinfo is completely missing, 
        # but in a typical environment it should be there.
        zoneinfo = None

from typing import Any, Dict, Optional
from pydantic import BaseModel
from dagor import Operator, register_operator, Input, Output

CITY_TIMEZONES = {
    "New York": "America/New_York",
    "Tokyo": "Asia/Tokyo",
}

@register_operator("CityTimeOp")
class CityTimeOp(Operator, BaseModel):
    city: Input = ""
    result: Output = ""

    def setup(self, params: Dict[str, Any]) -> None:
        pass

    async def reset(self) -> None:
        await super().reset()

    async def run(self, ctx: Any) -> None:
        if self.city is None:
            raise ValueError("CityTimeOp: city input is None")
            
        tz_name = CITY_TIMEZONES.get(self.city)
        if not tz_name:
            raise ValueError(f"CityTimeOp: unsupported city {self.city!r} (supported: {list(CITY_TIMEZONES.keys())})")
        
        if zoneinfo is None:
             raise ImportError("CityTimeOp: zoneinfo or backports.zoneinfo is required for timezone support")

        try:
            tz = zoneinfo.ZoneInfo(tz_name)
            now = datetime.datetime.now(tz)
            # RFC3339 is basically ISO8601. Go's RFC3339 typically doesn't include microseconds.
            self.result = now.replace(microsecond=0).isoformat()
        except Exception as e:
            raise RuntimeError(f"CityTimeOp: failed to get time for {self.city}: {e}")
