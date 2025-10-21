import botocore
import structlog

from ap.aws.base import AWSService

logger = structlog.get_logger(__name__)


class IAMService(AWSService):
    aws_service_name = "iam"

    def __init__(self, catalog_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.catalog_id = catalog_id or self.account_id
        self.clients = {}

    def get_role(self, role_name):
        try:
            response = self.client.get_role(RoleName=role_name)
            return response.get("Role", {})
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                logger.warning(f"Role {role_name} does not exist.")
                raise e
