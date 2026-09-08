using System.Numerics;
using Raylib_cs;
using RaylibGameFramework.Assets;
using RaylibGameFramework.ThreeD;

namespace RaylibSpeeder.Game;

public sealed class Player
{
    private readonly AssetManager _assets;
    public Player(AssetManager assets) => _assets = assets;
    public const float Size = 1.2f;
    public const float MovementSpeed = 12f;
    public Transform3D Transform { get; private set; } = new(new(0, Size / 2, 0), Quaternion.Identity, Vector3.One);
    public Vector3 Position => Transform.Position;
    public Quaternion Orientation => Transform.Rotation;
    public BoundingBox Bounds => new(Position - new Vector3(Size / 2), Position + new Vector3(Size / 2));

    public void Reset() => Transform = new(new(0, Size / 2, 0), Quaternion.Identity, Vector3.One);
    public Vector3 LocalToWorld(Vector3 localPoint) => Transform.TransformPoint(localPoint);

    public void Update(float steering, float deltaTime)
    {
        float limit = SpeederGame.TrackHalfWidth - Size / 2;
        Transform = new Transform3D(new(
            Math.Clamp(Position.X + Math.Clamp(steering, -1, 1) * MovementSpeed * deltaTime, -limit, limit),
            Size / 2, 0), Orientation, Transform.Scale);
    }

    public void Draw()
    {
        Vector3 modelPosition = Position - Vector3.UnitY * (Size / 2);
        Raylib.DrawModel(_assets.GetModel("PlayerShip"), modelPosition, 1f, Color.White);
    }
}
