# -*- coding: utf-8 -*-
"""Loader for image sequences."""
import os
import uuid
from pathlib import Path

import clique

from avalon import api, harmony
from avalon.pipeline import get_representation_context
import pype.lib



class LoadImageSequence(api.Loader):
    """Load image sequences.

    Stores the imported asset in a container named after the asset.
    """

    families = ["scene", "shot", "render", "image", "plate", "reference"]
    representations = ["psd", "tga", "exr", "jpeg", "png", "jpg"]
    label = "Load Image / Image Sequence"
    icon = "gift"
    order = 0

    def load(self, context, name=None, namespace=None, data=None):
        """Plugin entry point.

        Args:
            context (:class:`pyblish.api.Context`): Context.
            name (str, optional): Container name.
            namespace (str, optional): Container namespace.
            data (dict, optional): Additional data passed into loader.

        """
        self_name = self.__class__.__name__

        path = api.get_representation_path(context["representation"])
        collections, remainder = clique.assemble(
            os.listdir(os.path.dirname(path))
        )

        asset = context["asset"]["name"]
        subset = context["subset"]["name"]

        # Create a uuid to be added to the container node's attrs
        group_id = "{}".format(uuid.uuid4())
        # Add this container's uuid to the scene data
        data["uuid"] = group_id

        container_read = harmony.send(
            {
                "function": f"PypeHarmony.Loaders.{self_name}.loadFiles",
                "args": [[path], asset, subset, 1, group_id]
            }
        )["result"]

        return harmony.containerise(
            name=name,
            namespace=container_read,
            node=container_read,
            context=context,
            loader=self_name,
            suffix=None,
            data=data
        )

    def update(self, container, representation):
        """Update loaded containers.

        Args:
            container (dict): Container data.
            representation (dict): Representation data.

        """
        self_name = self.__class__.__name__
        node = container["objectName"]
        context = get_representation_context(representation)
        asset = context["asset"]["name"]
        subset = context["subset"]["name"]

        collections, remainder = clique.assemble(
            os.listdir(os.path.dirname(self.fname))
        )

        updated_container = self.load(context,
                                      container["name"],
                                      container.get("namespace"),
                                      container.get("data")
                                      )

        # Colour node.
        if pype.lib.is_latest(representation):
            harmony.send(
                {
                    "function": "PypeHarmony.setColor",
                    "args": [updated_container, [0, 255, 0, 255]]
                })
        else:
            harmony.send(
                {
                    "function": "PypeHarmony.setColor",
                    "args": [updated_container, [255, 0, 0, 255]]
                })

        harmony.imprint(
            node, {"representation": str(representation["_id"])}
        )


    def remove(self, container):
        """Remove loaded container.

        Args:
            container (dict): Container data.

        """

        harmony.send(
            {"function": "PypeHarmony.deleteNode",
             "args": [container["objectName"]]}
        )

        harmony.imprint(container["objectName"], {}, remove=True)

    def switch(self, container, representation):
        """Switch loaded representations."""
        self.update(container, representation)