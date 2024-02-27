using Godot;
using System;
using System.Collections.Generic;
using System.Text;
using System.Reflection;
using static DebugGUI.Settings;

namespace WeavUtils
{
    public partial class LogWindow : DebugGUIWindow
    {
        List<TransientLog> transientLogs = new();
        HashSet<Node> attributeContainers = new();
        Dictionary<Node, Type> typeCache = new();
        Dictionary<Type, int> typeInstanceCounts = new();
        Dictionary<object, string> persistentLogs = new();
        Dictionary<Node, List<PersistentLogAttributeKey>> attributeKeys = new();
        Dictionary<Type, HashSet<FieldInfo>> debugGUIPrintFields = new();
        Dictionary<Type, HashSet<PropertyInfo>> debugGUIPrintProperties = new();

        StringBuilder persistentLogStringBuilder = new();

        double time;

        public override void _Ready()
        {
            Name = nameof(LogWindow);

            // Register attributes of all nodes present at start
            // See also: ReinitializeAttributes()
            RegisterAttributes(((SceneTree)Engine.GetMainLoop()).Root);
        }

        public override void _Process(double delta)
        {
            time += delta;

            // Clean up expired logs
            int expiredCt = 0;
            for (int i = 0; i < transientLogs.Count; i++)
            {
                if (transientLogs[i].expiryTime <= time)
                {
                    expiredCt++;
                }
            }
            transientLogs.RemoveRange(0, expiredCt);

            if (debugGUIPrintFields.Count + debugGUIPrintProperties.Count + persistentLogs.Count + transientLogs.Count > 0)
            {
                QueueRedraw();
            }

            CallDeferred(nameof(CleanUpDeletedAttributes));
        }

        public override void _Draw()
        {
            persistentLogStringBuilder.Clear();

            var viewportRect = GetViewportRect();
            var lineHeight = textFont.GetHeight();

            foreach (var node in attributeContainers)
            {
                Type type = typeCache[node];
                if (debugGUIPrintFields.ContainsKey(type))
                {
                    foreach (var field in debugGUIPrintFields[type])
                    {
                        persistentLogStringBuilder.AppendLine($"{node.Name} {field.Name}: {field.GetValue(node)}");
                    }
                }
                if (debugGUIPrintProperties.ContainsKey(type))
                {
                    foreach (var property in debugGUIPrintProperties[type])
                    {
                        persistentLogStringBuilder.AppendLine($"{node.Name} {property.Name}: {property.GetValue(node, null)}");
                    }
                }
            }

            foreach (var log in persistentLogs.Values)
            {
                persistentLogStringBuilder.AppendLine(log);
            }

            if (persistentLogStringBuilder.Length > 0 && transientLogs.Count != 0)
            {
                persistentLogStringBuilder.AppendLine();
            }

            var persistentLogStr = persistentLogStringBuilder.ToString();
            var textSize = textFont.GetMultilineStringSize(persistentLogStr);
            Size = textSize + Vector2.One * 10;

            float transientLogY = textSize.Y;

            foreach (var log in transientLogs)
            {
                var size = textFont.GetStringSize(log.text);
                textSize = new Vector2(
                    Mathf.Max(size.X, textSize.X),
                    textSize.Y + size.Y
                );
            }


            var backgroundRect = new Rect2(Vector2.Zero, textSize.X + 10, textSize.Y + 10);
            DrawRect(backgroundRect, backgroundColor);
            // Draw a little bit extra for the draggable area
            DrawRect(new Rect2(0, 0, GetRect().Size), new Color(1, 1, 1, 0.05f));

            // Draw persistent logs
            DrawMultilineString(textFont, new Vector2(0, textFont.GetHeight()), persistentLogStr);

            // Draw separator
            if (persistentLogStringBuilder.Length > 0 && transientLogs.Count != 0)
            {
                DrawDashedLine(
                    new Vector2(0, transientLogY),
                    new Vector2(textSize.X, transientLogY),
                    Colors.White,
                    2
                );
            }

            // Draw transient logs
            for (int i = transientLogs.Count - 1; i >= 0; i--)
            {
                transientLogY += lineHeight;
                // Clear up transient logs going off screen
                if (transientLogY > viewportRect.Size.Y)
                {
                    transientLogs.RemoveRange(0, i + 1);
                    break;
                }

                var log = transientLogs[i];
                DrawString(textFont, new Vector2(0, transientLogY), log.text);
            }
        }

        public void Log(string str)
        {
            transientLogs.Add(new TransientLog(str, time + temporaryLogLifetime));
        }

        public void LogPersistent(object key, string message)
        {
            if (persistentLogs.ContainsKey(key))
                persistentLogs[key] = message;
            else
                persistentLogs.Add(key, message);
        }

        public void RemovePersistent(object key)
        {
            if (persistentLogs.ContainsKey(key))
            {
                persistentLogs.Remove(key);
            }
        }

        public void ClearPersistent()
        {
            persistentLogs.Clear();
        }

        public void ReinitializeAttributes()
        {
            // Clean up graphs
            List<object> toRemove = new List<object>();
            foreach (var key in persistentLogs.Keys)
            {
                if (key is PersistentLogAttributeKey)
                    toRemove.Add(key);
            }
            foreach (var key in toRemove)
            {
                persistentLogs.Remove(key);
            }

            attributeContainers = new();
            debugGUIPrintFields = new();
            debugGUIPrintProperties = new();
            typeInstanceCounts = new();
            attributeKeys = new();
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
                    DebugGUIPrintAttribute printAttribute = Attribute.GetCustomAttribute(objectFields[i], typeof(DebugGUIPrintAttribute)) as DebugGUIPrintAttribute;

                    if (printAttribute != null)
                    {
                        uniqueAttributeContainers.Add(node);
                        typeCache[node] = node.GetType();
                        if (!debugGUIPrintFields.ContainsKey(nodeType))
                        {
                            debugGUIPrintFields.Add(nodeType, new HashSet<FieldInfo>());
                        }

                        GD.Print("Found field " + objectFields[i].Name + " on " + node);
                        debugGUIPrintFields[nodeType].Add(objectFields[i]);
                    }
                }
            }

            // Properties
            {
                PropertyInfo[] objectProperties = nodeType.GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);

                for (int i = 0; i < objectProperties.Length; i++)
                {
                    if (Attribute.GetCustomAttribute(objectProperties[i], typeof(DebugGUIPrintAttribute)) is DebugGUIPrintAttribute)
                    {
                        uniqueAttributeContainers.Add(node);
                        typeCache[node] = node.GetType();

                        if (!debugGUIPrintProperties.ContainsKey(nodeType))
                        {
                            debugGUIPrintProperties.Add(nodeType, new HashSet<PropertyInfo>());
                        }
                        debugGUIPrintProperties[nodeType].Add(objectProperties[i]);
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
                    attributeKeys.Remove(node);
                    typeCache.Remove(node);

                    Type type = node.GetType();
                    typeInstanceCounts[type]--;
                    if (typeInstanceCounts[type] == 0)
                    {
                        if (debugGUIPrintFields.ContainsKey(type))
                            debugGUIPrintFields.Remove(type);
                        if (debugGUIPrintProperties.ContainsKey(type))
                            debugGUIPrintProperties.Remove(type);
                    }
                }
            }

            // Finally clear out removed nodes
            attributeContainers.RemoveWhere(node => node.IsQueuedForDeletion());
        }

        private struct TransientLog
        {
            public string text;
            public double expiryTime;

            public TransientLog(string text, double expiryTime)
            {
                this.text = text;
                this.expiryTime = expiryTime;
            }
        }

        // Wrapper to differentiate attributes from
        // manually created logs
        public class PersistentLogAttributeKey
        {
            public MemberInfo memberInfo;
            public PersistentLogAttributeKey(MemberInfo memberInfo)
            {
                this.memberInfo = memberInfo;
            }
        }
    }
}
