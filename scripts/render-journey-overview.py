#!/usr/bin/env python3
"""Blender EEVEE scene renderer. Run with Blender --background --python FILE -- ...

--work SCRATCH --chapter day-02 [--sample] [--preview-scale 50]
The scene is deterministic. Frames are written only to the external scratch
directory; encode-journey-overview.py consumes one chapter at a time.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
COLORS = {"rail": "315a47", "cable_car": "39758e", "bus": "aa6a2b",
          "rideshare": "6f5968", "hike": "b44f39", "paper": "f2ede0",
          "cream": "faf6ec", "ink": "302f27", "water": "6eafb4", "dark": "273b36"}
MODE_NAMES = {"rail": "RAIL", "cable_car": "CABLE CAR", "bus": "BUS", "rideshare": "CAR", "hike": "HIKE"}
RADIUS = 6371.0088


def rgb(value):
    channels = [int(value[i:i+2], 16)/255 for i in (0, 2, 4)]
    return tuple(c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in channels)


def project(point):
    return np.array([(point[0]-9)*math.pi/180*RADIUS*math.cos(math.radians(47)),
                     (point[1]-47)*math.pi/180*RADIUS])


def material(name, color, emission=False):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb(color), 1)
    mat.use_nodes = True
    tree = mat.node_tree
    bsdf = tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb(color), 1)
    bsdf.inputs["Roughness"].default_value = .85
    if emission:
        tree.nodes.remove(bsdf)
        emitter = tree.nodes.new("ShaderNodeEmission")
        emitter.inputs["Color"].default_value = (*rgb(color), 1)
        tree.links.new(emitter.outputs[0], tree.nodes.get("Material Output").inputs[0])
    return mat


def cube(name, position, scale, mat, parent=None, bevel=.05):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    if bevel:
        mod = ob.modifiers.new("Soft model edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        ob.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    if parent:
        ob.parent = parent
    return ob


def sphere(name, position, scale, mat, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=1, location=position)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    ob.data.materials.append(mat)
    for poly in ob.data.polygons:
        poly.use_smooth = True
    if parent:
        ob.parent = parent
    return ob


def line(name, points, width, mat, parent=None):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 1
    data.bevel_depth = width
    data.bevel_resolution = 1
    spline = data.splines.new("POLY")
    spline.points.add(len(points)-1)
    for point, co in zip(spline.points, points):
        point.co = (*co, 1)
    ob = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(ob)
    data.materials.append(mat)
    if parent:
        ob.parent = parent
    return ob


def text(name, value, position, size, mat, font, parent=None, align="LEFT"):
    data = bpy.data.curves.new(name, "FONT")
    data.body = value
    data.font = font
    data.size = size
    data.align_x = align
    data.space_line = 1.12
    ob = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(ob)
    ob.location = position
    data.materials.append(mat)
    if parent:
        ob.parent = parent
    return ob


class Terrain:
    def __init__(self, path):
        data = np.load(path)
        self.x, self.y, self.z = data["x"], data["y"], data["z"]
        self.water, self.forest = data["water"], data["forest"]

    def height(self, x, y):
        u = np.clip((np.asarray(x)-self.x[0])/(self.x[-1]-self.x[0])*(len(self.x)-1), 0, len(self.x)-1.001)
        v = np.clip((np.asarray(y)-self.y[0])/(self.y[-1]-self.y[0])*(len(self.y)-1), 0, len(self.y)-1.001)
        i, j = u.astype(int), v.astype(int)
        a, b = u-i, v-j
        return ((1-a)*(1-b)*self.z[j, i]+a*(1-b)*self.z[j, i+1]
                +(1-a)*b*self.z[j+1, i]+a*b*self.z[j+1, i+1])

    def build(self):
        ny, nx = self.z.shape
        xx, yy = np.meshgrid(self.x, self.y)
        vertices = np.column_stack((xx.ravel(), yy.ravel(), self.z.ravel()))
        corners = (np.arange(ny-1)[:, None]*nx + np.arange(nx-1)).ravel()
        faces = np.column_stack((corners, corners+1, corners+nx+1, corners+nx)).astype(np.int32)
        mesh = bpy.data.meshes.new("Copernicus surface")
        mesh.vertices.add(len(vertices))
        mesh.vertices.foreach_set("co", vertices.ravel())
        mesh.loops.add(faces.size)
        mesh.loops.foreach_set("vertex_index", faces.ravel())
        mesh.polygons.add(len(faces))
        mesh.polygons.foreach_set("loop_start", np.arange(0, faces.size, 4, dtype=np.int32))
        mesh.polygons.foreach_set("loop_total", np.full(len(faces), 4, dtype=np.int32))
        mesh.polygons.foreach_set("use_smooth", np.ones(len(faces), dtype=bool))
        mesh.update()
        ob = bpy.data.objects.new("Real Alpine relief", mesh)
        bpy.context.collection.objects.link(ob)
        grad_y, grad_x = np.gradient(self.z, self.y[1]-self.y[0], self.x[1]-self.x[0])
        slope = np.hypot(grad_x, grad_y)
        low = np.array(rgb("adbb94"))
        high = np.array(rgb("dfd5bf"))
        stone = np.clip((self.z-1.65)/1.8 + np.maximum(slope-.5, 0)*.7, 0, 1)
        colors = low[None, None, :]*(1-stone[:, :, None]) + high[None, None, :]*stone[:, :, None]
        forest = (self.forest/255*.6)[:, :, None]
        colors = colors*(1-forest)+np.array(rgb("56775e"))*forest
        snow = np.clip((self.z-3.05)/.6, 0, 1)[:, :, None]
        colors = colors*(1-snow)+np.array(rgb("f4f0e6"))*snow
        colors[self.water > 128] = rgb(COLORS["water"])
        rgba = np.column_stack((colors.reshape(-1, 3), np.ones(nx*ny))).astype(np.float32)
        attribute = mesh.color_attributes.new(name="Landscape", type="FLOAT_COLOR", domain="POINT")
        attribute.data.foreach_set("color", rgba.ravel())
        mat = material("Muted relief / OSM forest and water", "adbb94")
        node = mat.node_tree.nodes.new("ShaderNodeVertexColor")
        node.layer_name = "Landscape"
        mat.node_tree.links.new(node.outputs["Color"], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
        mesh.materials.append(mat)
        return ob


def make_vehicle(mode, mats):
    root = bpy.data.objects.new("Cartoon " + mode, None)
    bpy.context.collection.objects.link(root)
    limbs = []
    body, cream, glass, dark = mats[mode], mats["cream"], mats["glass"], mats["dark"]
    if mode in ("rail", "bus", "rideshare"):
        length = 2.7 if mode == "rail" else 2.25 if mode == "bus" else 1.8
        cube("Body", (0, 0, .6), (1.0, length, .7), body, root, .15)
        cube("Roof", (0, 0, 1.04), (.97, length-.06, .20), cream, root, .08)
        cube("Front window", (0, length/2+.01, .82), (.72, .035, .30), glass, root, .02)
        for side in (-1, 1):
            for y in np.linspace(-length*.31, length*.31, 4 if mode != "rideshare" else 2):
                cube("Side window", (side*.505, y, .83), (.028, .35, .31), glass, root, .025)
            for y in (-length*.30, length*.30):
                sphere("Wheel", (side*.5, y, .23), (.11, .23, .23), dark, root)
            sphere("Headlamp", (side*.32, length/2+.025, .53), (.09, .04, .07), cream, root)
        if mode == "rail":
            line("Pantograph", [(-.25, -.3, 1.16), (0, -.3, 1.5), (.25, -.3, 1.16)], .035, dark, root)
            cube("Second carriage", (0, -3.1, .62), (1.0, 2.65, .76), body, root, .14)
            cube("Carriage roof", (0, -3.1, 1.05), (1.0, 2.65, .18), cream, root, .06)
            for side in (-1, 1):
                for y in (-3.9, -3.3, -2.7, -2.1):
                    cube("Carriage window", (side*.506, y, .85), (.025, .37, .3), glass, root, .02)
                for y in (-3.85, -2.35):
                    sphere("Carriage wheel", (side*.5, y, .23), (.1, .23, .23), dark, root)
            line("Coupling", [(0, -1.35, .4), (0, -1.8, .4)], .06, dark, root)
    elif mode == "cable_car":
        cube("Gondola cabin", (0, 0, .48), (1.2, 1.0, .75), body, root, .16)
        cube("Glass cabin", (0, 0, .98), (1.1, .92, .45), glass, root, .10)
        cube("Gondola roof", (0, 0, 1.25), (1.32, 1.1, .12), cream, root, .06)
        line("Hanger", [(0, 0, 1.26), (0, 0, 1.85), (0, .25, 2.05)], .06, dark, root)
        line("Cable", [(0, -3.2, 2.05), (0, 3.2, 2.05)], .018, dark, root)
        for side in (-1, 1):
            cube("Cabin frame", (side*.51, 0, 1), (.045, 1, .055), cream, root, 0)
    elif mode == "hike":
        skin = mats["skin"]
        sphere("Head", (0, 0, 1.62), (.23, .23, .26), skin, root)
        sphere("Walking hat", (0, .02, 1.83), (.32, .29, .1), body, root)
        cube("Jacket", (0, 0, 1.04), (.54, .35, .72), body, root, .13)
        cube("Backpack", (0, -.29, 1.09), (.4, .23, .55), mats["rail"], root, .07)
        for side in (-1, 1):
            leg = cube("Walking leg", (side*.15, 0, .41), (.19, .23, .65), dark, root, .06)
            arm = cube("Walking arm", (side*.37, 0, 1.06), (.16, .19, .60), body, root, .05)
            limbs.append((leg, side, .6))
            limbs.append((arm, -side, .45))
        line("Walking pole", [(.5, .3, .05), (.48, .15, 1.10)], .023, dark, root)
    return root, limbs


def set_visible(root, visible):
    for child in root.children_recursive:
        child.hide_render = not visible


def load_parts(leg, features, playback, terrain, span):
    geom = features[leg["feature_id"]]["geometry"]
    raw = geom["coordinates"] if geom["type"] == "MultiLineString" else [geom["coordinates"]]
    raw = [[p for p in part] for part in raw]
    options = playback.get(leg["id"], {})
    for i in options.get("reverse_parts", []):
        raw[i].reverse()
    if options.get("reverse"):
        raw = [part[::-1] for part in raw[::-1]]
    if options.get("return"):
        raw += [part[::-1] for part in raw[::-1]]
    parts = []
    for part in raw:
        xy = np.array([project(p) for p in part])
        steps = [xy[0]]
        for a, b in zip(xy[:-1], xy[1:]):
            n = max(1, int(np.linalg.norm(b-a)/max(.035, span/400)))
            steps.extend(a+(b-a)*(i/n) for i in range(1, n+1))
        xy = np.array(steps)
        z = terrain.height(xy[:, 0], xy[:, 1]) + max(.022, span*.0006)
        if leg["mode"] == "cable_car":
            z = np.linspace(z[0], z[-1], len(z)) + .09
            z = np.maximum(z, terrain.height(xy[:, 0], xy[:, 1])+.035)
        xyz = np.column_stack((xy, z))
        distances = np.r_[0, np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))]
        parts.append({"points": xyz, "distance": distances, "length": distances[-1]})
    return parts


def location(parts, t):
    distance = sum(p["length"] for p in parts)*np.clip(t, 0, .999999)
    for index, part in enumerate(parts):
        if distance <= part["length"] or index == len(parts)-1:
            d = part["distance"]
            i = min(max(np.searchsorted(d, distance)-1, 0), len(d)-2)
            f = (distance-d[i])/max(1e-9, d[i+1]-d[i])
            a, b = part["points"][i:i+2]
            return a+(b-a)*f, b-a, index, distance/max(part["length"], 1e-9)
        distance -= part["length"]


def make_hud(camera, mats):
    root = bpy.data.objects.new("Camera-facing editorial labels", None)
    bpy.context.collection.objects.link(root)
    root.parent = camera
    root.location = (0, 0, -1)
    bpy.ops.mesh.primitive_plane_add(size=2)
    plane = bpy.context.object
    plane.name = "Crisp page-font labels"
    plane.parent = root
    plane.location = (0, 0, -.03)
    plane.scale = (640, 480, 1)
    if hasattr(plane, "visible_shadow"):
        plane.visible_shadow = False
    mat = bpy.data.materials.new("Transparent editorial overlay")
    mat.use_nodes = True
    mat.surface_render_method = "BLENDED"
    nodes = mat.node_tree.nodes
    nodes.clear()
    image = nodes.new("ShaderNodeTexImage")
    image.interpolation = "Linear"
    emitter = nodes.new("ShaderNodeEmission")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    output = nodes.new("ShaderNodeOutputMaterial")
    links = mat.node_tree.links
    links.new(image.outputs["Color"], emitter.inputs["Color"])
    links.new(image.outputs["Alpha"], mix.inputs[0])
    links.new(transparent.outputs[0], mix.inputs[1])
    links.new(emitter.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs["Surface"])
    plane.data.materials.append(mat)
    progress = cube("Journey progress", (-570, -383, 0), (1, 4, .001), mats["rail_ui"], root, 0)
    return root, image, progress


def fit_title(ob, text_value, max_width=1135):
    # The locally vendored Latin fonts do not include arrow glyphs.
    ob.data.body = text_value.replace("→", "/").replace("↔", "/")
    ob.data.size = 57
    bpy.context.view_layer.update()
    width = max(v[0] for v in ob.bound_box)-min(v[0] for v in ob.bound_box)
    if width > max_width:
        ob.data.size *= max_width/width


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--chapter", required=True)
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--preview-scale", type=int, default=100)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    work = args.work.resolve()
    assert ROOT not in work.parents and work != ROOT
    payload = json.loads((work / "journey.json").read_text())
    config, journey = payload["config"], payload["journey"]
    features = {f["properties"]["id"]: f for f in payload["routes"]["features"]}
    fps = config["fps"]
    bookend = args.chapter in ("opening", "ending")
    day = None if bookend else next(d for d in config["days"] if d["id"] == args.chapter)
    chapter_length = 3 if bookend else day["seconds"]
    region_name = "overview" if bookend else day["region"]
    span = 550 if bookend else day["camera_span"]
    output = work / ("samples" if args.sample else "frames") / args.chapter
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples = 12
    scene.render.resolution_x, scene.render.resolution_y = config["resolution"]
    scene.render.resolution_percentage = args.preview_scale
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 15
    scene.render.fps = fps
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast" if "Medium High Contrast" in [i.name for i in scene.view_settings.bl_rna.properties["look"].enum_items] else "None"
    scene.view_settings.exposure = 0
    world = bpy.data.worlds.new("Warm cream atmosphere")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (*rgb(COLORS["paper"]), 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = .8
    scene.world = world
    mats = {k: material(k, v) for k, v in COLORS.items()}
    mats.update({"glass": material("Pale blue glass", "bed7d1"), "skin": material("Warm skin", "dcb28b")})
    for k in ("paper", "ink", "rail", "cable_car", "bus", "rideshare", "hike"):
        mats[k+"_ui"] = material(k+" UI", COLORS[k], True)
    mats["muted_ui"] = material("Muted typography", "817563", True)
    terrain = Terrain(work / f"terrain-{region_name}.npz")
    if region_name == "overview":
        terrain.forest.fill(0)  # Regional views generalize land cover; detailed polygons appear in scenic chapters.
    terrain.build()
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 100))
    sun = bpy.context.object
    sun.rotation_euler = (math.radians(28), math.radians(-25), math.radians(-28))
    sun.data.energy = 1.4
    sun.data.angle = math.radians(15)
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span
    camera.data.clip_start = .0001
    camera.data.clip_end = 4000
    scene.camera = camera
    hud, label_image, progress = make_hud(camera, mats)
    label_images = {p.stem: bpy.data.images.load(str(p)) for p in (work / "labels").glob("*.png")}
    if bookend:
        legs = journey["route_legs"]
    else:
        legs = [leg for leg in journey["route_legs"] if leg["day_id"] == day["id"]]
    paths = []
    weights = [config["playback"].get(leg["id"], {}).get("weight", 1.5 if leg["mode"] == "hike" else 1) for leg in legs]
    for leg, weight in zip(legs, weights):
        parts = load_parts(leg, features, config["playback"], terrain, span)
        curves = []
        for p in parts:
            line("Cream route underlay", p["points"], span*.0025, mats["cream"])
            curves.append(line(leg["id"], p["points"]+np.array([0, 0, span*.002]), span*.0015, mats[leg["mode"]]))
        paths.append({"leg": leg, "parts": parts, "curves": curves, "weight": weight})
    total_weight = sum(weights)
    boundaries = np.r_[0, np.cumsum(weights)/total_weight*chapter_length]
    vehicles = {mode: make_vehicle(mode, mats) for mode in MODE_NAMES}
    for root, _ in vehicles.values():
        set_visible(root, False)
    place_ids = {p["id"] for p in journey["places"]} if bookend else set(next(d for d in journey["days"] if d["id"] == day["id"])["place_ids"])
    places = [p for p in journey["places"] if p["id"] in place_ids]
    for place in places:
        x, y = project([place["longitude"], place["latitude"]])
        z = float(terrain.height(x, y))
        sphere("Waypoint " + place["id"], (x, y, z+span*.0025), (span*.0022, span*.0022, span*.0022), mats["cream"])
        if place["id"].endswith("airport"):
            airport = bpy.data.objects.new("Airport symbol / no flight path", None)
            bpy.context.collection.objects.link(airport)
            airport.location = (x, y, z+span*.006)
            airport.scale = (span*.016,)*3
            cube("Aircraft fuselage", (0, 0, .05), (.14, 1.5, .13), mats["cream"], airport, .06)
            cube("Aircraft wings", (0, .12, .06), (1.25, .24, .10), mats["cream"], airport, .04)
            cube("Aircraft tail", (0, -.54, .1), (.5, .13, .15), mats["cream"], airport, .03)
    weather = bpy.data.objects.new("Ortisei changing weather", None)
    bpy.context.collection.objects.link(weather)
    for position, scale in [((-.55, 0, 0), (.7, .43, .4)), ((.1, .04, .25), (.8, .55, .6)), ((.75, 0, .04), (.6, .4, .42))]:
        sphere("Soft cloud", position, scale, mats["cream"], weather)
    rain = []
    for i in range(9):
        drop = line("Rain", [(i*.16-.6, 0, -.3), (i*.16-.7, 0, -.6)], .015, mats["cable_car"], weather)
        rain.append(drop)
    set_visible(weather, False)
    frames = [int(fps*chapter_length*.5)] if args.sample else list(range(int(fps*chapter_length)))
    if args.limit:
        frames = frames[:args.limit]
    current_key = None
    day_index = 0 if bookend else int(day["id"][-2:])
    chapter_start = 0 if args.chapter == "opening" else 69 if args.chapter == "ending" else 3+sum(d["seconds"] for d in config["days"][:day_index-1])
    for frame in frames:
        seconds = frame/fps
        progress_value = (chapter_start+seconds)/72
        if bookend:
            center = np.array([0., 15., .7])
            camera_span = span*(1-.035*seconds/chapter_length)
            angle = -.08+.06*seconds/chapter_length
            label_image.image = label_images[args.chapter]
        else:
            index = min(np.searchsorted(boundaries, seconds, side="right")-1, len(paths)-1)
            entry = paths[index]
            leg = entry["leg"]
            fraction = (seconds-boundaries[index])/(boundaries[index+1]-boundaries[index])
            pos, tangent, part_index, part_fraction = location(entry["parts"], fraction)
            # Camera leads the moving model slightly, with no interpolation across geometry gaps.
            ahead, _, ahead_part, _ = location(entry["parts"], min(1, fraction+.06))
            center = pos*.8+ahead*.2 if ahead_part == part_index else pos.copy()
            camera_span = span
            if leg["mode"] == "hike" and day["id"] == "day-06":
                camera_span = 8
            angle = -.16+.06*math.sin(seconds/chapter_length*math.pi)
            mode = leg["mode"]
            if current_key != leg["id"]:
                for key, (root, _) in vehicles.items():
                    set_visible(root, key == mode)
                current_key = leg["id"]
                label_image.image = label_images[current_key]
                print(f"SHOT {day['id']} / {leg['id']}", flush=True)
            root, limbs = vehicles[mode]
            root.location = pos
            vehicle_scale = camera_span/(48 if mode == "rail" else 26 if mode == "hike" else 30)
            root.scale = (vehicle_scale,)*3
            root.rotation_euler[2] = -math.atan2(tangent[0], tangent[1])
            for limb, phase, amplitude in limbs:
                limb.rotation_euler[0] = math.sin(seconds*9)*phase*amplitude
            for i, path in enumerate(paths):
                for j, curve in enumerate(path["curves"]):
                    curve.data.bevel_factor_end = 1 if i < index else 0 if i > index else 1 if j < part_index else part_fraction if j == part_index else 0
            if day_index == 7:
                cloudy = seconds > .9
                set_visible(weather, cloudy)
                weather.location = (center[0]+camera_span*.22, center[1], center[2]+camera_span*.10)
                weather.scale = (camera_span*.07,)*3
                for i, drop in enumerate(rain):
                    drop.hide_render = seconds < 2.4
                    drop.location.z = -(seconds*1.6+i*.1) % .7-.5
                sun.data.energy = 1.4 if seconds < 1 else 1.1
        offset = np.array([math.sin(angle)*camera_span*.70, -math.cos(angle)*camera_span*.70, camera_span*.67])
        camera.location = center+offset
        # Lift the optical target slightly so terrain occupies the middle of the editorial frame.
        target = center+np.array([0, 0, camera_span*.025])
        camera.rotation_euler = (Vector(target)-camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.ortho_scale = camera_span
        hud.scale = (camera_span/1280,)*3
        progress.scale.x = max(.001, progress_value*1140)
        progress.location.x = -570+progress_value*570
        bpy.context.view_layer.update()
        scene.render.filepath = str(output / f"{frame:05}.png")
        bpy.ops.render.render(write_still=True)
        if frame % 24 == 0:
            print(f"FRAME {args.chapter} {frame}/{int(fps*chapter_length)}", flush=True)
    print(f"CHAPTER_COMPLETE {args.chapter} {len(frames)} frames", flush=True)


if __name__ == "__main__":
    main()
