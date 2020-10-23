import sys
import json
import pyblish.api
import six


class IntegrateFtrackStatus(pyblish.api.InstancePlugin):
    """Set status in Ftrack."""

    # Must be after integrate asset new
    order = pyblish.api.IntegratorOrder + 0.49999
    label = "Set Ftrack status"
    families = ["request"]
    optional = True

    def process(self, instance):
        """
        :param pyblish.plugin.Instance instance:
        """
        # assert type(instance) is pyblish.plugin.Instance
        # assert type(instance.data) is dict
        # assert type(instance.context) is list
        # assert type(instance.context[0]) is pyblish.plugin.Instance
        # assert type(instance.context.data) is dict

        asset_versions_key = "ftrackIntegratedAssetVersions"
        asset_versions = instance.data.get(asset_versions_key)

        if not asset_versions:
            self.log.debug("AssetVersion not found in Instance \"{}\"".format(instance))
            self.log.debug("Searching for an Instance with AssetVersion")
            for context in instance.context:
                asset_versions = context.data.get(asset_versions_key)
                if asset_versions:
                    self.log.debug("Using AssetVersion from \"{}\"".format(context))
                    break

        if not asset_versions:
            self.log.warning("Could not find any AssetVersion in available contexts")
            return

        session = instance.context.data["ftrackSession"]

        user = session.query("User where username is \"{}\"".format(session.api_user)).first()
        if not user:
            self.log.warning("Could not find current User \"{}\"".format(session.api_user))

        status = session.query("select id, name from Status where name is Render").one()
        self.log.debug("Found ftrack status \"{}\"".format(status["name"]))

        for asset_version in asset_versions:
            asset_version["status"] = status

            try:
                session.commit()
                self.log.debug("Set status to \"{}\" for AssetVersion \"{}\"".format(status["name"], str(asset_version)))
            except Exception:
                tp, value, tb = sys.exc_info()
                session.rollback()
                six.reraise(tp, value, tb)
