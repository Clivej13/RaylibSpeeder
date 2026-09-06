using System.Numerics;
using Raylib_cs;

namespace RaylibSpeeder.Game;

public sealed class Player
{
    public const float Size = 1.2f;
    public const float MovementSpeed = 12f;
    public Vector3 Position { get; private set; } = new(0, Size / 2, 0);
    public BoundingBox Bounds => new(Position - new Vector3(Size / 2), Position + new Vector3(Size / 2));

    public void Reset() => Position = new Vector3(0, Size / 2, 0);

    public void Update(float steering, float deltaTime)
    {
        float limit = SpeederGame.TrackHalfWidth - Size / 2;
        Position = new Vector3(
            Math.Clamp(Position.X + Math.Clamp(steering, -1, 1) * MovementSpeed * deltaTime, -limit, limit),
            Size / 2, 0);
    }

    public void Draw()
    {
        Raylib.DrawCube(Position, Size, Size, Size, Color.SkyBlue);
        Raylib.DrawCubeWires(Position, Size, Size, Size, Color.White);
    }
}
