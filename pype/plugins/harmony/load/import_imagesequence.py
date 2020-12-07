# -*- coding: utf-8 -*-
"""Loader for image sequences."""
import os
import uuid
from pathlib import Path

import clique
from avalon import api, harmony

import pype.lib


class ImportImageSequenceLoader(api.Loader):
    """Import image sequences.

    Stores the imported asset in a container named after the asset.
    """

    families = ["scene", "shot", "render", "image", "plate", "reference"]
    representations = ["psd", "tga", "exr", "jpeg", "png", "jpg"]
    label = "Import Image / Image Sequence"
    icon = "arrow-down"
    order = 2

    def load(self, context, name=None, namespace=None, data=None):
        """Plugin entry point.

        Args:
            context (:class:`pyblish.api.Context`): Context.
            name (str, optional): Container name.
            namespace (str, optional): Container namespace.
            data (dict, optional): Additional data passed into loader.

        """

        asset_name = context["asset"]["name"]
        subset_name = context["subset"]["name"]

        fname = Path(self.fname)
        self_name = self.__class__.__name__
        collections, remainder = clique.assemble(
            os.listdir(fname.parent.as_posix())
        )
        files = []
        if collections:
            for f in list(collections[0]):
                files.append(fname.parent.joinpath(f).as_posix())
        else:
            files.append(fname.parent.joinpath(remainder[0]).as_posix())

        # Create a uuid to be added to the container node's attrs
        group_id = "{}".format(uuid.uuid4())
        # Add this container's uuid to the scene data
        data["uuid"] = group_id

        container_read = harmony.send(
            {
                "function": f"PypeHarmony.Loaders.{self_name}.importFiles",
                "args": [files, asset_name, subset_name, 1, group_id]
            }
        )["result"]

        container = harmony.containerise(
            name=name,
            namespace=container_read,
            node=container_read,
            context=context,
            loader=self_name,
            suffix=None,
            data=data
        )

        if container and self.notifier:
            self.notifier.show_notice(
                f"\"Loaded: \"<b>{asset_name}</b>\" -> Subset: <b>{subset_name}</b>\" "
                f"to: \"<b>{container_read}</b>\"",
                bg_color="#935BA2")

        return container

    def update(self, container, representation):
        """Update loaded containers.

        Args:
            container (dict): Container data.
            representation (dict): Representation data.

        """
        self_name = self.__class__.__name__
        node = container["objectName"]

        collections, remainder = clique.assemble(
            os.listdir(os.path.dirname(self.fname))
        )
        files = []
        if collections:
            for f in list(collections[0]):
                files.append(
                    os.path.join(
                        os.path.dirname(self.fname), f
                    ).replace("\\", "/")
                )
        else:
            files.append(
                os.path.join(
                    os.path.dirname(self.fname), remainder[0]
                ).replace("\\", "/")
            )

        success = harmony.send(
            {
                "function": f"PypeHarmony.Loaders.{self_name}.replaceFiles",
                "args": [files, node, 1]
            }
        )

        # Colour node.
        if pype.lib.is_latest(representation):
            harmony.send(
                {
                    "function": "PypeHarmony.setColor",
                    "args": [node, [0, 255, 0, 255]]
                })
        else:
            harmony.send(
                {
                    "function": "PypeHarmony.setColor",
                    "args": [node, [255, 0, 0, 255]]
                })

        harmony.imprint(
            node, {"representation": str(representation["_id"])}
        )

        return success

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
