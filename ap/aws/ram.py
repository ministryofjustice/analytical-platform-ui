from . import base


class RAMService(base.AWSService):
    aws_service_name = "ram"

    def get_resource_shares(self, **kwargs: dict) -> list:
        kwargs = kwargs or {}
        kwargs.update({"resourceOwner": "OTHER-ACCOUNTS", "maxResults": 100})
        response = self._request("get_resource_shares", **kwargs)
        if not response:
            return []

        shares = response["resourceShares"]
        if "nextToken" in response:
            kwargs["nextToken"] = response["nextToken"]
            shares.extend(self.get_resource_shares(**kwargs))

        shares = [share for share in shares if share.get("name", "").startswith("LakeFormation-V4")]
        return shares

    def get_active_resource_shares(self, **kwargs: dict) -> list:
        kwargs = kwargs or {}
        kwargs.update({"resourceShareStatus": "ACTIVE"})
        return self.get_resource_shares(**kwargs)
