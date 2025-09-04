from collections.abc import Generator
from typing import Any

from . import base


class RAMService(base.AWSService):
    aws_service_name = "ram"

    def get_resource_shares(self, **kwargs: Any) -> Generator[dict]:
        kwargs = kwargs or {}
        kwargs.setdefault("resourceOwner", "OTHER-ACCOUNTS")
        kwargs.setdefault("resourceShareStatus", "ACTIVE")
        paginator = self.client.get_paginator("get_resource_shares")

        for page in paginator.paginate(**kwargs, PaginationConfig={"PageSize": 100}):
            for share in page.get("resourceShares", []):
                if share.get("name", "").startswith("LakeFormation-V4"):
                    yield share

    def list_resources(self, resource_share_arns: list[str], **kwargs: Any) -> Generator[dict]:
        kwargs = kwargs or {}
        kwargs.setdefault("resourceOwner", "OTHER-ACCOUNTS")
        paginator = self.client.get_paginator("list_resources")

        for page in paginator.paginate(
            resourceShareArns=resource_share_arns,
            **kwargs,
            PaginationConfig={"PageSize": 100},
        ):
            yield from page.get("resources", [])

    def list_all_resources(self) -> list[dict]:
        shares = self.get_resource_shares()
        share_arns = [share["resourceShareArn"] for share in shares]
        if not share_arns:
            return []
        return self.list_resources(share_arns)
