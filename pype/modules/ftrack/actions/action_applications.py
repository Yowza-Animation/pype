import os
from uuid import uuid4

from pype.api import config
from pype.modules.ftrack.lib import BaseAction
from pype.lib import (
    ApplicationManager,
    ApplicationLaunchFailed
)
from avalon.api import AvalonMongoDB


class AppplicationsAction(BaseAction):
    """Application Action class.

    Args:
        session (ftrack_api.Session): Session where action will be registered.
        label (str): A descriptive string identifing your action.
        varaint (str, optional): To group actions together, give them the same
            label and specify a unique variant per action.
        identifier (str): An unique identifier for app.
        description (str): A verbose descriptive text for you action.
        icon (str): Url path to icon which will be shown in Ftrack web.
    """

    type = "Application"
    label = "Application action"
    identifier = "pype_app.{}.".format(str(uuid4()))
    icon_url = os.environ.get("PYPE_STATICS_SERVER")

    def __init__(self, session, plugins_presets=None):
        super().__init__(session, plugins_presets)

        self.application_manager = ApplicationManager()
        self.dbcon = AvalonMongoDB()

    def construct_requirements_validations(self):
        # Override validation as this action does not need them
        return

    def register(self):
        """Registers the action, subscribing the discover and launch topics."""

        discovery_subscription = (
            "topic=ftrack.action.discover and source.user.username={0}"
        ).format(self.session.api_user)

        self.session.event_hub.subscribe(
            discovery_subscription,
            self._discover,
            priority=self.priority
        )

        launch_subscription = (
            "topic=ftrack.action.launch"
            " and data.actionIdentifier={0}"
            " and source.user.username={1}"
        ).format(
            self.identifier + "*",
            self.session.api_user
        )
        self.session.event_hub.subscribe(
            launch_subscription,
            self._launch
        )

    def _discover(self, event):
        entities = self._translate_event(event)
        items = self.discover(self.session, entities, event)
        if items:
            return {"items": items}

    def discover(self, session, entities, event):
        """Return true if we can handle the selected entities.

        Args:
            session (ftrack_api.Session): Helps to query necessary data.
            entities (list): Object of selected entities.
            event (ftrack_api.Event): Ftrack event causing discover callback.
        """

        if (
            len(entities) != 1
            or entities[0].entity_type.lower() != "task"
        ):
            return False

        entity = entities[0]
        if entity["parent"].entity_type.lower() == "project":
            return False

        avalon_project_apps = event["data"].get("avalon_project_apps", None)
        avalon_project_doc = event["data"].get("avalon_project_doc", None)
        if avalon_project_apps is None:
            if avalon_project_doc is None:
                ft_project = self.get_project_from_entity(entity)
                project_name = ft_project["full_name"]
                if not self.dbcon.is_installed():
                    self.dbcon.install()
                self.dbcon.Session["AVALON_PROJECT"] = project_name
                avalon_project_doc = self.dbcon.find_one({
                    "type": "project"
                }) or False
                event["data"]["avalon_project_doc"] = avalon_project_doc

            if not avalon_project_doc:
                return False

            project_apps_config = avalon_project_doc["config"].get("apps", [])
            avalon_project_apps = [
                app["name"] for app in project_apps_config
            ] or False
            event["data"]["avalon_project_apps"] = avalon_project_apps

        if not avalon_project_apps:
            return False

        items = []
        for app_name in avalon_project_apps:
            app = self.application_manager.applications.get(app_name)
            if not app or not app.enabled:
                continue

            app_icon = app.icon
            if app_icon and self.icon_url:
                try:
                    app_icon = app_icon.format(self.icon_url)
                except Exception:
                    self.log.warning((
                        "Couldn't fill icon path. Icon template: \"{}\""
                        " --- Icon url: \"{}\""
                    ).format(app_icon, self.icon_url))
                    app_icon = None

            items.append({
                "label": app.label,
                "variant": app.variant_label,
                "description": None,
                "actionIdentifier": self.identifier + app_name,
                "icon": app_icon
            })

        return items

    def launch(self, session, entities, event):
        """Callback method for the custom action.

        return either a bool (True if successful or False if the action failed)
        or a dictionary with they keys `message` and `success`, the message
        should be a string and will be displayed as feedback to the user,
        success should be a bool, True if successful or False if the action
        failed.

        *session* is a `ftrack_api.Session` instance

        *entities* is a list of tuples each containing the entity type and
        the entity id. If the entity is a hierarchical you will always get
        the entity type TypedContext, once retrieved through a get operation
        you will have the "real" entity type ie. example Shot, Sequence
        or Asset Build.

        *event* the unmodified original event
        """
        identifier = event["data"]["actionIdentifier"]
        app_name = identifier[len(self.identifier):]

        entity = entities[0]

        task_name = entity["name"]
        asset_name = entity["parent"]["name"]
        project_name = entity["project"]["full_name"]
        self.log.info((
            "Ftrack launch app: \"{}\" on Project/Asset/Task: {}/{}/{}"
        ).format(app_name, project_name, asset_name, task_name))
        try:
            self.application_manager.launch(
                app_name,
                project_name=project_name,
                asset_name=asset_name,
                task_name=task_name
            )

        except ApplicationLaunchFailed as exc:
            self.log.error(str(exc))
            return {
                "success": False,
                "message": str(exc)
            }

        except Exception:
            msg = "Unexpected failure of application launch {}".format(
                self.label
            )
            self.log.error(msg, exc_info=True)
            return {
                "success": False,
                "message": msg
            }

        # TODO Move to prelaunch/afterlaunch hooks
        # TODO change to settings
        # Change status of task to In progress
        presets = config.get_presets()["ftrack"]["ftrack_config"]

        if "status_update" in presets:
            statuses = presets["status_update"]

            actual_status = entity["status"]["name"].lower()
            already_tested = []
            ent_path = "/".join(
                [ent["name"] for ent in entity["link"]]
            )
            while True:
                next_status_name = None
                for key, value in statuses.items():
                    if key in already_tested:
                        continue
                    if actual_status in value or "_any_" in value:
                        if key != "_ignore_":
                            next_status_name = key
                            already_tested.append(key)
                        break
                    already_tested.append(key)

                if next_status_name is None:
                    break

                try:
                    query = "Status where name is \"{}\"".format(
                        next_status_name
                    )
                    status = session.query(query).one()

                    entity["status"] = status
                    session.commit()
                    self.log.debug("Changing status to \"{}\" <{}>".format(
                        next_status_name, ent_path
                    ))
                    break

                except Exception:
                    session.rollback()
                    msg = (
                        "Status \"{}\" in presets wasn't found"
                        " on Ftrack entity type \"{}\""
                    ).format(next_status_name, entity.entity_type)
                    self.log.warning(msg)

        return {
            "success": True,
            "message": "Launching {0}".format(self.label)
        }


def register(session, plugins_presets=None):
    '''Register action. Called when used as an event plugin.'''
    from pype.lib import env_value_to_bool
    if env_value_to_bool("PYPE_USE_APP_MANAGER", default=False):
        AppplicationsAction(session, plugins_presets).register()
