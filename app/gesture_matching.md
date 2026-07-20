**Gesture Matching Integration Plan**

1. **Define the app-side contract**
   - Decide what a gesture match result looks like in the desktop app, for example: `gestureId`, `score`, `timestamp`, and `matched`.
   - Keep this payload stable so `SessionBridge` and the frontend can consume it cleanly.

2. **Add an app-side gesture matching layer**
   - Create `app/gesture_matcher.py` as a thin wrapper around `backend/matching_engine/matching/pose_matcher.py`.
   - This wrapper should convert live pose output into the matcher’s expected input format and manage loaded gesture templates.

3. **Keep `PoseProcessor` focused on pose extraction**
   - Leave `app/pose_processor.py` responsible for turning frames into pose landmarks only.
   - If needed, extend its emitted pose payload slightly so downstream matching has enough data.

4. **Run matching from `CameraManager`**
   - In `app/camera_manager.py`, after pose estimation succeeds, call the new `GestureMatcher`.
   - Emit a new signal like `gestureMatched` or `matchUpdated` alongside the existing pose/frame flow.

5. **Forward results through `SessionBridge`**
   - In `app/session_bridge.py`, add a Qt signal for gesture match updates.
   - Subscribe to the new `CameraManager` signal and re-emit the match payload to the frontend.

6. **Expose the bridge event in the frontend**
   - In `frontend/src/services/sessionBridge.ts`, add a listener method for the new gesture-match signal.
   - Mirror the existing `onSessionStatus` / `onPreviewAspectRatio` pattern.

7. **Add frontend types**
   - In `frontend/src/types/session.ts`, define the TypeScript type for gesture match events.
   - Keep it aligned with the Python payload shape.

8. **Integrate into UI**
   - Update the relevant session/calibration page or component to subscribe to gesture matches.
   - Use the result for UI feedback, state changes, or action triggering.

9. **Template and config handling**
   - Decide where gesture templates come from: hardcoded, local file, or backend API.
   - Load them once, not per frame, to avoid unnecessary overhead.

10. **Validate end-to-end**
   - Test this path: `camera -> pose extraction -> gesture matching -> session bridge -> frontend update`.
   - Verify behavior for no pose detected, low-confidence matches, and matcher errors.

**Files likely involved**

- `app/gesture_matcher.py`
- `app/camera_manager.py`
- `app/session_bridge.py`
- `app/pose_processor.py`
- `backend/matching_engine/matching/pose_matcher.py`
- `frontend/src/services/sessionBridge.ts`
- `frontend/src/types/session.ts`
- relevant frontend session UI component(s)

**Recommended architecture**

```text
camera -> CameraManager -> PoseProcessor -> GestureMatcher -> CameraManager -> SessionBridge -> frontend
```

If you want, I can turn this into a more concrete implementation checklist tied to your exact files and signal names.