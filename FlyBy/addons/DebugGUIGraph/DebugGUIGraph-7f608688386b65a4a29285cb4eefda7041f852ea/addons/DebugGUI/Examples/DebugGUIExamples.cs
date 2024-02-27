using Godot;
using System.Collections.Generic;
using System.Linq;

public partial class DebugGUIExamples : Node
{
	/* * * *
	* 
	*   [DebugGUIGraph]
	*   Renders the variable in a graph on-screen. Attribute based graphs will updates every _Process.
	*    Lets you optionally define:
	*        max, min  - The range of displayed values
	*        r, g, b   - The RGB color of the graph (0~1)
	*        group     - Graphs can be grouped into the same window and overlaid
	*        autoScale - If true the graph will readjust min/max to fit the data
	*   
	*   [DebugGUIPrint]
	*    Draws the current variable continuously on-screen as 
	*    $"{GameObject name} {variable name}: {value}"
	*   
	*   For more control, these features can be accessed manually.
	*    DebugGUI.SetGraphProperties(key, ...) - Set the properties of the graph with the provided key
	*    DebugGUI.Graph(key, value)            - Push a value to the graph
	*    DebugGUI.LogPersistent(key, value)    - Print a persistent log entry on screen
	*    DebugGUI.Log(value)                   - Print a temporary log entry on screen
	*    
	*   See DebugGUI.cs for more info
	* 
	* * * */

	// Disable Field Unused warning
#pragma warning disable 0414

	// Works with regular fields
	[DebugGUIGraph(min: -1, max: 1, r: 0, g: 1, b: 0, autoScale: true)]
	float SinField;

	// As well as properties
	[DebugGUIGraph(min: -1, max: 1, r: 0, g: 1, b: 1, autoScale: true)]
	float CosProperty { get { return Mathf.Cos(time * 6); } }

	// Also works for expression-bodied properties
	[DebugGUIGraph(min: -1, max: 1, r: 1, g: 0.3f, b: 1)]
	float SinProperty => Mathf.Sin((time + Mathf.Pi / 2) * 6);

	// User inputs, print and graph in one!
	[DebugGUIPrint, DebugGUIGraph(group: 1, r: 1, g: 0.3f, b: 0.3f)]
	float mouseX;
	[DebugGUIPrint, DebugGUIGraph(group: 1, r: 0, g: 1, b: 0)]
	float mouseY;

	Queue<double> deltaTimeBuffer = new();
	double smoothDeltaTime => deltaTimeBuffer.Sum() / deltaTimeBuffer.Count;
	float time;
	float physicsTime;
	bool wasMouseDown;

	public override void _Ready()
	{
		
		// Init smooth DT
		for (int i = 0; i < 10; i++)
		{
			deltaTimeBuffer.Enqueue(0);
		}

		// Log (as opposed to LogPersistent) will disappear automatically after some time.
		DebugGUI.Log("Hello! I will disappear after some time!");

		// Set up graph properties using our graph keys
		DebugGUI.SetGraphProperties("smoothFrameRate", "SmoothFPS", 0, 200, 2, new Color(0, 1, 1), false);
		DebugGUI.SetGraphProperties("frameRate", "FPS", 0, 200, 2, new Color(1, 0.5f, 1), false);
		DebugGUI.SetGraphProperties("fixedFrameRateSin", "FixedSin", -1, 1, 3, new Color(1, 1, 0), true);
	}

	public override void _Process(double delta)
	{
		time += (float)delta;

		// Update smooth delta time queue
		deltaTimeBuffer.Dequeue();
		deltaTimeBuffer.Enqueue(delta);

		// Update the fields our attributes are graphing
		SinField = Mathf.Sin(time * 6);

		// Update graphed mouse XY values
		var mousePos = GetViewport().GetMousePosition();
		var viewportRect = GetViewport().GetVisibleRect();
		mouseX = Mathf.Clamp(mousePos.X, 0, viewportRect.Size.X);
		mouseY = Mathf.Clamp(mousePos.Y, 0, viewportRect.Size.Y);

		// Manual persistent logging
		DebugGUI.LogPersistent("smoothFrameRate", "SmoothFPS: " + (1 / smoothDeltaTime).ToString("F3"));
		DebugGUI.LogPersistent("frameRate", "FPS: " + (1 / delta).ToString("F3"));

		// Manual logging of mouse clicks
		if (Input.IsMouseButtonPressed(MouseButton.Left))
		{
			if (!wasMouseDown)
			{
				wasMouseDown = true;
				DebugGUI.Log(string.Format(
					"Mouse down ({0}, {1})",
					mouseX.ToString("F3"),
					mouseY.ToString("F3")
				));
			}
		}
		else
		{
			wasMouseDown = false;
		}

		if (smoothDeltaTime != 0)
		{
			DebugGUI.Graph("smoothFrameRate", 1 / (float)smoothDeltaTime);
		}
		if (delta != 0)
		{
			DebugGUI.Graph("frameRate", 1 / (float)delta);
		}

		if (Input.IsKeyPressed(Key.Space))
		{
			QueueFree();
		}
	}

	public override void _PhysicsProcess(double delta)
	{
		physicsTime += (float)delta;

		// Manual graphing
		DebugGUI.Graph("fixedFrameRateSin", Mathf.Sin(physicsTime * 6));
	}

	public override void _ExitTree()
	{
		// Clean up our logs and graphs when this object leaves tree
		DebugGUI.RemoveGraph("frameRate");
		DebugGUI.RemoveGraph("fixedFrameRateSin");
		DebugGUI.RemoveGraph("smoothFrameRate");

		DebugGUI.RemovePersistent("frameRate");
		DebugGUI.RemovePersistent("smoothFrameRate");
	}
}
