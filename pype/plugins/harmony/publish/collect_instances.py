import json
import os

import pyblish.api
from avalon import harmony


class CollectInstances(pyblish.api.ContextPlugin):
    """Gather instances by nodes metadata.

    This collector takes into account assets that are associated with
    a composite node and marked with a unique identifier;

    Identifier:
        id (str): "pyblish.avalon.instance"
    """

    label = "Instances"
    order = pyblish.api.CollectorOrder
    hosts = ["harmony"]
    families_mapping = {
        "render": ["image", "review"],
        "scene": ["scene", "ftrack"],
        "palette": ["palette", "ftrack"]
    }

    pair_media = True

    def process(self, context):
        nodes = harmony.send(
            {"function": "node.subNodes", "args": ["Top"]}
        )["result"]

        for node in nodes:
            data = harmony.read(node)

            # Skip non-tagged nodes.
            if not data:
                continue

            # Skip containers.
            if "container" in data["id"]:
                continue

            instance = context.create_instance(node.split("/")[-1])
            instance.append(node)
            instance.data.update(data)
            instance.data["publish"] = harmony.send(
                {"function": "node.getEnable", "args": [node]}
            )["result"]
            instance.data["families"] = self.families_mapping[data["family"]]

            # If set in plugin, pair the scene Version in ftrack with
            # thumbnails and review media.
            if (self.pair_media and
                instance.data["family"] == "scene"):
                context.data["scene_instance"] = instance

            # Produce diagnostic message for any graphical
            # user interface interested in visualising it.
            self.log.info(
                "Found: \"{0}\": \n{1}".format(
                    instance.data["name"], json.dumps(instance.data, indent=4)
                )
            )

        self.process_status(context)

    def process_status(self, context):
        family = "request"
        task = "sendToRender"
        sanitized_task_name = task[0].upper() + task[1:]
        subset = "{}{}".format(family, sanitized_task_name)
        # base_name = os.path.basename(context.data["currentFile"])
        base_name = "sendToRender"

        # Create instance
        instance = context.create_instance(subset)
        instance.data.update({
            "subset": subset,
            "label": base_name,
            "name": base_name,
            "family": family,
            "families": ["request", "ftrack"],
            "representations": [],
            "asset": os.environ["AVALON_ASSET"],
        })

        self.log.info(
            "Created instance:\n" + json.dumps(
                instance.data, sort_keys=True, indent=4
            )
        )
