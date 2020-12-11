/* global PypeHarmony:writable, include */
// ***************************************************************************
// *                        LoadTemplateLoader                               *
// ***************************************************************************


// check if PypeHarmony is defined and if not, load it.
if (typeof PypeHarmony !== 'undefined') {
    var PYPE_HARMONY_JS = System.getenv('PYPE_HARMONY_JS');
    include(PYPE_HARMONY_JS + '/PypeHarmony.js');
}


/**
 * @namespace
 * @classdesc Image Sequence loader JS code.
 */
var LoadTemplateLoader = function () {
};


/**
 * Load template as container.
 * @function
 * @param {array} args Arguments, see example.
 * @return {string} Name of container.
 *
 * @example
 * // arguments are in following order:
 * var args = [
 *  templatePath, // Path to tpl file.
 *  assetName,    // Asset name.
 *  subsetName,   // Subset name.
 *  groupId       // unique ID (uuid4)
 * ];
 */
LoadTemplateLoader.prototype.loadContainer = function (args) {
    var doc = $.scn;
    var templatePath = args[0];
    var assetName = args[1];
    var subset = args[2];
    var groupId = args[3];

    // First disable interactive color mode
    var prefs = $.app.preferences;
    prefs.COLOR_ENABLE_INTERACTIVE_COLOR_RECOVERY = false;

    var currentGroup = doc.$node(PypeHarmony.getCurrentGroup());

    // Get a unique iterative name for the container group
    var num = 0;
    var containerGroupName = '';
    do {
        containerGroupName = assetName + '_' + (num++) + '_' + subset;
    } while (currentGroup.getNodeByName(containerGroupName) != null);

    // import the template
    var tplNodes = currentGroup.importTemplate(templatePath);

    // Create the container group
    Action.perform("onActionSelCreateGroupWithComposite()", "Node View");

    var containerGroup = doc.$node(doc.selectedNodes[0]);
    containerGroup.name = containerGroupName;

    // Add uuid to attribute of the container group
    node.createDynamicAttr(containerGroup, 'STRING', 'uuid', 'uuid', false);
    node.setTextAttr(containerGroup, 'uuid', 1.0, groupId);

    return String(containerGroup.path);
};


/**
 * Replace existing node container.
 * @function
 * @param  {array}  args[0] {String} Harmony path to destination Node.
 args[1] {String} Harmony path to source Node.
 args[1] {boolean} Rename the replaced container
 * @return {boolean}             Success
 * @todo   This is work in progress.
 */
LoadTemplateLoader.prototype.replaceNode = function (args) {
    var doc = $.scn;
    var link, inNode, inPort, outPort, outNode, success;

    srcNode = doc.$node(args[0]);
    dstNode = doc.$node(args[1]);
    rename_container = args[2];

    const dstNodeName = new String(dstNode.name);
    $.beginUndo();

    // Move this container to the same group as the container it is replacing
    if (srcNode.group.path != dstNode.group.path) {
        srcNode.moveToGroup(dstNode);
    }

    // Connect all the old node's in links to the new node
    var inLinks = dstNode.getInLinks();

    for (var l in inLinks) {
        if (Object.prototype.hasOwnProperty.call(inLinks, l)) {
            link = inLinks[l];
            inPort = Number(link.inPort);
            outPort = Number(link.outPort);
            outNode = link.outNode;
            success = srcNode.linkInNode(outNode, inPort, outPort);
            if (success) {
                $.log('Successfully connected ' + outNode + ' : ' +
                    outPort + ' -> ' + srcNode + ' : ' + inPort);
            } else {
                $.alert('Failed to connect ' + outNode + ' : ' +
                    outPort + ' -> ' + srcNode + ' : ' + inPort);
            }
        }
    }

    // Connect all the old node's out links to the new node
    var outLinks = dstNode.getOutLinks();

    for (l in outLinks) {
        if (Object.prototype.hasOwnProperty.call(outLinks, l)) {
            link = outLinks[l];
            inPort = Number(link.inPort);
            outPort = Number(link.outPort);
            inNode = link.inNode;
            // first we must disconnect the port from the node being
            // replaced to this links inNode port
            inNode.unlinkInPort(inPort);
            success = srcNode.linkOutNode(inNode, outPort, inPort);

            if (success) {
                $.log('Successfully connected ' + inNode + ' : ' +
                    inPort + ' <- ' + srcNode + ' : ' + outPort);
            } else {
                if (inNode.type == 'MultiLayerWrite') {
                    $.log('Attempting standard api to connect the nodes...');
                    success = node.link(
                        srcNode, outPort, inNode,
                        inPort, node.numberOfInputPorts(inNode) + 1);
                    if (success) {
                        $.log('Successfully connected ' + inNode + ' : ' +
                            inPort + ' <- ' + srcNode + ' : ' + outPort);
                    }
                }
            }

            if (!success) {
                $.alert('Failed to connect ' + inNode + ' : ' +
                    inPort + ' <- ' + srcNode + ' : ' + outPort);
            }
        }
    }

    // Place the replacement node in the same coords
    srcNode.x = dstNode.x;
    srcNode.y = dstNode.y;

    // Link all the attrs
    var _attributes = dstNode.attributes;

    for (var i in _attributes) {
        var _clonedAttribute = srcNode.getAttributeByName(_attributes[i].keyword);
        _clonedAttribute.setToAttributeValue(_attributes[i]);
        $.log(_clonedAttribute.column == null);
    }

    // Link all palettes
    var palettes = dstNode.palettes;
    for (var i in palettes) {
        srcNode.linkPalette(palettes[i]);
    }

    // Remove the old container from the scene data
    var metadata = scene.metadata('avalon');
    if (metadata) {
        metadata = JSON.parse(metadata.value);
        delete metadata[dstNode.path]
        scene.setMetadata({
            'name': 'avalon',
            'type': 'string',
            'creator': 'Avalon',
            'version': '1.0',
            'value': JSON.stringify(metadata)
        });
    };

    // Delete the original node
    dstNode.remove(false, false);
    if (rename_container) {
        srcNode.name = dstNodeName;
    }
    $.endUndo();
    return true;
};


LoadTemplateLoader.prototype.askForColumnsUpdate = function () {
    // Ask user if they want to also update columns and linked attributes here

    msg = "Choose \"Yes\" to reconnect all \n" +
        "ins/outs, attributes, and columns? \n" +
        "If you choose \"No\", the Version will only be loaded.";

    title = "Update & Replace";

	msgBox = new QMessageBox(
		QMessageBox.question,
		title,
		msg,
		QMessageBox.Yes
	);

	msgBox.addButton(QMessageBox.No);

	msgBox.setWindowFlags(
		msgBox.windowFlags() | Qt.WindowStaysOnTopHint
	);

	screen_size = new QDesktopWidget().screenGeometry(0);

	msgBox.move(
		screen_size.width()/2 +150,
		screen_size.height()/2 -900
	);

	if(msgBox.exec() == QMessageBox.Yes){
		return true;
	};
	return false;
};

// add self to Pype Loaders
PypeHarmony.Loaders.LoadTemplateLoader = new LoadTemplateLoader();