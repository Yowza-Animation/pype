import json
import os
import uuid

from avalon import api, harmony

import pype.lib
import psd_tools
import PIL

copy_files = """function copyFile(srcFilename, dstFilename)
{
    var srcFile = new PermanentFile(srcFilename);
    var dstFile = new PermanentFile(dstFilename);
    srcFile.copy(dstFile);
}
"""

import_files = """var PNGTransparencyMode = 1; //Premultiplied wih Black
var TGATransparencyMode = 0; //Premultiplied wih Black
var SGITransparencyMode = 0; //Premultiplied wih Black
var LayeredPSDTransparencyMode = 1; //Straight
var FlatPSDTransparencyMode = 2; //Premultiplied wih White

 
function import_files(args)
{
    var root = args[0];
    var files = args[1];
    var name = args[2];
    var start_frame = args[3];

    var vectorFormat = null;
    var extension = null;
    var filename = files[0];

    var pos = filename.lastIndexOf(".");
    if( pos < 0 )
        return null;

    extension = filename.substr(pos+1).toLowerCase();

    if(extension == "jpeg")
        extension = "jpg";
    if(extension == "tvg")
    {
        vectorFormat = "TVG"
        extension ="SCAN"; // element.add() will use this.
    }

    var elemId = element.add(
        name,
        "BW",
        scene.numberOfUnitsZ(),
        extension.toUpperCase(),
        vectorFormat
    );
    if (elemId == -1)
    {
        // hum, unknown file type most likely -- let's skip it.
        return null; // no read to add.
    }

    var uniqueColumnName = AvalonHarmony.getUniqueColumnName(name);
    column.add(uniqueColumnName , "DRAWING");
    column.setElementIdOfDrawing(uniqueColumnName, elemId);

    var read = node.add(root, name, "READ", 0, 0, 0);
    var transparencyAttr = node.getAttr(
        read, frame.current(), "READ_TRANSPARENCY"
    );
    var opacityAttr = node.getAttr(read, frame.current(), "OPACITY");
    transparencyAttr.setValue(true);
    opacityAttr.setValue(true);

    var alignmentAttr = node.getAttr(read, frame.current(), "ALIGNMENT_RULE");
    alignmentAttr.setValue("ASIS");

    var transparencyModeAttr = node.getAttr(
        read, frame.current(), "applyMatteToColor"
    );
    if (extension == "png")
        transparencyModeAttr.setValue(PNGTransparencyMode);
    if (extension == "tga")
        transparencyModeAttr.setValue(TGATransparencyMode);
    if (extension == "sgi")
        transparencyModeAttr.setValue(SGITransparencyMode);
    if (extension == "psd")
        transparencyModeAttr.setValue(FlatPSDTransparencyMode);
    if (extension == "jpg")
        transparencyModeAttr.setValue(LayeredPSDTransparencyMode);

    node.linkAttr(read, "DRAWING.ELEMENT", uniqueColumnName);

    if (files.length == 1)
    {
        // Create a drawing drawing, 'true' indicate that the file exists.
        Drawing.create(elemId, 1, true);
        // Get the actual path, in tmp folder.
        var drawingFilePath = Drawing.filename(elemId, "1");
        copyFile(files[0], drawingFilePath);
        // Expose the image for the entire frame range.
        for( var i =0; i <= frame.numberOf() - 1; ++i)
        {
            timing = start_frame + i
            column.setEntry(uniqueColumnName, 1, timing, "1");
        }
    } else {
        // Create a drawing for each file.
        for( var i =0; i <= files.length - 1; ++i)
        {
            timing = start_frame + i
            // Create a drawing drawing, 'true' indicate that the file exists.
            Drawing.create(elemId, timing, true);
            // Get the actual path, in tmp folder.
            var drawingFilePath = Drawing.filename(elemId, timing.toString());
            copyFile( files[i], drawingFilePath );

            column.setEntry(uniqueColumnName, 1, timing, timing.toString());
        }
    }

    var green_color = new ColorRGBA(0, 255, 0, 255);
    node.setColor(read, green_color);

    return read;
}
import_files
"""

replace_files = """var PNGTransparencyMode = 1; //Premultiplied wih Black
var TGATransparencyMode = 0; //Premultiplied wih Black
var SGITransparencyMode = 0; //Premultiplied wih Black
var LayeredPSDTransparencyMode = 1; //Straight
var FlatPSDTransparencyMode = 2; //Premultiplied wih White

function replace_files(args)
{
    var files = args[0];
    MessageLog.trace(files);
    MessageLog.trace(files.length);
    var _node = args[1];
    var start_frame = args[2];

    var _column = node.linkedColumn(_node, "DRAWING.ELEMENT");
    var elemId = column.getElementIdOfDrawing(_column);

    // Delete existing drawings.
    var timings = column.getDrawingTimings(_column);
    for( var i =0; i <= timings.length - 1; ++i)
    {
        column.deleteDrawingAt(_column, parseInt(timings[i]));
    }


    var filename = files[0];
    var pos = filename.lastIndexOf(".");
    if( pos < 0 )
        return null;
    var extension = filename.substr(pos+1).toLowerCase();

    if(extension == "jpeg")
        extension = "jpg";

    var transparencyModeAttr = node.getAttr(
        _node, frame.current(), "applyMatteToColor"
    );
    if (extension == "png")
        transparencyModeAttr.setValue(PNGTransparencyMode);
    if (extension == "tga")
        transparencyModeAttr.setValue(TGATransparencyMode);
    if (extension == "sgi")
        transparencyModeAttr.setValue(SGITransparencyMode);
    if (extension == "psd")
        transparencyModeAttr.setValue(FlatPSDTransparencyMode);
    if (extension == "jpg")
        transparencyModeAttr.setValue(LayeredPSDTransparencyMode);

    if (files.length == 1)
    {
        // Create a drawing drawing, 'true' indicate that the file exists.
        Drawing.create(elemId, 1, true);
        // Get the actual path, in tmp folder.
        var drawingFilePath = Drawing.filename(elemId, "1");
        copyFile(files[0], drawingFilePath);
        MessageLog.trace(files[0]);
        MessageLog.trace(drawingFilePath);
        // Expose the image for the entire frame range.
        for( var i =0; i <= frame.numberOf() - 1; ++i)
        {
            timing = start_frame + i
            column.setEntry(_column, 1, timing, "1");
        }
    } else {
        // Create a drawing for each file.
        for( var i =0; i <= files.length - 1; ++i)
        {
            timing = start_frame + i
            // Create a drawing drawing, 'true' indicate that the file exists.
            Drawing.create(elemId, timing, true);
            // Get the actual path, in tmp folder.
            var drawingFilePath = Drawing.filename(elemId, timing.toString());
            copyFile( files[i], drawingFilePath );

            column.setEntry(_column, 1, timing, timing.toString());
        }
    }

    var green_color = new ColorRGBA(0, 255, 0, 255);
    node.setColor(_node, green_color);
}
replace_files
"""


class ImportBackgroundLoader(api.Loader):
    """Load images
    Stores the imported asset in a container named after the asset.
    """
    families = ["scene", "render", "image", "background", "plate"]
    # @TODO: this action is WIP
    representations = []#"psd", "exr"]
    label = "Import to Layers"
    icon = "list-ol"

    def load(self, context, name=None, namespace=None, data=None):

        self_name = self.__class__.__name__

        # Create a uuid to be added to the container node's attrs
        group_id = "{}".format(uuid.uuid4())
        # Add this container's uuid to the scene data
        data["uuid"] = group_id

        layers = []

        data = self.get_image_layers(data, context)

        for child in data['children']:
            if child.get("filename"):
                layers.append(child["filename"])
            else:
                for layer in child['children']:
                    if layer.get("filename"):
                        layers.append(layer["filename"])

        bg_folder = os.path.dirname(self.fname)

        subset_name = context["subset"]["name"]

        current_group = harmony.send(
            {
                "function": "PypeHarmony.getCurrentGroup",
                "args": []
            }
        )["result"]

        container_node = harmony.send({
            "function": "AvalonHarmony.createNode",
            "args": [name, "GROUP", current_group, 0, 0, 0]})["result"]

        container_children = []

        for layer in sorted(layers):
            file_to_import = [
                os.path.join(bg_folder, layer).replace("\\", "/")
            ]

            read_node = harmony.send(
                {
                    "function": copy_files + import_files,
                    "args": ["Top", file_to_import, layer, 1]
                }
            )["result"]
            container_children.append(read_node)

        return harmony.containerise(
            name=subset_name,
            namespace=container_node,
            node=container_node,
            context=context,
            loader=self_name,
            suffix=None,
            data=data
        )

    def update(self, container, representation):

        context = representation["context"]
        layers = []
        data = container["data"]

        for child in data['children']:
            if child.get("filename"):
                print(child["filename"])
                layers.append(child["filename"])
            else:
                for layer in child['children']:
                    if layer.get("filename"):
                        print(layer["filename"])
                        layers.append(layer["filename"])

        bg_folder = os.path.dirname(self.fname)

        print(container)

        for layer in sorted(layers):
            file_to_import = [
                os.path.join(bg_folder, layer).replace("\\", "/")
            ]
            print(20 * "#")
            print(f"FILE TO REPLACE: {file_to_import}")
            print(f"LAYER: {layer}")
            node = harmony.find_node_by_name(layer, "READ")
            print(f"{node}")

            if node in container['nodes']:
                harmony.send(
                    {
                        "function": copy_files + replace_files,
                        "args": [file_to_import, node, 1]
                    }
                )
            else:
                read_node = harmony.send(
                    {
                        "function": copy_files + import_files,
                        "args": ["Top", file_to_import, layer, 1]
                    }
                )["result"]
                container['nodes'].append(read_node)

            # Colour node.
            sig = harmony.signature("set_color")
            func = """function %s(args){
                for( var i =0; i <= args[0].length - 1; ++i)
                {
                    var red_color = new ColorRGBA(255, 0, 0, 255);
                    var green_color = new ColorRGBA(0, 255, 0, 255);
                    if (args[1] == "red"){
                        node.setColor(args[0], red_color);
                    }
                    if (args[1] == "green"){
                        node.setColor(args[0], green_color);
                    }
                }
            }
            %s
            """ % (sig, sig)
            if pype.lib.is_latest(representation):
                harmony.send({"function": func, "args": [node, "green"]})
            else:
                harmony.send({"function": func, "args": [node, "red"]})

        harmony.imprint(
            container['name'], {"representation": str(representation["_id"]),
                                "nodes": container['nodes']}
        )

    def remove(self, container):
        for node in container.get("nodes"):
            func = """function deleteNode(_node)
            {
                node.deleteNode(_node, true, true);
            }
            deleteNode
            """
            harmony.send(
                {"function": func, "args": [node]}
            )
            harmony.imprint(container['name'], {}, remove=True)

    def switch(self, container, representation):
        self.update(container, representation)


    def get_image_layers(self, data, context):

        path = api.get_representation_path(context["representation"])

        dirname, basename = os.path.split(path)
        filename, ext = os.path.splitext(basename)

        if ext == ".psd":
            pass
        elif ext == ".exr":
            pass
        elif ext == ".json":
            with open(path) as json_file:
                json_data = json.load(json_file)
                data.update(json_data)

        return data