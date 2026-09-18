#!/usr/bin/env python3
"""Perspective-camera renderer for the sample or separately approved full film.

Blender --background --python scripts/render-journey-cinematic.py --
  --work SCRATCH --shot SHOT_ID [--still]
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("journey_scene", ROOT / "scripts/render-journey-overview.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
scenery_spec = importlib.util.spec_from_file_location("journey_scenery", ROOT / "scripts/journey-scenery.py")
scenery = importlib.util.module_from_spec(scenery_spec)
scenery_spec.loader.exec_module(scenery)


def mesh_object(name, vertices, faces, materials, indices=None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    for mat in materials:
        mesh.materials.append(mat)
    if indices is not None:
        mesh.polygons.foreach_set("material_index", np.asarray(indices, dtype=np.int32))
    return ob


class Terrain:
    def __init__(self, path, origin):
        data = np.load(path)
        self.x = data["x"]*1000-origin[0]
        self.y = data["y"]*1000-origin[1]
        self.z = data["z"]*1000
        self.water, self.forest = data["water"], data["forest"]

    def sample(self, x, y, field=None):
        array = self.z if field is None else field
        x = np.clip(np.asarray(x),self.x[0],self.x[-1])
        y = np.clip(np.asarray(y),self.y[0],self.y[-1])
        i = np.clip(np.searchsorted(self.x,x,side="right")-1,0,len(self.x)-2)
        j = np.clip(np.searchsorted(self.y,y,side="right")-1,0,len(self.y)-2)
        a, b = (x-self.x[i])/(self.x[i+1]-self.x[i]), (y-self.y[j])/(self.y[j+1]-self.y[j])
        if field is None:
            # Match the explicit mesh diagonal. Bilinear height would put feet,
            # sleepers and path ribbons below the actual sloping triangles.
            first = array[j, i]+a*(array[j, i+1]-array[j, i])+b*(array[j+1, i+1]-array[j, i+1])
            second = array[j, i]+a*(array[j+1, i+1]-array[j+1, i])+b*(array[j+1, i]-array[j, i])
            value = np.where(a >= b, first, second)
            patch = getattr(self, "visual_patch", None)
            if patch is not None:
                inside = (x>=patch.x[0])&(x<=patch.x[-1])&(y>=patch.y[0])&(y<=patch.y[-1])
                value = np.where(inside, patch.sample(x,y), value)
            return value
        return (1-a)*(1-b)*array[j, i]+a*(1-b)*array[j, i+1]+(1-a)*b*array[j+1, i]+a*b*array[j+1, i+1]

    def normal(self, x, y):
        return np.array([-(self.sample(x+2, y)-self.sample(x-2, y))/4,
                         -(self.sample(x, y+2)-self.sample(x, y-2))/4, 1])

    def join_detail(self, detail):
        """Align the distant grid to the detail border, without open mesh gaps."""
        x = np.unique(np.r_[self.x,detail.x[[0,-1]]])
        y = np.unique(np.r_[self.y,detail.y[[0,-1]]])
        xx,yy = np.meshgrid(x,y)
        z = self.sample(xx,yy)
        water = self.sample(xx,yy,self.water)
        forest = self.sample(xx,yy,self.forest)
        self.x,self.y,self.z,self.water,self.forest = x,y,z,water,forest
        xx,yy = np.meshgrid(detail.x,detail.y)
        edge = np.minimum.reduce([xx-detail.x[0],detail.x[-1]-xx,yy-detail.y[0],detail.y[-1]-yy])
        weight = np.clip(edge/350,0,1)
        weight = weight*weight*(3-2*weight)
        # Only the remote 350 m patch border blends into the lighter DEM;
        # foreground terrain and traveled scenic intervals remain detailed.
        detail.z = detail.z*weight+self.sample(xx,yy)*(1-weight)

    def carve_lakes(self, lakes, origin):
        # Flatten only lake interiors below the separate water surface. Without
        # this, small DSM height variations break the lake into blue fragments.
        self.lake_surfaces = []
        for lake in lakes:
            ring = np.asarray(lake["xy"])*1000-origin
            self.lake_surfaces.append((ring, lake["height"]*1000))
            a, b = ring[:-1], ring[1:]
            for j in np.flatnonzero((self.y >= ring[:, 1].min()) & (self.y <= ring[:, 1].max())):
                y = self.y[j]
                crossing = (a[:, 1] > y) != (b[:, 1] > y)
                if not crossing.any():
                    continue
                aa, bb = a[crossing], b[crossing]
                intersections = np.sort(aa[:, 0]+(y-aa[:, 1])*(bb[:, 0]-aa[:, 0])/(bb[:, 1]-aa[:, 1]))
                for west, east in zip(intersections[::2], intersections[1::2]):
                    inside = (self.x >= west) & (self.x <= east)
                    self.z[j, inside] = np.minimum(self.z[j, inside], lake["height"]*1000-1.5)

    def lake_level(self, x, y):
        """Use the rendered water plane, not the deliberately submerged DEM bed."""
        for ring, height in self.lake_surfaces:
            a, b = ring[:-1], ring[1:]
            crossing = (a[:, 1] > y) != (b[:, 1] > y)
            if not crossing.any():
                continue
            aa, bb = a[crossing], b[crossing]
            xs = aa[:, 0]+(y-aa[:, 1])*(bb[:, 0]-aa[:, 0])/(bb[:, 1]-aa[:, 1])
            if np.count_nonzero(xs > x) % 2:
                return height
        return None

    def build(self, name, exclude=None, edge_fade=False, profile=None):
        xx, yy = np.meshgrid(self.x, self.y)
        ny, nx = self.z.shape
        corners = (np.arange(ny-1)[:, None]*nx+np.arange(nx-1)).ravel()
        faces = np.column_stack((corners, corners+1, corners+nx+1, corners+nx))
        if exclude is not None:
            # Detail patches replace distant faces instead of sitting on top of them.
            centers_x = xx.ravel()[faces].mean(axis=1)
            centers_y = yy.ravel()[faces].mean(axis=1)
            keep = ~((centers_x >= exclude.x[0]) & (centers_x <= exclude.x[-1]) &
                     (centers_y >= exclude.y[0]) & (centers_y <= exclude.y[-1]))
            faces = faces[keep]
        faces = np.vstack((faces[:, [0, 1, 2]], faces[:, [0, 2, 3]]))
        mat = base.material(name+" / matte illustrated terrain", "a4b388")
        ob = mesh_object(name, np.column_stack((xx.ravel(), yy.ravel(), self.z.ravel())).tolist(), faces.tolist(), [mat])
        ob.data.polygons.foreach_set("use_smooth", np.ones(len(faces), dtype=bool))
        gy, gx = np.gradient(self.z, self.y, self.x)
        slope = np.hypot(gx, gy)
        if profile and profile.get("ridge_material"):
            # Real thirty-metre cliff facets, not displaced or enlarged peaks.
            smooth_faces = slope.ravel()[faces].mean(axis=1) < 1.15
            ob.data.polygons.foreach_set("use_smooth", smooth_faces)
        stone = np.clip((self.z-1850)/950+np.clip((slope-.45)/.75, 0, 1)*.95, 0, 1)[:, :, None]
        colors = np.array(base.rgb("9caa7d"))*(1-stone)+np.array(base.rgb("beb7ac"))*stone
        forest = np.asarray(self.forest/255*.38)[:, :, None]
        colors = colors*(1-forest)+np.array(base.rgb("6e8761"))*forest
        snow = np.clip((self.z-3030)/650, 0, 1)[:, :, None]
        colors = colors*(1-snow)+np.array(base.rgb("f5f0e4"))*snow
        if profile:
            colors = scenery.terrain_palette(self, xx, yy, profile, base.rgb)
        rgba = np.column_stack((colors.reshape(-1, 3), np.ones(nx*ny)))
        attribute = ob.data.color_attributes.new(name="Terrain palette", type="FLOAT_COLOR", domain="POINT")
        attribute.data.foreach_set("color", rgba.astype(np.float32).ravel())
        tree = mat.node_tree
        vertex = tree.nodes.new("ShaderNodeVertexColor")
        vertex.layer_name = attribute.name
        noise = tree.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = .028
        noise.inputs["Detail"].default_value = 3
        geometry = tree.nodes.new("ShaderNodeNewGeometry")
        tree.links.new(geometry.outputs["Position"], noise.inputs["Vector"])
        bump = tree.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .26
        bump.inputs["Distance"].default_value = 2.8 if profile else .5
        tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        bsdf = tree.nodes.get("Principled BSDF")
        tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        # Distance haze reveals mountain layers without expensive volume rendering.
        camera = tree.nodes.new("ShaderNodeCameraData")
        depth = tree.nodes.new("ShaderNodeMapRange")
        depth.inputs["From Min"].default_value = 1200
        depth.inputs["From Max"].default_value = 24000
        depth.inputs["To Max"].default_value = profile["haze"] if profile else .68
        depth.clamp = True
        tree.links.new(camera.outputs["View Distance"], depth.inputs["Value"])
        haze = tree.nodes.new("ShaderNodeMixRGB")
        haze.inputs[2].default_value = (*base.rgb("c6d4cf"), 1)
        pigment = tree.nodes.new("ShaderNodeValToRGB")
        pigment.color_ramp.elements[0].position = .15
        pigment.color_ramp.elements[0].color = (.53, .53, .53, 1)
        pigment.color_ramp.elements[1].position = .82
        pigment.color_ramp.elements[1].color = (1, 1, 1, 1)
        tree.links.new(noise.outputs["Fac"], pigment.inputs["Fac"])
        mottled = tree.nodes.new("ShaderNodeMixRGB")
        mottled.blend_type = "MULTIPLY"
        mottled.inputs[0].default_value = .4
        tree.links.new(vertex.outputs["Color"], mottled.inputs[1])
        tree.links.new(pigment.outputs["Color"], mottled.inputs[2])
        tree.links.new(mottled.outputs[0], haze.inputs[1])
        if profile and profile.get("ridge_material"):
            # Scoped layering; sculpted relief is a separate audited patch.
            wave = tree.nodes.new("ShaderNodeTexWave")
            wave.wave_type = "BANDS"
            wave.bands_direction = "Z"
            wave.inputs["Scale"].default_value = .055
            wave.inputs["Distortion"].default_value = 4
            wave.inputs["Detail"].default_value = 3
            if profile.get("sculpted_ridge"):
                coordinates = tree.nodes.new("ShaderNodeVectorRotate")
                coordinates.rotation_type = "EULER_XYZ"
                coordinates.inputs["Rotation"].default_value = (.15,-.24,0)
                tree.links.new(geometry.outputs["Position"],coordinates.inputs["Vector"])
                tree.links.new(coordinates.outputs["Vector"],wave.inputs["Vector"])
                wave.inputs["Scale"].default_value = .10
                wave.inputs["Distortion"].default_value = 1.2
            else:
                tree.links.new(geometry.outputs["Position"], wave.inputs["Vector"])
            strata = tree.nodes.new("ShaderNodeValToRGB")
            strata.color_ramp.elements[0].color = (.48,.48,.46,1)
            strata.color_ramp.elements[1].color = (1,1,1,1)
            tree.links.new(wave.outputs["Fac"],strata.inputs["Fac"])
            layered = tree.nodes.new("ShaderNodeMixRGB")
            layered.blend_type = "MULTIPLY"
            separate = tree.nodes.new("ShaderNodeSeparateXYZ")
            tree.links.new(geometry.outputs["Normal"],separate.inputs[0])
            rock_mask = tree.nodes.new("ShaderNodeMapRange")
            rock_mask.inputs["From Min"].default_value = .45
            rock_mask.inputs["From Max"].default_value = .8
            rock_mask.inputs["To Min"].default_value = .18 if profile.get("sculpted_ridge") else .12
            rock_mask.inputs["To Max"].default_value = 0
            rock_mask.clamp = True
            tree.links.new(separate.outputs["Z"],rock_mask.inputs["Value"])
            tree.links.new(rock_mask.outputs["Result"],layered.inputs[0])
            tree.links.new(mottled.outputs[0],layered.inputs[1])
            tree.links.new(strata.outputs["Color"],layered.inputs[2])
            tree.links.new(layered.outputs[0],haze.inputs[1])
            stretched = tree.nodes.new("ShaderNodeVectorMath")
            stretched.operation = "MULTIPLY"
            stretched.inputs[1].default_value = (1,1,.16)
            tree.links.new(geometry.outputs["Position"],stretched.inputs[0])
            crag = tree.nodes.new("ShaderNodeTexNoise")
            crag.inputs["Scale"].default_value = .055
            crag.inputs["Detail"].default_value = 5
            crag.inputs["Roughness"].default_value = .7
            tree.links.new(stretched.outputs["Vector"],crag.inputs["Vector"])
            cliff_bump = tree.nodes.new("ShaderNodeBump")
            cliff_bump.inputs["Strength"].default_value = .52
            cliff_bump.inputs["Distance"].default_value = 12
            tree.links.new(crag.outputs["Fac"],cliff_bump.inputs["Height"])
            tree.links.new(bump.outputs["Normal"],cliff_bump.inputs["Normal"])
            normal_mix = tree.nodes.new("ShaderNodeMixRGB")
            strength = tree.nodes.new("ShaderNodeMath")
            strength.operation = "MULTIPLY"
            strength.inputs[1].default_value = 7
            tree.links.new(rock_mask.outputs["Result"],strength.inputs[0])
            tree.links.new(strength.outputs[0],normal_mix.inputs[0])
            tree.links.new(bump.outputs["Normal"],normal_mix.inputs[1])
            tree.links.new(cliff_bump.outputs["Normal"],normal_mix.inputs[2])
            tree.links.new(normal_mix.outputs[0],bsdf.inputs["Normal"])
        tree.links.new(depth.outputs["Result"], haze.inputs[0])
        tree.links.new(haze.outputs[0], bsdf.inputs["Base Color"])
        if edge_fade:
            # Feather only the distant map boundary into the paper background;
            # the DEM elevations and all traveled terrain remain untouched.
            edge_distance = np.minimum.reduce([xx-self.x[0],self.x[-1]-xx,yy-self.y[0],self.y[-1]-yy])
            edge = np.clip(edge_distance/55000,0,1)
            edge = edge*edge*(3-2*edge)
            attr = ob.data.attributes.new(name="Regional edge fade",type="FLOAT",domain="POINT")
            attr.data.foreach_set("value",edge.astype(np.float32).ravel())
            vertex_edge = tree.nodes.new("ShaderNodeAttribute")
            vertex_edge.attribute_name = attr.name
            paper = tree.nodes.new("ShaderNodeEmission")
            paper.inputs["Color"].default_value = (*base.rgb("f2ede0"),1)
            blend_edge = tree.nodes.new("ShaderNodeMixShader")
            tree.links.new(vertex_edge.outputs["Fac"],blend_edge.inputs[0])
            tree.links.new(paper.outputs[0],blend_edge.inputs[1])
            tree.links.new(bsdf.outputs[0],blend_edge.inputs[2])
            tree.links.new(blend_edge.outputs[0],tree.nodes.get("Material Output").inputs["Surface"])
        return ob


def route_parts(leg, payload, terrain, origin, raw=None, step=2):
    prepared = raw is not None
    if not prepared:
        geometry = next(f["geometry"] for f in payload["routes"]["features"] if f["properties"]["id"] == leg["feature_id"])
        raw = geometry["coordinates"] if geometry["type"] == "MultiLineString" else [geometry["coordinates"]]
    parts = [np.array([base.project(p)*1000-origin for p in part]) for part in raw]
    options = {} if prepared else payload["playback"].get(leg["id"], {})
    for i in options.get("reverse_parts", []):
        parts[i] = parts[i][::-1]
    if options.get("reverse"):
        parts = [p[::-1] for p in parts[::-1]]
    if options.get("return"):
        parts += [p[::-1] for p in parts[::-1]]
    result = []
    for xy in parts:
        distances = np.r_[0, np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))]
        if distances[-1] < .01:
            continue
        samples = np.linspace(0, distances[-1], max(2, math.ceil(distances[-1]/step)+1))
        xy = np.column_stack([np.interp(samples, distances, xy[:, i]) for i in range(2)])
        ground = terrain.sample(xy[:, 0], xy[:, 1])
        z = ground+.12
        if leg["mode"] == "cable_car":
            t = samples/max(samples[-1], 1)
            # Explicitly illustrative vertical clearance; not surveyed cable heights.
            z = np.maximum(np.linspace(ground[0]+18, ground[-1]+18, len(t))-18*4*t*(1-t), ground+12)
        result.append({"points": np.column_stack((xy, z)), "distance": samples, "length": samples[-1]})
    return result


def at_distance(part, distance):
    d = np.clip(distance, 0, part["length"])
    point = np.array([np.interp(d, part["distance"], part["points"][:, k]) for k in range(3)])
    a, b = np.clip([d-4, d+4], 0, part["length"])
    tangent = np.array([np.interp(b, part["distance"], part["points"][:, k])-np.interp(a, part["distance"], part["points"][:, k]) for k in range(3)])
    return point, tangent/max(np.linalg.norm(tangent), 1e-9)


def original_vehicle(mode, mats):
    root, limbs = base.make_vehicle(mode, mats)
    dimensions = {"rail": (3, 50, 4.2), "bus": (2.5, 12, 3.5),
                  "rideshare": (1.8, 4.5, 1.6), "cable_car": (3, 2.5, 4.2), "hike": (.7, .55, 1.7)}
    if mode == "cable_car":
        for child in root.children_recursive:
            if child.name == "Cable":
                child.hide_render = True
    bpy.context.view_layer.update()
    bounds = np.array([tuple(child.matrix_world @ Vector(corner)) for child in root.children_recursive
                       if not child.hide_render for corner in child.bound_box])
    minimum, maximum = bounds.min(axis=0), bounds.max(axis=0)
    root.scale = np.array(dimensions[mode])/(maximum-minimum)
    root["ground_offset"] = float(-minimum[2]*root.scale.z)
    root["support_points"] = [float(v) for x in (minimum[0],maximum[0])
        for y in np.linspace(minimum[1],maximum[1],9) for v in (x,y,minimum[2])]
    return root, limbs


def tree_mesh(mats):
    vertices, faces, indices = [], [], []
    for radius, bottom, top, material_index in [(.15, 0, 7, 0), (2.2, 2.7, 7.5, 1), (1.6, 5, 9.1, 1), (1.0, 7.0, 10.3, 1)]:
        start = len(vertices)
        vertices.extend([(math.cos(a)*radius, math.sin(a)*radius, bottom) for a in np.linspace(0, 2*math.pi, 9)[:-1]])
        vertices.append((0, 0, top))
        for i in range(8):
            faces.append((start+i, start+(i+1)%8, start+8))
            indices.append(material_index)
    return mesh_object("Original stylized fir prototype", vertices, faces, [mats["bark"], mats["pine"]], indices)


def foreground(terrain, part, center, camera_hint, mats, seed, camera_end=None):
    rng = np.random.default_rng(seed)
    prototype = tree_mesh(mats)
    prototype.hide_render = True
    path_xy = part["points"][::3, :2]
    camera_end = camera_hint if camera_end is None else camera_end
    camera_delta = camera_end[:2]-camera_hint[:2]
    count = 0
    for xy in center[:2]+rng.uniform(-1250, 1250, size=(14000, 2)):
        if terrain.sample(*xy, terrain.forest) < 130 or terrain.sample(*xy, terrain.water) > 40:
            continue
        camera_t = np.clip(np.dot(xy-camera_hint[:2],camera_delta)/max(np.dot(camera_delta,camera_delta),1e-9),0,1)
        if np.linalg.norm(xy-camera_hint[:2]-camera_t*camera_delta) < 22 or np.min(np.linalg.norm(path_xy-xy, axis=1)) < 9:
            continue
        normal = terrain.normal(*xy)
        if np.linalg.norm(normal[:2]) > 1.15 or terrain.sample(*xy) > 2240:
            continue
        tree = bpy.data.objects.new("Forest / illustrative individual tree", prototype.data)
        bpy.context.collection.objects.link(tree)
        tree.location = (*xy, float(terrain.sample(*xy))-.15)
        size = rng.uniform(.6, 1.65)
        tree.scale = (size, size, size*rng.uniform(.9, 1.2))
        tree.rotation_euler.z = rng.uniform(0, 2*math.pi)
        count += 1
        if count >= 3200:
            break
    vertices, faces = [], []
    for xy in center[:2]+rng.uniform(-100, 100, size=(4200, 2)):
        if terrain.sample(*xy, terrain.water) > 40 or np.min(np.linalg.norm(path_xy-xy, axis=1)) < 1.4:
            continue
        z = float(terrain.sample(*xy))
        height = rng.uniform(.16, .48)
        start = len(vertices)
        vertices.extend([(xy[0]-.07, xy[1], z), (xy[0]+.07, xy[1], z), (xy[0]+.05, xy[1], z+height),
                         (xy[0], xy[1]-.08, z), (xy[0], xy[1]+.08, z), (xy[0], xy[1], z+height*.9)])
        faces.extend([(start, start+1, start+2), (start+3, start+4, start+5)])
    mesh_object("Original foreground meadow blades", vertices, faces, [mats["grass"]])
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1)
    rock = bpy.context.object
    rock.name = "Original stone prototype"
    rock.data.materials.append(mats["stone"])
    rock.hide_render = True
    for xy in center[:2]+rng.uniform(-100, 100, size=(100, 2)):
        if terrain.sample(*xy, terrain.water) > 40 or np.min(np.linalg.norm(path_xy-xy, axis=1)) < 1.7:
            continue
        ob = bpy.data.objects.new("Small foreground stone", rock.data)
        bpy.context.collection.objects.link(ob)
        size = rng.uniform(.15, .65)
        ob.location = (*xy, float(terrain.sample(*xy)))
        ob.scale = (size, size*.8, size*.6)
        ob.rotation_euler = rng.uniform(-.2, .2, 3)
    print(f"FOREGROUND {count} mapped-forest trees; original rocks and grass", flush=True)


def lakes(payload, origin, terrain, mats):
    for lake in payload["lakes"]:
        xy = np.array(lake["xy"])*1000-origin
        if xy[:, 0].max() < terrain.x[0] or xy[:, 0].min() > terrain.x[-1] or xy[:, 1].max() < terrain.y[0] or xy[:, 1].min() > terrain.y[-1]:
            continue
        vertices = np.column_stack((xy[:-1], np.full(len(xy)-1, lake["height"]*1000)))
        mesh_object("Geographic lake / calm reflective surface", vertices.tolist(), [list(range(len(vertices)))], [mats["water"]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path)
    parser.add_argument("--shot")
    parser.add_argument("--still", action="store_true")
    parser.add_argument("--film", action="store_true", help="Use the explicitly approved full-film payload")
    parser.add_argument("--scenery-sample", action="store_true", help="Only the separate, configured scenery sample")
    parser.add_argument("--scenery-film", action="store_true", help="Approved full scenery revision, isolated from the original film")
    parser.add_argument("--scenery-dir", default="cinematic-v3")
    parser.add_argument("--proof-sequence", action="store_true", help="Render all three audited stills")
    parser.add_argument("--audit", action="store_true", help="Evaluate first/middle/last camera poses without rendering")
    parser.add_argument("--limit", type=int, help="Bounded motion benchmark; never changes the full-film approval gate")
    parser.add_argument("--self-test", action="store_true", help="No rendering or source downloads")
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    if args.self_test:
        self_test()
        return
    if not args.work or not args.shot:
        parser.error("--work and --shot are required for rendering")
    work = args.work.resolve()
    assert work != ROOT and ROOT not in work.parents
    assert not (args.scenery_sample and args.scenery_film)
    if args.scenery_sample or args.scenery_film:
        args.film = True  # Prepared geometry interface, not full-film authorization.
    assert Path(args.scenery_dir).name==args.scenery_dir and args.scenery_dir.startswith("cinematic-v3")
    assert not args.proof_sequence or (args.still and args.audit)
    directory = work / ("cinematic-v3-film" if args.scenery_film else args.scenery_dir if args.scenery_sample else "cinematic-film" if args.film else "cinematic-v2")
    payload = json.loads((directory / ("film.json" if args.film else "sample.json")).read_text())
    config = payload["config"]
    if config["approval_status"] != ("approved" if args.film and not args.scenery_sample else "sample_only"):
        raise RuntimeError("The chosen render is not approved")
    if args.scenery_sample:
        assert config["approval_sample"] and config["duration"] == config["sample_duration"]
        assert sum(s["seconds"] for s in config["shots"]) == config["duration"]
    minimum = config["minimum_free_gib" if args.film else "sample_minimum_free_gib"]
    if shutil.disk_usage(work).free < minimum*1024**3:
        raise RuntimeError(f"At least {minimum} GiB free is required before rendering a shot")
    shot = next(s for s in config["shots" if args.film else "sample_shots"] if s["id"] == args.shot)
    profile = config["scenery"]["weather_profiles"][shot["weather_profile"]] if shot.get("atmosphere_3d") else None
    places = payload["places"] if args.film else {p["id"]: p for p in payload["journey"]["places"]}
    leg = next((l for l in payload["journey"]["route_legs"] if l["id"] == shot.get("leg_id")), {"id":shot["id"],"mode":"rail"})
    region = config["regions"][shot["region"]]["bounds"]
    origin = base.project([(region[0]+region[2])/2, (region[1]+region[3])/2])*1000
    if profile and "ridge_clouds" in profile:
        profile = {**profile, "ridge_clouds": [{**c, "center_m": [*(base.project(c["lonlat"])*1000-origin),c["elevation_m"]]} for c in profile["ridge_clouds"]]}
    region_config = config["regions"][shot["region"]]
    regional = shot["camera"] == "regional_aerial"
    terrain = Terrain(Path(payload["terrain_files"][shot["region"]]) if args.film else work / f"cinematic-v2/terrain-{shot['region']}.npz", origin)
    background = region_config.get("background")
    far = Terrain(Path(payload["terrain_files"][background]),origin) if args.film and background else None if args.film else Terrain(work / "terrain-jungfrau.npz", origin)
    terrain.carve_lakes(payload["lakes"], origin)
    if far:
        far.carve_lakes(payload["lakes"], origin)
        if args.film:
            far.join_detail(terrain)
    relief = Terrain(Path(config["seceda_relief"]["path"]),origin) if shot.get("ridge_camera") and config.get("seceda_relief") else None
    if relief is not None:
        terrain.visual_patch = relief
    geometry = payload["shot_geometry"][shot["id"]] if args.film else None
    parts = route_parts(leg,payload,terrain,origin,raw=[geometry["travel"]] if args.film else None,step=250 if regional else 2)
    part = parts[0 if args.film else shot["part"]]
    initial, initial_tangent = at_distance(part, shot["fraction"]*part["length"])
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples = config["samples"]
    # The matte illustrated style uses environment/specular reflections. Full
    # screen-space ray tracing adds substantial cost without useful detail here.
    scene.eevee.use_raytracing = bool(profile and shot.get("scenery") == "lakeside")
    scene.render.resolution_x, scene.render.resolution_y = config["resolution"]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 15
    scene.render.fps = config["fps"]
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = -.1
    scene.world = bpy.data.worlds.new("Pale alpine sky")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (*base.rgb("cbdcd8"), 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .85
    sky_tree = scene.world.node_tree
    direction = sky_tree.nodes.new("ShaderNodeTexCoord")
    separate = sky_tree.nodes.new("ShaderNodeSeparateXYZ")
    sky_tree.links.new(direction.outputs["Normal"], separate.inputs[0])
    gradient = sky_tree.nodes.new("ShaderNodeMapRange")
    gradient.inputs["From Min"].default_value = -.1
    gradient.inputs["From Max"].default_value = .65
    gradient.clamp = True
    invert = sky_tree.nodes.new("ShaderNodeMath")
    invert.operation = "MULTIPLY"
    invert.inputs[1].default_value = -1
    sky_tree.links.new(separate.outputs["Z"], invert.inputs[0])
    sky_tree.links.new(invert.outputs[0], gradient.inputs["Value"])
    blend = sky_tree.nodes.new("ShaderNodeMixRGB")
    blend.inputs[1].default_value = (*base.rgb("e9eadc"), 1)
    blend.inputs[2].default_value = (*base.rgb("a9c8d2"), 1)
    sky_tree.links.new(gradient.outputs["Result"], blend.inputs[0])
    sky_tree.links.new(blend.outputs[0], sky_tree.nodes["Background"].inputs["Color"])
    if regional:
        background_color = sky_tree.nodes["Background"].inputs["Color"]
        for link in list(background_color.links):
            sky_tree.links.remove(link)
        background_color.default_value = (*base.rgb("f2ede0"),1)
        sky_tree.nodes["Background"].inputs["Strength"].default_value = 1
    mats = {name: base.material(name, color) for name, color in base.COLORS.items()}
    mats.update({name: base.material(name, color) for name, color in {"glass": "aacdd0", "skin": "d7aa87", "bark": "6d5c47", "pine": "527151", "grass": "839460", "stone": "c4baa8"}.items()})
    water_bsdf = mats["water"].node_tree.nodes.get("Principled BSDF")
    water_bsdf.inputs["Roughness"].default_value = .22
    water_bsdf.inputs["Metallic"].default_value = .22
    noise = mats["water"].node_tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = .25
    position = mats["water"].node_tree.nodes.new("ShaderNodeNewGeometry")
    mats["water"].node_tree.links.new(position.outputs["Position"], noise.inputs["Vector"])
    bump = mats["water"].node_tree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .1
    bump.inputs["Distance"].default_value = .06
    mats["water"].node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    mats["water"].node_tree.links.new(bump.outputs["Normal"], water_bsdf.inputs["Normal"])
    if far:
        far.build("Distant real mountain silhouettes", exclude=terrain, profile=profile)
    terrain.build("Regional terrain" if regional else "Thirty-metre scenic terrain",exclude=relief,edge_fade=regional,profile=profile)
    if relief is not None:
        relief.build("Photo-guided Seceda blades / artistic local reconstruction",profile=profile)
    lakes(payload, origin, terrain, mats)
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 15000))
    sun = bpy.context.object
    sun.rotation_euler = (math.radians(29), math.radians(-20), math.radians(-32))
    sun.data.energy = 1.55
    sun.data.angle = math.radians(7)
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = "PERSP"
    camera.data.lens = 38
    # A metre-scale near plane avoids depth fighting across kilometre-wide lakes.
    camera.data.clip_start = 500 if regional else 20 if shot["show_route"] else 2
    camera.data.clip_end = 1500000 if regional else 120000
    scene.camera = camera
    root, limbs = original_vehicle(leg["mode"], mats)
    if args.film and (shot["show_route"] or shot.get("weather") or shot["camera"] == "passenger_window" or shot.get("destination_camera") or shot.get("show_pair")):
        for child in root.children_recursive:
            child.hide_render = True
    if shot.get("ridge_camera") and (shot["ridge_camera"].get("passenger_view") or "lonlat" in shot["ridge_camera"]):
        for child in root.children_recursive:
            child.hide_render = True
    pair = scenery.WalkingPair(base,config["scenery"]["walking_pair"],terrain,part,at_distance) if profile and shot.get("show_pair") else None
    landmark_anchor = scenery.make_props(base,mesh_object,terrain,origin,shot,config["scenery"],initial,part) if profile else None
    atmosphere = scenery.Atmosphere(base,scene,sun,blend,terrain,landmark_anchor if landmark_anchor is not None else initial,profile,shot.get("destination_camera")) if profile else None
    endpoint_positions = {}
    for key, reference in [("from", shot["from_place"]), ("to", shot["to_place"])]:
        place = places[reference]
        xy = base.project(geometry["anchors"][key] if args.film else [place["longitude"], place["latitude"]])*1000-origin
        endpoint_positions[key] = np.array([*xy, float(terrain.sample(*xy))+10])
    if shot["show_route"]:
        aerial_parts = route_parts(leg,payload,terrain,origin,raw=geometry["lines"],step=250 if regional else 20) if args.film else parts[:1]
        span = np.linalg.norm(endpoint_positions["to"][:2]-endpoint_positions["from"][:2])
        width = max(1.5,span*.0007) if regional else 1.5
        for i,p in enumerate(aerial_parts):
            points = p["points"]+np.array([0,0,max(5,width*2)])
            base.line("Thin aerial route underlay",points,width*2,mats["cream"])
            mode = geometry["modes"][i] if args.film else leg["mode"]
            base.line("Thin aerial route",points+np.array([0,0,max(2,width*2)]),width,mats[mode])
    elif leg["mode"] == "hike":
        # This is the existing mapped trail, not a fabricated shortcut.
        vertices, faces = [], []
        for i, point in enumerate(part["points"]):
            other = part["points"][min(i+1, len(part["points"])-1)]-part["points"][max(i-1, 0)]
            normal = np.array([-other[1], other[0]])
            normal /= max(np.linalg.norm(normal), 1e-9)
            for side in [-1, 1]:
                xy = point[:2]+normal*side*.65
                vertices.append([*xy, float(terrain.sample(*xy))+.06])
            if i:
                faces.append((i*2-2, i*2-1, i*2+1, i*2))
        mesh_object("Mapped footpath / flat earth ribbon", vertices, faces, [mats["stone"]])
    elif leg["mode"] == "rail":
        center_distance = shot["fraction"]*part["length"]
        distances = np.arange(max(0, center_distance-100), min(part["length"], center_distance+220), 2)
        rail_points = []
        for distance in distances:
            point, tangent = at_distance(part, distance)
            normal = np.array([-tangent[1], tangent[0], 0])
            rail_points.append((point, normal))
        for side in [-1, 1]:
            base.line("Mapped railway / rail", [p+n*side*.7175+np.array([0, 0, .15]) for p, n in rail_points], .065, mats["dark"])
        sleeper_vertices, sleeper_faces = [], []
        for p, n in rail_points:
            tangent = np.array([n[1], -n[0], 0])
            start = len(sleeper_vertices)
            sleeper_vertices.extend([p+n*a+tangent*b for a, b in [(-1.25, -.13), (1.25, -.13), (1.25, .13), (-1.25, .13)]])
            sleeper_faces.append(tuple(range(start, start+4)))
        mesh_object("Original railway sleepers", sleeper_vertices, sleeper_faces, [mats["bark"]])
    elif leg["mode"] in ("bus","rideshare"):
        vertices,faces = [],[]
        for i,p in enumerate(part["points"]):
            other = part["points"][min(i+1,len(part["points"])-1)]-part["points"][max(i-1,0)]
            normal = np.array([-other[1],other[0]])
            normal /= max(np.linalg.norm(normal),1e-9)
            for side in (-1,1):
                xy = p[:2]+normal*side*2.4
                vertices.append([*xy,float(terrain.sample(*xy))+.05])
            if i:
                faces.append((i*2-2,i*2-1,i*2+1,i*2))
        road = base.material("Illustrative surface on the mapped road","96988b")
        mesh_object("Mapped road surface",vertices,faces,[road])
    if leg["mode"] == "cable_car":
        wire = part["points"]+np.array([0, 0, 4.2])
        base.line("Illustrative cable above mapped alignment", wire, .055, mats["dark"])
    if not shot["show_route"]:
        defaults = {"hike":([-15,-25,3.5],[0,180,55]),"rail":([300,-130,8],[0,100,85]),"bus":([35,-45,5],[0,100,45]),"rideshare":([28,-38,5],[0,100,45]),"cable_car":([65,-30,6],[0,180,55])}
        if args.film:
            defaults["cable_car"] = ([65,-30,6],[0,0,12])
        offset,target_offset = defaults[leg["mode"]]
        shot.setdefault("camera_offset_m",offset)
        shot.setdefault("look_offset_m",target_offset)
        shot.setdefault("lens_mm",28 if leg["mode"] != "hike" else 24)
        hint_offset = np.array(shot["camera_offset_m"],dtype=float)
        if shot.get("camera_axes") == "route":
            forward = initial_tangent.copy()
            forward[2] = 0
            forward /= max(np.linalg.norm(forward),1e-9)
            side = np.array([-forward[1],forward[0],0])
            candidates = [(float(terrain.sample(*(initial+sign*side*hint_offset[0]+forward*hint_offset[1])[:2])),sign) for sign in (1,-1)]
            sign = shot.get("camera_side",min(candidates)[1])
            shot["camera_offset_m"] = [hint_offset[0]*sign,hint_offset[1],hint_offset[2]]
            hint_offset = side*hint_offset[0]*sign+forward*hint_offset[1]+[0,0,hint_offset[2]]
        hint = initial+hint_offset
        end_hint = hint+initial_tangent*shot["speed_mps"]*shot["seconds"]
        if shot.get("destination_camera"):
            hint=landmark_anchor+np.array(shot["destination_camera"]["offset_m"])
            foreground(terrain,part,landmark_anchor,hint,mats,246,camera_end=hint)
        else:
            foreground(terrain,part,initial,hint,mats,246,camera_end=end_hint)
    output = directory / "frames" / shot["id"]
    output.mkdir(parents=True, exist_ok=True)
    total = int(shot["seconds"]*config["fps"])
    frames = [0,total//2,total-1] if args.audit else [total//2] if args.still else range(total)
    if args.limit:
        frames = list(frames)[:args.limit]
    records = []
    for frame in frames:
        seconds = frame/config["fps"]
        u = seconds/shot["seconds"]
        position, tangent = at_distance(part, shot["fraction"]*part["length"]+shot["speed_mps"]*seconds)
        root.location = position+np.array([0, 0, root["ground_offset"]])
        root.rotation_euler = Vector(tangent).to_track_quat("Y", "Z").to_euler()
        if leg["mode"] in ("hike", "cable_car"):
            root.rotation_euler = (0, 0, -math.atan2(tangent[0], tangent[1]))
        visual_lift = 0.
        if args.film and not shot["show_route"] and shot["camera"] != "passenger_window" and leg["mode"] in ("rail","bus","rideshare"):
            support = np.asarray(root["support_points"]).reshape(-1,3)*np.array(root.scale)
            forward = tangent[:2]/max(np.linalg.norm(tangent[:2]),1e-9)
            along = np.unique(support[:,1])
            sample_xy = position[:2]+along[:,None]*forward
            ground = terrain.sample(sample_xy[:,0],sample_xy[:,1])
            slope,intercept = np.polyfit(along,ground,1)
            # Average pitch over the fixed vehicle length rather than using a
            # single 4 m slope, which can tilt a carriage into the next DSM cell.
            root.rotation_euler = Vector([*forward,slope]).to_track_quat("Y","Z").to_euler()
            root.location.z = float(intercept)+root["ground_offset"]+.12
            support = support @ np.array(root.rotation_euler.to_matrix()).T+np.array(root.location)
            # Metre-scale vehicle models must not disappear into rough DSM
            # cells. This is display clearance, not a bridge or surveyed height.
            visual_lift = max(0.,float(np.max(terrain.sample(support[:,0],support[:,1])+.08-support[:,2])))
            root.location.z += visual_lift
        for limb, phase, amplitude in limbs:
            limb.rotation_euler.x = math.sin(seconds*6)*phase*amplitude
        walker_records = pair.update(shot["fraction"]*part["length"]+shot["speed_mps"]*seconds,shot["speed_mps"],seconds) if pair else []
        if args.film and shot["show_route"]:
            anchor = shot.get("anchor","both")
            if anchor == "both":
                center = (endpoint_positions["from"]+endpoint_positions["to"])/2
                distance = max(2200,np.linalg.norm(endpoint_positions["to"][:2]-endpoint_positions["from"][:2]))
                # Identical endpoints of the first/last shot make the cream fade loop cleanly.
                movement = 0 if shot["id"] in ("opening","ending") else u*.04
                camera.location = center+np.array([-distance*.1,-distance*1.2,distance*.8])*(1-movement)
                target = center+np.array([0,0,120])
                camera.data.lens = 34
            else:
                center = endpoint_positions[anchor]
                camera.location = center+np.array([-1250+u*40,-1350,980])
                camera.location.z = max(camera.location.z,float(terrain.sample(camera.location.x,camera.location.y))+400)
                target = center+np.array([160,80,100])
                camera.data.lens = 37
        elif shot["camera"] == "departure_aerial":
            start, end = endpoint_positions["from"], endpoint_positions["to"]
            center = (start+end)/2
            distance = np.linalg.norm(end[:2]-start[:2])
            offset = np.array([-distance*.1, -distance*1.2, distance*.8])*(1-u*.05)
            camera.location = center+offset
            target = center+np.array([0, 0, 120])
            camera.data.lens = 34
        elif shot["camera"] == "arrival_aerial":
            center = endpoint_positions["to"]
            camera.location = center+np.array([-1250+u*40, -1350, 980])
            target = center+np.array([230, 100, 100])
            camera.data.lens = 37
        else:
            camera_offset = np.array(shot["camera_offset_m"],dtype=float)
            look_offset = np.array(shot["look_offset_m"],dtype=float)
            if shot.get("camera_axes") == "route":
                forward = tangent.copy()
                forward[2] = 0
                forward /= max(np.linalg.norm(forward),1e-9)
                side = np.array([-forward[1],forward[0],0])
                camera_offset = side*camera_offset[0]+forward*camera_offset[1]+[0,0,camera_offset[2]]
                look_offset = side*look_offset[0]+forward*look_offset[1]+[0,0,look_offset[2]]
            desired = position+camera_offset
            if shot.get("camera_height_mode") == "terrain":
                desired[2] = float(terrain.sample(*desired[:2]))+shot["camera_offset_m"][2]
            desired[2] = max(desired[2], float(terrain.sample(*desired[:2]))+3)
            camera.location = desired
            target = position+look_offset
            if args.film and shot.get("camera_axes") == "route":
                horizon_lift = 2 if leg["mode"] == "cable_car" else 20
                target[2] = max(target[2],desired[2]+horizon_lift,float(terrain.sample(*target[:2]))+20)
            camera.data.lens = shot.get("lens_mm", 38)
        if shot.get("destination_camera"):
            setup=shot["destination_camera"]
            desired=landmark_anchor+np.array(setup["offset_m"])+np.array(setup["drift_m"])*u
            desired[2]=float(terrain.sample(*desired[:2]))+setup["offset_m"][2]
            camera.location=desired
            target=landmark_anchor+np.array(setup["look_offset_m"])
            camera.data.lens=shot["lens_mm"]
        if shot.get("ridge_camera"):
            setup=shot["ridge_camera"]
            if "lonlat" in setup:
                xy=base.project(setup["lonlat"])*1000-origin
                desired=np.array([*xy,float(terrain.sample(*xy))+setup["height_m"]])
                if "elevation_m" in setup:
                    desired[2]=setup["elevation_m"]
            else:
                desired=position+np.array(setup["offset_m"])
                desired[2]=max(desired[2],float(terrain.sample(*desired[:2]))+setup["offset_m"][2])
            desired+=np.array(setup["drift_m"])*u
            desired[2]=max(desired[2],float(terrain.sample(*desired[:2]))+3)
            camera.location=desired
            target=np.array([*(base.project(setup["target"]["lonlat"])*1000-origin),setup["target"]["elevation_m"]])
            camera.data.lens=setup["lens_mm"]
        if atmosphere:
            atmosphere.update(seconds,u)
        elif shot.get("weather"):
            cloud = min(1,max(0,(u-.2)/.35))
            sun.data.energy = 1.55-cloud*.9
            blend.inputs[2].default_value = (*((1-cloud)*np.array(base.rgb("a9c8d2"))+cloud*np.array(base.rgb("a6afab"))),1)
        camera.rotation_euler = (Vector(target)-camera.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        clearance = camera.location.z-float(terrain.sample(camera.location.x, camera.location.y))
        if clearance < 2.5:
            raise RuntimeError(f"Camera intersects terrain in {shot['id']} frame {frame}: {clearance}")
        if args.film and not regional:
            if not (terrain.x[0]+50 < camera.location.x < terrain.x[-1]-50 and terrain.y[0]+50 < camera.location.y < terrain.y[-1]-50):
                raise RuntimeError(f"Camera is too close to a terrain edge: {shot['id']}")
        labels = []
        for key in shot["endpoint_labels"]:
            screen = world_to_camera_view(scene, camera, Vector(endpoint_positions[key]))
            if screen.z > 0:
                labels.append({"text": places[shot[key+"_place"]]["name"], "kind": key,
                               "point": [float(screen.x*1280), float((1-screen.y)*960)]})
        projected = world_to_camera_view(scene, camera, Vector(position+np.array([0, 0, 1])))
        locator = None
        if args.film and regional and shot.get("leg_id"):
            # Regional orientation uses a small locator, never an enlarged train.
            # Select a disconnected part explicitly rather than bridging gaps.
            remaining = u*sum(p["length"] for p in aerial_parts)
            for route_part in aerial_parts:
                if remaining <= route_part["length"]:
                    break
                remaining -= route_part["length"]
            route_point,_ = at_distance(route_part,remaining)
            dot = world_to_camera_view(scene,camera,Vector(route_point+[0,0,20]))
            locator = [float(dot.x*1280),float((1-dot.y)*960)]
        elif shot["show_route"] and not args.film:
            locator = [float(projected.x*1280),float((1-projected.y)*960)]
        records.append({"frame": frame, "time": seconds, "camera_clearance_m": clearance,
                        "vehicle_visual_clearance_m": visual_lift,
                        "vehicle_scale": list(root.scale), "labels": labels,
                        "walkers": walker_records,
                        "vehicle_visible": not all(c.hide_render for c in root.children_recursive),
                        "atmosphere_3d": bool(atmosphere),
                        "mist_bands": atmosphere.mist_audit() if atmosphere else [],
                        "ridge_reveal_density_fraction": 1-float(scenery.smooth(seconds/profile["reveal_seconds"])) if profile and profile.get("reveal_seconds") else None,
                        "ridge_cloud_groups": atmosphere.ridge_cloud_audit() if atmosphere else [],
                        "seceda_relief": config.get("seceda_relief",{}).get("sha256") if relief else None,
                        "ridge_camera": {"position_m":list(camera.location),"target_m":list(target)} if shot.get("ridge_camera") else None,
                        "locator": locator,
                        "vehicle_screen": [float(projected.x*1280),float((1-projected.y)*960)],
                        "weather_progress":u if shot.get("weather") else None})
        scene.render.filepath = str(output / f"{frame:05}.png")
        if not args.audit or (args.still and (args.proof_sequence or frame == total//2)):
            bpy.ops.render.render(write_still=True)
        if frame % 24 == 0:
            print(f"FRAME {shot['id']} {frame}/{total}", flush=True)
    (output / "screen-labels.json").write_text(json.dumps({"shot": shot, "leg": leg, "records": records}, ensure_ascii=False))
    print(f"CINEMATIC_SHOT_COMPLETE {shot['id']} {len(records)} frames", flush=True)


def self_test():
    """Exercise actual Blender model/shader APIs without rendering a frame."""
    config = json.loads((ROOT / "config/journey-cinematic.json").read_text())
    mats = {name: base.material(name, color) for name, color in base.COLORS.items()}
    mats.update({"glass": base.material("Glass", "bed7d1"), "skin": base.material("Skin", "dcb28b")})
    for mode, expected in config["vehicle_dimensions_metres"].items():
        root, _ = original_vehicle(mode, mats)
        bpy.context.view_layer.update()
        bounds = np.array([tuple(child.matrix_world @ Vector(corner)) for child in root.children_recursive
                           if not child.hide_render for corner in child.bound_box])
        measured = bounds.max(axis=0)-bounds.min(axis=0)
        assert np.allclose(measured, expected, rtol=.015), (mode, measured, expected)
        print(f"FIXED_MODEL_METRES {mode}: {measured.tolist()}")
    terrain = Terrain.__new__(Terrain)
    terrain.x = terrain.y = np.array([-30., 0., 30.])
    terrain.z = np.array([[1000., 1002., 1004.]]*3)
    terrain.water = np.zeros((3, 3))
    terrain.forest = np.ones((3, 3))*100
    assert abs(float(terrain.sample(15, 0))-1003) < 1e-9
    terrain.build("Unit-test-only synthetic surface")
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = "PERSP"
    camera.data.lens = 38
    assert camera.data.type == "PERSP"
    print("CINEMATIC_BLENDER_CHECKS_OK; zero frames rendered")


if __name__ == "__main__":
    main()
