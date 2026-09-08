using RaylibGameFramework.Assets;
using RaylibGameFramework.Configuration;
using RaylibGameFramework.Input;
using RaylibGameFramework.Menus;
using RaylibSpeeder.Application;

var application = new GameApplication(
    ConfigLoader.Load("config.json"),
    InputConfigLoader.Load("input.json"),
    MenuConfigLoader.Load("menu.json"),
    AssetConfigLoader.Load("assets.json"));
application.Run();
