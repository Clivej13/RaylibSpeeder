using System.Numerics;
using Raylib_cs;
using RaylibGameFramework.Assets;
using RaylibGameFramework.ThreeD;

namespace RaylibSpeeder.Game;

public sealed class Pedestrian : IDisposable
{
    public const float Width = 0.926f;
    public const float Height = 1.80f;
    public const float Depth = 0.325f;
    private static readonly Vector3 ModelDimensions = new(Width, Height, Depth);
    private static readonly Vector3 CollisionForgiveness = new(0.81f, 1.7f / Height, 0.30f / Depth);
    private readonly AssetManager _assets;
    private readonly int _runIndex;
    private readonly AnimationPlayer _animation;
    private bool _released;

    public ModelInstance Instance { get; }
    public Transform3D Transform { get; private set; }
    public Vector3 Position => Transform.Position;
    public Vector3 Scale => Transform.Scale;
    public float DestinationX { get; }
    public Vector3 RunningVelocity { get; }
    public float YawDegrees { get; }
    private Vector3 CollisionSize => ModelDimensions * Scale;
    public BoundingBox Bounds => new(
        Position + Vector3.UnitY * (CollisionSize.Y / 2) - CollisionSize / 2,
        Position + Vector3.UnitY * (CollisionSize.Y / 2) + CollisionSize / 2);
    public bool HasLeftPlayableArea => Position.Z - CollisionSize.Z / 2 > 12f
        || (RunningVelocity.X < 0 ? Position.X <= DestinationX : Position.X >= DestinationX);

    public Pedestrian(AssetManager assets, float x, float z, float destinationX,
        float lateralSpeed, float forwardSpeed, float animationPhase, Vector3 scale,
        PedestrianAppearance appearance)
    {
        _assets = assets;
        ReadOnlySpan<ModelAnimation> animations = assets.GetModelAnimations("PedestrianAnimations");
        _runIndex = -1;
        for (int i = 0; i < animations.Length; i++)
        {
            if (animations[i].NameToString() == "Run" && animations[i].KeyFrameCount > 0)
            {
                _runIndex = i;
                break;
            }
        }
        if (_runIndex < 0)
            throw new InvalidOperationException("PedestrianAnimations must contain a non-empty Run clip.");

        Vector3 position = new(x, 0, z);
        RunningVelocity = new Vector3(MathF.CopySign(lateralSpeed, destinationX - x), 0, forwardSpeed);
        YawDegrees = MathF.Atan2(-RunningVelocity.X, -RunningVelocity.Z) * (180f / MathF.PI);
        Quaternion rotation = Quaternion.CreateFromAxisAngle(Vector3.UnitY, YawDegrees * MathF.PI / 180f);
        Transform = new Transform3D(position, rotation, scale);
        DestinationX = destinationX;
        Instance = assets.CreateModelInstance("Pedestrian");
        try
        {
            _animation = new AnimationPlayer(Instance, animations[_runIndex], phase: animationPhase);
            PedestrianMaterialMapping.Apply(Instance, appearance);
        }
        catch
        {
            Dispose();
            throw;
        }
    }

    public void Update(float deltaTime, float gameSpeed)
    {
        if (_released) return;
        Transform = new Transform3D(
            Position + (RunningVelocity + Vector3.UnitZ * gameSpeed) * deltaTime,
            Transform.Rotation, Transform.Scale);
        _animation.Update(deltaTime);
    }

    public void Draw()
    {
        if (!_released)
            Raylib.DrawModelEx(Instance.Model, Transform.Position, Vector3.UnitY, YawDegrees, Transform.Scale, Color.White);
    }

    public void Dispose()
    {
        if (_released) return;
        _assets.ReleaseModelInstance(Instance);
        _released = true;
    }
}
