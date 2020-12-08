/* global PypeHarmony:writable, include */
// ***************************************************************************
// *                           ExtractTemplate                               *
// ***************************************************************************


// check if PypeHarmony is defined and if not, load it.
if (typeof PypeHarmony !== 'undefined') {
    var PYPE_HARMONY_JS = System.getenv('PYPE_HARMONY_JS');
    include(PYPE_HARMONY_JS + '/PypeHarmony.js');
}


/**
 * @namespace
 * @classdesc Code for extracting templates.
 */
var ExtractTemplate = function() {};

/**
 * Get backdrops for given node.
 * @function
 * @param   {string} _node Node path to probe for backdrops.
 * @return  {array} list of backdrops.
 */
ExtractTemplate.prototype.getBackdropsByNode = function(_node) {
    doc = $.scn;
    var backdrops = Backdrop.backdrops(doc.$node(_node).group.path);
    var valid_backdrops = [];
    for(var i=0; i<backdrops.length; i++)
    {
        var position = backdrops[i].position;

        var x_valid = false;
        var node_x = node.coordX(_node);
        if (position.x < node_x && node_x < (position.x + position.w)){
            x_valid = true;
        }

        var y_valid = false;
        var node_y = node.coordY(_node);
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
