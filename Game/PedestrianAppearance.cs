using Raylib_cs;

namespace RaylibSpeeder.Game;

// The appearance is generated once and retained for the pedestrian's lifetime.
public readonly record struct PedestrianAppearance(
    Color SkinColor,
    Color HairColor,
    Color ShirtColor,
    Color TrousersColor,
    Color ShoesColor)
{
    private static readonly Color[] SkinColors =
    [
        new(255, 224, 189, 255),
        new(241, 194, 156, 255),
        new(210, 161, 123, 255),
        new(174, 112, 78, 255),
        new(124, 76, 48, 255),
        new(89, 52, 35, 255)
    ];

    private static readonly Color[] HairColors =
    [
        new(24, 21, 20, 255),
        new(54, 35, 25, 255),
        new(92, 57, 35, 255),
        new(184, 139, 76, 255),
        new(128, 57, 35, 255),
        new(128, 128, 128, 255)
    ];

    private static readonly Color[] ShirtColors =
    [
        new(42, 104, 170, 255),
        new(198, 55, 58, 255),
        new(45, 145, 99, 255),
        new(224, 147, 45, 255),
        new(126, 75, 160, 255),
        new(226, 226, 216, 255),
        new(38, 145, 155, 255)
    ];

    private static readonly Color[] TrousersColors =
    [
        new(55, 91, 132, 255),
        new(27, 48, 78, 255),
        new(32, 34, 38, 255),
        new(105, 108, 112, 255),
        new(105, 71, 48, 255),
        new(144, 132, 83, 255)
    ];

    private static readonly Color[] ShoesColors =
    [
        new(26, 28, 31, 255),
        new(54, 51, 48, 255),
        new(82, 82, 78, 255),
        new(106, 76, 53, 255)
    ];

    public static IReadOnlyList<Color> SkinPalette => SkinColors;
    public static IReadOnlyList<Color> HairPalette => HairColors;
    public static IReadOnlyList<Color> ShirtPalette => ShirtColors;
    public static IReadOnlyList<Color> TrousersPalette => TrousersColors;
    public static IReadOnlyList<Color> ShoesPalette => ShoesColors;

    public static PedestrianAppearance Default => new(
        SkinColors[1], HairColors[1], ShirtColors[0], TrousersColors[0], ShoesColors[0]);

    public static PedestrianAppearance Create(Random random) => new(
        Pick(random, SkinColors),
        Pick(random, HairColors),
        Pick(random, ShirtColors),
        Pick(random, TrousersColors),
        Pick(random, ShoesColors));

    private static Color Pick(Random random, Color[] palette) => palette[random.Next(palette.Length)];
}
