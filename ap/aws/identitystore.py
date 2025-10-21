from cmath import log

import structlog
from django.conf import settings

from ap.aws.base import AWSService

logger = structlog.get_logger(__name__)


class AWSSSOAdmin(AWSService):
    def __init__(self, assume_role_name=None, profile_name=None, region_name=None):
        super().__init__(assume_role_name, profile_name, region_name)
        region = region_name or settings.AWS_DEFAULT_REGION
        self.client = self.boto3_session.client("sso-admin", region_name=region)
        self.identity_store_id = None

    def get_identity_store_id(self):
        if self.identity_store_id:
            return self.identity_store_id

        response = self.client.list_instances()
        self.identity_store_id = response["Instances"][0]["IdentityStoreId"]
        return self.identity_store_id


class AWSIdentityStore(AWSService):
    def __init__(self, assume_role_name=None, profile_name=None, region_name=None):
        super().__init__(assume_role_name, profile_name, region_name)
        region = region_name or settings.AWS_DEFAULT_REGION
        self.client = self.boto3_session.client("identitystore", region_name=region)
        self.sso_client = AWSSSOAdmin(
            assume_role_name=assume_role_name, profile_name=profile_name, region_name=region_name
        )

    def get_user_id(self, user_email):
        try:
            response = self.client.get_user_id(
                IdentityStoreId=self.sso_client.get_identity_store_id(),
                AlternateIdentifier={
                    "UniqueAttribute": {"AttributePath": "userName", "AttributeValue": user_email}
                },
            )

            return response["UserId"]
        except self.client.exceptions.ResourceNotFoundException as error:
            logger.warning(f"User {user_email} not found in Identity Store - {error}")
            return None

    def get_group_id(self, group_name):
        try:
            response = self.client.get_group_id(
                IdentityStoreId=self.sso_client.get_identity_store_id(),
                AlternateIdentifier={
                    "UniqueAttribute": {
                        "AttributePath": "displayName",
                        "AttributeValue": group_name,
                    }
                },
            )

            return response["GroupId"]
        except self.client.exceptions.ResourceNotFoundException as error:
            logger.warning(f"Group {group_name} not found in Identity Store - {error}")
            raise error

    def get_group_membership_id(self, group_name, user_email):
        group_id = self.get_group_id(group_name)
        user_id = self.get_user_id(user_email)

        try:
            response = self.client.get_group_membership_id(
                IdentityStoreId=self.sso_client.get_identity_store_id(),
                GroupId=group_id,
                MemberId={"UserId": user_id},
            )

            return response["MembershipId"]
        except self.client.exceptions.ResourceNotFoundException as error:
            logger.warning(
                f"Membership for user {user_email} in group {group_name} not found - {error}"
            )
            return None

    def get_name_from_email(self, user_email):
        """
        gets name from justice email as user.name is not guaranteed to be a name
        (can be an email, forename only or handle)
        """

        name, address = user_email.split("@")

        if address.lower() != "justice.gov.uk":
            raise ValueError("Expecting justice email")

        if "." not in name:
            raise ValueError("Expecting forename.surname from justice email")

        forename, surname = name.split(".")
        surname = "".join(c for c in surname if not c.isdigit())
        return forename.title(), surname.title()

    def create_user(self, user_email):
        if self.get_user_id(user_email):
            logger.info(f"User {user_email} already exists in Identity Store.")
            return

        try:
            forename, surname = self.get_name_from_email(user_email)

            self.client.create_user(
                IdentityStoreId=self.sso_client.get_identity_store_id(),
                UserName=user_email,
                DisplayName=user_email,
                Name={
                    "FamilyName": surname,
                    "GivenName": forename,
                },
                Emails=[{"Value": user_email, "Type": "EntraId", "Primary": True}],
            )

            logger.info(f"User {user_email} created in Identity Center")
        except Exception as error:
            logger.warning(f"Error creating user {user_email} in Identity Center: {error}")
            raise error

    def create_group_membership(self, user_email, group_name):
        logger.info(f"Attempting to add {user_email} to group {group_name}")
        group_id = self.get_group_id(group_name)
        user_id = self.get_user_id(user_email)

        try:
            membership_id = self.get_group_membership_id(group_name, user_email)

            if membership_id is not None:
                logger.info("User is already a member of this group. Skipping")
                return

            response = self.client.create_group_membership(
                IdentityStoreId=self.sso_client.get_identity_store_id(),
                GroupId=group_id,
                MemberId={"UserId": user_id},
            )

            logger.info(f"User {user_email} added to group {group_name}")
            return response
        except Exception as error:
            logger.warning(
                f"Error creating group membership for user {user_email} "
                f"in group {group_name}: {error}"
            )
            raise error

    def delete_group_membership(self, user_email, group_name):
        logger.info(f"Attempting to remove {user_email} from group {group_name}")

        try:
            membership_id = self.get_group_membership_id(group_name, user_email)

            if membership_id is None:
                logger.info("User is not a member of this group. Skipping")
                return

            self.client.delete_group_membership(
                IdentityStoreId=self.sso_client.get_identity_store_id(),
                MembershipId=membership_id,
            )

            logger.info(f"User {user_email} removed from group {group_name}")
        except Exception as error:
            logger.warning(f"Error removing user {user_email} from group {group_name}: {error}")
            raise error

    def add_user_to_group(self, justice_email, group_name):
        logger.info(f"Attempting to add {justice_email} to azure and {group_name} groups")

        if not justice_email:
            message = (
                "Cannot create an Identity Center user without an associated @justice.gov.uk email"
            )
            log.error(message)
            raise ValueError(message)

        self.create_user(justice_email)
        self.create_group_membership(justice_email, group_name)
        # self.create_group_membership(justice_email, settings.AZURE_HOLDING_GROUP_NAME)
