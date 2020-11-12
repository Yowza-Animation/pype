/* global PypeHarmony:writable, include */
// ***************************************************************************
// *                           ExtractTemplate                               *
// ***************************************************************************


// check if PypeHarmony is defined and if not, load it.
if (typeof PypeHarmony !== 'undefined') {
    var PYPE_HARMONY_JS = System.getenv('PYPE_HARMONY_JS');
    include(PYPE_HARMONY_JS + '/pype_harmony.js');
}


/**
 * @namespace
 * @classdesc Code for extracting templates.
 */
var ExtractTemplate = function() {};


ExtractTemplate.prototype.exportTemplate = function(args) {
    $.beginUndo();
    try {
        var doc = $.scene;
        var backdrops = args[0];
        var _nodes = args[1].map(function (x) {
            return doc.$node(x)
        });
        var filename = args[2];
        var folder = args[3];
        var _refNode = doc.$node(_nodes[0])
        var currentGroup = _refNode.group
        const templateGroup = currentGroup.addGroup("temp_group", false, false)

        doc.selectedNodes = _nodes;

        Action.perform("copy()", "Node View");
        doc.selectedNodes = [templateGroup];
        Action.perform("onActionEnterGroup()", "Node View");
        Action.perform("paste()", "Node View");

        // We need to determine the offset deltas
        var _copiedRefNode = doc.$node(
            templateGroup.path + "/" + _refNode.name);

        var deltaX = _refNode.x - _copiedRefNode.x;
        var deltaY = _refNode.y - _copiedRefNode.y;

        // Recreate backdrops in group...
        // @TODO: eventually this should be in callback which does this in a batch
        //  subprocess to the saved tpl in the temp dir.
        for (var i = 0; i < backdrops.length; i++) {
            var backdropData = backdrops[i]
            var newData = JSON.parse(JSON.stringify(backdropData));
            MessageLog.trace(backdropData);

            // Now fix the backdrop pos with the delta offsets
            newData["position"]["x"] = backdropData["position"]["x"] + deltaX;
            newData["position"]["y"] = backdropData["position"]["y"] + deltaY;
            Backdrop.addBackdrop(templateGroup, newData);
        }

        Action.perform("selectAll()", "Node View");
        doc.selectedNodes = templateGroup.nodes
        MessageLog.trace("****************************************************")
        MessageLog.trace(filename)
        MessageLog.trace(folder)
        MessageLog.trace(doc.selectedNodes)
        MessageLog.trace("****************************************************")
        copyPaste.createTemplateFromSelection(filename, folder);
        // Unfocus the group in Node view, delete all nodes and backdrops
        // created during the process.
        Action.perform("onActionUpToParent()", "Node View");
        node.deleteNode(templateGroup, true, true);
    }
    catch(err) {
        $.endUndo();
        MessageLog.trace(err);
        return false;
    }
    $.endUndo();
    return true;
};


/**
 * Get backdrops for given node.
 * @function
 * @param   {string} probeNode Node path to probe for backdrops.
 * @return  {array} list of backdrops.
 */
ExtractTemplate.prototype.getBackdropsByNode = function(probeNode, groupPath) {
    var backdrops = Backdrop.backdrops(groupPath);
    var valid_backdrops = [];
    for(var i=0; i<backdrops.length; i++)
    {
        var position = backdrops[i].position;

        var x_valid = false;
        var node_x = node.coordX(probeNode);
        if (position.x < node_x && node_x < (position.x + position.w)){
            x_valid = true;
        }

        var y_valid = false;
        var node_y = node.coordY(probeNode);
        if (position.y < node_y && node_y < (position.y + position.h)){
            y_valid = true;
        }

        if (x_valid && y_valid){
            valid_backdrops.push(backdrops[i]);
        }
    }
    return valid_backdrops;
};

// add self to Pype Loaders
PypeHarmony.Publish.ExtractTemplate = new ExtractTemplate();
