from typing import Any

from . import base


class RAMService(base.AWSService):
    aws_service_name = "ram"

    def get_resource_shares(self, **kwargs: Any) -> list[dict]:
        kwargs = kwargs or {}
        kwargs.setdefault("resourceOwner", "OTHER-ACCOUNTS")
        kwargs.setdefault("resourceShareStatus", "ACTIVE")
        paginator = self.client.get_paginator("get_resource_shares")

        shares: list[dict] = []
        for page in paginator.paginate(**kwargs, PaginationConfig={"PageSize": 100}):
            shares.extend(
                share
                for share in page.get("resourceShares", [])
                if share.get("name", "").startswith("LakeFormation-V4")
            )
        return shares

    def list_resources(self, resource_share_arns: list[str], **kwargs: Any) -> list[dict]:
        kwargs = kwargs or {}
        kwargs.setdefault("resourceOwner", "OTHER-ACCOUNTS")
        paginator = self.client.get_paginator("list_resources")
        resources: list[dict] = []
        for page in paginator.paginate(
            resourceShareArns=resource_share_arns,
            **kwargs,
            PaginationConfig={"PageSize": 100},
        ):
            resources.extend(page.get("resources", []))
        return resources
