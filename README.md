# RaylibSpeeder

A primitive-only 3D endless speeder prototype targeting .NET 9.

## Run

```
dotnet restore
dotnet build
dotnet run
```

NuGet.Config uses the shared ../Packages feed for the framework packages and
nuget.org for public dependencies. The project consumes Configuration 0.1.0,
Input 0.1.4, Menus 0.1.1, Assets 0.1.0 and Raylib-cs 8.0.0.

## Play

Choose Start Game. Steer with A/D, left/right arrows, the controller left stick,
or D-pad. Dodge orange boxes and survive to increase your distance score.
The player stays at Z = 0; the track markers and obstacles travel towards you.
Escape/controller B abandons the run and returns to the main menu.

Menus support mouse, arrow keys or controller navigation, Enter/controller A
to confirm, and Escape/controller B to go back. Game Over offers Retry and
Main Menu. Retry resets the player, obstacles, spawn timer, speed and score.

Options applies fullscreen and VSync immediately. Controls uses the framework
menu's keyboard/controller rebinding. Changes last for the current session;
edit the game-owned JSON files for startup defaults. The framework rebinds
the first binding for the selected device family; alternate bindings remain.

## Ownership and tuning

- Application/GameApplication.cs owns the window, package instances and
  MainMenu / Playing / GameOver orchestration.
- Game/SpeederGame.cs owns simulation, distance/time, collision and 3D drawing.
- Game/Player.cs owns bounded, delta-time horizontal steering.
- Game/Obstacle.cs owns box geometry, movement and bounds.
- Game/ObstacleSpawner.cs owns random box placement and wave timing.
- Program.cs loads the four game-owned JSON files through package loaders.
  The project copies these files into build and publish output.
- assets.json intentionally contains an empty catalogue; AssetManager owns
  its lifecycle without adding a second asset system.

Speed rises from 18 to a cap of 55 world units/second at 0.45 units/second
per survival second. One obstacle per wave leaves horizontal escape space.
The 14-unit track constrains the entire player cube. Simulation steps are
at most 1/120 second to prevent high-speed boxes skipping BoundingBox checks.
Frame stalls beyond 0.25 seconds are discarded, so survival time and distance
measure simulated play time. Passed obstacles are removed.

Fixed-camera setup, box bounds and simulation stepping might inform a future
3D framework, but remain game-local until another game demonstrates reuse.
No framework implementation is copied into this repository.

## Manual playtest

1. Start a run with keyboard and controller; check both steering directions,
   proportional stick movement and bounds at both track edges.
2. Survive long enough to see speed and distance increase; pass several boxes
   and deliberately hit one. Confirm simulation/score stop at Game Over.
3. Retry and confirm a centered player, empty track and reset score/speed.
4. Return to Main Menu from Playing and Game Over, then start another run.
5. Exercise Options with mouse, keyboard and controller. Toggle fullscreen
   and VSync, then return; test startup settings by editing config.json.
6. Rebind each movement action in Controls for keyboard and controller,
   return to play, and check the new bindings.
7. Exit through the menu and through the window close button.

Restore and build pass. Interactive rendering, controller hardware and
fullscreen behaviour require a local playtest.
