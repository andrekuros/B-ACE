#if TOOLS
using Godot;

[Tool]
public partial class DebugGUISettingsInitializer : EditorPlugin
{
	const string DEBUGGUI_RES_PATH = "res://addons/DebugGUI/DebugGUI.cs";

    public override void _EnterTree()
    {
        DebugGUI.Settings.Init();
		AddAutoloadSingleton(nameof(DebugGUI), DEBUGGUI_RES_PATH);
    }

	public override void _ExitTree()
	{
		RemoveAutoloadSingleton(nameof(DebugGUI));
    }
}
#endif
