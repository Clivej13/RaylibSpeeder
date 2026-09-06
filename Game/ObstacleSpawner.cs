using System.Numerics;

namespace RaylibSpeeder.Game;

public sealed class ObstacleSpawner
{
    private readonly Random _random = new();
    private float _remaining = 0.6f;

    public void Reset() => _remaining = 0.6f;

    public void Update(float deltaTime, float speed, List<Obstacle> obstacles)
    {
        _remaining -= deltaTime;
        if (_remaining > 0)
            return;

        // One box per wave always leaves room to dodge; spacing scales with speed.
        float width = 1.5f + _random.NextSingle() * 1.2f;
        float limit = SpeederGame.TrackHalfWidth - width / 2;
        float x = (_random.NextSingle() * 2 - 1) * limit;
        obstacles.Add(new Obstacle(x, -90f, new Vector3(width, 1.8f + _random.NextSingle(), 2f)));
        _remaining += Math.Max(0.65f, 1.35f - (speed - SpeederGame.InitialSpeed) * 0.012f)
            + _random.NextSingle() * 0.35f;
    }
}
