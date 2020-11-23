# -*- coding: utf-8 -*-
"""Load template."""
import tempfile
import zipfile
import os
import shutil
import uuid

from avalon import api, harmony
from avalon.pipeline import get_representation_context

import pype.lib


class TemplateLoader(api.Loader):
    """Load Harmony template as container.

    .. todo::

        This must be implemented properly.

    """

    families = ["scene"]
    representations = ["*"]
    label = "Load Template"
    icon = "gift"

    def load(self, context, name=None, namespace=None, data=None):
        """Plugin entry point.

        Args:
            context (:class:`pyblish.api.Context`): Context.
            name (str, optional): Container name.
            namespace (str, optional): Container namespace.
            data (dict, optional): Additional data passed into loader.

        """
        # Load template.
        self_name = self.__class__.__name__
        temp_dir = tempfile.mkdtemp()
        zip_file = api.get_representation_path(context["representation"])
        template_path = os.path.join(temp_dir, "temp.tpl")
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(template_path)

        group_id = "{}".format(uuid.uuid4())

        container_group = harmony.send(
            {
                "function": f"PypeHarmony.Loaders.{self_name}.loadContainer",
                "args": [template_path,
                         context["asset"]["name"],
                         context["subset"]["name"],
                         group_id]
            }
        )["result"]

        # Cleanup the temp directory
        # shutil.rmtree(temp_dir)

        # We must validate the group_node
        return harmony.containerise(
            name,
            container_group,
            container_group,
            context,
            self_name
        )

    def update(self, container, representation):
        """Update loaded containers.

        Args:
            container (dict): Container data.
            representation (dict): Representation data.

        """

        update_and_replace = False
        container_to_update = container["objectName"]


        self_name = self.__class__.__name__
        context = get_representation_context(representation)

        if pype.lib.is_latest(representation):
            self._set_green(container_to_update)
        else:
            self._set_red(container_to_update)

        update_and_replace = harmony.send(
            {
                "function": f"PypeHarmony.Loaders.{self_name}."
                            "askForColumnsUpdate",
                "args": []
            }
        )["result"]

        updated_container = self.load(context,
                                      container["name"],
                                      container.get("namespace"),
                                      container.get("data")
                                      )

        print("*"*80)

        print(container_to_update)
        print(updated_container)
        print("*" * 80)

        if update_and_replace:

            success = harmony.send(
                {
                    "function": f"PypeHarmony.Loaders.{self_name}.replaceNode",
                    "args": [updated_container, container_to_update]
                }
            )["result"]

            if success:
                # now remove old the container from scene data
                harmony.remove(container_to_update)

    def remove(self, container):
        """Remove container.

        Args:
            container (dict): container definition.

        """
        node = harmony.find_node_by_name(container["name"], "GROUP")
        harmony.send(
            {"function": "PypeHarmony.deleteNode", "args": [node]}
        )

    def switch(self, container, representation):
        """Switch representation containers."""
        self.update(container, representation)

    def _set_green(self, node):
        """Set node color to green `rgba(0, 255, 0, 255)`."""
        harmony.send(
            {
                "function": "PypeHarmony.setColor",
                "args": [node, [0, 255, 0, 255]]
            })

    def _set_red(self, node):
        """Set node color to red `rgba(255, 0, 0, 255)`."""
        harmony.send(
            {
                "function": "PypeHarmony.setColor",
                "args": [node, [255, 0, 0, 255]]
            })
