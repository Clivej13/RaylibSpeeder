using System.Text.Json;
using Raylib_cs;
using RaylibGameFramework.Assets;
using RaylibGameFramework.Configuration;
using RaylibGameFramework.Input;
using RaylibGameFramework.Menus;
using RaylibSpeeder.Game;

namespace RaylibSpeeder.Application;

public sealed class GameApplication
{
    private readonly GameConfig _config;
    private readonly InputController _input;
    private readonly MenuManager _menus;
    private readonly MenuManager _gameOverMenu;
    private readonly MenuDefinition _gameOverDefinition;
    private readonly AssetManager _assets;
    private readonly SpeederGame _game;
    private readonly CharacterDefinition _character = new();
    private CharacterCreatorScreen? _characterCreator;
    private GameState _state = GameState.MainMenu;
    private bool _exitRequested;

    public GameApplication(GameConfig config, InputConfig input, MenuConfig menus, AssetConfig assets)
    {
        _config = config;
        _input = new InputController(input);
        // Reflect the loaded window settings instead of trusting duplicated JSON defaults.
        foreach (MenuItemDefinition item in menus.Menus["Options"].Items)
        {
            if (item.Function == "SetFullscreen")
                item.Value = JsonSerializer.SerializeToElement(config.Fullscreen);
            else if (item.Function == "SetVSync")
                item.Value = JsonSerializer.SerializeToElement(config.VSync);
        }
        _menus = new MenuManager(menus, _input, input);
        _gameOverDefinition = menus.Menus["GameOver"];
        _gameOverMenu = new MenuManager(new MenuConfig
        {
            StartMenu = "GameOver",
            Menus = menus.Menus
        }, _input, input);
        _assets = new AssetManager(assets);
        _game = new SpeederGame(_assets);
    }

    public void Run()
    {
        bool windowReady = false;
        try
        {
            ConfigFlags flags = 0;
            if (_config.VSync) flags |= ConfigFlags.VSyncHint;
            if (_config.Fullscreen) flags |= ConfigFlags.FullscreenMode;
            Raylib.SetConfigFlags(flags);
            Raylib.InitWindow(Math.Max(640, _config.WindowWidth), Math.Max(480, _config.WindowHeight),
                _config.WindowTitle);
            windowReady = Raylib.IsWindowReady();
            if (!windowReady)
                throw new InvalidOperationException("Raylib could not initialize the window.");
            Raylib.SetExitKey(KeyboardKey.Null);
            Raylib.SetTargetFPS(Math.Max(1, _config.TargetFps));
            // Keep shared models and clips resident until all pedestrian instances are released.
            _assets.SetRequiredAssets("PlayerShip", "Pedestrian", "PedestrianAnimations");
            while (_assets.HasPendingWork)
                _assets.ProcessNext();

            while (!_exitRequested && !Raylib.WindowShouldClose())
            {
                _input.Update();
                Update(Raylib.GetFrameTime());
                Raylib.BeginDrawing();
                Raylib.ClearBackground(_state == GameState.Playing || _state == GameState.GameOver
                    ? new Color(14, 24, 38, 255)
                    : _state == GameState.CharacterCreator
                        ? new Color(25, 34, 44, 255)
                        : Color.RayWhite);
                if (_state == GameState.Playing)
                    _game.Draw();
                else if (_state == GameState.GameOver)
                {
                    _game.Draw();
                    _gameOverMenu.Draw();
                }
                else if (_state == GameState.CharacterCreator)
                    _characterCreator!.Draw();
                else
                    _menus.Draw();
                Raylib.EndDrawing();
            }
        }
        finally
        {
            if (windowReady)
            {
                try
                {
                    try
                    {
                        _game.ClearPedestrians();
                        LeaveCharacterCreator();
                    }
                    finally { _assets.UnloadAll(); }
                }
                finally { Raylib.CloseWindow(); }
            }
        }
    }

    private void Update(float deltaTime)
    {
        switch (_state)
        {
            case GameState.MainMenu:
                HandleMenuAction(_menus.Update());
                break;
            case GameState.CharacterCreator:
                _characterCreator!.Update(deltaTime);
                if (_characterCreator.StartRequested)
                {
                    LeaveCharacterCreator();
                    _game.Reset(_character);
                    _state = GameState.Playing;
                }
                else if (_characterCreator.BackRequested)
                {
                    LeaveCharacterCreator();
                    _menus.ReturnToStartMenu();
                    _state = GameState.MainMenu;
                }
                break;
            case GameState.Playing:
                if (_input.WasPressed("MenuBack"))
                {
                    ReturnToMainMenu();
                    break;
                }
                // Axis actions retain their physical sign; use magnitudes for each direction.
                float steering = Math.Abs(_input.GetValue("MoveRight")) - Math.Abs(_input.GetValue("MoveLeft"));
                _game.Update(deltaTime, steering);
                if (_game.IsGameOver)
                {
                    _gameOverDefinition.Title = $"Game Over - {_game.Distance:0} m";
                    _gameOverMenu.ReturnToStartMenu();
                    _state = GameState.GameOver;
                }
                break;
            case GameState.GameOver:
                if (_input.WasPressed("MenuBack"))
                    ReturnToMainMenu();
                else
                {
                    _game.Update(deltaTime, 0);
                    HandleMenuAction(_gameOverMenu.Update());
                }
                break;
        }
    }

    private void HandleMenuAction(MenuAction? action)
    {
        switch (action?.Function)
        {
            case "CharacterCreator":
                EnterCharacterCreator();
                break;
            case "StartGame":
                EnterCharacterCreator();
                break;
            case "RetryGame":
                _game.Reset(_character);
                _state = GameState.Playing;
                break;
            case "MainMenu":
                ReturnToMainMenu();
                break;
            case "ExitGame":
                _exitRequested = true;
                break;
            case "SetFullscreen" when action.Value is bool fullscreen:
                if (Raylib.IsWindowFullscreen() != fullscreen)
                    Raylib.ToggleFullscreen();
                _config.Fullscreen = fullscreen;
                break;
            case "SetVSync" when action.Value is bool vsync:
                if (vsync)
                    Raylib.SetWindowState(ConfigFlags.VSyncHint);
                else
                    Raylib.ClearWindowState(ConfigFlags.VSyncHint);
                _config.VSync = vsync;
                break;
        }
    }

    private void EnterCharacterCreator()
    {
        LeaveCharacterCreator();
        _characterCreator = new CharacterCreatorScreen(_assets, _input, _character);
        _state = GameState.CharacterCreator;
    }

    private void LeaveCharacterCreator()
    {
        _characterCreator?.Dispose();
        _characterCreator = null;
    }

    private void ReturnToMainMenu()
    {
        _game.ClearPedestrians();
        LeaveCharacterCreator();
        _menus.ReturnToStartMenu();
        _state = GameState.MainMenu;
    }
}

internal enum GameState
{
    MainMenu,
    CharacterCreator,
    Playing,
    GameOver
}
