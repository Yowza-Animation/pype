/* global PypeHarmony:writable, include */
// ***************************************************************************
// *                        TemplateLoader                                   *
// ***************************************************************************


// check if PypeHarmony is defined and if not, load it.
if (typeof PypeHarmony !== 'undefined') {
    var PYPE_HARMONY_JS = System.getenv('PYPE_HARMONY_JS');
    include(PYPE_HARMONY_JS + '/pype_harmony.js');
}


/**
 * @namespace
 * @classdesc Image Sequence loader JS code.
 */
var TemplateLoader = function() {};


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
TemplateLoader.prototype.loadContainer = function(args) {
    MessageLog.trace("000000000")
    var doc = $.scn;
    MessageLog.trace("000000001")
    var templatePath = args[0];
    MessageLog.trace("000000002")
    var assetName = args[1];
    MessageLog.trace("000000003")
    var subset = args[2];
    MessageLog.trace("000000004")
    var groupId = args[3];
    MessageLog.trace("000000005")
    // Get the current group
    // Below does not work when the Node View is docked
    // var nodeViewWidget = $.app.getWidgetByName('Node View');
    // if (!nodeViewWidget) {
    //     $.alert('You must have a Node View open!', 'No Node View!', 'OK!');
    //     return;
    // }
    //
    // nodeViewWidget.setFocus();
    MessageLog.trace("1")
    nodeView = '';
    for (i = 0; i < 200; i++) {
        nodeView = 'View' + (i);
        if (view.type(nodeView) == 'Node View') {
            break;
        }
    }
    MessageLog.trace("2")
    if (!nodeView) {
        $.alert('You must have a Node View open!',
                'No Node View is currently open!\n'+
                'Open a Node View and Try Again.',
                'OK!');
        return;
    }
    MessageLog.trace("3")
    var currentGroup;
    if (!nodeView) {
        currentGroup = doc.root;
    } else {
        currentGroup = doc.$node(view.group(nodeView));
    }
    MessageLog.trace("4")
    // Get a unique iterative name for the container group
    var num = 0;
    var containerGroupName = '';
    do {
        containerGroupName = assetName + '_' + (num++) + '_' + subset;
    } while (currentGroup.getNodeByName(containerGroupName) != null);
    MessageLog.trace("5")
    // import the template
    var tplNodes = currentGroup.importTemplate(templatePath);

    // Create the container group

    //@TODO: instead of using the Action to create the group,
    // this should be done manually since Harmony can be unreliable when it
    // comes to always giving the selection of nodes after an Action

    // var containerGroup = currentGroup.addGroup(
    //     containerGroupName, false, false, tplNodes);

    Action.perform("onActionSelCreateGroupWithComposite()", "Node View");
    MessageLog.trace("6")
    var containerGroup = doc.$node(doc.selectedNodes[0]);
    containerGroup.name = containerGroupName;
    MessageLog.trace("7")
    // Add uuid to attribute of the container group
    node.createDynamicAttr(containerGroup, 'STRING', 'uuid', 'uuid', false);
    node.setTextAttr(containerGroup, 'uuid', 1.0, groupId);

    return String(containerGroup.path);
};


/**
 * Replace existing node container.
 * @function
 * @param  {array}  args[0] Harmony path to destination Node.
                    args[1] Harmony path to source Node.
 * @return {boolean}             Success
 * @todo   This is work in progress.
 */
TemplateLoader.prototype.replaceNode = function(args)
{
    var doc = $.scn;
    var link, inNode, inPort, outPort, outNode, success;

    srcNode = doc.$node(args[0]);

    dstNode = doc.$node(args[1]);
    const dstNodeName = new String(dstNode.name);

    MessageLog.trace(srcNode);
    MessageLog.trace(dstNode);

    $.beginUndo();

    // Move this container to the same group as the container it is replacing
    if (srcNode.group.path != dstNode.group.path)
    {
        srcNode.moveToGroup(dstNode);
    }

    var inLinks = dstNode.getInLinks();

    for (var l in inLinks)
    {
        if (Object.prototype.hasOwnProperty.call(inLinks, l))
        {
            link = inLinks[l];
            inPort = Number(link.inPort);
            outPort = Number(link.outPort);
            outNode = link.outNode;
            success = srcNode.linkInNode(outNode, inPort, outPort);
            if (success)
            {
                $.log('Successfully connected ' + outNode + ' : ' +
                    outPort + ' -> ' + srcNode + ' : ' + inPort);
            }
            else
            {
                $.alert('Failed to connect ' + outNode + ' : ' +
                    outPort + ' -> ' + srcNode + ' : ' + inPort);
            }
        }
    }

    var outLinks = dstNode.getOutLinks();

    for (l in outLinks)
    {
        if (Object.prototype.hasOwnProperty.call(outLinks, l))
        {
            link = outLinks[l];
            inPort = Number(link.inPort);
            outPort = Number(link.outPort);
            inNode = link.inNode;
            // first we must disconnect the port from the node being
            // replaced to this links inNode port
            inNode.unlinkInPort(inPort);
            success = srcNode.linkOutNode(inNode, outPort, inPort);

            if (success)
            {
                $.log('Successfully connected ' + inNode + ' : ' +
                    inPort + ' <- ' + srcNode + ' : ' + outPort);
            }
            else
            {
                if (inNode.type == 'MultiLayerWrite')
                {
                    $.log('Attempting standard api to connect the nodes...');
                    success = node.link(
                        srcNode, outPort, inNode,
                        inPort, node.numberOfInputPorts(inNode) + 1);
                    if (success)
                    {
                        $.log('Successfully connected ' + inNode + ' : ' +
                            inPort + ' <- ' + srcNode + ' : ' + outPort);
                    }
                }
            }

            if (!success)
            {
                $.alert('Failed to connect ' + inNode + ' : ' +
                    inPort + ' <- ' + srcNode + ' : ' + outPort);
                $.endUndo();
                return false;
            }
        }
    }

    dstNode.remove(false, false);
    srcNode.name = dstNodeName;
    $.endUndo();
    return true;
};


TemplateLoader.prototype.askForColumnsUpdate = function() {
    // Ask user if they want to also update columns and
    // linked attributes here
    return ($.confirm(
        'Would you like to update in place and reconnect all \n' +
      'ins/outs, attributes, and columns?',
        'Update & Replace?\n' +
      'If you choose No, the version will only be loaded.',
        'Yes',
        'No'));
};

// add self to Pype Loaders
PypeHarmony.Loaders.TemplateLoader = new TemplateLoader();
