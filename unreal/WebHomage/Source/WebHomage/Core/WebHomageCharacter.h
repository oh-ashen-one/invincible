// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "InputActionValue.h"
#include "WebHomageCharacter.generated.h"

class USpringArmComponent;
class UCameraComponent;
class UStaticMeshComponent;
class UInputAction;
class UInputMappingContext;

/**
 * Third-person placeholder hero: capsule + visible cylinder proxy, spring-arm camera,
 * Enhanced Input (WASD move, mouse look, Space jump, gamepad sticks/face button).
 *
 * Input assets are optional: if MappingContext/MoveAction/... are left null, the character
 * builds transient UInputAction / UInputMappingContext objects at runtime, so the project
 * runs with zero input .uasset files. Later pieces can assign real assets in a subclass/BP.
 *
 * Automation: console variable `wh.AutoMove 1` (or command line `-WHAutoMove`) makes the
 * character run forward, turn slowly and jump every few seconds, for unattended
 * capture/perf runs of real movement.
 */
UCLASS(config=Game)
class WEBHOMAGE_API AWebHomageCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	AWebHomageCharacter();

	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION(BlueprintPure, Category="WebHomage")
	USpringArmComponent* GetCameraBoom() const { return CameraBoom; }

	UFUNCTION(BlueprintPure, Category="WebHomage")
	UCameraComponent* GetFollowCamera() const { return FollowCamera; }

protected:
	virtual void BeginPlay() override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void NotifyControllerChanged() override;

	void Move(const FInputActionValue& Value);
	void Look(const FInputActionValue& Value);

	/** Creates transient input actions/mapping for any that are not assigned. */
	void EnsureDefaultInput();
	void AddMappingContext();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Camera")
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Camera")
	TObjectPtr<UCameraComponent> FollowCamera;

	/** Visible stand-in for the hero mesh (engine cylinder). Hidden once a skeletal mesh is set. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Placeholder")
	TObjectPtr<UStaticMeshComponent> ProxyBody;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Input")
	TObjectPtr<UInputMappingContext> MappingContext;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Input")
	TObjectPtr<UInputAction> MoveAction;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Input")
	TObjectPtr<UInputAction> LookAction;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Input")
	TObjectPtr<UInputAction> JumpAction;

	/** Mouse look sensitivity multiplier (degrees per mouse unit). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Input")
	float LookSensitivity = 1.0f;

private:
	float AutoMoveJumpTimer = 0.f;
};
