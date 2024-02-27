using Godot;
using System;
using System.Collections.Generic;
using System.Reflection;
using static DebugGUI.Settings;

namespace WeavUtils
{
    public partial class GraphWindow : DebugGUIWindow
    {
        const int graphLabelFontSize = 12;
        const int graphLabelPadding = 5;
        const int graphBlockPadding = 3;
        const int scrubberBackgroundWidth = 55;
        const int windowOutOfScreenPadding = 30;

        List<GraphContainer> graphs = new();
        HashSet<Node> attributeContainers = new();
        Dictionary<Type, int> typeInstanceCounts = new();
        Dictionary<object, GraphContainer> graphDictionary = new();
        Dictionary<Node, List<GraphAttributeKey>> attributeKeys = new();
        Dictionary<Type, HashSet<FieldInfo>> debugGUIGraphFields = new();
        Dictionary<Type, HashSet<PropertyInfo>> debugGUIGraphProperties = new();
        SortedDictionary<int, List<GraphContainer>> graphGroups = new();

        bool freezeGraphs;
        float graphLabelBoxWidth;

        public override void _Ready()
        {
            Name = nameof(GraphWindow);

            // Register attributes of all nodes present at start
            // See also: ReinitializeAttributes()
            RegisterAttributes(((SceneTree)Engine.GetMainLoop()).Root);

            // Default to top right
            Position = new Vector2(GetViewportRect().Size.X - GetRect().Size.X, 0);
        }

        public override void _Process(double delta)
        {
            if (!Input.IsMouseButtonPressed(MouseButton.Left))
            {
                freezeGraphs = false;
            }

            if (!freezeGraphs)
            {
                CallDeferred(nameof(PollGraphAttributes));
            }

            QueueRedraw();

            // Clean up any nodes queued to free
            CallDeferred(nameof(CleanUpDeletedAttributes));
        }

        public override void _Draw()
        {
            int groupNum = 0;
            foreach (var group in graphGroups.Values)
            {
                DrawGraphGroup(group, groupNum);
                groupNum++;
            }
        }

        public void Graph(object key, float val)
        {
            if (!graphDictionary.ContainsKey(key))
            {
                CreateGraph(key);
            }

            if (freezeGraphs) return;

            graphDictionary[key].Push(val);
            // Todo: optimize away?
            RecalculateGraphLabelWidth();
        }

        public void CreateGraph(object key)
        {
            AddGraph(key, new GraphContainer(graphWidth));
            RecalculateGraphLabelWidth();
        }

        public void ClearGraph(object key)
        {
            if (graphDictionary.ContainsKey(key))
                graphDictionary[key].Clear();
        }

        public void RemoveGraph(object key)
        {
            if (graphDictionary.ContainsKey(key))
            {
                var graph = graphDictionary[key];
                graphs.Remove(graph);
                graphDictionary.Remove(key);
                graphGroups[graph.group].Remove(graph);
                if (graphGroups[graph.group].Count == 0)
                {
                    graphGroups.Remove(graph.group);
                }
                RecalculateGraphLabelWidth();
            }
        }

        public void SetGraphProperties(object key, string label, float min, float max, int group, Color color, bool autoScale)
        {
            if (graphDictionary.ContainsKey(key))
            {
                RemoveGraph(key);
            }

            var graph = new GraphContainer(graphWidth, group);
            AddGraph(key, graph);

            graph.name = label;
            graph.SetMinMax(min, max);
            graph.color = color;
            graph.autoScale = autoScale;
        }

        public void ReinitializeAttributes()
        {
            // Clean up graphs
            List<object> toRemove = new List<object>();
            foreach (var key in graphDictionary.Keys)
            {
                if (key is GraphAttributeKey)
                    toRemove.Add(key);
            }
            foreach (var key in toRemove)
            {
                RemoveGraph(key);
            }

            attributeContainers = new();
            debugGUIGraphFields = new();
            debugGUIGraphProperties = new();
            typeInstanceCounts = new();
            attributeKeys = new();

            RegisterAttributes(((SceneTree)Engine.GetMainLoop()).Root);
        }

        public string ToJson()
        {
            var data = new Godot.Collections.Array<Variant>();

            foreach (var node in graphs)
            {
                data.Add(node.ToDataVariant());
            }

            return data.ToString();
        }

        public override Rect2 GetRect()
        {
            RefreshRect();
            return base.GetRect();
        }

        private void AddGraph(object key, GraphContainer graph)
        {
            graph.OnLabelSizeChange += RefreshRect;

            graphDictionary.Add(key, graph);
            graphs.Add(graph);

            if (!graphGroups.ContainsKey(graph.group))
            {
                graphGroups.Add(graph.group, new List<GraphContainer>());
            }

            graphGroups[graph.group].Add(graph);

            RecalculateGraphLabelWidth();
        }

        private void PollGraphAttributes()
        {
            foreach (var node in attributeContainers)
            {
                if (node != null && attributeKeys.ContainsKey(node))
                {
                    foreach (var key in attributeKeys[node])
                    {
                        if (key.memberInfo is FieldInfo fieldInfo)
                        {
                            float? val = fieldInfo.GetValue(node) as float?;
                            if (val != null)
                                graphDictionary[key].Push(val.Value);
                        }
                        else if (key.memberInfo is PropertyInfo propertyInfo)
                        {
                            float? val = propertyInfo.GetValue(node, null) as float?;
                            if (val != null)
                                graphDictionary[key].Push(val.Value);
                        }
                    }
                }
            }
        }

        GraphContainer lastPressedGraphLabel;
        private void DrawGraphGroup(List<GraphContainer> group, int groupNum)
        {
            var mousePos = GetLocalMousePosition();

            Vector2 graphBlockSize = new Vector2(graphWidth + graphBlockPadding, graphHeight + graphBlockPadding);

            var groupOrigin = new Vector2(0, graphBlockSize.Y * groupNum);
            var groupGraphRect = new Rect2(
                groupOrigin.X + graphLabelBoxWidth + graphBlockPadding,
                groupOrigin.Y,
                graphWidth,
                graphHeight
            );

            // Label background
            DrawRect(new Rect2(
                groupOrigin.X,
                groupOrigin.Y,
                graphLabelBoxWidth,
                graphHeight),
            backgroundColor);

            // Graph background
            DrawRect(new Rect2(
                groupOrigin.X + graphBlockPadding + graphLabelBoxWidth,
                groupOrigin.Y,
                graphBlockSize.X,
                graphHeight),
            backgroundColor);

            // Magic padding offsets
            Vector2 textOrigin = groupOrigin + new Vector2(0, 14);
            Vector2 minMaxOrigin = groupOrigin + new Vector2(graphLabelBoxWidth - 10, 16);
            foreach (var graph in group)
            {
                var textSize = textFont.GetStringSize(graph.name, fontSize: graphLabelFontSize);
                textOrigin.Y += textSize.Y;
                var maxWidthOfMinMaxStrings = Mathf.Max(
                    textFont.GetStringSize(graph.minString, fontSize: graphLabelFontSize).X,
                    textFont.GetStringSize(graph.maxString, fontSize: graphLabelFontSize).X
                );
                minMaxOrigin += Vector2.Left * (maxWidthOfMinMaxStrings + graphLabelPadding);

                // Label button logic
                var labelRect = new Rect2(textOrigin - textSize + new Vector2(graphLabelBoxWidth - (graphLabelPadding * 2), graphLabelPadding), textSize);
                // Enable disable
                var isHovered = labelRect.HasPoint(mousePos);
                var isPressed = isHovered && Input.IsMouseButtonPressed(MouseButton.Left);

                // Button click
                if (lastPressedGraphLabel == graph && !isPressed && isHovered)
                {
                    graph.visible = !graph.visible;
                }

                if (isPressed)
                {
                    lastPressedGraphLabel = graph;
                }
                else if (lastPressedGraphLabel == graph)
                {
                    lastPressedGraphLabel = null;
                }

                var graphColor = graph.GetModifiedColor(isHovered);

                // Name
                DrawString(
                    textFont,
                    textOrigin - new Vector2(textSize.X + 10 - graphLabelBoxWidth, 0),
                    graph.name,
                    fontSize: graphLabelFontSize,
                    modulate: graphColor,
                    alignment: HorizontalAlignment.Right
                );

                // Max
                DrawString(
                    textFont,
                    minMaxOrigin,
                    graph.maxString,
                    modulate: graphColor,
                    fontSize: graphLabelFontSize,
                    alignment: HorizontalAlignment.Right
                );

                // Min
                DrawString(
                    textFont,
                    minMaxOrigin + new Vector2(0, graphHeight - 20),
                    graph.minString,
                    modulate: graphColor,
                    fontSize: graphLabelFontSize,
                    alignment: HorizontalAlignment.Right
                );

                // Graph
                if (graph.visible)
                {
                    graph.Draw(groupGraphRect, this);
                }
            }

            // Scrubber
            if (groupGraphRect.HasPoint(mousePos))
            {
                if (Input.IsMouseButtonPressed(MouseButton.Left))
                {
                    freezeGraphs = true;
                }

                // Background
                Vector2 scrubberOrigin = new Vector2(mousePos.X, groupOrigin.Y);
                if (mousePos.X > groupGraphRect.End.X - scrubberBackgroundWidth)
                {
                    scrubberOrigin.X -= scrubberBackgroundWidth;
                }

                var rect = new Rect2(
                    scrubberOrigin,
                    scrubberBackgroundWidth,
                    graphHeight
                );
                DrawRect(rect, backgroundColor);

                DrawLine(
                    new Vector2(
                        mousePos.X,
                        groupOrigin.Y
                    ), new Vector2(
                        mousePos.X,
                        groupOrigin.Y + graphHeight
                    ),
                    scrubberColor
                );

                // Scrubber labels
                Vector2 textPos = scrubberOrigin + new Vector2(graphLabelPadding, graphLabelPadding * 3);
                var groupMousePosX = (mousePos.X - groupOrigin.X);
                int sampleIndex = (int)(groupGraphRect.Size.X - groupMousePosX + graphLabelBoxWidth + graphBlockPadding);
                foreach (GraphContainer graph in group)
                {
                    var text = graph.GetValue(sampleIndex).ToString("F3");
                    DrawString(
                        textFont,
                        textPos,
                        text,
                        modulate: graph.color,
                        fontSize: graphLabelFontSize
                    );
                    textPos.Y += textFont.GetHeight(graphLabelFontSize);
                }
            }
        }

        private Rect2 GetGraphWindowRect()
        {
            return new Rect2(
                new Vector2(-graphLabelBoxWidth, 0) + Position,
                graphWidth + graphLabelBoxWidth + graphBlockPadding,
                (graphHeight + graphBlockPadding) * graphGroups.Count
            );
        }

        private void RegisterAttributes(Node node)
        {
            foreach (Node child in node.GetChildren())
            {
                GD.Print(child);
                RegisterAttributes(child);
            }

            Type nodeType = node.GetType();

            HashSet<Node> uniqueAttributeContainers = new();
            // Fields
            {
                // Retreive the fields from the mono instance
                FieldInfo[] objectFields = nodeType.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);

                // search all fields/properties for the [DebugGUIVar] attribute
                for (int i = 0; i < objectFields.Length; i++)
                {
                    DebugGUIGraphAttribute graphAttribute = Attribute.GetCustomAttribute(objectFields[i], typeof(DebugGUIGraphAttribute)) as DebugGUIGraphAttribute;

                    if (graphAttribute != null)
                    {
                        // Can't cast to float so we don't bother registering it
                        if (objectFields[i].GetValue(node) as float? == null)
                        {
                            GD.PrintErr(string.Format("Cannot cast {0}.{1} to float. This member will be ignored.", nodeType.Name, objectFields[i].Name));
                            continue;
                        }

                        uniqueAttributeContainers.Add(node);
                        if (!debugGUIGraphFields.ContainsKey(nodeType))
                            debugGUIGraphFields.Add(nodeType, new HashSet<FieldInfo>());
                        if (!debugGUIGraphProperties.ContainsKey(nodeType))
                            debugGUIGraphProperties.Add(nodeType, new HashSet<PropertyInfo>());

                        debugGUIGraphFields[nodeType].Add(objectFields[i]);
                        GraphContainer graph =
                            new GraphContainer(graphWidth, graphAttribute.group)
                            {
                                name = objectFields[i].Name,
                                max = graphAttribute.max,
                                min = graphAttribute.min,
                                autoScale = graphAttribute.autoScale
                            };
                        graph.OnLabelSizeChange += RefreshRect;
                        if (!graphAttribute.color.Equals(default(Color)))
                            graph.color = graphAttribute.color;

                        var key = new GraphAttributeKey(objectFields[i]);
                        if (!attributeKeys.ContainsKey(node))
                            attributeKeys.Add(node, new List<GraphAttributeKey>());
                        attributeKeys[node].Add(key);

                        AddGraph(key, graph);
                    }
                }
            }

            // Properties
            {
                PropertyInfo[] objectProperties = nodeType.GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);

                for (int i = 0; i < objectProperties.Length; i++)
                {
                    if (Attribute.GetCustomAttribute(objectProperties[i], typeof(DebugGUIGraphAttribute)) is DebugGUIGraphAttribute graphAttribute)
                    {
                        // Can't cast to float so we don't bother registering it
                        if (objectProperties[i].GetValue(node, null) as float? == null)
                        {
                            GD.PrintErr("Cannot cast " + objectProperties[i].Name + " to float. This member will be ignored.");
                            continue;
                        }

                        uniqueAttributeContainers.Add(node);

                        if (!debugGUIGraphFields.ContainsKey(nodeType))
                            debugGUIGraphFields.Add(nodeType, new HashSet<FieldInfo>());
                        if (!debugGUIGraphProperties.ContainsKey(nodeType))
                            debugGUIGraphProperties.Add(nodeType, new HashSet<PropertyInfo>());

                        debugGUIGraphProperties[nodeType].Add(objectProperties[i]);

                        GraphContainer graph =
                            new GraphContainer(graphWidth, graphAttribute.group)
                            {
                                name = objectProperties[i].Name,
                                max = graphAttribute.max,
                                min = graphAttribute.min,
                                autoScale = graphAttribute.autoScale
                            };
                        graph.OnLabelSizeChange += RefreshRect;
                        if (!graphAttribute.color.Equals(default(Color)))
                            graph.color = graphAttribute.color;

                        var key = new GraphAttributeKey(objectProperties[i]);
                        if (!attributeKeys.ContainsKey(node))
                            attributeKeys.Add(node, new List<GraphAttributeKey>());
                        attributeKeys[node].Add(key);

                        AddGraph(key, graph);
                    }
                }
            }

            foreach (var attributeContainer in uniqueAttributeContainers)
            {
                attributeContainers.Add(attributeContainer);
                Type type = attributeContainer.GetType();
                if (!typeInstanceCounts.ContainsKey(type))
                    typeInstanceCounts.Add(type, 0);
                typeInstanceCounts[type]++;
            }
        }

        private void CleanUpDeletedAttributes()
        {
            // Clear out associated keys
            foreach (var node in attributeContainers)
            {
                if (node.IsQueuedForDeletion())
                {
                    var keys = attributeKeys[node];
                    foreach (var key in keys)
                    {
                        RemoveGraph(key);
                    }
                    attributeKeys.Remove(node);

                    Type type = node.GetType();
                    typeInstanceCounts[type]--;
                    if (typeInstanceCounts[type] == 0)
                    {
                        if (debugGUIGraphFields.ContainsKey(type))
                            debugGUIGraphFields.Remove(type);
                        if (debugGUIGraphProperties.ContainsKey(type))
                            debugGUIGraphProperties.Remove(type);
                    }
                }
            }

            // Finally clear out removed nodes
            attributeContainers.RemoveWhere(node => node.IsQueuedForDeletion());
        }

        void RefreshRect()
        {
            var lastWidth = Size.X;
            RecalculateGraphLabelWidth();
            Size = new Vector2(
                graphWidth + graphLabelBoxWidth + graphBlockPadding,
                (graphHeight + graphBlockPadding) * graphGroups.Count);
            // Grow to the left instead of right
            Position += new Vector2(lastWidth - Size.X, 0);
        }

        void RecalculateGraphLabelWidth()
        {
            float width = 0;
            foreach (var group in graphGroups.Values)
            {
                float minMaxWidth = graphLabelPadding;
                foreach (var graph in group)
                {
                    // Names
                    width = Mathf.Max(textFont.GetStringSize(graph.name, fontSize: graphLabelFontSize).X, width);

                    // Minmax labels per group
                    var maxWidthOfMinMaxStrings = Mathf.Max(
                        textFont.GetStringSize(graph.minString, fontSize: graphLabelFontSize).X,
                        textFont.GetStringSize(graph.maxString, fontSize: graphLabelFontSize).X
                    );
                    minMaxWidth += maxWidthOfMinMaxStrings + graphLabelPadding;
                }
                width = Mathf.Max(minMaxWidth, width);
            }
            graphLabelBoxWidth = width + graphLabelPadding * 2;
        }

        private class GraphContainer
        {
            public Action OnLabelSizeChange;

            public string name;

            // Value at the top of the graph
            public float max = 1;
            // Value at the bottom of the graph
            public float min = 0;
            public bool autoScale;
            public Color color;
            // Graph order on screen
            public readonly int group;

            private int currentIndex;
            private readonly float[] values;
            private readonly Vector2[] graphPoints;

            public string minString = null;
            public string maxString = null;
            public bool visible = true;

            public Color GetModifiedColor(bool highlighted)
            {
                if (!highlighted && visible) return color;
                color.ToHsv(out float h, out float s, out float v);

                if (!visible) v *= 0.3f;
                if (highlighted) v *= (v > 0.9f ? 0.7f : 1.2f);
                return Color.FromHsv(h, s, v);
            }

            public void SetMinMax(float min, float max)
            {
                OnLabelSizeChange?.Invoke();
                this.min = min;
                this.max = max;

                minString = min.ToString("F2");
                maxString = max.ToString("F2");
            }

            public GraphContainer(int width, int group = 0)
            {
                this.group = group;
                values = new float[width];
                graphPoints = new Vector2[width];
                SetMinMax(min, max);
            }

            // Add a data point to the beginning of the graph
            public void Push(float val)
            {
                if (autoScale && (val > max || val < min))
                {
                    SetMinMax(Mathf.Min(val, min), Mathf.Max(val, max));
                }
                else
                {
                    // Prevent drawing outside frame
                    val = Mathf.Clamp(val, min, max);
                }

                values[currentIndex] = val;
                currentIndex = (currentIndex + 1) % values.Length;
            }

            public void Clear()
            {
                for (int i = 0; i < values.Length; i++)
                {
                    values[i] = 0;
                }
            }

            public void Draw(Rect2 rect, CanvasItem canvasItem)
            {
                int num = values.Length;
                for (int i = 0; i < num; i++)
                {
                    float value = values[Mod(currentIndex - i - 1, values.Length)];
                    // Note flipped inverse lerp min max to account for y = down in godot
                    graphPoints[i] = new Vector2(
                        rect.Position.X + (rect.Size.X * ((float)i / num)),
                        rect.Position.Y + (Mathf.InverseLerp(max, min, value) * graphHeight)
                    );
                }

                canvasItem.DrawPolyline(graphPoints, color);
            }

            public float GetValue(int index)
            {
                return values[Mod(currentIndex + index, values.Length)];
            }

            class DataExport
            {
                public string name;
                public float[] values;

                public DataExport(string name, float[] values)
                {
                    this.name = name;
                    this.values = values;
                }
            }

            public Variant ToDataVariant()
            {
                var vals = new float[values.Length];
                for (int i = 0; i < vals.Length; i++)
                {
                    vals[i] = values[Mod(currentIndex + i, values.Length)];
                }

                var dict = new Godot.Collections.Dictionary<string, Variant>();
                dict.Add("name", name);
                dict.Add("values", vals);

                return dict;
            }

            private static int Mod(int n, int m)
            {
                return ((n % m) + m) % m;
            }
        }

        public class GraphAttributeKey
        {
            public MemberInfo memberInfo;
            public GraphAttributeKey(MemberInfo memberInfo)
            {
                this.memberInfo = memberInfo;
            }
        }
    }
}