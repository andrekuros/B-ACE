using Godot;
using System.IO;
using WeavUtils;

public partial class DebugGUI : Control
{
    // Other scripts may use us right off the bat, so we make sure we initialize first
    public DebugGUI()
    {
        ProcessPhysicsPriority = int.MinValue;
    }

    static DebugGUI Instance;

    #region Settings

    public static class Settings
    {
        const string DEBUGGUI_SETTINGS_DIR = "DebugGUI/Settings/";

        public static void Init()
        {
            if (!Engine.IsEditorHint()) return;

            // Inits defaults or load current if present
            Load();

            ProjectSettings.SetSetting($"{DEBUGGUI_SETTINGS_DIR}{nameof(enableGraphs)}", enableGraphs);
            ProjectSettings.SetSetting($"{DEBUGGUI_SETTINGS_DIR}{nameof(enableLogs)}", enableLogs);

            ProjectSettings.SetSetting($"{DEBUGGUI_SETTINGS_DIR}{nameof(backgroundColor)}", backgroundColor);
            ProjectSettings.SetSetting($"{DEBUGGUI_SETTINGS_DIR}{nameof(scrubberColor)}", scrubberColor);
            ProjectSettings.SetSetting($"{DEBUGGUI_SETTINGS_DIR}{nameof(graphWidth)}", graphWidth);
            ProjectSettings.SetSetting($"{DEBUGGUI_SETTINGS_DIR}{nameof(graphHeight)}", graphHeight);
            ProjectSettings.SetSetting($"{DEBUGGUI_SETTINGS_DIR}{nameof(temporaryLogLifetime)}", temporaryLogLifetime);

            ProjectSettings.SetAsBasic($"{DEBUGGUI_SETTINGS_DIR}{nameof(enableGraphs)}", true);
            ProjectSettings.SetAsBasic($"{DEBUGGUI_SETTINGS_DIR}{nameof(enableLogs)}", true);

            ProjectSettings.SetAsBasic($"{DEBUGGUI_SETTINGS_DIR}{nameof(backgroundColor)}", true);
            ProjectSettings.SetAsBasic($"{DEBUGGUI_SETTINGS_DIR}{nameof(scrubberColor)}", true);
            ProjectSettings.SetAsBasic($"{DEBUGGUI_SETTINGS_DIR}{nameof(graphWidth)}", true);
            ProjectSettings.SetAsBasic($"{DEBUGGUI_SETTINGS_DIR}{nameof(graphHeight)}", true);
            ProjectSettings.SetAsBasic($"{DEBUGGUI_SETTINGS_DIR}{nameof(temporaryLogLifetime)}", true);

            var err = ProjectSettings.Save();
            if(err != Error.Ok)
            {
                GD.PrintErr(err);
            }
        }

        public static void Load()
        {
            textFont = ThemeDB.FallbackFont;

            enableGraphs = ProjectSettings.GetSetting(
                $"{DEBUGGUI_SETTINGS_DIR}{nameof(enableGraphs)}",
                true
            ).AsBool();
            enableLogs = ProjectSettings.GetSetting(
                $"{DEBUGGUI_SETTINGS_DIR}{nameof(enableLogs)}",
                true
            ).AsBool();

            backgroundColor = ProjectSettings.GetSetting(
                $"{DEBUGGUI_SETTINGS_DIR}{nameof(backgroundColor)}",
                new Color(0f, 0f, 0f, 0.7f)
            ).AsColor();
            scrubberColor = ProjectSettings.GetSetting(
                $"{DEBUGGUI_SETTINGS_DIR}{nameof(scrubberColor)}",
                new Color(1f, 1f, 0f, 0.7f)
            ).AsColor();
            graphWidth = ProjectSettings.GetSetting(
                $"{DEBUGGUI_SETTINGS_DIR}{nameof(graphWidth)}",
                300
            ).AsInt32();
            graphHeight = ProjectSettings.GetSetting(
                $"{DEBUGGUI_SETTINGS_DIR}{nameof(graphHeight)}",
                100
            ).AsInt32();
            temporaryLogLifetime = ProjectSettings.GetSetting(
                $"{DEBUGGUI_SETTINGS_DIR}{nameof(temporaryLogLifetime)}",
                5
            ).AsDouble();
        }

        public static bool enableGraphs;
        public static bool enableLogs;

        public static Color backgroundColor;
        public static Color scrubberColor;
        public static int graphWidth;
        public static int graphHeight;
        public static double temporaryLogLifetime;

        public static Font textFont;
    }

    #endregion

    #region Graph

    /// <summary>
    /// Set the properties of a graph.
    /// </summary>
    /// <param name="key">The graph's key</param>
    /// <param name="label">The graph's label</param>
    /// <param name="min">Value at the bottom of the graph box</param>
    /// <param name="max">Value at the top of the graph box</param>
    /// <param name="group">The graph's ordinal position on screen</param>
    /// <param name="color">The graph's color</param>
    public static void SetGraphProperties(object key, string label, float min, float max, int group, Color color, bool autoScale)
    {
        if (Settings.enableGraphs)
            Instance?.graphWindow.SetGraphProperties(key, label, min, max, group, color, autoScale);
    }

    /// <summary>
    /// Set the properties of a graph.
    /// </summary>
    /// <param name="key">The graph's key</param>
    /// <param name="label">The graph's label</param>
    /// <param name="min">Value at the bottom of the graph box</param>
    /// <param name="max">Value at the top of the graph box</param>
    /// <param name="group">The graph's ordinal position on screen</param>
    /// <param name="color">The graph's color</param>
    public static void SetGraphProperties(GodotObject key, string label, float min, float max, int group, Color color, bool autoScale)
    {
        SetGraphProperties((object)key, label, min, max, group, color, autoScale);
    }

    /// <summary>
    /// Add a data point to a graph.
    /// </summary>
    /// <param name="key">The graph's key</param>
    /// <param name="val">Value to be added</param>
    public static void Graph(object key, float val)
    {
        if (Settings.enableGraphs)
            Instance?.graphWindow.Graph(key, val);
    }

    /// <summary>
    /// Add a data point to a graph.
    /// </summary>
    /// <param name="key">The graph's key</param>
    /// <param name="val">Value to be added</param>
    public static void Graph(GodotObject key, float val)
    {
        Graph((object)key, val);
    }

    /// <summary>
    /// Remove an existing graph.
    /// </summary>
    /// <param name="key">The graph's key</param>
    public static void RemoveGraph(object key)
    {
        if (Settings.enableGraphs)
            Instance?.graphWindow.RemoveGraph(key);
    }

    /// <summary>
    /// Remove an existing graph.
    /// </summary>
    /// <param name="key">The graph's key</param>
    public static void RemoveGraph(GodotObject key)
    {
        RemoveGraph((object)key);
    }

    /// <summary>
    /// Resets a graph's data.
    /// </summary>
    /// <param name="key">The graph's key</param>
    public static void ClearGraph(object key)
    {
        if (Settings.enableGraphs)
            Instance?.graphWindow.ClearGraph(key);
    }

    /// <summary>
    /// Resets a graph's data.
    /// </summary>
    /// <param name="key">The graph's key</param>
    public static void ClearGraph(GodotObject key)
    {
        ClearGraph((object)key);
    }

    /// <summary>
    /// Export graphs to a json file. See path in log.
    /// </summary>
    public static void ExportGraphs()
    {
        if (Instance == null || !Settings.enableGraphs)
            return;

        string dateTimeStr = Time.GetDatetimeStringFromSystem().Replace(':', '-');
        string filename = $"debuggui_graph_export_{dateTimeStr}.json";

        using var file = Godot.FileAccess.Open(
            "user://" + filename,
            Godot.FileAccess.ModeFlags.Write
        );

        if (file == null)
        {
            GD.Print("DebugGUI graph export failed: " + Godot.FileAccess.GetOpenError());
        }
        else
        {
            file.StoreString(Instance.graphWindow.ToJson());
            GD.Print($"Wrote graph data to {Path.Combine(OS.GetUserDataDir(), filename)}");
        }
    }

    #endregion

    #region Log

    /// <summary>
    /// Create or update an existing message with the same key.
    /// </summary>
    public static void LogPersistent(object key, string message)
    {
        if (Settings.enableLogs)
            Instance?.logWindow.LogPersistent(key, message);
    }

    /// <summary>
    /// Create or update an existing message with the same key.
    /// </summary>
    public static void LogPersistent(GodotObject key, string message)
    {
        LogPersistent((object)key, message);
    }

    /// <summary>
    /// Remove an existing persistent message.
    /// </summary>
    public static void RemovePersistent(object key)
    {
        if (Settings.enableLogs)
            Instance?.logWindow.RemovePersistent(key);
    }

    /// <summary>
    /// Remove an existing persistent message.
    /// </summary>
    public static void RemovePersistent(GodotObject key)
    {
        RemovePersistent((object)key);
    }

    /// <summary>
    /// Clears all persistent logs.
    /// </summary>
    public static void ClearPersistent()
    {
        if (Settings.enableLogs)
            Instance?.logWindow.ClearPersistent();
    }

    /// <summary>
    /// Print a temporary message.
    /// </summary>
    public static void Log(object message)
    {
        Log(message.ToString());
    }

    /// <summary>
    /// Print a temporary message.
    /// </summary>
    public static void Log(string message)
    {
        if (Settings.enableLogs)
            Instance?.logWindow.Log(message);
    }

    #endregion

    /// <summary>
    /// Re-scans for DebugGUI attribute holders (i.e. [DebugGUIGraph] and [DebugGUIPrint])
    /// </summary>
    public static void ForceReinitializeAttributes()
    {
        if (Instance == null) return;

        Instance.graphWindow.ReinitializeAttributes();
        Instance.logWindow.ReinitializeAttributes();
    }

    GraphWindow graphWindow;
    LogWindow logWindow;

    public override void _Ready()
    {
        Instance = this;
        Settings.Load();

        if (Settings.enableGraphs)
        {
            AddChild(graphWindow = new());
        }
        if (Settings.enableGraphs)
        {
            AddChild(logWindow = new());
        }
    }
}
