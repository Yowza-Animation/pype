/* global PypeHarmony:writable, include */
// ***************************************************************************
// *                        CollectPalettes                                  *
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
var CollectPalettes = function() {};

CollectPalettes.prototype.getPalettes = function(nodes) {

    // var palette_list = PaletteObjectManager.getScenePaletteList();
    //
    // var palettes = {};
    // for(var i=0; i < palette_list.numPalettes; ++i) {
    //     var palette = palette_list.getPaletteByIndex(i);
    //     palettes[palette.getName()] = palette.id;
    // }

    // Only collect palettes which are in use by a drawing.
    var doc = $.scene;
    var palettes = {};
    var drawings = new $.oList(
        doc.root.subNodes(true)).filterByProperty("type", "READ")

    for (i in drawings){
        var d = drawings[i]
        var used_palettes = d.getUsedPalettes()
        for (p in used_palettes){
            var palette = used_palettes[p]
            palettes[palette.name] = palette.id;
        }

    }
    return palettes;
};

// add self to Pype Loaders
PypeHarmony.Publish.CollectPalettes = new CollectPalettes();
