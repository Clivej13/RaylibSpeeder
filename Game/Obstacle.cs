using System.Numerics;
using Raylib_cs;

namespace RaylibSpeeder.Game;

public sealed class Obstacle(float x, float z, Vector3 size)
{
    public Vector3 Position { get; private set; } = new(x, size.Y / 2, z);
    public Vector3 Size { get; } = size;
    public BoundingBox Bounds => new(Position - Size / 2, Position + Size / 2);
    public bool HasPassed => Position.Z - Size.Z / 2 > 12f;

    public void Update(float distance) => Position += new Vector3(0, 0, distance);

    public void Draw()
    {
        Raylib.DrawCubeV(Position, Size, Color.Orange);
        Raylib.DrawCubeWiresV(Position, Size, Color.Maroon);
    }
}
