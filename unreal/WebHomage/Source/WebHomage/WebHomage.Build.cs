// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
using UnrealBuildTool;

public class WebHomage : ModuleRules
{
	public WebHomage(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		// Sub-folders (Core, Traversal, Combat, ...) are include roots so pieces can
		// #include "Core/WebHomageCharacter.h" style paths.
		PublicIncludePaths.Add(ModuleDirectory);

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"UMG",
			"Niagara",
			"AnimGraphRuntime",
			"GeometryCollectionEngine",
			"Chaos",
			"PhysicsCore",
			"Json",
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"Slate",
			"SlateCore",
			"RHI",
			"ApplicationCore", // FDisplayMetrics (settings menu: window mode at desktop resolution)
		});
	}
}
