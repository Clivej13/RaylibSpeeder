using System.Numerics;
using RaylibGameFramework.Assets;

namespace RaylibSpeeder.Game;

public sealed class PedestrianSpawner(AssetManager assets)
{
    public const int MaximumPopulation = 22;
    private const float InitialDelay = 0.6f;
    private readonly Random _random = new();
    private float _remaining = InitialDelay;

    public void Reset() => _remaining = InitialDelay;

    public void Update(float deltaTime, List<Pedestrian> pedestrians)
    {
        // Do not accumulate a spawn backlog while full.
        if (pedestrians.Count >= MaximumPopulation)
            return;

        _remaining -= deltaTime;
        if (_remaining > 0)
            return;

        int side = _random.Next(2) == 0 ? -1 : 1;
        Vector3 scale = CreateBodyScale();
        PedestrianAppearance appearance = PedestrianAppearance.Create(_random);
        float scaledWidth = Pedestrian.Width * scale.X;
        float limit = SpeederGame.TrackHalfWidth - scaledWidth / 2;
        // Start in the opposite half so even fast runners have time on the road.
        // Overlap is deliberately unrestricted for the animation stress test.
        float x = -side * _random.NextSingle() * limit;
        float destinationX = side * (SpeederGame.TrackHalfWidth + scaledWidth / 2);
        pedestrians.Add(new Pedestrian(assets, x, -90f, destinationX,
            2.8f + _random.NextSingle() * 0.8f,
            0.8f + _random.NextSingle() * 0.4f, _random.NextSingle(), scale, appearance));
        // Reach 22 in roughly 1.8 seconds, before the earliest departure.
        // Replacements also arrive one at a time, including after frame stalls.
        _remaining = 0.045f + _random.NextSingle() * 0.02f;
    }

    private Vector3 CreateBodyScale()
    {
        // One shared build value prevents implausible combinations. Positive means broader/heavier;
        // negative means taller/slimmer. Small independent noise keeps the crowd from looking uniform.
        float build = _random.NextSingle() * 2f - 1f;
        float height = Math.Clamp(1f - build * 0.10f + Jitter(0.035f), 0.85f, 1.15f);
        float width = Math.Clamp(1f + build * 0.16f + Jitter(0.035f), 0.82f, 1.20f);
        float depth = Math.Clamp(1f + build * 0.04f + Jitter(0.02f), 0.90f, 1.10f);
        return new Vector3(width, height, depth);
    }

    private float Jitter(float range) => (_random.NextSingle() * 2f - 1f) * range;
}
