# -*- coding: utf-8 -*-
"""Extract template."""
import os

import pype.hosts.harmony
import shutil

import pype.api
from avalon import harmony
import pype.hosts.harmony


class ExtractTemplate(pype.api.Extractor):
    """Extract the connected nodes to the composite instance."""

    label = "Extract Template"
    hosts = ["harmony"]
    families = ["scene"]

    def process(self, instance):
        """Plugin entry point."""
        staging_dir = self.staging_dir(instance)
        filepath = os.path.join(staging_dir, f"{instance.name}.tpl")

        self.log.info(f"Outputting template to {staging_dir}")

        dependencies = []
        self.get_dependencies(instance[0], dependencies)

        self.log.info("dependencies: {0}".format(dependencies))

        current_group = harmony.send({
            "function": "AvalonHarmony.getCurrentGroup",
            "args": []})["result"]

        # Get backdrops.
        backdrops = {}
        for dependency in dependencies:
            for backdrop in self.get_backdrops(dependency, current_group):
                backdrops[backdrop["title"]["text"]] = backdrop

        unique_backdrops = [backdrops[x] for x in set(backdrops.keys())]

        # Get non-connected nodes within backdrops.
        all_nodes = instance.context.data.get("allNodes");

        self.log.info("all_nodes: {0}".format(all_nodes))

        for node in [x for x in all_nodes if x not in dependencies]:
            within_unique_backdrops = bool(
                [x for x in self.get_backdrops(node, current_group) if x in unique_backdrops]
            )
            if within_unique_backdrops:
                dependencies.append(node)

        self.log.info("dependencies: {0}".format(dependencies))

        # Make sure we dont export the instance node.
        if instance[0] in dependencies:
            dependencies.remove(instance[0])

        self_name = self.__class__.__name__

        export_result = harmony.send({
            "function": f"PypeHarmony.Publish.{self_name}.exportTemplate",
            "args": [unique_backdrops, dependencies, filepath]})["result"]

        # Prep representation.
        os.chdir(staging_dir)
        shutil.make_archive(
            f"{instance.name}",
            "zip",
            os.path.join(staging_dir, f"{instance.name}.tpl")
        )

        representation = {
            "name": "tpl",
            "ext": "zip",
            "files": f"{instance.name}.zip",
            "stagingDir": staging_dir
        }

        self.log.info(instance.data.get("representations"))
        if instance.data.get("representations"):
            instance.data["representations"].extend([representation])
        else:
            instance.data["representations"] = [representation]

        instance.data["version_name"] = "{}_{}".format(
            instance.data["subset"], os.environ["AVALON_TASK"])

    def get_backdrops(self, node: str, group: str) -> list:
        """Get backdrops for the node.

        Args:
            node (str): Node path.

        Returns:
            list: list of Backdrops.

        """
        self_name = self.__class__.__name__
        return harmony.send({
            "function": f"PypeHarmony.Publish.{self_name}.getBackdropsByNode",
            "args": [node, group]})["result"]

    def get_dependencies(
            self, node: str, dependencies: list = None) -> list:
        """Get node dependencies.

        This will return recursive dependency list of given node.

        Args:
            node (str): Path to the node.
            dependencies (list, optional): existing dependency list.

        Returns:
            list: List of dependent nodes.

        """
        current_dependencies = harmony.send(
            {
                "function": "PypeHarmony.getDependencies",
                "args": node}
        )["result"]

        for dependency in current_dependencies:
            if not dependency:
                continue

            if dependency in dependencies:
                continue

            dependencies.append(dependency)

            self.get_dependencies(dependency, dependencies)
