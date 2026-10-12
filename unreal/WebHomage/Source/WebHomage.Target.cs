// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
using UnrealBuildTool;
using System.Collections.Generic;

public class WebHomageTarget : TargetRules
{
	public WebHomageTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("WebHomage");
	}
}
