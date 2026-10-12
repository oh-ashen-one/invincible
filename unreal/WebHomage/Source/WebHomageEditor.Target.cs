// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
using UnrealBuildTool;
using System.Collections.Generic;

public class WebHomageEditorTarget : TargetRules
{
	public WebHomageEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("WebHomage");
	}
}
