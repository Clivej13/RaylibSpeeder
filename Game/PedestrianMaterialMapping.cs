using Raylib_cs;
using RaylibGameFramework.Assets;
using RaylibGameFramework.ThreeD;

namespace RaylibSpeeder.Game;

// Raylib exposes one generated default material before the six materials from pedestrian.glb.
// Keep this model-specific mapping in one place so preview and spawned pedestrians agree.
public static class PedestrianMaterialMapping
{
    public const int Default = 0;
    public const int Skin = 1;
    public const int Hair = 2;
    public const int Shirt = 3;
    public const int Trousers = 4;
    public const int Shoes = 5;
    public const int Details = 6;
    public const int ExpectedMaterialCount = Details + 1;

    public static void Apply(ModelInstance instance, PedestrianAppearance appearance)
    {
        Validate(instance.Model);
        MaterialOverrides.SetAlbedoColor(instance, Skin, appearance.SkinColor);
        MaterialOverrides.SetAlbedoColor(instance, Hair, appearance.HairColor);
        MaterialOverrides.SetAlbedoColor(instance, Shirt, appearance.ShirtColor);
        MaterialOverrides.SetAlbedoColor(instance, Trousers, appearance.TrousersColor);
        MaterialOverrides.SetAlbedoColor(instance, Shoes, appearance.ShoesColor);
        // Details contains the eyes/details material and is intentionally unchanged.
    }

    public static void Validate(Model model)
    {
        if (model.MaterialCount != ExpectedMaterialCount)
        {
            throw new InvalidOperationException(
                $"Pedestrian material layout changed: expected {ExpectedMaterialCount} runtime materials " +
                $"(Default 0, Skin 1, Hair 2, Shirt 3, Trousers 4, Shoes 5, Details 6), " +
                $"but Raylib loaded {model.MaterialCount}.");
        }
    }
}
