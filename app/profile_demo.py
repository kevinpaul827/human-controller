"""Quick manual demo for ProfileManager."""

from __future__ import annotations

import json
from pathlib import Path

from app.profile_manager import GameProfile, GestureBinding, PatientProfile, ProfileManager
from app.profile_manager.exceptions import ProfileAlreadyExistsError, ProfileNotFoundError

PROFILES_DIR = Path(__file__).resolve().parent / "data" / "profiles"


def main() -> None:
    manager = ProfileManager(PROFILES_DIR)

    profile = PatientProfile(
        patient_id="patient-b",
        patient_name="Patient B",
        notes="Created from profile_demo.py",
        game_profiles=[
            GameProfile(
                game_name="Celeste",
                gestures=[
                    GestureBinding(name="Lean Left", key="ArrowLeft", threshold=0.78),
                    GestureBinding(name="Lean Right", key="ArrowRight", threshold=0.8),
                ],
            )
        ],
    )

    saved_path = manager.save(profile)
    print(f"Saved profile to: {saved_path}")

    loaded = manager.load("patient-b")
    print(f"Loaded patient: {loaded.patient_name}")
    print(f"Gesture count: {sum(len(game.gestures) for game in loaded.game_profiles)}")

    duplicate_id = "patient-b-copy"
    try:
        duplicate = manager.duplicate("patient-b", duplicate_id)
        print(f"Duplicated profile: {duplicate.patient_id} -> {duplicate.patient_name}")
    except ProfileAlreadyExistsError:
        duplicate = manager.load(duplicate_id)
        print(f"Duplicate skipped (already exists): {duplicate.patient_id} -> {duplicate.patient_name}")

    delete_demo_id = "demo-delete-target"
    if not manager.exists(delete_demo_id):
        manager.save(
            PatientProfile(
                patient_id=delete_demo_id,
                patient_name="Delete Demo",
                game_profiles=[
                    GameProfile(
                        game_name="Temp Game",
                        gestures=[GestureBinding(name="Wave", key="W")],
                    )
                ],
            )
        )
    print(f"Before delete, exists({delete_demo_id}): {manager.exists(delete_demo_id)}")
    manager.delete(delete_demo_id)
    print(f"Deleted profile: {delete_demo_id}")
    print(f"After delete, exists({delete_demo_id}): {manager.exists(delete_demo_id)}")
    try:
        manager.load(delete_demo_id)
    except ProfileNotFoundError:
        print(f"load({delete_demo_id}) correctly raised ProfileNotFoundError")

    print("\nAll profiles:")
    for item in manager.list_profiles():
        games = ", ".join(game.game_name for game in item.game_profiles)
        gesture_total = sum(len(game.gestures) for game in item.game_profiles)
        print(f"- {item.patient_id}: {item.patient_name} | games=[{games}] | gestures={gesture_total}")

    print("\nJSON schema excerpt:")
    schema = manager.export_schema()
    print(json.dumps({"schemaVersion": schema.get("properties", {}).get("schemaVersion")}, indent=2))


if __name__ == "__main__":
    main()
