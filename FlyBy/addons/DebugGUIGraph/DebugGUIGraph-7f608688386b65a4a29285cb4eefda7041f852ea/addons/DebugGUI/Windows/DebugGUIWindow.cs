using Godot;
using System;

namespace WeavUtils
{
    // Draggable window clamped to the corners
    public abstract partial class DebugGUIWindow : Control
    {
        protected const int outOfScreenClampPadding = 30;

        static bool dragInProgress;
        bool dragged;

        new public virtual Rect2 GetRect()
        {
            return base.GetRect();
        }

        public override void _Input(InputEvent @event)
        {
            if (@event is InputEventMouseButton mb)
            {
                if (!dragInProgress && mb.Pressed && mb.ButtonIndex == MouseButton.Middle)
                {
                    if (GetRect().HasPoint(mb.Position))
                    {
                        dragged = true;
                        dragInProgress = true;
                    }
                }
                if (mb.IsReleased() && mb.ButtonIndex == MouseButton.Middle)
                {
                    if (dragged) dragInProgress = false;
                    dragged = false;
                }
            }

            if (@event is InputEventMouseMotion motion)
            {
                if (dragged)
                {
                    Move(motion.Relative);
                }
            }
        }

        protected void Move(Vector2 delta = default)
        {
            Position += delta;

            var viewportRect = GetViewportRect();

            // Limit graph window offset so we can't get lost off screen
            Position = Position.Clamp(
                -GetRect().Size + Vector2.One * outOfScreenClampPadding,
                viewportRect.Size - Vector2.One * outOfScreenClampPadding
            );
        }

    }
}