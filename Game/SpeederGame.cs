using System.Numerics;
using Raylib_cs;

namespace RaylibSpeeder.Game;

public sealed class SpeederGame
{
    public const float TrackHalfWidth = 7f;
    public const float InitialSpeed = 18f;
    private const float MaximumSpeed = 55f;
    private readonly Player _player = new();
    private readonly List<Obstacle> _obstacles = [];
    private readonly ObstacleSpawner _spawner = new();
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

    public void Reset()
    {
        _player.Reset();
        _obstacles.Clear();
        _spawner.Reset();
        Speed = InitialSpeed;
        Distance = 0;
        SurvivalTime = 0;
        IsGameOver = false;
    }

    public void Update(float deltaTime, float steering)
    {
        if (IsGameOver || !float.IsFinite(deltaTime) || deltaTime <= 0)
            return;

        // Discard long stalls, and subdivide movement so boxes cannot skip the player.
        float remaining = Math.Min(deltaTime, 0.25f);
        while (remaining > 0 && !IsGameOver)
        {
            float step = Math.Min(remaining, 1f / 120f);
            remaining -= step;
            _player.Update(steering, step);
            SurvivalTime += step;
            Speed = Math.Min(MaximumSpeed, InitialSpeed + (float)SurvivalTime * 0.45f);
            float distance = Speed * step;
            Distance += distance;
            _spawner.Update(step, Speed, _obstacles);
            foreach (Obstacle obstacle in _obstacles)
            {
                obstacle.Update(distance);
                if (Raylib.CheckCollisionBoxes(_player.Bounds, obstacle.Bounds))
                    IsGameOver = true;
            }
            _obstacles.RemoveAll(obstacle => obstacle.HasPassed);
        }
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
        foreach (Obstacle obstacle in _obstacles)
            obstacle.Draw();
        _player.Draw();
        Raylib.EndMode3D();

        Raylib.DrawRectangle(16, 16, 330, 98, new Color(12, 20, 30, 220));
        Raylib.DrawText($"DISTANCE  {Distance:0} m", 30, 28, 28, Color.White);
        Raylib.DrawText($"TIME  {SurvivalTime:0.0}s    SPEED  {Speed:0} m/s", 30, 66, 18, Color.SkyBlue);
    }
}
