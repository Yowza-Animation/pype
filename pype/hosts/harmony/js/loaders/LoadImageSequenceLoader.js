/* global PypeHarmony:writable, include */
// ***************************************************************************
// *                        LoadImageSequenceLoader                          *
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
var LoadImageSequenceLoader = function() {};


/**
 * Load file sequences into Harmony.
 * @function
 * @param  {object}  args  Arguments for import, see Example.
 * @return {string}  Read node name
 *
 * @example
 * // Agrguments are in following order:
 * var args = [
 *    files, // Files in file sequences.
 *    asset, // Asset name.
 *    subset, // Subset name.
 *    startFrame, // Sequence starting frame.
 *    groupId // Unique group ID (uuid4).
 * ];
 */
LoadImageSequenceLoader.prototype.loadFiles = function(args) {
    var doc = $.scn;
    var files = args[0];
    var asset = args[1];
    var subset = args[2];
    var startFrame = args[3];
    var groupId = args[4];
    var vectorFormat = null;
    var extension = null;
    var filename = files[0];
    var pos = filename.lastIndexOf('.');
    if (pos < 0) {
        return null;
    }

    PNGTransparencyMode = 0; // Premultiplied wih Black
    TGATransparencyMode = 0; // Premultiplied wih Black
    SGITransparencyMode = 0; // Premultiplied wih Black
    LayeredPSDTransparencyMode = 1; // Straight
    FlatPSDTransparencyMode = 2; // Premultiplied wih White

    var currentGroup = PypeHarmony.getCurrentGroup()

    // Get a unique iterative name for the container read node
    var num = 0;
    var name = '';
    do {
        name = asset + '_' + (num++) + '_' + subset;
    } while (currentGroup.getNodeByName(name) != null);

    extension = filename.substr(pos+1).toLowerCase();
    if (extension == 'jpeg') {
        extension = 'jpg';
    }

    if (extension == 'tvg') {
        vectorFormat = 'TVG';
        extension ='SCAN'; // element.add() will use this.
    }

    var elemId = element.add(
        name,
        'BW',
        scene.numberOfUnitsZ(),
        extension.toUpperCase(),
        vectorFormat
    );

    if (elemId == -1) {
        // hum, unknown file type most likely -- let's skip it.
        return null; // no read to add.
    }

    var uniqueColumnName = AvalonHarmony.getUniqueColumnName(name);
    column.add(uniqueColumnName, 'DRAWING');
    column.setElementIdOfDrawing(uniqueColumnName, elemId);

    var read = node.add(currentGroup, name, 'READ', 0, 0, 0);

    var transparencyAttr = node.getAttr(
        read, frame.current(), 'READ_TRANSPARENCY'
    );
    transparencyAttr.setValue(true);

    var opacityAttr = node.getAttr(read, frame.current(), 'OPACITY');
    opacityAttr.setValue(true);

    var alignmentAttr = node.getAttr(read, frame.current(), 'ALIGNMENT_RULE');
    alignmentAttr.setValue('ASIS');

    var transparencyModeAttr = node.getAttr(
        read, frame.current(), 'applyMatteToColor'
    );

    if (extension === 'png') {
        transparencyModeAttr.setValue(PNGTransparencyMode);
    }
    if (extension === 'tga') {
        transparencyModeAttr.setValue(TGATransparencyMode);
    }
    if (extension === 'sgi') {
        transparencyModeAttr.setValue(SGITransparencyMode);
    }
    if (extension === 'psd') {
        transparencyModeAttr.setValue(FlatPSDTransparencyMode);
    }
    if (extension === 'jpg') {
        transparencyModeAttr.setValue(LayeredPSDTransparencyMode);
    }

    var drawingFilePath;
    var timing;

    node.linkAttr(read, 'DRAWING.ELEMENT', uniqueColumnName);

    if (files.length === 1) {

        // Create a drawing drawing, 'true' indicate that the file exists.
        // Drawing.create(elemId, 1, true);

        // Get the actual path, in tmp folder.
        //drawingFilePath = Drawing.filename(elemId, '1');
        node.setAttr(
        read, frame.current(), 'applyMatteToColor'
         );
        // Expose the image for the entire frame range.
        for (var i =0; i <= frame.numberOf() - 1; ++i) {
            timing = startFrame + i;
            column.setEntry(uniqueColumnName, 1, timing, '1');
        }

    } else {

        // Create a drawing for each file.
        for (var j =0; j <= files.length - 1; ++j) {
            timing = startFrame + j;
            // Create a drawing drawing, 'true' indicate that the file exists.
            //Drawing.create(elemId, timing, true);
            // Get the actual path, in tmp folder.
            //drawingFilePath = Drawing.filename(elemId, timing.toString());

            column.setEntry(uniqueColumnName, 1, timing, timing.toString());

        }
    }

    var greenColor = new ColorRGBA(0, 255, 0, 255);
    node.setColor(read, greenColor);

    // Add uuid to attribute of the container read node
    node.createDynamicAttr(read, 'STRING', 'uuid', 'uuid', false);
    node.setTextAttr(read, 'uuid', 1.0, groupId);
    MessageLog.trace("6")
    return read;
};

LoadImageSequenceLoader.prototype.updateFiles = function(args) {


}
// add self to Pype Loaders
PypeHarmony.Loaders.LoadImageSequenceLoader = new LoadImageSequenceLoader();
