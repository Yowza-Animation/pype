from avalon import api, harmony

sig = harmony.signature()

import_audio = """
function %s(args)
{
    var uniqueColumnName = AvalonHarmony.getUniqueColumnName(args[0]);
    column.add(uniqueColumnName , "SOUND");
    column.importSound(uniqueColumnName, 1, args[1]);
}
%s
""" % (sig, sig)


class ImportAudioLoader(api.Loader):
    """Import audio."""

    families = ["shot", "audio"]
    representations = ["wav"]
    label = "Import Audio"
    icon = "file-audio-o"

    def load(self, context, name=None, namespace=None, data=None):
        wav_file = api.get_representation_path(context["representation"])
        harmony.send(
            {
                "function": import_audio,
                "args": [context["subset"]["name"], wav_file]
            }
        )

        subset_name = context["subset"]["name"]

        return harmony.containerise(
            subset_name,
            namespace,
            subset_name,
            context,
            self.__class__.__name__
        )

    def update(self, container, representation):
        pass

    def remove(self, container):
        pass
