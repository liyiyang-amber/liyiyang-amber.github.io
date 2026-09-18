"""Original, photo-guided Blender scenery for the approval-gated v3 film.

No photographic textures or third-party models. Coordinates are geographic;
building details, cloud placement and seasonal snow are explicitly illustrative.
"""
import math

import bpy
import numpy as np
from mathutils import Vector


def smooth(value):
    value = np.clip(value, 0, 1)
    return value * value * (3 - 2 * value)


def terrain_palette(terrain, xx, yy, profile, rgb):
    gy, gx = np.gradient(terrain.z, terrain.y, terrain.x)
    slope = np.hypot(gx, gy)
    stone = np.clip((terrain.z - 2050) / 820 + np.maximum(slope - .46, 0) * 1.2, 0, 1)
    if profile.get("ridge_material"):
        # Seceda's steep cliffs contrast with its grassy ridge; never change DEM heights.
        stone = np.maximum(np.clip((slope-.42)/.65, 0, 1), smooth((terrain.z-2460)/220))
    if profile.get("sculpted_ridge"):
        stone = np.maximum(smooth((slope-.48)/.65), smooth((terrain.z-2720)/180))
    # Spatially coherent bands reveal rocky cliffs without inventing peak shapes.
    variation = .5 + .25 * np.sin(xx / 83 + np.sin(yy / 117)) + .25 * np.sin(yy / 47 + terrain.z / 31)
    rock = np.array(rgb("aaa99e"))[None, None, :] * (.85 + variation[:, :, None] * .25)
    meadow = np.array(rgb("91a36a"))[None, None, :] * (.92 + variation[:, :, None] * .12)
    if profile.get("ridge_material"):
        rock = np.array(rgb("aaa9a5"))[None, None, :] * (.77 + variation[:, :, None] * .33)
        meadow = np.array(rgb("849b50"))[None, None, :] * (.9 + variation[:, :, None] * .16)
    if profile.get("sculpted_ridge"):
        layers=.5+.3*np.sin(terrain.z/11+xx/160-yy/210)+.2*np.sin(terrain.z/3+yy/250)
        rock=np.array(rgb("b6b0a4"))[None,None,:]*(.62+.38*layers[:,:,None])
    colors = meadow * (1-stone[:, :, None]) + rock * stone[:, :, None]
    forest = np.clip(terrain.forest / 255 * .6, 0, .6)[:, :, None]
    colors = colors * (1-forest) + np.array(rgb("456746")) * forest
    north = np.clip(gy / np.maximum(slope, .1), -1, 1)
    curvature = np.gradient(gx, terrain.x, axis=1) + np.gradient(gy, terrain.y, axis=0)
    gully = np.clip(curvature * 170, -.7, .7)
    threshold = profile["snowline_m"] - north * 170 - gully * 170 + (variation-.5) * 220
    accumulation = smooth((terrain.z-threshold) / (profile["snow_full_m"]-profile["snowline_m"]))
    retention = 1-smooth((slope-.45)/1.15)*.94
    snow = np.clip(accumulation * retention * (1-forest[:, :, 0]), 0, 1)
    if profile.get("ridge_material"):
        # Exposed convex crests stay bare; photo-inspired snow survives in gullies.
        snow *= np.clip(.2+gully*2,0,1)
    if profile.get("sculpted_ridge"):
        snow *= smooth((terrain.z-2540)/220)
    snow = smooth((snow-.14)/.7)[:, :, None]
    return colors * (1-snow) + np.array(rgb("f4f4eb")) * snow


def parent(name):
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    return root


def roof(base, mesh, name, width, length, eave, rise, material, root):
    w, l = width/2, length/2
    vertices = [(-w,-l,eave),(w,-l,eave),(0,-l,eave+rise),
                (-w,l,eave),(w,l,eave),(0,l,eave+rise)]
    ob = mesh(name, vertices, [(0,1,2),(3,5,4),(0,3,4,1),(0,2,5,3),(1,4,5,2)], [material])
    ob.parent = root
    return ob


def spire(mesh, name, position, profile, mat, root, facets=16):
    vertices = [(position[0]+r*math.cos(a), position[1]+r*math.sin(a), position[2]+z)
                for r,z in profile for a in np.linspace(0,2*math.pi,facets,endpoint=False)]
    faces = [(j*facets+i, j*facets+(i+1)%facets, (j+1)*facets+(i+1)%facets, (j+1)*facets+i)
             for j in range(len(profile)-1) for i in range(facets)]
    ob = mesh(name, vertices, faces, [mat])
    ob.parent = root
    return ob


def chalet(base, mesh, mats, name, xy, terrain, width=13, length=18, height=8, rotation=0):
    root = parent(name)
    # A modest embedded foundation avoids buildings floating on a sloping DEM.
    ground = float(terrain.sample(*xy))
    base.cube(name+" foundation", (0,0,-1), (width,length,3), mats["stone"], root, .1)
    base.cube(name+" plaster", (0,0,height/2), (width,length,height), mats["plaster"], root, .1)
    roof(base,mesh,name+" roof",width+2,length+2,height,3,mats["roof"],root)
    for side in (-1,1):
        for x in (-width*.28,width*.28):
            for z in (height*.35,height*.72):
                base.cube("Recessed timber window",(x,side*(length/2+.03),z),(1.25,.1,1.5),mats["wood"],root,.06)
                base.cube("Pale window glass",(x,side*(length/2+.11),z),(.8,.04,1.12),mats["glass"],root,.01)
    root.location = (*xy,ground)
    root.rotation_euler.z = rotation
    return root


def church(base, mesh, mats, landmark, xy, terrain):
    onion = landmark["model"] == "onion-church"
    root = parent("Geographic landmark / "+landmark["model"])
    wall = mats["pink"] if onion else mats["plaster"]
    w,l,h = (18,35,15) if onion else (12,23,11)
    base.cube("Church masonry",(0,0,h/2),(w,l,h),wall,root,.25)
    base.cube("Embedded church foundation",(0,0,-1.3),(w+1,l+1,4),mats["stone"],root,.15)
    roof(base,mesh,"Church nave pitched roof",w+1.2,l+1.5,h,7,mats["roof"],root)
    tx,ty = (-w*.46,-l*.30) if onion else (-w*.32,-l*.30)
    th,tw = (31,7) if onion else (24,5)
    base.cube("Church bell tower",(tx,ty,th/2),(tw,tw,th),wall,root,.14)
    for z in (th*.57,th*.84):
        base.cube("Tower pale cornice",(tx,ty,z),(tw+.65,tw+.65,.5),mats["plaster"],root,.06)
    for side in (-1,1):
        base.cube("Bell opening",(tx,ty+side*(tw/2+.02),th*.85),(tw*.35,.15,3.7),mats["wood"],root,.1)
        # Small dark dials and hands are original simplified geometry, not textures.
        dial = base.sphere("Clock dial",(tx,ty+side*(tw/2+.13),th*.66),(1.45,.08,1.45),mats["clock"],root)
        base.line("Clock hour hand",[(tx,ty+side*(tw/2+.23),th*.66),(tx+.6,ty+side*(tw/2+.23),th*.66+.4)],.065,mats["wood"],root)
        base.line("Clock minute hand",[(tx,ty+side*(tw/2+.24),th*.66),(tx,ty+side*(tw/2+.24),th*.66+1.05)],.05,mats["wood"],root)
    shape = [(3.8,0),(3.4,1.1),(4.7,3.3),(4.0,5.9),(1.8,8.0),(.45,10),(.08,12)] if onion else [(4,0),(.02,15)]
    spire(mesh,"Onion cupola" if onion else "Gothic pointed spire",(tx,ty,th),shape,mats["copper"] if onion else mats["roof"],root,16 if onion else 4)
    top = th+shape[-1][1]
    base.line("Tower cross",[(tx,ty,top),(tx,ty,top+2.5)],.12,mats["gold"],root)
    base.line("Cross arm",[(tx-.7,ty,top+1.7),(tx+.7,ty,top+1.7)],.1,mats["gold"],root)
    for side in (-1,1):
        for y in (-l*.18,l*.15,l*.35):
            base.cube("Tall church window",(side*(w/2+.03),y,h*.56),(.12,1.8,4.5),mats["wood"],root,.1)
    root.location = (*xy,float(terrain.sample(*xy)))
    root.rotation_euler.z = math.radians(landmark["rotation_degrees"])
    root["source_url"] = landmark["source_url"]
    return root


def make_props(base, mesh, terrain, origin, shot, config, center, part):
    mats = {name:base.material("Scenery / "+name,color) for name,color in {
        "plaster":"e5dcc2","pink":"ce9b92","roof":"696e64","copper":"915d4f",
        "wood":"4d4739","glass":"a5c4c4","clock":"e8d8a9","gold":"b69b58",
        "stone":"aaa291","flower":"e9d483","flower-white":"e5e3ce"}.items()}
    anchor = None
    if shot.get("full_scenery"):
        anchor = destination_props(base, mesh, mats, terrain, origin, shot, config, center)
        if not shot.get("show_pair"):
            return anchor
    if shot.get("landmark"):
        if shot.get("full_scenery"):
            return anchor
        definition = config["landmarks"][shot["landmark"]]
        xy = base.project(definition["lonlat"])*1000-origin
        ob = church(base,mesh,mats,definition,xy,terrain)
        anchor = np.array(ob.location)
        rng = np.random.default_rng(452)
        # Surrounding town/farm silhouettes are explicitly illustrative, not mapped buildings.
        town = definition["model"] == "onion-church"
        accepted = []
        for candidate in xy+rng.uniform([-500,-350],[500,450],size=(180,2)):
            if np.linalg.norm(candidate-xy) < 65 or any(np.linalg.norm(candidate-old)<34 for old in accepted):
                continue
            if terrain.sample(*candidate,terrain.water)>40 or np.linalg.norm(terrain.normal(*candidate)[:2]) > .48:
                continue
            if not town and terrain.sample(*candidate,terrain.forest)>80:
                continue
            chalet(base,mesh,mats,"Illustrative village house" if town else "Illustrative alpine farm",candidate,terrain,
                width=rng.uniform(10,17),length=rng.uniform(15,23),height=rng.uniform(7,12),rotation=rng.uniform(-.5,.5))
            accepted.append(candidate)
            if len(accepted) == (38 if town else 9):
                break
    # Wildflowers: a single batched mesh, never photographic ground texture.
    rng = np.random.default_rng(108)
    vertices,faces,indices = [],[],[]
    for xy in center[:2]+rng.uniform(-42,42,(2300,2)):
        if terrain.sample(*xy,terrain.water)>40 or np.min(np.linalg.norm(part["points"][::3,:2]-xy,axis=1))<1:
            continue
        z = float(terrain.sample(*xy))+rng.uniform(.12,.28)
        radius = rng.uniform(.04,.08)
        start = len(vertices)
        vertices.extend([(xy[0],xy[1],z)]+[(xy[0]+math.cos(a)*radius,xy[1]+math.sin(a)*radius,z+.015)
            for a in np.linspace(0,2*math.pi,6,endpoint=False)])
        for i in range(6):
            faces.append((start,start+1+i,start+1+(i+1)%6))
            indices.append(int(rng.random()<.3))
    mesh("Original meadow wildflowers",vertices,faces,[mats["flower"],mats["flower-white"]],indices)
    return anchor


def destination_props(base, mesh, mats, terrain, origin, shot, config, center):
    """Original destination silhouettes; only major anchors claim real positions."""
    kind = shot.get("scenery", "transport")
    if shot.get("station_lonlat"):
        xy = base.project(shot["station_lonlat"])*1000-origin
        definition = None
    elif shot.get("landmark"):
        definition = config["landmarks"][shot["landmark"]]
        xy = base.project(definition["lonlat"])*1000-origin
    elif shot.get("place_anchor"):
        xy = base.project(config["place_anchors"][shot["place_anchor"]])*1000-origin
        definition = None
    else:
        xy, definition = center[:2], None
    anchor = np.array([*xy, float(terrain.sample(*xy))])
    if kind in ("transport", "trail", "ridge-trail", "meadow-trail"):
        return None
    root = parent("Original destination / "+kind)
    root.location = anchor
    if kind == "lift-station":
        base.cube("Illustrative mapped cableway terminal",(0,0,4),(18,25,8),mats["stone"],root,.2)
        roof(base,mesh,"Mountain station roof",20,27,8,2,mats["roof"],root)
        base.cube("Station glazing",(0,-12.55,4.5),(14,.15,4.5),mats["glass"],root,.04)
        base.cube("Station entry opening",(0,-12.7,2.5),(4,.2,5),mats["wood"],root,.03)
    elif definition and definition["model"] in ("onion-church", "gothic-church"):
        church(base, mesh, mats, definition, xy, terrain)
    elif kind == "castle-vineyard":
        base.cube("Castle limestone keep", (0,0,17), (14,14,34), mats["stone"], root, .25)
        roof(base, mesh, "Castle steep keep roof", 17,17,34,12,mats["roof"],root)
        for x,y,w,l,h in [(-19,3,24,16,15),(12,12,18,23,13)]:
            wing=parent("Castle residential wing"); wing.parent=root; wing.location=(x,y,0)
            base.cube("Castle white walls",(0,0,h/2),(w,l,h),mats["plaster"],wing,.15)
            roof(base,mesh,"Castle wing roof",w+1,l+1,h,5,mats["roof"],wing)
            for u in range(-8,9,4):
                for z in (5,10):
                    base.cube("Castle timber window",(u,-l/2-.1,z),(1.6,.12,2.3),mats["wood"],wing,.03)
        vine=base.material("Illustrative vineyard foliage","628450")
        for row in range(14):
            points=[]
            for t in np.linspace(0,1,60):
                p=xy+[-140+t*170,-45-row*5]
                if terrain.sample(*p,terrain.water)>40 or terrain.lake_level(*p) is not None:
                    if len(points)>1:
                        base.line("Illustrative vineyard row",points,.25,vine)
                    points=[]
                    continue
                points.append((*p,float(terrain.sample(*p))+.8))
            if len(points)>1:
                base.line("Illustrative vineyard row",points,.25,vine)
    elif kind == "pastel-street":
        # 72 m original tower silhouette, placed on the actual OSM footprint.
        base.cube("White Tower stone shaft",(0,0,24),(10,10,48),mats["stone"],root,.14)
        spire(mesh,"White Tower pointed roof",(0,0,48),[(6.5,0),(.1,24)],mats["roof"],root,4)
        for side in (-1,1):
            base.cube("Clock surround",(0,side*5.1,32),(7,.2,7),mats["copper"],root,.04)
            base.sphere("Clock face",(0,side*5.25,32),(3,.1,3),mats["clock"],root)
            base.line("Clock long hand",[(0,side*5.4,32),(0,side*5.4,34.2)],.12,mats["wood"],root)
            base.line("Clock short hand",[(0,side*5.4,32),(1.6,side*5.4,32.7)],.12,mats["wood"],root)
            for u in (-1.6,1.6):
                base.cube("Gothic bell opening",(u,side*5.1,43),(1.6,.15,5),mats["wood"],root,.2)
        for i in range(12):
            # A deliberately illustrative street axis frames the mapped tower.
            p=xy+[-18 if i%2 else 18, 18+(i//2)*18]
            colors=["e4c6a2","c7cda7","ddc8b8","e6dcbf"]
            local={**mats,"plaster":base.material("Pastel facade",colors[i%4])}
            chalet(base,mesh,local,"Illustrative old-town facade",p,terrain,width=15,length=17,height=15+i%3*2)
    if kind == "town-flags":
        red=base.material("Swiss flag red","ac483d")
        for offset in [(-24,28),(20,30)]:
            p=xy+offset; z=float(terrain.sample(*p))
            base.line("Flagpole",[(*p,z),(*p,z+14)],.08,mats["stone"])
            base.cube("Original Swiss banner",(p[0]+.95,p[1],z+11),(1.9,.07,3.8),red,None,.02)
            base.cube("Flag cross vertical",(p[0]+.95,p[1]+.045,z+11),(.32,.03,1.7),mats["plaster"],None,0)
            base.cube("Flag cross horizontal",(p[0]+.95,p[1]+.047,z+11),(1.1,.03,.32),mats["plaster"],None,0)
    if kind == "waterfall-village":
        fall=config["landmarks"]["staubbachfall"]
        fp=base.project(fall["lonlat"])*1000-origin
        # Follow the actual DEM's cliff face eastward into the valley; the
        # painted-water ribbon is illustrative, not a new cliff mesh.
        points=[]
        for t in np.linspace(0,1,65):
            p=fp+[-70+190*t,0]
            points.append((*p,float(terrain.sample(*p))+3))
        foam=base.material("Staubbach water and spray","e4ede6")
        base.line("Mapped Staubbach cliff cascade",points,2.2,foam)
        for i in range(3):
            base.line("Separated waterfall spray",[(x,y+i*2-2,z+1) for x,y,z in points],.6,foam)
    if kind in ("alpine-village","waterfront","waterfall-village","town-flags","village-weather","castle-vineyard"):
        rng=np.random.default_rng(452)
        accepted=[]
        for candidate in xy+rng.uniform([-300,-230],[300,260],size=(240,2)):
            if np.linalg.norm(candidate-xy)<55 or any(np.linalg.norm(candidate-old)<32 for old in accepted):
                continue
            if terrain.sample(*candidate,terrain.water)>40 or np.linalg.norm(terrain.normal(*candidate)[:2])>.45:
                continue
            if terrain.sample(*candidate,terrain.forest)>100:
                continue
            if shot.get("destination_camera"):
                camera_xy=xy+np.array(shot["destination_camera"]["offset_m"][:2])
                delta=xy-camera_xy
                t=np.clip(np.dot(candidate-camera_xy,delta)/max(np.dot(delta,delta),1),0,1)
                if np.linalg.norm(candidate-camera_xy-t*delta)<23:
                    continue
            chalet(base,mesh,mats,"Illustrative chalet cluster",candidate,terrain,
                   width=rng.uniform(11,16),length=rng.uniform(15,20),height=rng.uniform(7,11),rotation=rng.uniform(-.4,.4))
            accepted.append(candidate)
            if len(accepted)>=22:
                break
    if shot.get("boats") or kind=="waterfront":
        rng=np.random.default_rng(502)
        count=0
        for candidate in xy+rng.uniform(-300,300,(600,2)):
            if terrain.sample(*candidate,terrain.water)<200:
                continue
            water_level=terrain.lake_level(*candidate)
            if water_level is None:
                continue
            boat=parent("Illustrative rowing boat on mapped lake")
            boat.location=(*candidate,float(water_level)+.15)
            boat.rotation_euler.z=rng.uniform(0,6.28)
            vertices=[(-.8,-2,0),(.8,-2,0),(1,1.2,0),(0,2.5,.2),(-1,1.2,0),
                      (-.45,-1.6,-.4),(.45,-1.6,-.4),(.5,1,-.4),(-.5,1,-.4)]
            hull=mesh("Original wooden boat hull",vertices,[(0,1,6,5),(1,2,7,6),(2,3,7),(3,4,8,7),(4,0,5,8),(5,6,7,8)],[mats["wood"]]); hull.parent=boat
            for y in (-.8,.5):
                base.cube("Rowing bench",(0,y,.08),(1.5,.28,.12),mats["plaster"],boat,.03)
            base.line("Oar",[(-2.2,-.3,.2),(2.2,.4,.2)],.05,mats["wood"],boat)
            count+=1
            if count>=6:
                break
    return anchor


def cloud(base, center, scale, density, index, elevation_band=None):
    """Bounded procedural volume with a soft edge; no screen-space cloud sprites."""
    bpy.ops.mesh.primitive_cube_add(size=2, location=center)
    ob = bpy.context.object
    ob.name = f"Localized 3D alpine mist {index}"
    ob.scale = scale
    mat = bpy.data.materials.new(ob.name)
    mat.use_nodes = True
    nodes,links = mat.node_tree.nodes,mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.inputs["Color"].default_value = (*base.rgb("ebeee9"),1)
    volume.inputs["Anisotropy"].default_value = .25
    coords = nodes.new("ShaderNodeTexCoord")
    subtract = nodes.new("ShaderNodeVectorMath"); subtract.operation="SUBTRACT"
    subtract.inputs[1].default_value=(.5,.5,.5)
    links.new(coords.outputs["Generated"],subtract.inputs[0])
    length=nodes.new("ShaderNodeVectorMath"); length.operation="LENGTH"
    links.new(subtract.outputs[0],length.inputs[0])
    falloff=nodes.new("ShaderNodeMapRange"); falloff.clamp=True
    falloff.inputs["From Min"].default_value=.10; falloff.inputs["From Max"].default_value=.5
    falloff.inputs["To Min"].default_value=1; falloff.inputs["To Max"].default_value=0
    links.new(length.outputs["Value"],falloff.inputs["Value"])
    noise=nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value=7; noise.inputs["Detail"].default_value=3
    links.new(coords.outputs["Generated"],noise.inputs["Vector"])
    multiply=nodes.new("ShaderNodeMath"); multiply.operation="MULTIPLY"
    links.new(noise.outputs["Fac"],multiply.inputs[0]); links.new(falloff.outputs["Result"],multiply.inputs[1])
    density_pattern=multiply.outputs[0]
    if elevation_band is not None:
        # World-space elevation stays fixed as the volume drifts. Mask both
        # scattering and its ambient fill, so no glow leaks below the cloud base.
        position=nodes.new("ShaderNodeNewGeometry")
        xyz=nodes.new("ShaderNodeSeparateXYZ")
        links.new(position.outputs["Position"],xyz.inputs[0])
        altitude=nodes.new("ShaderNodeMapRange")
        altitude.name="Upper-slope elevation mask"
        altitude.clamp=True
        altitude.interpolation_type="SMOOTHSTEP"
        altitude.inputs["From Min"].default_value=elevation_band[0]
        altitude.inputs["From Max"].default_value=elevation_band[1]
        altitude.inputs["To Min"].default_value=0
        altitude.inputs["To Max"].default_value=1
        links.new(xyz.outputs["Z"],altitude.inputs["Value"])
        masked=nodes.new("ShaderNodeMath"); masked.operation="MULTIPLY"
        links.new(density_pattern,masked.inputs[0])
        links.new(altitude.outputs["Result"],masked.inputs[1])
        density_pattern=masked.outputs[0]
    strength=nodes.new("ShaderNodeMath"); strength.operation="MULTIPLY"
    strength.inputs[1].default_value=density
    links.new(density_pattern,strength.inputs[0]); links.new(strength.outputs[0],volume.inputs["Density"])
    # EEVEE does not supply the overcast sky's ambient multiple scattering here.
    # Density-weighted fill approximates it without brightening empty space or
    # drawing a flat overlay; terrain occlusion and volume shadows remain real.
    ambient=nodes.new("ShaderNodeMath"); ambient.operation="MULTIPLY"
    ambient.inputs[1].default_value=.65
    links.new(strength.outputs[0],ambient.inputs[0])
    links.new(ambient.outputs[0],volume.inputs["Emission Strength"])
    volume.inputs["Emission Color"].default_value=(*base.rgb("e5ece8"),1)
    links.new(volume.outputs[0],output.inputs["Volume"])
    ob.data.materials.append(mat)
    return ob,strength


class Atmosphere:
    def __init__(self, base, scene, sun, sky, terrain, center, profile, destination_camera=None):
        self.base,self.scene,self.sun,self.sky,self.profile=base,scene,sun,sky,profile
        self.clouds=[]
        self.mist_bands=[]
        # Blender's 100 m default silently clips mountain-scale mist entirely.
        scene.eevee.use_volume_custom_range=True
        scene.eevee.volumetric_start=10
        scene.eevee.volumetric_end=16000
        scene.eevee.volumetric_samples=96
        scene.eevee.volumetric_sample_distribution=.5
        scene.eevee.use_volumetric_shadows=True
        scene.eevee.volumetric_shadow_samples=16
        scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value=profile["ambient"]
        # Light the matte terrain gently without dimming the visible blue sky.
        world=scene.world.node_tree
        visible_sky=world.nodes.new("ShaderNodeBackground")
        visible_sky.inputs["Strength"].default_value=1
        world.links.new(sky.outputs[0],visible_sky.inputs["Color"])
        light_path=world.nodes.new("ShaderNodeLightPath")
        mix=world.nodes.new("ShaderNodeMixShader")
        world.links.new(light_path.outputs["Is Camera Ray"],mix.inputs[0])
        world.links.new(world.nodes["Background"].outputs[0],mix.inputs[1])
        world.links.new(visible_sky.outputs[0],mix.inputs[2])
        world.links.new(mix.outputs[0],world.nodes["World Output"].inputs["Surface"])
        sky.inputs[1].default_value=(*base.rgb("b5d2dc"),1)
        sun.data.angle=math.radians(2.5)
        if profile.get("sun_rotation_degrees"):
            sun.rotation_euler=tuple(math.radians(v) for v in profile["sun_rotation_degrees"])
        if "ridge_clouds" in profile:
            for i,definition in enumerate(profile["ridge_clouds"]):
                ob,strength=cloud(base,definition["center_m"],definition["scale_m"],definition.get("density",profile["cloud_density"]),i)
                self.clouds.append((ob,strength,np.array(ob.location)))
            self.update(0,0)
            return
        # Changing valley mist sits on the hills, never across the foreground church.
        valley=profile.get("transition",False)
        clinging = profile["snowline_m"] > 2400
        placement=profile.get("mist_placement")
        if placement:
            assert valley and placement["kind"]=="upper-slopes" and destination_camera
            camera=center+np.array(destination_camera["offset_m"])
            camera[2]=float(terrain.sample(*camera[:2]))+destination_camera["offset_m"][2]
            target=center+np.array(destination_camera["look_offset_m"])
            bearing=math.atan2(target[0]-camera[0],target[1]-camera[1])
            distances=np.arange(*placement["ridge_distance_m"],placement["ridge_step_m"])
            for i,angle in enumerate(placement["ridge_ray_angles_degrees"]):
                theta=bearing+math.radians(angle)
                direction=np.array([math.sin(theta),math.cos(theta)])
                xy=camera[:2]+distances[:,None]*direction
                assert np.all((xy[:,0]>=terrain.x[0])&(xy[:,0]<=terrain.x[-1])&(xy[:,1]>=terrain.y[0])&(xy[:,1]<=terrain.y[-1]))
                heights=terrain.sample(xy[:,0],xy[:,1])
                # The maximum elevation angle is the visible skyline, not a
                # taller, hidden summit farther behind the foreground ridge.
                crest_index=int(np.argmax((heights-camera[2])/distances))
                crest=float(heights[crest_index])
                assert crest>center[2]+100
                band=[float(center[2]+(crest-center[2])*placement[key])
                      for key in ("zero_below_rise","full_above_rise")]
                anchor=camera[:2]+(xy[crest_index]-camera[:2])*placement["ridge_approach_fraction"]
                height=float(terrain.sample(*anchor))+placement["lift_m"]
                ob,strength=cloud(base,(*anchor,height),placement["volume_scale_m"],profile["cloud_density"],i,band)
                self.clouds.append((ob,strength,np.array(ob.location)))
                self.mist_bands.append({"church_elevation_m":float(center[2]),"ridge_elevation_m":crest,
                    "ridge_xy":xy[crest_index].tolist(),"zero_below_m":band[0],"full_above_m":band[1]})
            self.update(0,0)
            return
        locations = [(150,600,18),(620,950,22),(-530,850,25),(1100,1400,40)] if valley else [(900,-2000,20),(1200,-2800,40),(2600,-3300,55)] if clinging else [(1400,-1900,180),(-1800,-2600,240),(2500,600,150)]
        for i,(dx,dy,dz) in enumerate(locations):
            xy=center[:2]+[dx,dy]
            height=float(terrain.sample(*xy))+dz
            if not valley and not clinging:
                height=max(height,2700 if profile["snowline_m"]>2400 else 3100)
            ob,strength=cloud(base,(*xy,height),(620,290,210) if valley else (1000,460,220),profile["cloud_density"],i)
            self.clouds.append((ob,strength,np.array(ob.location)))
        self.update(0,0)

    def mist_audit(self):
        result=[]
        for band,(ob,_,_) in zip(self.mist_bands,self.clouds):
            node=ob.data.materials[0].node_tree.nodes["Upper-slope elevation mask"]
            low=float(node.inputs["From Min"].default_value)
            high=float(node.inputs["From Max"].default_value)
            probes=[band["church_elevation_m"],low-1,low,(low+high)/2,high]
            result.append({**band,"center_m":list(ob.location),"scale_m":list(ob.scale),
                "shader_zero_below_m":low,"shader_full_above_m":high,
                "mask_probes":[[z,float(smooth((z-low)/(high-low)))] for z in probes]})
        return result

    def ridge_cloud_audit(self):
        return [{"group":definition.get("group","reveal"),"density":float(strength.inputs[1].default_value),"center_m":list(ob.location),"scale_m":list(ob.scale)}
                for definition,(ob,strength,_) in zip(self.profile.get("ridge_clouds",[]),self.clouds)]

    def update(self,seconds,progress):
        p=self.profile
        if "ridge_clouds" in p:
            reveal=1-float(smooth(seconds/p["reveal_seconds"])) if p.get("reveal_seconds") else 0
            self.sun.data.energy=p["sun"]*(1-.12*reveal)
            self.sky.inputs[2].default_value=(*self.base.rgb(p["sky"]),1)
            for definition,(ob,strength,initial) in zip(p["ridge_clouds"],self.clouds):
                grouped = "group" in definition
                revealing = definition.get("group", "reveal") == "reveal"
                drift=float(smooth(seconds/p["reveal_seconds"])) if revealing and p.get("reveal_seconds") else seconds/4
                ob.location=initial+np.array(definition["drift_m"])*drift
                strength.inputs[1].default_value=definition.get("density",p["cloud_density"])*(reveal if revealing or not grouped else 1)
            return
        amount=float(smooth((progress-.2)/.65)) if p.get("transition") else .35
        self.sun.data.energy=p["sun"]*(1-.6*amount if p.get("transition") else 1)
        clear=np.array(self.base.rgb(p["sky"]))
        grey=np.array(self.base.rgb("bbc8c9"))
        self.sky.inputs[2].default_value=(*(clear*(1-amount*.65)+grey*(amount*.65)),1)
        for i,(ob,strength,initial) in enumerate(self.clouds):
            ob.location=initial+np.array([seconds*(5+i),seconds*2,math.sin(seconds*.3+i)*4])
            strength.inputs[1].default_value=p["cloud_density"]*(.06+amount*1.9 if p.get("transition") else 1)


def segment(base,name,mat,root,radius):
    ob=base.cube(name,(0,0,0),(1,1,1),mat,root,0)
    ob["radius"]=radius
    return ob


def connect(ob,a,b):
    a,b=Vector(a),Vector(b)
    ob.location=(a+b)/2
    ob.rotation_euler=(b-a).to_track_quat("Z","Y").to_euler()
    ob.scale=(ob["radius"],ob["radius"],(b-a).length)


class WalkingPair:
    def __init__(self,base,people,terrain,part,at_distance):
        self.base,self.terrain,self.part,self.at_distance=base,terrain,part,at_distance
        self.people=[]
        for index,person in enumerate(people):
            scale=person["height_m"]/1.75
            root=parent("Original adult "+person["id"])
            mats={k:base.material(person["id"]+" / "+k,c) for k,c in {
                "skin":"d9ad88","jacket":person["jacket"],"pack":person["pack"],"hair":person["hair"],
                "trousers":"414944","boot":"5b4637","eye":"342c24","cream":"ece4ce"}.items()}
            base.sphere("Jacket torso",(0,0,1.14*scale),(.235*scale,.15*scale,.32*scale),mats["jacket"],root)
            base.sphere("Head",(0,0,1.56*scale),(.145*scale,.14*scale,.17*scale),mats["skin"],root)
            base.sphere("Hair",(0,-.025*scale,1.67*scale),(.147*scale,.135*scale,.08*scale),mats["hair"],root)
            if person["id"]=="girl":
                tail=base.sphere("Ponytail",(0,-.20*scale,1.51*scale),(.075*scale,.10*scale,.22*scale),mats["hair"],root)
                tail.rotation_euler.x=-.3
            for side in (-1,1):
                base.sphere("Eye",(side*.052*scale,.132*scale,1.58*scale),(.013*scale,.018*scale,.013*scale),mats["eye"],root)
                base.line("Backpack shoulder strap",[(side*.14*scale,.14*scale,1.35*scale),(side*.16*scale,.16*scale,.97*scale)],.021*scale,mats["pack"],root)
            base.sphere("Nose",(0,.147*scale,1.54*scale),(.031*scale,.04*scale,.03*scale),mats["skin"],root)
            base.cube("Backpack",(0,-.205*scale,1.17*scale),(.35*scale,.18*scale,.43*scale),mats["pack"],root,.065)
            limbs=[]
            for side in (-1,1):
                thigh=segment(base,"Trouser thigh",mats["trousers"],root,.12*scale)
                shin=segment(base,"Trouser shin",mats["trousers"],root,.105*scale)
                arm=segment(base,"Jacket sleeve",mats["jacket"],root,.12*scale)
                forearm=segment(base,"Forearm",mats["jacket"],root,.10*scale)
                hand=base.sphere("Hand",(0,0,0),(.065*scale,)*3,mats["skin"],root)
                boot=base.cube("Walking boot",(0,0,0),(.15*scale,.29*scale,.12*scale),mats["boot"],root,.025)
                limbs.append((side,thigh,shin,arm,forearm,hand,boot))
            self.people.append(dict(root=root,limbs=limbs,scale=scale,person=person,index=index))

    def update(self,distance,speed,seconds):
        records=[]
        for person in self.people:
            root,scale=person["root"],person["scale"]
            d=distance-person["index"]*1.75
            position,tangent=self.at_distance(self.part,d)
            forward=tangent[:2]/max(np.linalg.norm(tangent[:2]),1e-9)
            right=np.array([forward[1],-forward[0]])
            ground=float(self.terrain.sample(*position[:2]))
            root.location=(*position[:2],ground)
            root.rotation_euler=(0,0,-math.atan2(forward[0],forward[1]))
            feet=[]
            for side,thigh,shin,arm,forearm,hand,boot in person["limbs"]:
                cycle=(seconds/1.0+person["person"]["phase"]+(0 if side==1 else .5))%1
                stride=speed*1.0
                if cycle<.62:
                    offset=(.31-cycle)*stride
                    lift=0
                else:
                    swing=(cycle-.62)/.38
                    offset=(-.31+.62*float(smooth(swing)))*stride
                    lift=math.sin(math.pi*swing)*.12*scale
                p,_=self.at_distance(self.part,d+offset)
                xy=p[:2]+right*side*.10*scale
                z=float(self.terrain.sample(*xy))+.06*scale+lift
                relative=xy-position[:2]
                foot=np.array([np.dot(relative,right),np.dot(relative,forward),z-ground])
                boot.location=foot+[0,.035*scale,0]
                ankle=foot+[0,0,.045*scale]
                hip=np.array([side*.10*scale,0,.87*scale])
                delta=ankle-hip
                length=np.linalg.norm(delta)
                direction=delta/max(length,1e-9)
                bend=np.array([0.,1.,0.])-direction*direction[1]
                bend/=max(np.linalg.norm(bend),1e-9)
                knee=(hip+ankle)/2+bend*math.sqrt(max((.46*scale)**2-(length/2)**2,.002))
                connect(thigh,hip,knee); connect(shin,knee,ankle)
                shoulder=np.array([side*.255*scale,0,1.33*scale])
                swing=math.sin(cycle*2*math.pi)*.18*scale
                elbow=shoulder+np.array([side*.015*scale,swing*.6,-.25*scale])
                wrist=elbow+np.array([0,swing*.6,-.22*scale])
                connect(arm,shoulder,elbow);connect(forearm,elbow,wrist);hand.location=wrist
                feet.append({"stance":cycle<.62,"sole_clearance_m":float(lift),"xy":xy.tolist()})
            records.append({"id":person["person"]["id"],"height_m":person["person"]["height_m"],"feet":feet,
                "position":list(root.location)})
        return records
