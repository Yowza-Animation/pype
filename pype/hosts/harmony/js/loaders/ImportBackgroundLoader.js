/* global PypeHarmony:writable, include */
// ***************************************************************************
// *                        ImportBackgroundLoader                           *
// ***************************************************************************


// check if PypeHarmony is defined and if not, load it.
if (typeof PypeHarmony !== 'undefined') {
    var PYPE_HARMONY_JS = System.getenv('PYPE_HARMONY_JS');
    include(PYPE_HARMONY_JS + '/PypeHarmony.js');
}


/**
 * @namespace
 * @classdesc Background Image loader JS code.
 */
var ImportBackgroundLoader = function() {};

ImportBackgroundLoader.prototype.import_files = function(args)
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

    PNGTransparencyMode = 0; // Premultiplied wih Black
    TGATransparencyMode = 0; // Premultiplied wih Black
    SGITransparencyMode = 0; // Premultiplied wih Black
    LayeredPSDTransparencyMode = 1; // Straight
    FlatPSDTransparencyMode = 2; // Premultiplied wih White

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
        // Skip unknown files
        return null; // no read to add.
    }

    var uniqueColumnName = AvalonHarmony.getUniqueColumnName(name);
    column.add(uniqueColumnName , "DRAWING");
    column.setElementIdOfDrawing(uniqueColumnName, elemId);

    var read = node.add(root, name, "READ", 0, 0, 0);

    var transparencyAttr = node.getAttr(
        read, frame.current(), "READ_TRANSPARENCY"
    );
    transparencyAttr.setValue(true);

    var opacityAttr = node.getAttr(read, frame.current(), "OPACITY");
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

// add self to Pype Loaders
PypeHarmony.Loaders.ImportBackgroundLoader = new ImportBackgroundLoader();
