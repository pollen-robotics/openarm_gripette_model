#!/usr/bin/env python3
"""Post-process onshape-to-robot MuJoCo output for the OpenArm Gripette model.

Run this after every `onshape-to-robot-mujoco openarm_right` generation.
It applies the following patches to robot.xml:

1. Remove meshdir="assets" from <compiler> and prefix mesh filenames with "assets/"
   → makes robot.xml includable from scene files in other directories

2. Set contype="2" conaffinity="1" on the collision geom class
   → prevents self-collision between adjacent robot links (CAD mesh overlaps)

3. Add the Gripette camera element next to the camera site
   → MuJoCo camera for offscreen rendering (with 180° pitch correction and wide FOV)

Usage:
    cd openarm_gripette_model
    uv run onshape-to-robot-mujoco openarm_right
    python postprocess_mujoco.py
"""

import re
from pathlib import Path

ROBOT_XML = Path(__file__).parent / "openarm_gripette_model" / "openarm_right" / "robot.xml"

# Camera element to insert after the camera site
CAMERA_ELEMENT = (
    '                    <!-- Gripette camera (180° pitch correction from site frame to MuJoCo camera convention) -->\n'
    '                    <!-- fovy=130° for wide pinhole render, fisheye distortion applied in post -->\n'
    '                    <camera name="gripette_cam" pos="0.0687999 0.0662004 0.0260816"'
    ' quat="0.500002 0.499998 0.499998 -0.500002" fovy="130"/>'
)


def postprocess():
    text = ROBOT_XML.read_text()
    original = text

    # 1. Remove meshdir="assets" from compiler, keep other attributes
    text = re.sub(
        r'(<compiler\b[^>]*)\s+meshdir="assets"([^>]*>)',
        r'\1\2',
        text,
    )

    # Prefix mesh file references with assets/
    # <mesh file="foo.stl"/> → <mesh file="assets/foo.stl"/>
    # Skip if already prefixed
    text = re.sub(
        r'<mesh file="(?!assets/)([^"]+)"',
        r'<mesh file="assets/\1"',
        text,
    )

    # 2. Set collision class contype/conaffinity
    text = re.sub(
        r'(<default class="collision">\s*<geom group="3")(\s*/>)',
        r'\1 contype="2" conaffinity="1"\2',
        text,
    )

    # 3. Add Gripette camera after the camera site (if not already present)
    if "gripette_cam" not in text:
        # Find the camera site line and insert after it
        camera_site_pattern = r'(<!-- Frame camera -->\n\s*<site group="3" name="camera"[^/]*/>\n)'
        match = re.search(camera_site_pattern, text)
        if match:
            text = text[:match.end()] + CAMERA_ELEMENT + "\n" + text[match.end():]
        else:
            print("WARNING: Could not find camera site to insert gripette_cam")

    if text != original:
        ROBOT_XML.write_text(text)
        print(f"Patched {ROBOT_XML}")
    else:
        print(f"No changes needed in {ROBOT_XML}")


if __name__ == "__main__":
    postprocess()
