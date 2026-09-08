using System.Numerics;
using Raylib_cs;
using RaylibGameFramework.Assets;
using RaylibGameFramework.ThreeD;

namespace RaylibSpeeder.Game;

public sealed class SpeederGame
{
    public const float TrackHalfWidth = 7f;
    public const float InitialSpeed = 18f;
    private const float MaximumSpeed = 55f;
    private readonly Player _player;
    private readonly ParticleSystem3D _particles = new(randomSeed: 0x5EED);
    private readonly List<Pedestrian> _pedestrians = [];
    private readonly PedestrianSpawner _spawner;
    // player_ship.glb faces -Z, so the rear engine outlets are on the +Z side.
    private static readonly Vector3[] ExhaustEmitterLocalOffsets =
    [
        new(-0.34f, -0.22f, 0.78f),
        new(0.34f, -0.22f, 0.78f)
    ];
    public CharacterDefinition SelectedCharacter { get; private set; } = new();
    private readonly Camera3D _camera = new()
    {
        Position = new Vector3(0, 7, 13),
        Target = new Vector3(0, 0.8f, -22),
        Up = Vector3.UnitY,
        FovY = 60,
        Projection = CameraProjection.Perspective
    };

    public float Speed { get; private set; } = InitialSpeed;
    public double Distance { get; private set; }
    public double SurvivalTime { get; private set; }
    public bool IsGameOver { get; private set; }
    public int ActiveParticleCount => _particles.ActiveCount;
    public int PeakParticleCount => _particles.PeakActiveCount;

    public SpeederGame(AssetManager assets)
    {
        _player = new Player(assets);
        _spawner = new PedestrianSpawner(assets);
    }

    public void ClearPedestrians()
    {
        foreach (Pedestrian pedestrian in _pedestrians)
            pedestrian.Dispose();
        _pedestrians.Clear();
    }

    public void Reset() => Reset(SelectedCharacter);

    public void Reset(CharacterDefinition character)
    {
        SelectedCharacter = character;
        _player.Reset();
        _particles.Clear();
        ClearPedestrians();
        _spawner.Reset();
        Speed = InitialSpeed;
        Distance = 0;
        SurvivalTime = 0;
        IsGameOver = false;
    }

    public void Update(float deltaTime, float steering)
    {
        if (!float.IsFinite(deltaTime) || deltaTime <= 0)
            return;

        if (IsGameOver)
        {
            _particles.Update(Math.Min(deltaTime, 0.25f));
            return;
        }

        // Discard long stalls, and subdivide movement so boxes cannot skip the player.
        float remaining = Math.Min(deltaTime, 0.25f);
        while (remaining > 0 && !IsGameOver)
        {
            float step = Math.Min(remaining, 1f / 120f);
            remaining -= step;
            _player.Update(steering, step);
            foreach (Vector3 emitterOffset in ExhaustEmitterLocalOffsets)
                _particles.EmitLocal(_player.Transform, emitterOffset,
                    new Vector3(0, 0, 4.0f + Speed * 0.08f), 0.30f, 0.08f,
                    new Color((byte)255, (byte)175, (byte)35, (byte)225),
                    new Vector3(0, -0.15f, 0));
            SurvivalTime += step;
            Speed = Math.Min(MaximumSpeed, InitialSpeed + (float)SurvivalTime * 0.45f);
            float distance = Speed * step;
            Distance += distance;
            _spawner.Update(step, _pedestrians);
            for (int i = _pedestrians.Count - 1; i >= 0; i--)
            {
                Pedestrian pedestrian = _pedestrians[i];
                pedestrian.Update(step, Speed);
                if (!IsGameOver && Raylib.CheckCollisionBoxes(_player.Bounds, pedestrian.Bounds))
                {
                    IsGameOver = true;
                    _particles.Burst(_player.Position, 72, speed: 6.5f, lifetime: 0.45f,
                        size: 0.08f, color: new Color((byte)255, (byte)150, (byte)30, (byte)240));
                }
                if (pedestrian.HasLeftPlayableArea)
                {
                    pedestrian.Dispose();
                    _pedestrians.RemoveAt(i);
                }
            }
            _particles.Update(step);
        }
        if (IsGameOver)
            ClearPedestrians();
    }

    public void Draw()
    {
        Raylib.BeginMode3D(_camera);
        Raylib.DrawPlane(new Vector3(0, -0.04f, -40), new Vector2(180, 220), new Color(24, 34, 43, 255));
        Raylib.DrawPlane(new Vector3(0, 0, -40), new Vector2(TrackHalfWidth * 2, 120), new Color(51, 65, 75, 255));
        for (int side = -1; side <= 1; side += 2)
            Raylib.DrawCube(new Vector3(side * (TrackHalfWidth + 0.15f), 0.12f, -40),
                0.15f, 0.24f, 120, Color.SkyBlue);

        float offset = (float)(Distance % 6);
        for (float z = -96 + offset; z < 14; z += 6)
        {
            Raylib.DrawCube(new Vector3(-TrackHalfWidth + 0.25f, 0.02f, z), 0.12f, 0.03f, 2, Color.White);
            Raylib.DrawCube(new Vector3(TrackHalfWidth - 0.25f, 0.02f, z), 0.12f, 0.03f, 2, Color.White);
        }
        foreach (Pedestrian pedestrian in _pedestrians)
            pedestrian.Draw();
        _player.Draw();
        _particles.Draw();
        Raylib.EndMode3D();

        string debug = $"FPS {Raylib.GetFPS()}   Pedestrians {_pedestrians.Count}/{PedestrianSpawner.MaximumPopulation}   Particles {_particles.ActiveCount}";
        int debugWidth = Raylib.MeasureText(debug, 16);
        int debugX = Raylib.GetScreenWidth() - debugWidth - 20;
        Raylib.DrawRectangle(debugX - 8, 16, debugWidth + 16, 28, new Color(12, 20, 30, 180));
        Raylib.DrawText(debug, debugX, 22, 16, Color.LightGray);

        Raylib.DrawRectangle(16, 16, 330, 98, new Color(12, 20, 30, 220));
        Raylib.DrawText($"DISTANCE  {Distance:0} m", 30, 28, 28, Color.White);
        Raylib.DrawText($"TIME  {SurvivalTime:0.0}s    SPEED  {Speed:0} m/s", 30, 66, 18, Color.SkyBlue);
    }
}
