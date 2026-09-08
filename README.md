# RaylibSpeeder

A 3D endless speeder prototype with animated pedestrians targeting .NET 9.

## Run

```
dotnet restore
dotnet build
dotnet run
```

NuGet.Config uses the shared ../Packages feed for the framework packages and
nuget.org for public dependencies. The project consumes Configuration 0.1.0,
Input 0.1.4, Menus 0.1.1, Assets 0.1.3 and Raylib-cs 8.0.0.

## Play

Choose Character Creator, configure a pedestrian, then choose Start Game. The creator
supports height, build/width, depth, five curated appearance palettes, and a rotating
animated preview. Steer Speeder with A/D, left/right arrows, the controller left stick,
or D-pad. Dodge running pedestrians and survive to increase your distance score.
The player stays at Z = 0; the track markers and pedestrians travel towards you.
Escape/controller B abandons the run and returns to the main menu.

Menus support mouse, arrow keys or controller navigation, Enter/controller A
to confirm, and Escape/controller B to go back. Game Over offers Retry and
Main Menu. Retry resets the player, pedestrians, spawn timer, speed and score.

Options applies fullscreen and VSync immediately. Controls uses the framework
menu's keyboard/controller rebinding. Changes last for the current session;
edit the game-owned JSON files for startup defaults. The framework rebinds
the first binding for the selected device family; alternate bindings remain.

## Ownership and tuning

- Application/GameApplication.cs owns the window, package instances and
  MainMenu / CharacterCreator / Playing / GameOver orchestration.
- Application/CharacterCreatorScreen.cs owns one preview ModelInstance, its Run playback,
  immediate scale/material updates, and release on leaving the screen.
- Game/CharacterDefinition.cs contains only the selected character data; SpeederGame retains
  it as SelectedCharacter without replacing the player ship.
- Game/SpeederGame.cs owns simulation, distance/time, collision and 3D drawing.
- Game/Player.cs owns bounded, delta-time horizontal steering.
- Game/Pedestrian.cs owns an independent model instance, Run playback, movement and bounds.
- Game/PedestrianSpawner.cs owns random pedestrian placement, correlated body-scale variation and spawn timing.
- Program.cs loads the four game-owned JSON files through package loaders.
  The project copies these files into build and publish output.
- assets.json registers PlayerShip, Pedestrian and PedestrianAnimations. Both GLBs
  are copied to build/publish output. AssetManager owns all model and clip loading.
  Each pedestrian creates its own ModelInstance and releases it on removal;
  reset, menu return and shutdown release all remaining instances before UnloadAll.
  Shared Run clips play at 60 sampled frames/second using per-instance delta-time
  frame accumulation, modulo KeyFrameCount, with random initial phases.

Speed rises from 18 to a cap of 55 world units/second at 0.45 units/second
per survival second. The stress test caps the live population at 22. After a
0.6-second delay, one pedestrian spawns every 0.045-0.065 simulated seconds
(rounded to simulation steps), reaching 22 at about two seconds. Full capacity
pauses the timer; departures are replaced gradually without a spawn backlog.
Overlap is unrestricted.

Pedestrians spawn at Z = -90 in the half opposite their randomly chosen destination
side. Each owns a constant running velocity: 2.8-3.6 units/second laterally and
0.8-1.2 along +Z. Speeder scrolling adds game speed along +Z separately.
Yaw is atan2(-runningVelocity.X, -runningVelocity.Z) in degrees about +Y,
mapping the source model's -Z forward to its road-relative running direction.
Each spawn also receives one correlated non-uniform body scale: X is 0.82-1.20,
Y is 0.85-1.15 and Z is 0.90-1.10. A shared build value makes taller runners
slightly slimmer and shorter runners sometimes broader, while small per-axis
jitter avoids identical proportions. DrawModelEx uses each pedestrian's yaw and
scale; the Blender asset is unchanged. The forgiving collision box derives from
the 0.926 x 1.80 x 0.325 model dimensions and is scaled on all three axes.
Shared world scrolling does not change facing or drive animation.
A small top-right display shows FPS and active pedestrians / 22.
The 14-unit track constrains the entire player cube. Simulation steps are
at most 1/120 second to prevent high-speed pedestrians skipping BoundingBox checks.
Frame stalls beyond 0.25 seconds are discarded, so survival time and distance
measure simulated play time. Pedestrians beyond Z = 12.15 or reaching their destination
half a model width beyond the road edge are released and removed. Game Over
immediately releases all remaining instances; reset, menu return and shutdown
also clear them safely. No pooling is used. Collision uses a forgiving
0.75 x 1.7 x 0.30 bounding box above each pedestrian's ground origin;
any overlap with the player's box triggers Game Over.

Fixed-camera setup, box bounds and simulation stepping might inform a future
3D framework, but remain game-local until another game demonstrates reuse.
No framework implementation is copied into this repository.

## Manual playtest

1. Start a run with keyboard and controller; check both steering directions,
   proportional stick movement and bounds at both track edges.
2. Survive long enough to see speed and distance increase; pass several pedestrians
   and deliberately hit one. Confirm simulation/score stop at Game Over.
3. Retry and confirm a centered player, empty track and reset score/speed.
4. Return to Main Menu from Playing and Game Over, then start another run.
5. Exercise Options with mouse, keyboard and controller. Toggle fullscreen
   and VSync, then return; test startup settings by editing config.json.
6. Rebind each movement action in Controls for keyboard and controller,
   return to play, and check the new bindings.
7. From Main Menu enter Character Creator, change each body and appearance option,
   confirm the animated preview, use Back, re-enter, then choose Start Game and confirm
   the selection persists. Repeat entering/backing out while monitoring instance usage.
8. Exit through the menu and through the window close button.

9. Watch the counter reach 22, with runners facing their chosen left/right side,
   using different animation phases, and visibly varied tall/short and broad/thin
   proportions. Confirm replacements after side/rear exits. Bounds stay axis-aligned,
   follow each model's ground position and scale with each body.
9. Record FPS with 22 active pedestrians, then repeat with VSync disabled to
   distinguish the configured frame cap from animation/rendering cost. Repeat
   collisions, Retry and menu returns while monitoring instance/resource usage.

Restore, build (zero warnings/errors) and Release publish pass for the directional
stress test. Runtime launch via the workspace validator is unavailable:
dotnet run is not an allowed validation subcommand. Left/right facing and FPS at
22 have therefore not been visually measured here and require a local playtest.

Potential future ThreeD candidates are clip lookup/playback (phase, elapsed-frame
accumulation and avoiding redundant pose updates), instance ownership/release,
and a Transform3D holding position, yaw and non-uniform scale for source-forward-aware
drawing plus position-relative bounds. The new pedestrian scale makes that transform
extraction more clearly justified, but it remains game-local until another game
demonstrates reuse; population tuning, road scrolling and collision outcomes belong here.
