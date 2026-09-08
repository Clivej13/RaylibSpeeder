using System.Numerics;
using Raylib_cs;
using RaylibGameFramework.Assets;
using RaylibGameFramework.Input;
using RaylibGameFramework.ThreeD;
using RaylibSpeeder.Game;

namespace RaylibSpeeder.Application;

public sealed class CharacterCreatorScreen : IDisposable
{
    private readonly AssetManager _assets;
    private readonly InputController _input;
    private readonly CharacterDefinition _character;
    private readonly ModelInstance _preview;
    private readonly int _runIndex;
    private readonly AnimationPlayer _animation;
    private Transform3D _transform = Transform3D.Identity;
    private readonly Camera3D _camera = new()
    {
        Position = new Vector3(2.7f, 1.55f, 5.3f),
        Target = new Vector3(0, 0.9f, 0),
        Up = Vector3.UnitY,
        FovY = 35,
        Projection = CameraProjection.Perspective
    };
    private float _rotationDegrees;
    private int _selection;
    private bool _disposed;

    private static readonly string[] OptionNames =
    [
        "Height", "Build / Width", "Depth", "Skin", "Hair", "Shirt",
        "Trousers", "Shoes", "Start Game", "Back"
    ];

    public bool StartRequested { get; private set; }
    public bool BackRequested { get; private set; }

    public CharacterCreatorScreen(
        AssetManager assets, InputController input, CharacterDefinition character)
    {
        _assets = assets;
        _input = input;
        _character = character;
        ReadOnlySpan<ModelAnimation> animations = assets.GetModelAnimations("PedestrianAnimations");
        _runIndex = FindRunAnimation(animations);
        if (_runIndex < 0)
            throw new InvalidOperationException("PedestrianAnimations must contain a non-empty Run clip.");

        _preview = assets.CreateModelInstance("Pedestrian");
        try
        {
            _animation = new AnimationPlayer(_preview, animations[_runIndex]);
            ApplyAppearance();
        }
        catch
        {
            assets.ReleaseModelInstance(_preview);
            throw;
        }
    }

    public void Update(float deltaTime)
    {
        if (_disposed)
            return;

        if (_input.WasPressed("MenuBack"))
        {
            BackRequested = true;
            return;
        }

        if (_input.WasPressed("MenuUp"))
            _selection = (_selection + OptionNames.Length - 1) % OptionNames.Length;
        if (_input.WasPressed("MenuDown"))
            _selection = (_selection + 1) % OptionNames.Length;

        float horizontal = Math.Abs(_input.GetValue("MoveRight"))
            - Math.Abs(_input.GetValue("MoveLeft"));
        if (MathF.Abs(horizontal) > 0.05f)
            _rotationDegrees += horizontal * 120f * deltaTime;
        else
            _rotationDegrees += 12f * deltaTime;

        if (_input.WasPressed("MenuLeft"))
            ChangeSelection(-1);
        if (_input.WasPressed("MenuRight"))
            ChangeSelection(1);
        if (_input.WasPressed("MenuConfirm"))
        {
            if (_selection == 8)
                StartRequested = true;
            else if (_selection == 9)
                BackRequested = true;
        }

        _animation.Update(deltaTime);
    }

    private void ChangeSelection(int direction)
    {
        switch (_selection)
        {
            case 0:
                _character.Scale = new Vector3(
                    _character.Scale.X,
                    Math.Clamp(_character.Scale.Y + direction * 0.01f, 0.85f, 1.15f),
                    _character.Scale.Z);
                break;
            case 1:
                _character.Scale = new Vector3(
                    Math.Clamp(_character.Scale.X + direction * 0.01f, 0.82f, 1.20f),
                    _character.Scale.Y,
                    _character.Scale.Z);
                break;
            case 2:
                _character.Scale = new Vector3(
                    _character.Scale.X,
                    _character.Scale.Y,
                    Math.Clamp(_character.Scale.Z + direction * 0.01f, 0.90f, 1.10f));
                break;
            case 3:
                _character.SkinColor = Cycle(PedestrianAppearance.SkinPalette, _character.SkinColor, direction);
                ApplyAppearance();
                break;
            case 4:
                _character.HairColor = Cycle(PedestrianAppearance.HairPalette, _character.HairColor, direction);
                ApplyAppearance();
                break;
            case 5:
                _character.ShirtColor = Cycle(PedestrianAppearance.ShirtPalette, _character.ShirtColor, direction);
                ApplyAppearance();
                break;
            case 6:
                _character.TrousersColor = Cycle(PedestrianAppearance.TrousersPalette, _character.TrousersColor, direction);
                ApplyAppearance();
                break;
            case 7:
                _character.ShoesColor = Cycle(PedestrianAppearance.ShoesPalette, _character.ShoesColor, direction);
                ApplyAppearance();
                break;
        }
    }

    private static Color Cycle(IReadOnlyList<Color> palette, Color current, int direction)
    {
        int index = 0;
        for (int i = 0; i < palette.Count; i++)
        {
            if (palette[i].Equals(current))
            {
                index = i;
                break;
            }
        }
        return palette[(index + direction + palette.Count) % palette.Count];
    }

    private void ApplyAppearance()
    {
        PedestrianMaterialMapping.Apply(_preview, _character.ToAppearance());
    }

    private static int FindRunAnimation(ReadOnlySpan<ModelAnimation> animations)
    {
        for (int i = 0; i < animations.Length; i++)
        {
            if (animations[i].NameToString() == "Run" && animations[i].KeyFrameCount > 0)
                return i;
        }
        return -1;
    }

    public void Draw()
    {
        if (_disposed)
            return;

        Raylib.BeginMode3D(_camera);
        Raylib.DrawPlane(new Vector3(0, -0.03f, 0), new Vector2(8, 8), new Color(40, 51, 62, 255));
        Raylib.DrawGrid(8, 1f);
        _transform = new Transform3D(Vector3.Zero,
            Quaternion.CreateFromAxisAngle(Vector3.UnitY, _rotationDegrees * MathF.PI / 180f), _character.Scale);
        Raylib.DrawModelEx(_preview.Model, _transform.Position, Vector3.UnitY, _rotationDegrees,
            _transform.Scale, Color.White);
        Raylib.EndMode3D();

        int width = Raylib.GetScreenWidth();
        Raylib.DrawRectangle(0, 0, width, 76, new Color(12, 20, 30, 245));
        Raylib.DrawText("CHARACTER CREATOR", 32, 22, 30, Color.White);
        Raylib.DrawText("Configure one pedestrian before entering Speeder", 36, 53, 16, Color.LightGray);

        int panelX = Math.Max(24, width - 380);
        Raylib.DrawRectangle(panelX, 104, 340, 492, new Color(12, 20, 30, 235));
        Raylib.DrawText("CHARACTER", panelX + 24, 126, 22, Color.SkyBlue);
        for (int i = 0; i < OptionNames.Length; i++)
        {
            int y = 166 + i * 39;
            bool selected = i == _selection;
            if (selected)
                Raylib.DrawRectangle(panelX + 14, y - 5, 312, 32, new Color(48, 102, 148, 255));
            Raylib.DrawText(OptionNames[i], panelX + 26, y, 18, Color.White);
            Raylib.DrawText(ValueText(i), panelX + 190, y, 18, selected ? Color.White : Color.LightGray);
        }

        Raylib.DrawText("UP/DOWN select   LEFT/RIGHT change", 32, Raylib.GetScreenHeight() - 60, 17, Color.White);
        Raylib.DrawText("A/D or left stick rotate   ENTER choose   ESC back",
            32, Raylib.GetScreenHeight() - 34, 16, Color.LightGray);
    }

    private string ValueText(int option)
    {
        return option switch
        {
            0 => _character.Scale.Y.ToString("0.00"),
            1 => _character.Scale.X.ToString("0.00"),
            2 => _character.Scale.Z.ToString("0.00"),
            3 => PaletteIndex(PedestrianAppearance.SkinPalette, _character.SkinColor),
            4 => PaletteIndex(PedestrianAppearance.HairPalette, _character.HairColor),
            5 => PaletteIndex(PedestrianAppearance.ShirtPalette, _character.ShirtColor),
            6 => PaletteIndex(PedestrianAppearance.TrousersPalette, _character.TrousersColor),
            7 => PaletteIndex(PedestrianAppearance.ShoesPalette, _character.ShoesColor),
            _ => ""
        };
    }

    private static string PaletteIndex(IReadOnlyList<Color> palette, Color color)
    {
        for (int i = 0; i < palette.Count; i++)
        {
            if (palette[i].Equals(color))
                return $"{i + 1}/{palette.Count}";
        }
        return "-";
    }

    public void Dispose()
    {
        if (_disposed)
            return;
        _assets.ReleaseModelInstance(_preview);
        _disposed = true;
    }
}
