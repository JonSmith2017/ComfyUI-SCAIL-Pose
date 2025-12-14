import numpy as np
import cv2
from PIL import Image
import pyrender
import trimesh

def render_colored_cylinders(cylinder_specs, focal, princpt, image_size=(1280, 1280), img=None):

    H, W = image_size
    if isinstance(focal, float) or isinstance(focal, int):
        fx, fy = focal, focal
    else:
        fx, fy = focal[0], focal[1]
    cx, cy = princpt


    # Initialize scene
    scene = pyrender.Scene(bg_color=[0, 0, 0, 0], ambient_light=[0.1, 0.1, 0.1])


    # Set up camera
    camera = pyrender.IntrinsicsCamera(fx=fx, fy=fy, cx=cx, cy=cy, znear=0.5, zfar=10000)
    pyrender2opencv = np.array([[1.0, 0, 0, 0],
                                 [0, -1, 0, 0],
                                 [0, 0, -1, 0],
                                 [0, 0, 0, 1]])
    cam_pose = pyrender2opencv @ np.eye(4)
    scene.add(camera, pose=cam_pose)

    # Add light source
    light = pyrender.DirectionalLight(color=np.ones(3), intensity=3.0)
    scene.add(light, pose=cam_pose)

    points_to_draw = []

    for start, end, color in cylinder_specs:
        start = np.array(start)
        end = np.array(end)
        vec = end - start
        height = np.linalg.norm(vec)
        if height == 0:
            continue

        tm = trimesh.creation.cylinder(radius=12, height=height, sections=16)

        # Rotate to align with z-axis
        z_axis = np.array([0, 0, 1])
        axis = np.cross(z_axis, vec)
        if np.linalg.norm(axis) > 1e-6:
            axis = axis / np.linalg.norm(axis)
            angle = np.arccos(np.dot(z_axis, vec) / height)
            rot = trimesh.transformations.rotation_matrix(angle, axis)
            tm.apply_transform(rot)

        tm.apply_translation(start + vec / 2)

        # Material color (supports RGBA)
        rgba = np.array(color)
        material = pyrender.MetallicRoughnessMaterial(
            metallicFactor=0.1,
            roughnessFactor=0.5,
            baseColorFactor=rgba
        )

        mesh = pyrender.Mesh.from_trimesh(tm, material=material)
        scene.add(mesh)

        # Projected points for visualization, check if projection is correct
        x1 = fx * (start[0] / start[2]) + cx
        y1 = fy * (start[1] / start[2]) + cy
        x2 = fx * (end[0] / end[2]) + cx
        y2 = fy * (end[1] / end[2]) + cy
        points_to_draw.append((x1, y1))
        points_to_draw.append((x2, y2))


    # Render
    r = pyrender.OffscreenRenderer(viewport_width=W, viewport_height=H, point_size=1.0)
    color, _ = r.render(scene, flags=pyrender.RenderFlags.RGBA)

    # Post-processing
    color = color.astype(np.float32) / 255.0
    final_img = (color * 255).astype(np.uint8)

    # Draw points, check if projection is correct
    for (x, y) in points_to_draw:
        print(f" debug point: {x}, {y}")
        x_draw = int(x)
        y_draw = int(y)
        cv2.circle(final_img, (x_draw, y_draw), radius=4, color=(0, 255, 0), thickness=-1)

    return Image.fromarray(final_img)

