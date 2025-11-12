from core.utils import convert_to_unix_timestamp
from regos.api import regos_async_api_request


class RegosReports:
    def __init__(self):
        pass

    async def partner_balance_report(self, token: str, partner_id: int, firm_id: int, start_time: str, end_time: str) -> dict:
        timestamp_start_time = convert_to_unix_timestamp(start_time)
        timestamp_end_time = convert_to_unix_timestamp(end_time)

        request_data = {
            "start_date": timestamp_start_time,
            "end_date": timestamp_end_time,
            "partner_id": partner_id,
            "firm_id": firm_id
        }
        partner_balance_data = await regos_async_api_request(
            request_data=request_data,
            endpoint="PartnerBalance/Get",
            token=token
        )

        return partner_balance_data



