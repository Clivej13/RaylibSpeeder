using System.Numerics;
using Raylib_cs;

namespace RaylibSpeeder.Game;

// Game-local character data. Native model resources belong to the screen that previews them.
public sealed class CharacterDefinition
{
    public Vector3 Scale { get; set; } = Vector3.One;
    public Color SkinColor { get; set; }
    public Color HairColor { get; set; }
    public Color ShirtColor { get; set; }
    public Color TrousersColor { get; set; }
    public Color ShoesColor { get; set; }

    public CharacterDefinition()
    {
        PedestrianAppearance appearance = PedestrianAppearance.Default;
        SkinColor = appearance.SkinColor;
        HairColor = appearance.HairColor;
        ShirtColor = appearance.ShirtColor;
        TrousersColor = appearance.TrousersColor;
        ShoesColor = appearance.ShoesColor;
    }

    public PedestrianAppearance ToAppearance() => new(
        SkinColor, HairColor, ShirtColor, TrousersColor, ShoesColor);
}
