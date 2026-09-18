"""Local photo-guided relief, not higher-resolution survey data.

Immutable DEM anchors and a 30 m path corridor surround asymmetric blades.
Only shoulders are trimmed: no random peaks or global elevation scaling.
"""
import math
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

K = math.pi / 180 * 6371008.8


def project(points):
    return (np.asarray(points, dtype=float)-[9,47])*[K*math.cos(math.radians(47)),K]


def smooth(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)


def sample(x,y,z,xx,yy):
    i=np.clip(np.searchsorted(x,xx,side="right")-1,0,len(x)-2)
    j=np.clip(np.searchsorted(y,yy,side="right")-1,0,len(y)-2)
    a,b=(xx-x[i])/(x[i+1]-x[i]),(yy-y[j])/(y[j+1]-y[j])
    first=z[j,i]+a*(z[j,i+1]-z[j,i])+b*(z[j+1,i+1]-z[j,i+1])
    second=z[j,i]+a*(z[j+1,i+1]-z[j+1,i])+b*(z[j+1,i]-z[j,i])
    return np.where(a>=b,first,second)


def prepare(source,definition,lines,destination):
    data=np.load(source)
    x,y,z=data["x"]*1000,data["y"]*1000,data["z"]*1000
    west,south,east,north=definition["bounds"]
    bounds=project([[west,south],[east,north]])
    ix=np.flatnonzero((x>=bounds[0,0])&(x<=bounds[1,0]))
    iy=np.flatnonzero((y>=bounds[0,1])&(y<=bounds[1,1]))
    divisions=definition["subdivisions"]
    # Integer subdivisions retain original triangle planes around the paths.
    xx1=np.linspace(x[ix[0]],x[ix[-1]],(len(ix)-1)*divisions+1)
    yy1=np.linspace(y[iy[0]],y[iy[-1]],(len(iy)-1)*divisions+1)
    xx,yy=np.meshgrid(xx1,yy1)
    original=sample(x,y,z,xx,yy)
    anchors=project(definition["crest_anchors"])
    elevations=sample(x,y,z,anchors[:,0],anchors[:,1])
    # A continuous family of north/south sections avoids Voronoi seams at bends.
    # Choosing the nearest independent ridge segment caused discontinuous faces.
    assert np.all(np.diff(anchors[:,0])>0)
    lengths=np.r_[0,np.cumsum(np.linalg.norm(np.diff(anchors,axis=0),axis=1))]
    along=np.interp(xx,anchors[:,0],lengths)
    traversed=lengths[-1]
    crest_height=np.interp(xx,anchors[:,0],elevations)
    offset=yy-np.interp(xx,anchors[:,0],anchors[:,1])
    distance,side=np.abs(offset),np.sign(offset)
    tower=smooth((crest_height-2690)/230)
    cliff=2.8*np.minimum(distance,150)+.48*np.maximum(distance-150,0)
    apron=(.54+1.55*tower)*distance
    target=crest_height-np.where(side>0,cliff,apron)
    # Eroded channels follow the descent, with two incommensurate spacings.
    # They only cut rock below the crest; they cannot create extra summit spikes.
    grooves=(14*np.maximum(0,np.sin(along/29+.28*np.sin(distance/130)))**8+
             8*np.maximum(0,np.sin(along/61+distance/380))**12)
    target-=grooves*smooth(distance/35)*(1-smooth((distance-260)/280))*(side>0)
    delta=np.clip(target-original,-definition["maximum_carve_m"],0)
    edge=np.minimum.reduce([xx-xx1[0],xx1[-1]-xx,yy-yy1[0],yy1[-1]-yy])
    weight=smooth(edge/180)*(1-smooth((distance-360)/240))
    weight*=smooth(along/400)*smooth((traversed-along)/300)
    weight*=.92  # Retain a little of the measured face relief, not perfect planes.
    anchor_distance=cKDTree(anchors).query(np.column_stack([xx.ravel(),yy.ravel()]))[0].reshape(xx.shape)
    weight*=smooth((anchor_distance-12)/24)
    path_points=[]
    for line in lines:
        points=project(line)
        for a,b in zip(points,points[1:]):
            if max(a[0],b[0])<xx1[0]-100 or min(a[0],b[0])>xx1[-1]+100 or max(a[1],b[1])<yy1[0]-100 or min(a[1],b[1])>yy1[-1]+100:
                continue
            path_points.extend(np.linspace(a,b,max(2,math.ceil(np.linalg.norm(b-a)/2)+1)))
    assert path_points,"A geographic route buffer is required"
    path_distance=cKDTree(path_points).query(np.column_stack([xx.ravel(),yy.ravel()]))[0].reshape(xx.shape)
    weight*=smooth((path_distance-definition["protected_path_m"])/120)
    sculpted=original+delta*weight
    fields={key:sample(x,y,data[key],xx,yy) for key in ("water","forest")}
    assert np.max(abs((sculpted-original)[edge==0]))==0
    protected=path_distance<=definition["protected_path_m"]
    assert np.max(abs((sculpted-original)[protected]))==0
    before=sample(xx1,yy1,original,anchors[:,0],anchors[:,1])
    after=sample(xx1,yy1,sculpted,anchors[:,0],anchors[:,1])
    assert np.max(abs(after-before))<1e-6
    assert sculpted.max()<=original.max()+1e-6
    np.savez_compressed(Path(destination),x=xx1/1000,y=yy1/1000,z=sculpted/1000,**fields)
    return {"classification":"photo-guided artistic reconstruction, not new survey data",
        "shape":list(sculpted.shape),"spacing_m":[float(np.diff(xx1).mean()),float(np.diff(yy1).mean())],
        "height_scale":1,"maximum_lowering_m":float(np.max(original-sculpted)),
        "maximum_raising_m":float(np.max(sculpted-original)),"seam_error_m":0,
        "protected_path_m":definition["protected_path_m"],"path_height_error_m":0,
        "anchors":[{"lonlat":ll,"source_height_m":float(h),"render_height_m":float(v)} for ll,h,v in zip(definition["crest_anchors"],elevations,after)],
        "anchor_error_m":float(np.max(abs(after-elevations)))}
